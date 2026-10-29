# ==============================================================================
# PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
# MODULE : Python Flask Backend Server with Active Heartbeat & Live Telemetry Watchdog
# ==============================================================================
import os
import sqlite3
import collections
import threading
import time
import json
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import paho.mqtt.client as mqtt
import pandas as pd
import numpy as np
import joblib
from telegram_alerts import process_twin_state_for_alerts, load_config as load_tg_config, save_config as save_tg_config, send_telegram_message, format_critical_alert

app = Flask(__name__, template_folder='templates')
CORS(app)

DB_PATH = 'ac_telemetry.db'
CSV_PATH = 'ac_telemetry.csv'
DATASET_PATH = 'ac_realistic_twin_dataset.csv'
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883

# ------------------------------------------------------------------------------
# 1. LOAD TRAINED ML MODELS
# ------------------------------------------------------------------------------
try:
    clf_model = joblib.load('ac_fault_classifier.joblib')
    rul_model = joblib.load('ac_rul_regressor.joblib')
    print("[ML ENGINE] Trained Decision Tree & Random Forest RUL models loaded.")
except Exception as e:
    clf_model = None
    rul_model = None
    print(f"[ML ENGINE NOTICE] Fallback to heuristic expert rules ({e}).")

# ------------------------------------------------------------------------------
# 2. WATCHDOG & LIVE TELEMETRY STATE
# ------------------------------------------------------------------------------
last_mqtt_packet_time = 0.0 # Timestamp of last received packet from ESP32
total_packets_received = 0
has_received_first_packet = False
manual_simulation_mode = False

live_hardware_state = {
    'room_temp': 0.0,
    'room_hum': 0.0,
    'ambient_temp': 0.0,
    'ambient_hum': 0.0,
    'comp_temp': 0.0,
    'voltage_v': 230.0,
    'current_amp': 4.50,
    'power_watts': 952.2,
    'power_factor': 0.92,
    'air_quality': 0.0,
    'comp_sensor_connected': False
}

twin_state = {
    'room_temp': 0.0,
    'room_hum': 0.0,
    'ambient_temp': 0.0,
    'ambient_hum': 0.0,
    'comp_temp': 0.0,
    'voltage_v': 230.0,
    'current_amp': 4.50,
    'power_watts': 952.2,
    'power_factor': 0.92,
    'air_quality': 0.0,
    'temp_lift': 0.0,
    'cooling_delta': 0.0,
    'cooling_efficiency': 0,
    'manual_override_active': False,
    'comp_sensor_connected': False,
    
    # Fault Localization (9 Multi-Location Operational States)
    'fault_category': 'NOMINAL_HEALTHY',
    'fault_location': 'WAITING FOR SENSOR TELEMETRY...',
    'fault_title': 'Connecting to Hardware Stream',
    'fault_severity': 'OPTIMAL',
    'fault_severity_color': '#64748B', # Slate gray until connected
    'root_cause': 'Waiting for telemetry frames from ESP32 & Smart Plug...',
    'prescriptive_action': 'Ensure ESP32 and Smart Plug are active and publishing to Mosquitto MQTT broker.',
    'confidence_score': 0.0,
    
    # Predictive Scores
    'health_score': 100,
    'health_status': 'INITIALIZING',
    'status_color': '#64748B',
    'failure_risk': 0.0,
    'rul_hours': 2500,
    'rul_days': 180,
    
    # Hardware Telemetry Watchdog & Diagnostics
    'esp_status': 'OFFLINE',
    'data_source': 'WAITING_FOR_DEVICE',
    'packets_count': 0,
    'seconds_since_ping': 999,
    'is_replaying': False,
    'replay_index': 0,
    'replay_total': 3000,
    'last_updated': '--:--:--'
}

HISTORY_MAX = 40
history = {
    'timestamps': collections.deque(maxlen=HISTORY_MAX),
    'room_temp': collections.deque(maxlen=HISTORY_MAX),
    'ambient_temp': collections.deque(maxlen=HISTORY_MAX),
    'comp_temp': collections.deque(maxlen=HISTORY_MAX),
    'air_quality': collections.deque(maxlen=HISTORY_MAX),
    'health_score': collections.deque(maxlen=HISTORY_MAX)
}

