import json
import os

html_path = r"C:\Users\dhara\.gemini\antigravity\scratch\ac_digital_twin\templates\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

curated_path = r"C:\Users\dhara\.gemini\antigravity\scratch\ac_digital_twin\nodered_flows\curated_replay_dataset.json"
with open(curated_path, "r", encoding="utf-8") as f:
    curated_dataset = json.load(f)

curated_json_str = json.dumps(curated_dataset)

flow_nodes = [
    {
        "id": "ac_twin_tab",
        "type": "tab",
        "label": "AC Digital Twin Dashboard",
        "disabled": False,
        "info": "Complete Attractive AC Digital Twin Dashboard & Fault Localization Engine"
    },
    {
        "id": "mqtt_broker_local",
        "type": "mqtt-broker",
        "name": "Mosquitto Broker (1883)",
        "broker": "localhost",
        "port": "1883",
        "clientid": "NodeRED_AC_DigitalTwin_Server",
        "autoConnect": True,
        "usetls": False,
        "protocolVersion": "4",
        "keepalive": "60",
        "cleansession": True,
        "autoUnsubscribe": True
    },
    {
        "id": "mqtt_sub_all",
        "type": "mqtt in",
        "z": "ac_twin_tab",
        "name": "ESP32 Telemetry (ac/#)",
        "topic": "ac/#",
        "qos": "0",
        "datatype": "utf8",
        "broker": "mqtt_broker_local",
        "nl": False,
        "rap": True,
        "rh": 0,
        "inputs": 0,
        "x": 160,
        "y": 140,
        "wires": [
            ["twin_engine_fn"]
        ]
    },
    {
        "id": "watchdog_timer",
        "type": "inject",
        "z": "ac_twin_tab",
        "name": "1-Sec Watchdog Heartbeat",
        "props": [
            {"p": "topic", "vt": "str", "v": "system/watchdog"}
        ],
        "repeat": "1",
        "crontab": "",
        "once": True,
        "onceDelay": 0.1,
        "topic": "system/watchdog",
        "x": 170,
        "y": 200,
        "wires": [
            ["twin_engine_fn"]
        ]
    },
    {
        "id": "twin_engine_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Digital Twin Engine & Fault Localization",
        "func": f"""// 45-Sample Curated Prototype Dataset (9 Phases, 5 Seconds Each)
const DATASET_ROWS = {curated_json_str};

let twin = global.get('twin_state') || {{
    room_temp: null,
    room_hum: null,
    ambient_temp: null,
    ambient_hum: null,
    comp_temp: null,
    voltage_v: null,
    current_amp: null,
    power_watts: null,
    power_factor: null,
    air_quality: null,
    vibration: 'DISCONNECTED',
    
    room_sensor_connected: false,
    ambient_sensor_connected: false,
    comp_sensor_connected: false,
    smartplug_connected: false,
    aqi_sensor_connected: false,
    vibration_sensor_connected: false,
    
    last_room_packet_time: 0,
    last_ambient_packet_time: 0,
    last_comp_packet_time: 0,
    last_smartplug_packet_time: 0,
    last_aqi_packet_time: 0,
    last_vibration_packet_time: 0,

    temp_lift: null,
    cooling_delta: null,
    cooling_efficiency: null,
    fault_category: 'OFFLINE',
    fault_location: '⚠️ SENSORS & SMART PLUG OFFLINE',
    fault_title: 'Awaiting Telemetry Stream',
    fault_severity: 'CRITICAL',
    fault_severity_color: '#EF4444',
    root_cause: 'ESP32 microcontroller and 16A Smart Plug are disconnected. Showing NOT CONNECTED on all sensor channels.',
    prescriptive_action: 'Power on ESP32 & Smart Plug, or click Play Prototype Dataset below to begin simulation.',
    confidence_score: null,
    health_score: null,
    health_status: 'OFFLINE',
    status_color: '#94A3B8',
    failure_risk: null,
    rul_hours: null,
    esp_status: 'OFFLINE',
    data_source: 'WAITING FOR SENSORS',
    packets_count: 0,
    seconds_since_ping: 999,
    last_packet_time: 0,
    is_replaying: false,
    replay_index: 0,
    replay_total: DATASET_ROWS.length,
    manual_override_active: false,
    last_updated: '--:--:--'
}};

let history = global.get('twin_history') || {{
    timestamps: [],
    comp_temp: [],
    ambient_temp: [],
    room_temp: [],
    health_score: [],
    air_quality: []
}};

let topic = msg.topic;
let payload = msg.payload;
let now = Date.now();

// 1. Process Real Hardware ESP32 & Smart Plug MQTT Telemetry
if (topic && topic.startsWith('ac/')) {{
    twin.last_packet_time = now;
    twin.packets_count = (twin.packets_count || 0) + 1;
    twin.esp_status = 'ONLINE';
    twin.seconds_since_ping = 0;
    
    if (!twin.is_replaying && !twin.manual_override_active) {{
        twin.data_source = 'REAL HARDWARE (ESP32 & SMART PLUG)';

        let strVal = String(payload || '').trim().toUpperCase();
        let val = parseFloat(payload);

        // DHT22 #1: Room Temperature & Humidity (GPIO 4)
        if (topic === 'ac/indoor/temperature') {{
            if (strVal === 'ERROR' || strVal === 'DISCONNECTED' || isNaN(val)) {{
                twin.room_temp = null;
                twin.room_sensor_connected = false;
                twin.last_room_packet_time = 0;
            }} else {{
                twin.room_temp = val;
                twin.room_sensor_connected = true;
                twin.last_room_packet_time = now;
            }}
        }}
        else if (topic === 'ac/indoor/humidity') {{
            if (!isNaN(val)) twin.room_hum = val;
        }}
        // DHT22 #2: Ambient Temperature & Humidity (GPIO 18)
        else if (topic === 'ac/outdoor/temperature') {{
            if (strVal === 'ERROR' || strVal === 'DISCONNECTED' || isNaN(val)) {{
                twin.ambient_temp = null;
                twin.ambient_sensor_connected = false;
                twin.last_ambient_packet_time = 0;
            }} else {{
                twin.ambient_temp = val;
                twin.ambient_sensor_connected = true;
                twin.last_ambient_packet_time = now;
            }}
        }}
        else if (topic === 'ac/outdoor/humidity') {{
            if (!isNaN(val)) twin.ambient_hum = val;
        }}
        // DS18B20: Compressor Dome Temperature (GPIO 5)
        else if (topic === 'ac/compressor/temp') {{
            if (strVal === 'ERROR' || strVal === 'DISCONNECTED' || isNaN(val) || val < -40 || val > 150) {{
                twin.comp_temp = null;
                twin.comp_sensor_connected = false;
                twin.last_comp_packet_time = 0;
            }} else {{
                twin.comp_temp = val;
                twin.comp_sensor_connected = true;
                twin.last_comp_packet_time = now;
            }}
        }}
        // SW-420: Mechanical Vibration Switch (GPIO 27)
        else if (topic === 'ac/vibration') {{
            if (strVal === 'DISCONNECTED' || strVal === 'ERROR') {{
                twin.vibration = 'DISCONNECTED';
                twin.vibration_sensor_connected = false;
                twin.last_vibration_packet_time = 0;
            }} else if (strVal === 'DETECTED' || strVal === '1' || strVal === 'HIGH' || strVal === 'VIBRATION DETECTED') {{
                twin.vibration = 'VIBRATION DETECTED';
                twin.vibration_sensor_connected = true;
                twin.last_vibration_packet_time = now;
            }} else {{
                twin.vibration = 'NORMAL';
                twin.vibration_sensor_connected = true;
                twin.last_vibration_packet_time = now;
            }}
        }}
        // MQ135: Air Quality (GPIO 34)
        else if (topic === 'ac/airquality') {{
            if (strVal === 'ERROR' || strVal === 'DISCONNECTED' || isNaN(val)) {{
                twin.air_quality = null;
                twin.aqi_sensor_connected = false;
                twin.last_aqi_packet_time = 0;
            }} else {{
                twin.air_quality = val;
                twin.aqi_sensor_connected = true;
                twin.last_aqi_packet_time = now;
            }}
        }}
        // 16A Smart Plug Telemetry (WiFi)
        else if (topic === 'ac/smartplug/voltage') {{
            if (!isNaN(val) && val > 0) {{
                twin.voltage_v = val;
                twin.smartplug_connected = true;
                twin.last_smartplug_packet_time = now;
            }} else {{
                twin.voltage_v = null;
            }}
        }}
        else if (topic === 'ac/smartplug/current') {{
            if (!isNaN(val) && val >= 0) {{
                twin.current_amp = val;
                twin.smartplug_connected = true;
                twin.last_smartplug_packet_time = now;
                if (twin.voltage_v && twin.voltage_v > 0) {{
                    twin.power_watts = Math.round(twin.voltage_v * twin.current_amp * (twin.power_factor || 0.92) * 10) / 10;
                }}
            }} else {{
                twin.current_amp = null;
            }}
        }}
        else if (topic === 'ac/smartplug/power') {{
            if (!isNaN(val) && val >= 0) {{
                twin.power_watts = val;
                twin.smartplug_connected = true;
                twin.last_smartplug_packet_time = now;
            }} else {{
                twin.power_watts = null;
            }}
        }}
        else if (topic === 'ac/smartplug/powerfactor') {{
            if (!isNaN(val)) twin.power_factor = val;
        }}
        else if (topic === 'ac/smartplug/json') {{
            try {{
                let pData = JSON.parse(payload);
                if (pData.voltage !== undefined) twin.voltage_v = parseFloat(pData.voltage);
                if (pData.current !== undefined) twin.current_amp = parseFloat(pData.current);
                if (pData.power !== undefined) twin.power_watts = parseFloat(pData.power);
                if (pData.power_factor !== undefined) twin.power_factor = parseFloat(pData.power_factor);
                twin.smartplug_connected = true;
                twin.last_smartplug_packet_time = now;
            }} catch(e) {{}}
        }}
    }}
}}

// 2. Process Replay Playback (Strictly Rate-Limited to 1 Step per Second / 5 Seconds per Phase)
if (topic === 'system/watchdog') {{
    if (twin.is_replaying && DATASET_ROWS.length > 0) {{
        let lastTick = global.get('last_replay_tick') || 0;
        if ((now - lastTick) >= 950) {{
            global.set('last_replay_tick', now);
            let idx = (twin.replay_index || 0) % DATASET_ROWS.length;
            let row = DATASET_ROWS[idx];
            twin.room_temp = row.indoor_temp;
            twin.room_hum = row.indoor_hum;
            twin.ambient_temp = row.outdoor_temp;
            twin.ambient_hum = row.outdoor_hum;
            twin.comp_temp = row.comp_temp;
            twin.voltage_v = row.voltage_v;
            twin.current_amp = row.current_amp;
            twin.power_watts = row.power_watts;
            twin.power_factor = row.power_factor;
            twin.air_quality = row.air_quality_pct;
            twin.vibration = (row.comp_temp >= 80.0) ? 'VIBRATION DETECTED' : 'NORMAL';
            
            twin.room_sensor_connected = true;
            twin.ambient_sensor_connected = true;
            twin.comp_sensor_connected = true;
            twin.smartplug_connected = true;
            twin.aqi_sensor_connected = true;
            twin.vibration_sensor_connected = true;

            twin.data_source = 'PROTOTYPE DATASET REPLAY';
            twin.replay_index = idx + 1;
            twin.replay_total = DATASET_ROWS.length;
            twin.manual_override_active = false;
        }}
    }}
}}

// 3. Strict Per-Sensor & Device Liveness Verification
if (!twin.is_replaying && !twin.manual_override_active) {{
    if (twin.last_packet_time > 0) {{
        let diffSec = Math.floor((now - twin.last_packet_time) / 1000);
        twin.seconds_since_ping = diffSec;
        if (diffSec > 6) {{
            twin.esp_status = 'OFFLINE';
            twin.room_sensor_connected = false;
            twin.ambient_sensor_connected = false;
            twin.comp_sensor_connected = false;
            twin.smartplug_connected = false;
            twin.aqi_sensor_connected = false;
            twin.vibration_sensor_connected = false;
            twin.room_temp = null;
            twin.room_hum = null;
            twin.ambient_temp = null;
            twin.ambient_hum = null;
            twin.comp_temp = null;
            twin.power_watts = null;
            twin.current_amp = null;
            twin.voltage_v = null;
            twin.air_quality = null;
            twin.vibration = 'DISCONNECTED';
        }} else {{
            twin.esp_status = 'ONLINE';
            
            // Check individual sensor timeouts (6 seconds threshold)
            if (!twin.last_room_packet_time || (now - twin.last_room_packet_time > 6000)) {{
                twin.room_sensor_connected = false;
                twin.room_temp = null;
                twin.room_hum = null;
            }}
            if (!twin.last_ambient_packet_time || (now - twin.last_ambient_packet_time > 6000)) {{
                twin.ambient_sensor_connected = false;
                twin.ambient_temp = null;
                twin.ambient_hum = null;
            }}
            if (!twin.last_comp_packet_time || (now - twin.last_comp_packet_time > 6000)) {{
                twin.comp_sensor_connected = false;
                twin.comp_temp = null;
            }}
            if (!twin.last_smartplug_packet_time || (now - twin.last_smartplug_packet_time > 6000)) {{
                twin.smartplug_connected = false;
                twin.power_watts = null;
                twin.current_amp = null;
                twin.voltage_v = null;
                twin.power_factor = null;
            }}
            if (!twin.last_aqi_packet_time || (now - twin.last_aqi_packet_time > 6000)) {{
                twin.aqi_sensor_connected = false;
                twin.air_quality = null;
            }}
            if (!twin.last_vibration_packet_time || (now - twin.last_vibration_packet_time > 6000)) {{
                twin.vibration_sensor_connected = false;
                twin.vibration = 'DISCONNECTED';
            }}
        }}
    }} else {{
        twin.esp_status = 'OFFLINE';
        twin.seconds_since_ping = 999;
        twin.room_sensor_connected = false;
        twin.ambient_sensor_connected = false;
        twin.comp_sensor_connected = false;
        twin.smartplug_connected = false;
        twin.aqi_sensor_connected = false;
        twin.vibration_sensor_connected = false;
        twin.room_temp = null;
        twin.room_hum = null;
        twin.ambient_temp = null;
        twin.ambient_hum = null;
        twin.comp_temp = null;
        twin.power_watts = null;
        twin.current_amp = null;
        twin.voltage_v = null;
        twin.air_quality = null;
        twin.vibration = 'DISCONNECTED';
    }}
}}

// 4. Derived Thermodynamic Physics Calculations
if (twin.comp_temp !== null && twin.ambient_temp !== null) {{
    twin.temp_lift = Math.round((twin.comp_temp - twin.ambient_temp) * 10) / 10;
}} else {{
    twin.temp_lift = null;
}}

if (twin.ambient_temp !== null && twin.room_temp !== null) {{
    twin.cooling_delta = Math.round((twin.ambient_temp - twin.room_temp) * 10) / 10;
    let deltaT = twin.cooling_delta;
    twin.cooling_efficiency = deltaT > 0 ? Math.min(100, Math.max(15, Math.round((deltaT / 8.0) * 100))) : 60;
}} else {{
    twin.cooling_delta = null;
    twin.cooling_efficiency = null;
}}

// 5. Multi-Location Fault Localization & Diagnostics Engine
let health = 100;
let location = '📍 ALL SUBSYSTEMS NOMINAL';
let title = 'Normal Baseline Operation';
let severity = 'OPTIMAL';
let color = '#10B981';
let root_cause = 'Thermodynamic heat lift, power consumption, and air quality are within normal operational limits.';
let action = 'System operating optimally. Routine preventive maintenance recommended in 180 days.';
let conf = 98.5;
let predicted_rul = 2500;

if (twin.esp_status === 'OFFLINE' && !twin.is_replaying && !twin.manual_override_active) {{
    location = '⚠️ SENSORS & SMART PLUG OFFLINE';
    title = 'Awaiting Telemetry Stream';
    severity = 'CRITICAL';
    color = '#EF4444';
    root_cause = 'ESP32 microcontroller and 16A Smart Plug are disconnected. Showing NOT CONNECTED on offline sensor channels.';
    action = 'Power on ESP32 & Smart Plug, or click Play Prototype Dataset below to begin simulation.';
    health = null;
    predicted_rul = null;
    conf = null;
}} else {{
    let comp = twin.comp_temp;
    let aqi = twin.air_quality;
    let cur = twin.current_amp;
    let coolDelta = twin.cooling_delta;
    let tempLift = twin.temp_lift;
    let volt = twin.voltage_v;
    let vib = twin.vibration || 'DISCONNECTED';

    // Check 1: Critical Multi-Point Compound Failure (3 locations: Indoor + Outdoor + Refrigerant)
    if (comp !== null && comp >= 85.0 && aqi !== null && aqi >= 60.0 && cur !== null && cur >= 7.0) {{
        health = 10;
        location = '📍 CRITICAL MULTI-POINT FAILURE: INDOOR + OUTDOOR + REFRIGERANT (3 Locations)';
        title = 'Critical Multi-Subsystem Breakdown Alert';
        severity = 'CRITICAL';
        color = '#DC2626';
        root_cause = 'Simultaneous breakdown across all 3 key subsystems: Extreme compressor overheat, filter blocked, high current surge.';
        action = 'Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings.';
        conf = 99.2;
        predicted_rul = 24;
    }}
    // Check 2: Dual Compound Fault - Refrigerant Leak + Condenser Fouling (2 locations)
    else if (comp !== null && comp >= 80.0 && coolDelta !== null && coolDelta <= 2.5) {{
        health = 25;
        location = '📍 COMPOUND FAULT: REFRIGERANT LEAK + CONDENSER FOULING (2 Locations)';
        title = 'Severe Compressor Thermal Overload Hazard';
        severity = 'CRITICAL';
        color = '#EF4444';
        root_cause = 'Dangerous combination: dirty condenser coil plus loss of suction gas cooling causes severe compressor overheating.';
        action = 'Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out.';
        conf = 97.8;
        predicted_rul = 48;
    }}
    // Check 3: Dual Compound Fault - Indoor Filter + Outdoor Condenser (2 locations)
    else if (aqi !== null && aqi >= 60.0 && comp !== null && comp >= 70.0) {{
        health = 35;
        location = '📍 COMPOUND FAULT: INDOOR FILTER + OUTDOOR CONDENSER (2 Locations)';
        title = 'Dual Heat Transfer Bottleneck (Indoor & Outdoor)';
        severity = 'CRITICAL';
        color = '#EF4444';
        root_cause = 'Simultaneous indoor airflow restriction and outdoor condenser fouling causing thermal buildup.';
        action = 'Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger.';
        conf = 96.5;
        predicted_rul = 120;
    }}
    // Check 4: Dual Compound Fault - Indoor Filter + Refrigerant Leak (2 locations)
    else if (aqi !== null && aqi >= 55.0 && coolDelta !== null && coolDelta <= 2.5) {{
        health = 30;
        location = '📍 COMPOUND FAULT: INDOOR FILTER + REFRIGERANT LEAK (2 Locations)';
        title = 'Indoor Filter Clog & Refrigerant Depletion';
        severity = 'CRITICAL';
        color = '#EF4444';
        root_cause = 'Zero room cooling and high dust levels. Evaporator coil at risk of frosting.';
        action = 'Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge.';
        conf = 96.0;
        predicted_rul = 100;
    }}
    // Check 5: Mechanical Shock Vibration Anomaly (SW-420)
    else if (vib === 'VIBRATION DETECTED') {{
        health = 40;
        location = '📍 MECHANICAL SUBSYSTEM: ABNORMAL VIBRATION (1 Location)';
        title = 'Excessive Compressor Mechanical Shock / Rotor Vibration';
        severity = 'CRITICAL';
        color = '#EF4444';
        root_cause = 'SW-420 sensor on GPIO 27 detected abnormal mechanical oscillation, bearing wear, or loose mounting grommets.';
        action = 'Inspect compressor anti-vibration rubber mounts, check outdoor fan balance, and inspect compressor scroll assembly.';
        conf = 97.0;
        predicted_rul = 150;
    }}
    // Check 6: Single Fault - Condenser Fouling (Outdoor Unit)
    else if ((comp !== null && comp >= 68.0) || (tempLift !== null && tempLift >= 20.0) || (cur !== null && cur >= 6.8)) {{
        health = 50;
        location = '📍 OUTDOOR UNIT: CONDENSER HEAT EXCHANGER (1 Location)';
        title = 'Condenser Coil Fouling & High Head Pressure';
        severity = 'WARNING';
        color = '#F59E0B';
        root_cause = 'Restricted condenser heat dissipation resulting in elevated discharge temperature and motor current draw.';
        action = 'Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow.';
        conf = 95.1;
        predicted_rul = 220;
    }}
    // Check 7: Single Fault - Refrigerant Undercharge (Refrigerant Circuit)
    else if (coolDelta !== null && coolDelta <= 2.5 && comp !== null && comp >= 55.0) {{
        health = 45;
        location = '📍 REFRIGERANT CIRCUIT: GAS LEAK / LOW CHARGE (1 Location)';
        title = 'Refrigerant Undercharge / Suction Line Depletion';
        severity = 'WARNING';
        color = '#F59E0B';
        root_cause = 'Low refrigerant mass flow rate causing complete loss of cooling capacity (collapsed ΔT).';
        action = 'Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A.';
        conf = 94.6;
        predicted_rul = 250;
    }}
    // Check 8: Single Fault - Grid Voltage Anomaly (Electrical System)
    else if ((volt !== null && (volt <= 205.0 || volt >= 250.0)) || (cur !== null && cur >= 7.5)) {{
        health = 60;
        location = '📍 ELECTRICAL SYSTEM: MAINS GRID SAG (1 Location)';
        title = 'Mains Grid Voltage Sag & Motor Overcurrent';
        severity = 'WARNING';
        color = '#F59E0B';
        root_cause = 'Mains grid voltage dropped (< 205V), forcing compressor motor to draw elevated current to deliver torque.';
        action = 'Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS).';
        conf = 94.0;
        predicted_rul = 420;
    }}
    // Check 9: Single Fault - Indoor Filter Clog (Indoor Unit)
    else if (aqi !== null && aqi >= 55.0) {{
        health = 60;
        location = '📍 INDOOR UNIT: EVAPORATOR AIR FILTER (1 Location)';
        title = 'Indoor Air Filter Dust Loading / Airflow Restriction';
        severity = 'WARNING';
        color = '#F59E0B';
        root_cause = 'High particulate accumulation on nylon mesh filter causing restricted airflow velocity.';
        action = 'Remove, wash with warm water, and thoroughly dry the indoor mesh filter.';
        conf = 95.5;
        predicted_rul = 550;
    }}
    else {{
        // Normal baseline
        health = 100;
        let unconn = [];
        if (!twin.comp_sensor_connected) unconn.push('DS18B20');
        if (!twin.smartplug_connected) unconn.push('Smart Plug');
        if (!twin.vibration_sensor_connected) unconn.push('SW-420');
        if (!twin.aqi_sensor_connected) unconn.push('MQ-135');
        
        if (unconn.length > 0 && !twin.is_replaying && !twin.manual_override_active) {{
            location = '📍 ACTIVE SENSORS NOMINAL (' + unconn.join(', ') + ' Unconnected)';
            title = 'Normal Operation on Active Sensor Channels';
            root_cause = 'Active physical sensors are reporting healthy baseline parameters. Unconnected sensor channels show NOT CONNECTED.';
            action = 'System operating nominally. Connect ' + unconn.join(' & ') + ' to enable full power & thermal telemetry.';
        }} else {{
            location = '📍 ALL SUBSYSTEMS NOMINAL';
            title = 'Normal Baseline Operation';
            root_cause = 'Thermodynamic heat lift, power consumption, and air quality are within normal operational limits.';
            action = 'System operating optimally. Routine preventive maintenance recommended in 180 days.';
        }}
        severity = 'OPTIMAL';
        color = '#10B981';
        conf = 98.5;
        predicted_rul = 2500;
    }}
}}

if (health !== null) {{
    twin.health_score = Math.max(5, Math.min(100, health));
    twin.failure_risk = Math.round((100 - twin.health_score * 0.96) * 10) / 10;
    twin.rul_hours = predicted_rul;
    twin.confidence_score = conf;
    if (twin.health_score >= 85) {{ twin.health_status = 'HEALTHY'; twin.status_color = '#10B981'; }}
    else if (twin.health_score >= 65) {{ twin.health_status = 'GOOD'; twin.status_color = '#3B82F6'; }}
    else if (twin.health_score >= 40) {{ twin.health_status = 'WARNING'; twin.status_color = '#F59E0B'; }}
    else {{ twin.health_status = 'CRITICAL'; twin.status_color = '#EF4444'; }}
}} else {{
    twin.health_score = null;
    twin.failure_risk = null;
    twin.rul_hours = null;
    twin.confidence_score = null;
    twin.health_status = 'OFFLINE';
    twin.status_color = '#94A3B8';
}}

twin.fault_location = location;
twin.fault_title = title;
twin.fault_severity = severity;
twin.fault_severity_color = color;
twin.root_cause = root_cause;
twin.prescriptive_action = action;
twin.last_updated = new Date().toLocaleTimeString();

// Record Ring Buffer History for Chart.js
if (twin.health_score !== null) {{
    let timeLabel = new Date().toLocaleTimeString().split(' ')[0];
    if (history.timestamps.length === 0 || history.timestamps[history.timestamps.length - 1] !== timeLabel) {{
        history.timestamps.push(timeLabel);
        history.comp_temp.push(twin.comp_temp !== null ? twin.comp_temp : null);
        history.ambient_temp.push(twin.ambient_temp !== null ? twin.ambient_temp : null);
        history.room_temp.push(twin.room_temp !== null ? twin.room_temp : null);
        history.health_score.push(twin.health_score);
        history.air_quality.push(twin.air_quality !== null ? twin.air_quality : null);
        if (history.timestamps.length > 25) {{
            history.timestamps.shift();
            history.comp_temp.shift();
            history.ambient_temp.shift();
            history.room_temp.shift();
            history.health_score.shift();
            history.air_quality.shift();
        }}
    }}
}}

global.set('twin_state', twin);
global.set('twin_history', history);

// Native Telegram HTTP Alert Message Generation
let tgMsgs = [];
let tgCfg = global.get('telegram_config') || {{
    bot_token: '8933462238:AAG5JO7iRPeNZxstzA-yRph8FGh3MyfkC-U',
    chat_id: '-5466215213, 1448262676',
    enabled: true
}};

let targetChatIds = ['-5466215213', '1448262676'];
if (tgCfg.chat_id) {{
    let splits = String(tgCfg.chat_id).split(',').map(function(s) {{ return s.trim(); }}).filter(Boolean);
    if (splits.length > 0) targetChatIds = splits;
}}

if (tgCfg.enabled && tgCfg.bot_token && targetChatIds.length > 0 && (twin.fault_severity === 'CRITICAL' || twin.fault_severity === 'WARNING') && twin.fault_location !== '⚠️ SENSORS & SMART PLUG OFFLINE') {{
    let lastTgAlert = global.get('last_tg_alert_time') || 0;
    let lastTgLoc = global.get('last_tg_alert_loc') || '';
    
    if (lastTgLoc !== twin.fault_location || (now - lastTgAlert) >= 4500) {{
        global.set('last_tg_alert_time', now);
        global.set('last_tg_alert_loc', twin.fault_location);
        
        let emoji = twin.fault_severity === 'CRITICAL' ? '🚨' : '⚠️';
        let alertText = `${{emoji}} *AIR CONDITIONER DIGITAL TWIN ALERT* ${{emoji}}\\n` +
            `━━━━━━━━━━━━━━━━━━━━\\n` +
            `*Severity*: \`${{twin.fault_severity}}\`\\n` +
            `*Timestamp*: \`${{new Date().toLocaleTimeString()}}\`\\n\\n` +
            `📍 *FAULT LOCATION*:\\n*${{twin.fault_location}}*\\n\\n` +
            `📋 *FAULT TITLE*:\\n_${{twin.fault_title}}_\\n\\n` +
            `📊 *DIAGNOSTIC & SMART PLUG METRICS*:\\n` +
            `• *Compressor Temp*: \`${{twin.comp_temp !== null ? twin.comp_temp.toFixed(1) + '°C' : 'NOT CONNECTED'}}\` (Lift: \`+${{twin.temp_lift !== null ? twin.temp_lift : '--'}}°C\`)\\n` +
            `• *Room / Ambient*: \`${{twin.room_temp !== null ? twin.room_temp.toFixed(1) + '°C' : 'NOT CONNECTED'}}\` / \`${{twin.ambient_temp !== null ? twin.ambient_temp.toFixed(1) + '°C' : 'NOT CONNECTED'}}\` (ΔT: \`${{twin.cooling_delta !== null ? twin.cooling_delta : '--'}}°C\`)\\n` +
            `• *Smart Plug Power*: \`${{twin.power_watts !== null ? Math.round(twin.power_watts) + ' W' : 'NOT CONNECTED'}}\` (\`${{twin.current_amp !== null ? twin.current_amp.toFixed(2) + ' A' : '--'}}\` / \`${{twin.voltage_v !== null ? Math.round(twin.voltage_v) + ' V' : '--'}}\`)\\n` +
            `• *Indoor Air Quality (AQI)*: \`${{twin.air_quality !== null ? Math.round(twin.air_quality) + '%' : 'NOT CONNECTED'}}\`\\n` +
            `• *Vibration Sensor (SW-420)*: \`${{twin.vibration_sensor_connected ? (twin.vibration || 'NORMAL') : 'NOT CONNECTED'}}\`\\n` +
            `• *System Health Score*: \`${{twin.health_score}}% \`\\n` +
            `• *Failure Risk*: \`${{twin.failure_risk}}% \`\\n` +
            `• *Remaining Useful Life*: \`${{twin.rul_hours}} Hours\`\\n\\n` +
            `🔍 *ROOT CAUSE*:\\n${{twin.root_cause}}\\n\\n` +
            `🛠️ *PRESCRIPTIVE ACTION*:\\n${{twin.prescriptive_action}}\\n` +
            `━━━━━━━━━━━━━━━━━━━━\\n` +
            `_Predictive Maintenance System - Digital Twin IoT_`;

        targetChatIds.forEach(function(cid) {{
            tgMsgs.push({{
                method: "POST",
                url: "https://api.telegram.org/bot" + tgCfg.bot_token + "/sendMessage",
                headers: {{
                    "content-type": "application/json"
                }},
                payload: JSON.stringify({{
                    chat_id: cid,
                    text: alertText,
                    parse_mode: "Markdown",
                    disable_web_page_preview: true
                }})
            }});
        }});
    }}
}}

node.status({{
    fill: twin.status_color === '#10B981' ? 'green' : (twin.status_color === '#F59E0B' ? 'yellow' : 'red'),
    shape: 'dot',
    text: (twin.health_score !== null ? 'Health: ' + twin.health_score + '% | ' : 'OFFLINE | ') + twin.fault_location
}});

msg.payload = {{ state: twin, history: history }};
return [msg, tgMsgs.length > 0 ? tgMsgs : null];""",
        "outputs": 2,
        "noerr": 0,
        "initialize": "",
        "finalize": "",
        "libs": [],
        "x": 510,
        "y": 170,
        "wires": [
            ["debug_twin_out"],
            ["tg_http_out"]
        ]
    },
    {
        "id": "tg_http_out",
        "type": "http request",
        "z": "ac_twin_tab",
        "name": "Post to Telegram API",
        "method": "use",
        "ret": "obj",
        "paytoqs": "ignore",
        "url": "",
        "tls": "",
        "persist": False,
        "proxy": "",
        "authType": "",
        "senderr": False,
        "headers": [],
        "x": 800,
        "y": 240,
        "wires": [
            ["debug_tg_out"]
        ]
    },
    {
        "id": "debug_tg_out",
        "type": "debug",
        "z": "ac_twin_tab",
        "name": "Telegram API Result",
        "active": True,
        "tosidebar": True,
        "console": False,
        "tostatus": False,
        "complete": "payload",
        "targetType": "msg",
        "statusVal": "",
        "statusType": "auto",
        "x": 1030,
        "y": 240,
        "wires": []
    },
    {
        "id": "http_in_dashboard",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "GET /dashboard",
        "url": "/dashboard",
        "method": "get",
        "upload": False,
        "swaggerDoc": "",
        "x": 160,
        "y": 300,
        "wires": [
            ["serve_dashboard_html"]
        ]
    },
    {
        "id": "http_in_actwin",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "GET /ac-twin",
        "url": "/ac-twin",
        "method": "get",
        "upload": False,
        "swaggerDoc": "",
        "x": 150,
        "y": 360,
        "wires": [
            ["serve_dashboard_html"]
        ]
    },
    {
        "id": "http_in_ui",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "GET /ui",
        "url": "/ui",
        "method": "get",
        "upload": False,
        "swaggerDoc": "",
        "x": 140,
        "y": 420,
        "wires": [
            ["serve_dashboard_html"]
        ]
    },
    {
        "id": "serve_dashboard_html",
        "type": "template",
        "z": "ac_twin_tab",
        "name": "Render Attractive UI HTML",
        "field": "payload",
        "fieldType": "msg",
        "format": "text",
        "syntax": "plain",
        "template": html_content,
        "output": "str",
        "x": 480,
        "y": 360,
        "wires": [
            ["set_html_header"]
        ]
    },
    {
        "id": "set_html_header",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Set Content-Type: text/html",
        "func": """msg.headers = {
    'Content-Type': 'text/html; charset=utf-8'
};
return msg;""",
        "outputs": 1,
        "noerr": 0,
        "x": 750,
        "y": 360,
        "wires": [
            ["http_response_out"]
        ]
    },
    {
        "id": "http_in_api_telemetry",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "GET /api/telemetry",
        "url": "/api/telemetry",
        "method": "get",
        "upload": False,
        "swaggerDoc": "",
        "x": 170,
        "y": 500,
        "wires": [
            ["get_api_telemetry_fn"]
        ]
    },
    {
        "id": "get_api_telemetry_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Return Live Telemetry State",
        "func": """let twin = global.get('twin_state') || {
    room_temp: null,
    room_hum: null,
    ambient_temp: null,
    ambient_hum: null,
    comp_temp: null,
    voltage_v: null,
    current_amp: null,
    power_watts: null,
    power_factor: null,
    air_quality: null,
    vibration: 'DISCONNECTED',
    room_sensor_connected: false,
    ambient_sensor_connected: false,
    comp_sensor_connected: false,
    smartplug_connected: false,
    aqi_sensor_connected: false,
    vibration_sensor_connected: false,
    temp_lift: null,
    cooling_delta: null,
    cooling_efficiency: null,
    fault_location: '⚠️ SENSORS & SMART PLUG OFFLINE',
    fault_title: 'Awaiting Telemetry Stream',
    fault_severity: 'CRITICAL',
    fault_severity_color: '#EF4444',
    root_cause: 'ESP32 microcontroller and 16A Smart Plug are disconnected. Showing NOT CONNECTED on offline sensor channels.',
    prescriptive_action: 'Power on ESP32 & Smart Plug, or click Play Prototype Dataset below to begin simulation.',
    confidence_score: null,
    health_score: null,
    health_status: 'OFFLINE',
    status_color: '#94A3B8',
    failure_risk: null,
    rul_hours: null,
    esp_status: 'OFFLINE',
    data_source: 'WAITING FOR SENSORS',
    packets_count: 0,
    seconds_since_ping: 999,
    last_packet_time: 0,
    is_replaying: false,
    replay_index: 0,
    replay_total: 45,
    manual_override_active: false,
    last_updated: '--:--:--'
};

let history = global.get('twin_history') || {
    timestamps: [],
    comp_temp: [],
    ambient_temp: [],
    room_temp: [],
    health_score: [],
    air_quality: []
};

msg.headers = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*'
};
msg.payload = { state: twin, history: history };
return msg;""",
        "outputs": 1,
        "noerr": 0,
        "x": 480,
        "y": 500,
        "wires": [
            ["http_response_out"]
        ]
    },
    {
        "id": "http_in_api_simulate",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/simulate",
        "url": "/api/simulate",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 170,
        "y": 570,
        "wires": [
            ["handle_simulate_fn"]
        ]
    },
    {
        "id": "handle_simulate_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Handle Simulation Override",
        "func": """let twin = global.get('twin_state') || {};
let history = global.get('twin_history') || { timestamps: [], comp_temp: [], ambient_temp: [], room_temp: [], health_score: [], air_quality: [] };
let p = msg.payload || {};
let now = Date.now();

twin.manual_override_active = true;
twin.is_replaying = false;
twin.data_source = 'MANUAL SIMULATION OVERRIDE';

twin.room_sensor_connected = true;
twin.ambient_sensor_connected = true;
twin.comp_sensor_connected = true;
twin.smartplug_connected = true;
twin.aqi_sensor_connected = true;
twin.vibration_sensor_connected = true;

if (p.comp_temp !== undefined) twin.comp_temp = parseFloat(p.comp_temp);
if (p.room_temp !== undefined) twin.room_temp = parseFloat(p.room_temp);
if (p.air_quality !== undefined) twin.air_quality = parseFloat(p.air_quality);
if (p.current_amp !== undefined) twin.current_amp = parseFloat(p.current_amp);
if (p.power_watts !== undefined) twin.power_watts = parseFloat(p.power_watts);
else twin.power_watts = Math.round(230.0 * (twin.current_amp || 4.5) * (twin.power_factor || 0.92) * 10) / 10;

twin.ambient_temp = 34.5;
twin.ambient_hum = 60.0;
twin.room_hum = 50.0;
twin.voltage_v = 230.0;
twin.vibration = (twin.comp_temp >= 80.0) ? 'VIBRATION DETECTED' : 'NORMAL';

// Derive physics
twin.temp_lift = Math.round((twin.comp_temp - twin.ambient_temp) * 10) / 10;
twin.cooling_delta = Math.round((twin.ambient_temp - twin.room_temp) * 10) / 10;
let deltaT = twin.cooling_delta;
twin.cooling_efficiency = deltaT > 0 ? Math.min(100, Math.max(15, Math.round((deltaT / 8.0) * 100))) : 60;

// Evaluate 9 fault states
let health = 100, loc = '📍 ALL SUBSYSTEMS NOMINAL', title = 'Normal Baseline Operation', sev = 'OPTIMAL', col = '#10B981', cause = 'Thermodynamic heat lift, power consumption, and air quality within normal limits.', act = 'Routine preventive maintenance in 180 days.', rul = 2500, conf = 98.5;

if (twin.comp_temp >= 85.0 && twin.air_quality >= 60.0 && twin.current_amp >= 7.0) {
    health = 10; loc = '📍 CRITICAL MULTI-POINT FAILURE: INDOOR + OUTDOOR + REFRIGERANT (3 Locations)';
    title = 'Critical Multi-Subsystem Breakdown Alert'; sev = 'CRITICAL'; col = '#DC2626';
    cause = 'Simultaneous breakdown across all 3 key subsystems: Extreme compressor overheat, filter blocked, high current surge.';
    act = 'Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings.';
    rul = 24; conf = 99.2;
} else if (twin.comp_temp >= 80.0 && twin.cooling_delta <= 2.5) {
    health = 25; loc = '📍 COMPOUND FAULT: REFRIGERANT LEAK + CONDENSER FOULING (2 Locations)';
    title = 'Severe Compressor Thermal Overload Hazard'; sev = 'CRITICAL'; col = '#EF4444';
    cause = 'Dangerous combination: dirty condenser coil plus loss of suction gas cooling causes severe compressor overheating.';
    act = 'Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out.';
    rul = 48; conf = 97.8;
} else if (twin.air_quality >= 60.0 && twin.comp_temp >= 70.0) {
    health = 35; loc = '📍 COMPOUND FAULT: INDOOR FILTER + OUTDOOR CONDENSER (2 Locations)';
    title = 'Dual Heat Transfer Bottleneck (Indoor & Outdoor)'; sev = 'CRITICAL'; col = '#EF4444';
    cause = 'Simultaneous indoor airflow restriction and outdoor condenser fouling causing thermal buildup.';
    act = 'Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger.';
    rul = 120; conf = 96.5;
} else if (twin.air_quality >= 55.0 && twin.cooling_delta <= 2.5) {
    health = 30; loc = '📍 COMPOUND FAULT: INDOOR FILTER + REFRIGERANT LEAK (2 Locations)';
    title = 'Indoor Filter Clog & Refrigerant Depletion'; sev = 'CRITICAL'; col = '#EF4444';
    cause = 'Zero room cooling and high dust levels. Evaporator coil at risk of frosting.';
    act = 'Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge.';
    rul = 100; conf = 96.0;
} else if (twin.comp_temp >= 68.0 || twin.temp_lift >= 20.0 || twin.current_amp >= 6.8) {
    health = 50; loc = '📍 OUTDOOR UNIT: CONDENSER HEAT EXCHANGER (1 Location)';
    title = 'Condenser Coil Fouling & High Head Pressure'; sev = 'WARNING'; col = '#F59E0B';
    cause = 'Restricted condenser heat dissipation resulting in elevated discharge temperature and motor current draw.';
    act = 'Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow.';
    rul = 220; conf = 95.1;
} else if (twin.cooling_delta <= 2.5 && twin.comp_temp >= 55.0) {
    health = 45; loc = '📍 REFRIGERANT CIRCUIT: GAS LEAK / LOW CHARGE (1 Location)';
    title = 'Refrigerant Undercharge / Suction Line Depletion'; sev = 'WARNING'; col = '#F59E0B';
    cause = 'Low refrigerant mass flow rate causing complete loss of cooling capacity (collapsed ΔT).';
    act = 'Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A.';
    rul = 250; conf = 94.6;
} else if (twin.current_amp >= 7.5 || twin.voltage_v <= 205.0) {
    health = 60; loc = '📍 ELECTRICAL SYSTEM: MAINS GRID SAG (1 Location)';
    title = 'Mains Grid Voltage Sag & Motor Overcurrent'; sev = 'WARNING'; col = '#F59E0B';
    cause = 'Mains grid voltage dropped (< 205V), forcing compressor motor to draw elevated current to deliver torque.';
    act = 'Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS).';
    rul = 420; conf = 94.0;
} else if (twin.air_quality >= 55.0) {
    health = 60; loc = '📍 INDOOR UNIT: EVAPORATOR AIR FILTER (1 Location)';
    title = 'Indoor Air Filter Dust Loading / Airflow Restriction'; sev = 'WARNING'; col = '#F59E0B';
    cause = 'High particulate accumulation on nylon mesh filter causing restricted airflow velocity.';
    act = 'Remove, wash with warm water, and thoroughly dry the indoor mesh filter.';
    rul = 550; conf = 95.5;
}

twin.health_score = health;
twin.fault_location = loc;
twin.fault_title = title;
twin.fault_severity = sev;
twin.fault_severity_color = col;
twin.root_cause = cause;
twin.prescriptive_action = act;
twin.confidence_score = conf;
twin.rul_hours = rul;
twin.failure_risk = Math.round((100 - health * 0.96) * 10) / 10;
twin.health_status = health >= 85 ? 'HEALTHY' : (health >= 65 ? 'GOOD' : (health >= 40 ? 'WARNING' : 'CRITICAL'));
twin.status_color = col;
twin.last_updated = new Date().toLocaleTimeString();

// Update history
let timeLabel = new Date().toLocaleTimeString().split(' ')[0];
history.timestamps.push(timeLabel);
history.comp_temp.push(twin.comp_temp);
history.ambient_temp.push(twin.ambient_temp);
history.room_temp.push(twin.room_temp);
history.health_score.push(twin.health_score);
history.air_quality.push(twin.air_quality);
if (history.timestamps.length > 25) {
    history.timestamps.shift();
    history.comp_temp.shift();
    history.ambient_temp.shift();
    history.room_temp.shift();
    history.health_score.shift();
    history.air_quality.shift();
}

global.set('twin_state', twin);
global.set('twin_history', history);

// Native Telegram Alert Dispatch
let tgMsgs = [];
let tgCfg = global.get('telegram_config') || {
    bot_token: '8933462238:AAG5JO7iRPeNZxstzA-yRph8FGh3MyfkC-U',
    chat_id: '-5466215213, 1448262676',
    enabled: true
};
let targetChatIds = ['-5466215213', '1448262676'];
if (tgCfg.chat_id) {
    let splits = String(tgCfg.chat_id).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
    if (splits.length > 0) targetChatIds = splits;
}

if (tgCfg.enabled && tgCfg.bot_token && targetChatIds.length > 0 && (twin.fault_severity === 'CRITICAL' || twin.fault_severity === 'WARNING')) {
    let lastTgAlert = global.get('last_tg_alert_time') || 0;
    let lastTgLoc = global.get('last_tg_alert_loc') || '';
    if (lastTgLoc !== twin.fault_location || (now - lastTgAlert) >= 4500) {
        global.set('last_tg_alert_time', now);
        global.set('last_tg_alert_loc', twin.fault_location);
        
        let emoji = twin.fault_severity === 'CRITICAL' ? '🚨' : '⚠️';
        let alertText = `${emoji} *AIR CONDITIONER DIGITAL TWIN ALERT* ${emoji}\\n` +
            `━━━━━━━━━━━━━━━━━━━━\\n` +
            `*Severity*: \`${twin.fault_severity}\`\\n` +
            `*Timestamp*: \`${new Date().toLocaleTimeString()}\`\\n\\n` +
            `📍 *FAULT LOCATION*:\\n*${twin.fault_location}*\\n\\n` +
            `📋 *FAULT TITLE*:\\n_${twin.fault_title}_\\n\\n` +
            `📊 *DIAGNOSTIC & SMART PLUG METRICS*:\\n` +
            `• *Compressor Temp*: \`${twin.comp_temp.toFixed(1)}°C\` (Lift: \`+${twin.temp_lift}°C\`)\\n` +
            `• *Room / Ambient*: \`${twin.room_temp.toFixed(1)}°C\` / \`${twin.ambient_temp.toFixed(1)}°C\` (ΔT: \`${twin.cooling_delta}°C\`)\\n` +
            `• *Smart Plug Power*: \`${Math.round(twin.power_watts)} W\` (\`${twin.current_amp.toFixed(2)} A\` / \`${twin.voltage_v.toFixed(0)} V\`)\\n` +
            `• *Indoor Air Quality (AQI)*: \`${Math.round(twin.air_quality)}% \`\\n` +
            `• *Vibration (SW-420)*: \`${twin.vibration || 'NORMAL'}\`\\n` +
            `• *System Health Score*: \`${twin.health_score}% \`\\n` +
            `• *Failure Risk*: \`${twin.failure_risk}% \`\\n` +
            `• *Remaining Useful Life*: \`${twin.rul_hours} Hours\`\\n\\n` +
            `🔍 *ROOT CAUSE*:\\n${twin.root_cause}\\n\\n` +
            `🛠️ *PRESCRIPTIVE ACTION*:\\n${twin.prescriptive_action}\\n` +
            `━━━━━━━━━━━━━━━━━━━━\\n` +
            `_Predictive Maintenance System - Digital Twin IoT_`;

        targetChatIds.forEach(function(cid) {
            tgMsgs.push({
                method: "POST",
                url: "https://api.telegram.org/bot" + tgCfg.bot_token + "/sendMessage",
                headers: {
                    "content-type": "application/json"
                },
                payload: JSON.stringify({
                    chat_id: cid,
                    text: alertText,
                    parse_mode: "Markdown",
                    disable_web_page_preview: true
                })
            });
        });
    }
}

msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
msg.payload = { status: 'success', state: twin, manual_mode: true };
return [msg, tgMsgs.length > 0 ? tgMsgs : null];""",
        "outputs": 2,
        "noerr": 0,
        "x": 480,
        "y": 570,
        "wires": [
            ["http_response_out"],
            ["tg_http_out"]
        ]
    },
    {
        "id": "http_in_api_simulate_reset",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/simulate/reset",
        "url": "/api/simulate/reset",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 180,
        "y": 630,
        "wires": [
            ["handle_simulate_reset_fn"]
        ]
    },
    {
        "id": "handle_simulate_reset_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Reset Simulation to Baseline",
        "func": """let twin = global.get('twin_state') || {};
twin.manual_override_active = false;
twin.is_replaying = false;
twin.room_temp = null;
twin.room_hum = null;
twin.ambient_temp = null;
twin.ambient_hum = null;
twin.comp_temp = null;
twin.voltage_v = null;
twin.current_amp = null;
twin.power_watts = null;
twin.power_factor = null;
twin.air_quality = null;
twin.vibration = 'DISCONNECTED';
twin.room_sensor_connected = false;
twin.ambient_sensor_connected = false;
twin.comp_sensor_connected = false;
twin.smartplug_connected = false;
twin.aqi_sensor_connected = false;
twin.vibration_sensor_connected = false;
twin.last_room_packet_time = 0;
twin.last_ambient_packet_time = 0;
twin.last_comp_packet_time = 0;
twin.last_smartplug_packet_time = 0;
twin.last_aqi_packet_time = 0;
twin.last_vibration_packet_time = 0;
twin.temp_lift = null;
twin.cooling_delta = null;
twin.cooling_efficiency = null;
twin.fault_location = '⚠️ SENSORS & SMART PLUG OFFLINE';
twin.fault_title = 'Awaiting Telemetry Stream';
twin.fault_severity = 'CRITICAL';
twin.fault_severity_color = '#EF4444';
twin.root_cause = 'ESP32 microcontroller and 16A Smart Plug are disconnected. Showing NOT CONNECTED on offline sensor channels.';
twin.prescriptive_action = 'Power on ESP32 & Smart Plug, or click Play Prototype Dataset below to begin simulation.';
twin.confidence_score = null;
twin.health_score = null;
twin.health_status = 'OFFLINE';
twin.status_color = '#94A3B8';
twin.failure_risk = null;
twin.rul_hours = null;
twin.data_source = 'REAL HARDWARE (ESP32 & SMART PLUG)';
global.set('twin_state', twin);

msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
msg.payload = { status: 'reset', state: twin, manual_mode: false };
return msg;""",
        "outputs": 1,
        "noerr": 0,
        "x": 480,
        "y": 630,
        "wires": [
            ["http_response_out"]
        ]
    },
    {
        "id": "http_in_api_replay_action",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/replay/:action",
        "url": "/api/replay/:action",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 180,
        "y": 700,
        "wires": [
            ["handle_replay_action_fn"]
        ]
    },
    {
        "id": "http_in_api_replay_start",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/replay/start",
        "url": "/api/replay/start",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 170,
        "y": 760,
        "wires": [
            ["handle_replay_action_fn"]
        ]
    },
    {
        "id": "http_in_api_replay_stop",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/replay/stop",
        "url": "/api/replay/stop",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 170,
        "y": 820,
        "wires": [
            ["handle_replay_action_fn"]
        ]
    },
    {
        "id": "handle_replay_action_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Control Prototype Replay",
        "func": """let twin = global.get('twin_state') || {};
let action = (msg.req && msg.req.params && msg.req.params.action) || (msg.req && msg.req.url && msg.req.url.includes('stop') ? 'stop' : 'start');

if (action === 'start') {
    twin.is_replaying = true;
    twin.manual_override_active = false;
    twin.replay_index = 0;
    twin.data_source = 'PROTOTYPE DATASET REPLAY';
    global.set('twin_state', twin);
    global.set('last_tg_alert_loc', '');
    global.set('last_replay_tick', 0);
    msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
    msg.payload = { status: 'started', is_replaying: true };
} else {
    twin.is_replaying = false;
    twin.replay_index = 0;
    twin.room_temp = null;
    twin.room_hum = null;
    twin.ambient_temp = null;
    twin.ambient_hum = null;
    twin.comp_temp = null;
    twin.voltage_v = null;
    twin.current_amp = null;
    twin.power_watts = null;
    twin.power_factor = null;
    twin.air_quality = null;
    twin.vibration = 'DISCONNECTED';
    twin.room_sensor_connected = false;
    twin.ambient_sensor_connected = false;
    twin.comp_sensor_connected = false;
    twin.smartplug_connected = false;
    twin.aqi_sensor_connected = false;
    twin.vibration_sensor_connected = false;
    twin.last_room_packet_time = 0;
    twin.last_ambient_packet_time = 0;
    twin.last_comp_packet_time = 0;
    twin.last_smartplug_packet_time = 0;
    twin.last_aqi_packet_time = 0;
    twin.last_vibration_packet_time = 0;
    twin.temp_lift = null;
    twin.cooling_delta = null;
    twin.cooling_efficiency = null;
    twin.data_source = 'REAL HARDWARE (ESP32 & SMART PLUG)';
    global.set('twin_state', twin);
    msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
    msg.payload = { status: 'stopped', is_replaying: false };
}
return msg;""",
        "outputs": 1,
        "noerr": 0,
        "x": 480,
        "y": 760,
        "wires": [
            ["http_response_out"]
        ]
    },
    {
        "id": "http_in_tg_get",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "GET /api/telegram/config",
        "url": "/api/telegram/config",
        "method": "get",
        "upload": False,
        "swaggerDoc": "",
        "x": 180,
        "y": 890,
        "wires": [
            ["handle_tg_get_fn"]
        ]
    },
    {
        "id": "handle_tg_get_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Get Telegram Config",
        "func": """let cfg = global.get('telegram_config') || {
    bot_token: '8933462238:AAG5JO7iRPeNZxstzA-yRph8FGh3MyfkC-U',
    chat_id: '-5466215213',
    enabled: true
};
msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
msg.payload = {
    bot_token: cfg.bot_token ? (cfg.bot_token.slice(0, 8) + '...') : '',
    chat_id: cfg.chat_id || '',
    enabled: cfg.enabled !== false,
    is_configured: Boolean(cfg.bot_token && cfg.chat_id)
};
return msg;""",
        "outputs": 1,
        "noerr": 0,
        "x": 480,
        "y": 890,
        "wires": [
            ["http_response_out"]
        ]
    },
    {
        "id": "http_in_tg_post",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/telegram/config",
        "url": "/api/telegram/config",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 180,
        "y": 950,
        "wires": [
            ["handle_tg_post_fn"]
        ]
    },
    {
        "id": "handle_tg_post_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Save Telegram Config",
        "func": """let p = msg.payload || {};
let cfg = {
    bot_token: String(p.bot_token || '').trim(),
    chat_id: String(p.chat_id || '').trim(),
    enabled: p.enabled !== false
};
global.set('telegram_config', cfg);
msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
msg.payload = { status: 'saved', message: 'Telegram credentials saved.' };
return msg;""",
        "outputs": 1,
        "noerr": 0,
        "x": 480,
        "y": 950,
        "wires": [
            ["http_response_out"]
        ]
    },
    {
        "id": "http_in_tg_test",
        "type": "http in",
        "z": "ac_twin_tab",
        "name": "POST /api/telegram/test",
        "url": "/api/telegram/test",
        "method": "post",
        "upload": False,
        "swaggerDoc": "",
        "x": 180,
        "y": 1010,
        "wires": [
            ["handle_tg_test_fn"]
        ]
    },
    {
        "id": "handle_tg_test_fn",
        "type": "function",
        "z": "ac_twin_tab",
        "name": "Send Test Telegram Alert",
        "func": """let cfg = global.get('telegram_config') || {
    bot_token: '8933462238:AAG5JO7iRPeNZxstzA-yRph8FGh3MyfkC-U',
    chat_id: '-5466215213, 1448262676',
    enabled: true
};
let targetChatIds = ['-5466215213', '1448262676'];
if (cfg.chat_id) {
    let splits = String(cfg.chat_id).split(',').map(function(s) { return s.trim(); }).filter(Boolean);
    if (splits.length > 0) targetChatIds = splits;
}

let testMsg = "🎉 *AC DIGITAL TWIN TELEGRAM ALERT SYSTEM CONNECTED!* 🎉\\n" +
    "━━━━━━━━━━━━━━━━━━━━\\n" +
    "✅ *Bot Status*: Active & Online\\n" +
    "📍 *Node*: AC Digital Twin Node-RED Server\\n" +
    "📡 *Smart Plug Power Telemetry*: 16A Live Active\\n" +
    "📳 *Vibration Sensor (SW-420)*: Monitored on GPIO 27\\n" +
    "⏰ *Timestamp*: " + new Date().toLocaleTimeString() + "\\n\\n" +
    "Your Digital Twin is now fully connected to Telegram. You will receive real-time push alerts whenever single, dual, or triple multi-location faults are detected on your Air Conditioner!\\n" +
    "━━━━━━━━━━━━━━━━━━━━\\n" +
    "_Predictive Maintenance System - Digital Twin IoT_";

let tgMsgs = [];
targetChatIds.forEach(function(cid) {
    tgMsgs.push({
        method: "POST",
        url: "https://api.telegram.org/bot" + cfg.bot_token + "/sendMessage",
        headers: {
            "content-type": "application/json"
        },
        payload: JSON.stringify({
            chat_id: cid,
            text: testMsg,
            parse_mode: "Markdown",
            disable_web_page_preview: true
        })
    });
});

msg.headers = { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' };
msg.payload = { success: true, message: 'Test message dispatched to all configured Telegram chats!' };
return [msg, tgMsgs.length > 0 ? tgMsgs : null];""",
        "outputs": 2,
        "noerr": 0,
        "x": 480,
        "y": 1010,
        "wires": [
            ["http_response_out"],
            ["tg_http_out"]
        ]
    },
    {
        "id": "http_response_out",
        "type": "http response",
        "z": "ac_twin_tab",
        "name": "HTTP Response Out",
        "statusCode": "200",
        "headers": {},
        "x": 780,
        "y": 630,
        "wires": []
    },
    {
        "id": "debug_twin_out",
        "type": "debug",
        "z": "ac_twin_tab",
        "name": "Live Fault Diagnostics Log",
        "active": True,
        "tosidebar": True,
        "console": False,
        "tostatus": True,
        "complete": "payload.state.fault_location",
        "targetType": "msg",
        "statusVal": "payload.state.fault_location",
        "statusType": "auto",
        "x": 800,
        "y": 170,
        "wires": []
    }
]

out_path = r"C:\Users\dhara\.gemini\antigravity\scratch\ac_digital_twin\nodered_flows\ac_digital_twin_attractive_flow.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(flow_nodes, f, indent=2)

complete_path = r"C:\Users\dhara\.gemini\antigravity\scratch\ac_digital_twin\nodered_flows\ac_digital_twin_complete_flow.json"
with open(complete_path, "w", encoding="utf-8") as f:
    json.dump(flow_nodes, f, indent=2)

print(f"Successfully generated {out_path} ({os.path.getsize(out_path)} bytes)")