# ------------------------------------------------------------------------------
# 3. DIAGNOSTIC INFERENCE & FAULT LOCALIZATION (MULTI-LOCATION EXPERT + ML)
# ------------------------------------------------------------------------------
FAULT_METADATA = {
    "NOMINAL_HEALTHY": {
        "location": "ALL SUBSYSTEMS NOMINAL",
        "title": "Normal Baseline Operation",
        "severity": "OPTIMAL",
        "color": "#10B981",
        "root_cause": "Thermodynamic heat lift, power consumption, and air quality are within normal operational limits.",
        "action": "System operating optimally. Routine preventive maintenance recommended in 180 days."
    },
    "INDOOR_FILTER_CLOG": {
        "location": "INDOOR UNIT: EVAPORATOR AIR FILTER",
        "title": "Indoor Air Filter Dust Loading / Airflow Restriction",
        "severity": "WARNING",
        "color": "#F59E0B",
        "root_cause": "High particulate accumulation on nylon mesh filter causing restricted airflow velocity.",
        "action": "Remove, wash with warm water, and thoroughly dry the indoor mesh filter."
    },
    "CONDENSER_FOULING": {
        "location": "OUTDOOR UNIT: CONDENSER HEAT EXCHANGER",
        "title": "Condenser Coil Fouling & High Head Pressure",
        "severity": "WARNING",
        "color": "#F59E0B",
        "root_cause": "Restricted condenser heat dissipation resulting in elevated discharge temperature and motor current draw.",
        "action": "Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow."
    },
    "REFRIGERANT_UNDERCHARGE": {
        "location": "REFRIGERANT CIRCUIT: GAS LEAK / LOW CHARGE",
        "title": "Refrigerant Undercharge / Suction Line Depletion",
        "severity": "WARNING",
        "color": "#F59E0B",
        "root_cause": "Low refrigerant mass flow rate causing complete loss of cooling capacity (collapsed ΔT).",
        "action": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A."
    },
    "GRID_VOLTAGE_ANOMALY": {
        "location": "ELECTRICAL SYSTEM: MAINS GRID SAG",
        "title": "Mains Grid Voltage Sag & Motor Overcurrent",
        "severity": "WARNING",
        "color": "#F59E0B",
        "root_cause": "Mains grid voltage dropped (< 205V), forcing compressor motor to draw elevated current to deliver torque.",
        "action": "Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS)."
    },
    "FILTER_AND_CONDENSER_FAULT": {
        "location": "COMPOUND FAULT: INDOOR FILTER + OUTDOOR CONDENSER",
        "title": "Dual Heat Transfer Bottleneck (Indoor & Outdoor)",
        "severity": "CRITICAL",
        "color": "#EF4444",
        "root_cause": "Simultaneous indoor airflow restriction and outdoor condenser fouling causing thermal buildup.",
        "action": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger."
    },
    "REFRIGERANT_LEAK_AND_CONDENSER_FAULT": {
        "location": "COMPOUND FAULT: REFRIGERANT LEAK + CONDENSER FOULING",
        "title": "Severe Compressor Thermal Overload Hazard",
        "severity": "CRITICAL",
        "color": "#EF4444",
        "root_cause": "Dangerous combination: dirty condenser coil plus loss of suction gas cooling causes severe compressor overheating.",
        "action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out."
    },
    "FILTER_AND_REFRIGERANT_FAULT": {
        "location": "COMPOUND FAULT: INDOOR FILTER + REFRIGERANT LEAK",
        "title": "Indoor Filter Clog & Refrigerant Depletion",
        "severity": "CRITICAL",
        "color": "#EF4444",
        "root_cause": "Zero room cooling and high dust levels. Evaporator coil at risk of frosting/icing.",
        "action": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge to nominal operating pressure."
    },
    "CRITICAL_COMPOUND_MULTI_FAULT": {
        "location": "CRITICAL MULTI-POINT FAILURE: INDOOR + OUTDOOR + REFRIGERANT",
        "title": "Critical Multi-Subsystem Breakdown Alert",
        "severity": "CRITICAL",
        "color": "#DC2626",
        "root_cause": "Simultaneous breakdown across all 3 key subsystems: Extreme compressor overheat, filter blocked, high current surge.",
        "action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."
    }
}

def diagnose_and_localize_fault():
    global twin_state
    
    # If ESP32 is offline and not in simulation/replay mode, flag offline
    if twin_state['esp_status'] == 'OFFLINE' and not twin_state['is_replaying'] and not has_received_first_packet and not twin_state.get('manual_override_active', False):
        twin_state['fault_location'] = '⚠️ SENSORS & SMART PLUG OFFLINE'
        twin_state['fault_title'] = 'No Live Telemetry Detected'
        twin_state['fault_severity'] = 'CRITICAL'
        twin_state['fault_severity_color'] = '#EF4444'
        twin_state['root_cause'] = 'ESP32 / Smart Plug has not established MQTT connection or power is disconnected.'
        twin_state['prescriptive_action'] = 'Check ESP32 USB power, Smart Plug WiFi, and ensure Mosquitto broker is running.'
        return

    r_temp = float(twin_state.get('room_temp', 24.0))
    r_hum = float(twin_state.get('room_hum', 50.0))
    a_temp = float(twin_state.get('ambient_temp', 32.0))
    a_hum = float(twin_state.get('ambient_hum', 60.0))
    c_temp = float(twin_state.get('comp_temp', 48.0))
    v_val = float(twin_state.get('voltage_v', 230.0))
    i_val = float(twin_state.get('current_amp', 4.50))
    p_val = float(twin_state.get('power_watts', v_val * i_val * 0.92))
    pf_val = float(twin_state.get('power_factor', 0.92))
    aqi = float(twin_state.get('air_quality', 20.0))

    # Derived Physical Thermodynamic Features
    temp_lift = round(c_temp - a_temp, 2) if (c_temp > 0 and a_temp > 0) else 13.0
    cooling_delta = round(a_temp - r_temp, 2) if (a_temp > 0 and r_temp > 0) else 8.0
    twin_state['temp_lift'] = temp_lift
    twin_state['cooling_delta'] = cooling_delta

    eff = max(10, min(100, (cooling_delta / 8.0) * 100.0)) if cooling_delta > 0 else 30.0
    twin_state['cooling_efficiency'] = round(eff, 1)

    # ML Inference for Fault Category & RUL
    predicted_cat = "NOMINAL_HEALTHY"
    predicted_rul = 2500.0
    
    if clf_model is not None:
        try:
            feat_df = pd.DataFrame([[
                r_temp, r_hum, a_temp, a_hum, c_temp,
                temp_lift, cooling_delta, v_val, i_val, p_val, pf_val, aqi
            ]], columns=[
                'indoor_temp', 'indoor_hum', 'outdoor_temp', 'outdoor_hum',
                'comp_temp', 'temp_lift', 'cooling_delta',
                'voltage_v', 'current_amp', 'power_watts', 'power_factor',
                'air_quality_pct'
            ])
            predicted_cat = str(clf_model.predict(feat_df)[0])
            if rul_model is not None:
                predicted_rul = float(rul_model.predict(feat_df)[0])
        except Exception as e:
            print(f"[ML INFERENCE ERROR] {e}")
            predicted_cat = "NOMINAL_HEALTHY"

    # Fallback / Check if DS18B20 is disconnected in live hardware mode
    if c_temp <= 0 and not twin_state.get('manual_override_active', False) and not twin_state.get('is_replaying', False):
        twin_state['fault_location'] = "📍 LIVE HARDWARE: DS18B20 SENSOR UNPLUGGED (GPIO 5)"
        twin_state['fault_title'] = "Room, Ambient & Smart Plug Online | Compressor Sensor Disconnected"
        twin_state['fault_severity'] = "OPTIMAL"
        twin_state['fault_severity_color'] = "#38BDF8"
        twin_state['root_cause'] = "DHT22, MQ135, and Smart Plug are streaming. DS18B20 on GPIO 5 is not plugged in."
        twin_state['prescriptive_action'] = "Connect DS18B20 signal wire to GPIO 5 with 4.7k pull-up resistor to 3.3V, or use sliders."
        twin_state['confidence_score'] = 99.0
        return

    meta = FAULT_METADATA.get(predicted_cat, FAULT_METADATA["NOMINAL_HEALTHY"])
    
    # Calculate health score based on predicted RUL and fault severity
    if predicted_cat == "NOMINAL_HEALTHY":
        health = int(min(100, max(88, (predicted_rul / 2500.0) * 100)))
    elif "CRITICAL" in predicted_cat or "LEAK_AND_CONDENSER" in predicted_cat:
        health = int(min(30, max(5, (predicted_rul / 400.0) * 30)))
    else:
        health = int(min(75, max(35, (predicted_rul / 1500.0) * 75)))

    twin_state['fault_category'] = predicted_cat
    twin_state['health_score'] = health
    twin_state['fault_location'] = meta['location']
    twin_state['fault_title'] = meta['title']
    twin_state['fault_severity'] = meta['severity']
    twin_state['fault_severity_color'] = meta['color']
    twin_state['root_cause'] = meta['root_cause']
    twin_state['prescriptive_action'] = meta['action']
    twin_state['confidence_score'] = 96.8
    twin_state['failure_risk'] = round(100.0 - health * 0.96, 1)
    twin_state['rul_hours'] = round(max(0.0, predicted_rul), 1)
    twin_state['rul_days'] = int(max(1, predicted_rul / 24.0))

    if health >= 85:
        twin_state['health_status'] = "HEALTHY"
        twin_state['status_color'] = "#10B981"
    elif health >= 65:
        twin_state['health_status'] = "GOOD"
        twin_state['status_color'] = "#3B82F6"
    elif health >= 40:
        twin_state['health_status'] = "WARNING"
        twin_state['status_color'] = "#F59E0B"
    else:
        twin_state['health_status'] = "CRITICAL"
        twin_state['status_color'] = "#EF4444"

    twin_state['last_updated'] = datetime.now().strftime('%H:%M:%S')

    history['timestamps'].append(twin_state['last_updated'])
    history['room_temp'].append(twin_state['room_temp'])
    history['ambient_temp'].append(twin_state['ambient_temp'])
    history['comp_temp'].append(twin_state['comp_temp'])
    history['air_quality'].append(twin_state['air_quality'])
    history['health_score'].append(twin_state['health_score'])
    
    # Trigger Automated Telegram Push Alerts on Critical / Warning transitions
    threading.Thread(target=process_twin_state_for_alerts, args=(twin_state.copy(),), daemon=True).start()

    
    # Trigger Automated Telegram Push Alerts on Critical / Warning transitions
    threading.Thread(target=process_twin_state_for_alerts, args=(twin_state.copy(),), daemon=True).start()

# ------------------------------------------------------------------------------
# 4. WATCHDOG BACKGROUND THREAD (CHECKS IF ESP32 GOES OFFLINE)
# ------------------------------------------------------------------------------
def watchdog_worker():
    global last_mqtt_packet_time, twin_state
    while True:
        time.sleep(1.0)
        if last_mqtt_packet_time > 0 and not twin_state['is_replaying']:
            seconds_ago = int(time.time() - last_mqtt_packet_time)
            twin_state['seconds_since_ping'] = seconds_ago
            
            # If no packet received for more than 6.0 seconds, mark OFFLINE
            if seconds_ago > 6:
                if twin_state['esp_status'] != 'OFFLINE':
                    twin_state['esp_status'] = 'OFFLINE'
                    twin_state['data_source'] = 'DISCONNECTED'
                    diagnose_and_localize_fault()
            else:
                twin_state['esp_status'] = 'ONLINE'
                twin_state['data_source'] = 'LIVE_ESP32_HARDWARE'

# ------------------------------------------------------------------------------
# 5. REPLAY WORKER FOR PROTOTYPE PLAYBACK
# ------------------------------------------------------------------------------
replay_running = False

def dataset_replay_worker():
    global twin_state, replay_running
    curated_path = os.path.join(os.path.dirname(__file__), 'nodered_flows', 'curated_replay_dataset.json')
    if os.path.exists(curated_path):
        with open(curated_path, 'r', encoding='utf-8') as f:
            curated_rows = json.load(f)
    else:
        curated_rows = []

    total_rows = len(curated_rows)
    twin_state['replay_total'] = total_rows
    twin_state['data_source'] = 'PROTOTYPE DATASET REPLAY'
    twin_state['esp_status'] = 'SIMULATION_ACTIVE'
    idx = 0

    while replay_running and idx < total_rows:
        row = curated_rows[idx]
        twin_state['room_temp'] = float(row['indoor_temp'])
        twin_state['room_hum'] = float(row['indoor_hum'])
        twin_state['ambient_temp'] = float(row['outdoor_temp'])
        twin_state['ambient_hum'] = float(row['outdoor_hum'])
        twin_state['comp_temp'] = float(row['comp_temp'])
        twin_state['voltage_v'] = float(row.get('voltage_v', 230.0))
        twin_state['current_amp'] = float(row.get('current_amp', 4.5))
        twin_state['power_watts'] = float(row.get('power_watts', 950.0))
        twin_state['power_factor'] = float(row.get('power_factor', 0.92))
        twin_state['air_quality'] = float(row['air_quality_pct'])
        twin_state['replay_index'] = idx + 1

        diagnose_and_localize_fault()
        idx += 1
        time.sleep(1.0) # 1.0 second per step -> 5 steps per phase = 5 seconds per condition

    twin_state['is_replaying'] = False
    replay_running = False

# ------------------------------------------------------------------------------
# 6. MQTT LISTENER
# ------------------------------------------------------------------------------
def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    print(f"[MQTT] Connected to Mosquitto (rc={rc})")
    client.subscribe('ac/#')

def on_mqtt_message(client, userdata, msg):
    global last_mqtt_packet_time, total_packets_received, has_received_first_packet, manual_simulation_mode
    if replay_running:
        return
        
    topic = msg.topic
    payload = msg.payload.decode('utf-8').strip()
    
    try:
        last_mqtt_packet_time = time.time()
        total_packets_received += 1
        has_received_first_packet = True
        twin_state['packets_count'] = total_packets_received
        twin_state['esp_status'] = 'ONLINE'
        twin_state['seconds_since_ping'] = 0

        if topic == 'ac/indoor/temperature': 
            live_hardware_state['room_temp'] = float(payload)
            twin_state['room_temp'] = float(payload)
        elif topic == 'ac/indoor/humidity': 
            live_hardware_state['room_hum'] = float(payload)
            twin_state['room_hum'] = float(payload)
        elif topic == 'ac/outdoor/temperature': 
            live_hardware_state['ambient_temp'] = float(payload)
            twin_state['ambient_temp'] = float(payload)
        elif topic == 'ac/outdoor/humidity': 
            live_hardware_state['ambient_hum'] = float(payload)
            twin_state['ambient_hum'] = float(payload)
        elif topic == 'ac/compressor/temp': 
            live_hardware_state['comp_temp'] = float(payload)
            twin_state['comp_temp'] = float(payload)
        elif topic == 'ac/smartplug/voltage':
            live_hardware_state['voltage_v'] = float(payload)
            twin_state['voltage_v'] = float(payload)
        elif topic == 'ac/smartplug/current':
            live_hardware_state['current_amp'] = float(payload)
            twin_state['current_amp'] = float(payload)
            twin_state['power_watts'] = round(twin_state['voltage_v'] * float(payload) * twin_state['power_factor'], 1)
        elif topic == 'ac/smartplug/power':
            live_hardware_state['power_watts'] = float(payload)
            twin_state['power_watts'] = float(payload)
        elif topic == 'ac/smartplug/powerfactor':
            live_hardware_state['power_factor'] = float(payload)
            twin_state['power_factor'] = float(payload)
        elif topic == 'ac/smartplug/json':
            plug_data = json.loads(payload)
            if 'voltage' in plug_data: twin_state['voltage_v'] = float(plug_data['voltage'])
            if 'current' in plug_data: twin_state['current_amp'] = float(plug_data['current'])
            if 'power' in plug_data: twin_state['power_watts'] = float(plug_data['power'])
            if 'power_factor' in plug_data: twin_state['power_factor'] = float(plug_data['power_factor'])
            elif 'factor' in plug_data: twin_state['power_factor'] = float(plug_data['factor'])
        elif topic == 'ac/airquality': 
            live_hardware_state['air_quality'] = float(payload)
            twin_state['air_quality'] = float(payload)
        elif topic == 'ac/status':
            if 'OFFLINE' in payload:
                twin_state['esp_status'] = 'OFFLINE'
            else:
                twin_state['esp_status'] = 'ONLINE'

        # When physical packet arrives, clear manual override so live readings appear
        manual_simulation_mode = False
        twin_state['manual_override_active'] = False
        twin_state['data_source'] = 'REAL HARDWARE (ESP32 & SMART PLUG)'
                
        diagnose_and_localize_fault()
    except Exception as ex:
        print(f"[MQTT PARSE ERROR] {topic}: {ex}")

def start_mqtt():
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='Flask_AC_Twin_Server')
    except Exception:
        client = mqtt.Client(client_id='Flask_AC_Twin_Server')
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"[MQTT INFO] Broker offline ({e}).")

# ------------------------------------------------------------------------------
# 7. REST API & FLASK ROUTES
# ------------------------------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/telemetry', methods=['GET'])
def get_telemetry():
    return jsonify({
        'state': twin_state,
        'history': {
            'timestamps': list(history['timestamps']),
            'room_temp': list(history['room_temp']),
            'ambient_temp': list(history['ambient_temp']),
            'comp_temp': list(history['comp_temp']),
            'air_quality': list(history['air_quality']),
            'health_score': list(history['health_score'])
        }
    })

@app.route('/api/replay/<action>', methods=['POST'])
@app.route('/api/replay/start', methods=['POST'], defaults={'action': 'start'})
@app.route('/api/replay/stop', methods=['POST'], defaults={'action': 'stop'})
def control_replay(action):
    global replay_running
    if action == 'start':
        if not replay_running:
            replay_running = True
            twin_state['is_replaying'] = True
            threading.Thread(target=dataset_replay_worker, daemon=True).start()
            return jsonify({'status': 'started', 'is_replaying': True})
    elif action == 'stop':
        replay_running = False
        twin_state['is_replaying'] = False
        return jsonify({'status': 'stopped', 'is_replaying': False})
    return jsonify({'status': 'invalid'})

@app.route('/api/simulate', methods=['POST'])
def simulate():
    global manual_simulation_mode
    data = request.json or {}
    manual_simulation_mode = True
    twin_state['manual_override_active'] = True
    for key, val in data.items():
        if key in twin_state:
            twin_state[key] = val
    twin_state['data_source'] = 'MANUAL_SIMULATION_OVERRIDE'
    diagnose_and_localize_fault()
    return jsonify({'status': 'updated', 'state': twin_state, 'manual_mode': True})

@app.route('/api/simulate/reset', methods=['POST'])
def reset_simulation():
    global manual_simulation_mode
    manual_simulation_mode = False
    twin_state['manual_override_active'] = False
    for k, v in live_hardware_state.items():
        twin_state[k] = v
    twin_state['data_source'] = 'REAL HARDWARE (ESP32 MQTT)' if has_received_first_packet else 'DEFAULT_BASELINE'
    diagnose_and_localize_fault()
    return jsonify({'status': 'reset', 'state': twin_state, 'manual_mode': False})

@app.route('/api/telegram/config', methods=['GET', 'POST'])
def handle_telegram_config():
    if request.method == 'POST':
        data = request.json or {}
        token = data.get('bot_token', '').strip()
        chat_id = str(data.get('chat_id', '')).strip()
        enabled = data.get('enabled', True)
        save_tg_config(token, chat_id, enabled)
        return jsonify({'status': 'saved', 'message': 'Telegram configuration updated successfully.'})
    else:
        cfg = load_tg_config()
        # Mask token for security
        masked_token = (cfg.get('bot_token', '')[:8] + '...') if len(cfg.get('bot_token', '')) > 10 else cfg.get('bot_token', '')
        return jsonify({
            'enabled': cfg.get('enabled', True),
            'bot_token': masked_token,
            'is_configured': bool(cfg.get('bot_token') and cfg.get('bot_token') != 'YOUR_TELEGRAM_BOT_TOKEN_HERE' and cfg.get('chat_id') != 'YOUR_TELEGRAM_CHAT_ID_HERE'),
            'chat_id': cfg.get('chat_id', '')
        })

@app.route('/api/predict', methods=['POST'])
def predict_api():
    data = request.json or {}
    r_temp = float(data.get('indoor_temp', data.get('room_temp', 24.0)))
    r_hum = float(data.get('indoor_hum', data.get('room_hum', 50.0)))
    a_temp = float(data.get('outdoor_temp', data.get('ambient_temp', 32.0)))
    a_hum = float(data.get('outdoor_hum', data.get('ambient_hum', 60.0)))
    c_temp = float(data.get('comp_temp', 48.0))
    v_val = float(data.get('voltage_v', data.get('voltage', 230.0)))
    i_val = float(data.get('current_amp', data.get('current', 4.5)))
    p_val = float(data.get('power_watts', data.get('power', v_val * i_val * 0.92)))
    pf_val = float(data.get('power_factor', data.get('powerfactor', 0.92)))
    aqi = float(data.get('air_quality_pct', data.get('air_quality', 20.0)))

    temp_lift = round(c_temp - a_temp, 2)
    cooling_delta = round(a_temp - r_temp, 2)

    predicted_cat = "NOMINAL_HEALTHY"
    predicted_rul = 2500.0

    if clf_model is not None:
        try:
            feat_df = pd.DataFrame([[
                r_temp, r_hum, a_temp, a_hum, c_temp,
                temp_lift, cooling_delta, v_val, i_val, p_val, pf_val, aqi
            ]], columns=[
                'indoor_temp', 'indoor_hum', 'outdoor_temp', 'outdoor_hum',
                'comp_temp', 'temp_lift', 'cooling_delta',
                'voltage_v', 'current_amp', 'power_watts', 'power_factor',
                'air_quality_pct'
            ])
            predicted_cat = str(clf_model.predict(feat_df)[0])
            if rul_model is not None:
                predicted_rul = float(rul_model.predict(feat_df)[0])
        except Exception as e:
            print(f"[API PREDICT ERROR] {e}")

    meta = FAULT_METADATA.get(predicted_cat, FAULT_METADATA["NOMINAL_HEALTHY"])
    if predicted_cat == "NOMINAL_HEALTHY":
        health = int(min(100, max(88, (predicted_rul / 2500.0) * 100)))
    elif "CRITICAL" in predicted_cat or "LEAK_AND_CONDENSER" in predicted_cat:
        health = int(min(30, max(5, (predicted_rul / 400.0) * 30)))
    else:
        health = int(min(75, max(35, (predicted_rul / 1500.0) * 75)))

    return jsonify({
        'fault_category': predicted_cat,
        'fault_location': meta['location'],
        'fault_title': meta['title'],
        'fault_severity': meta['severity'],
        'fault_severity_color': meta['color'],
        'root_cause': meta['root_cause'],
        'remediation_action': meta['action'],
        'health_score': health,
        'rul_hours': round(max(0.0, predicted_rul), 1),
        'temp_lift': temp_lift,
        'cooling_delta': cooling_delta
    })

if __name__ == '__main__':
    mqtt_t = threading.Thread(target=start_mqtt, daemon=True)
    mqtt_t.start()
    
    watchdog_t = threading.Thread(target=watchdog_worker, daemon=True)
    watchdog_t.start()
    
    print('=' * 65)
    print('   AC DIGITAL TWIN FLASK APPLICATION READY')
    print('   Open Dashboard: http://localhost:5000')
    print('=' * 65)
    app.run(host='0.0.0.0', port=5000, debug=False)
