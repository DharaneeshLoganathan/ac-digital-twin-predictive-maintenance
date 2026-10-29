"""
=============================================================================
PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
MODULE : Historical Data Logger (SQLite & CSV)
=============================================================================
This script subscribes to local Mosquitto MQTT topics and logs real sensor
telemetry into a local SQLite database (ac_telemetry.db) and CSV file.
=============================================================================
"""

import sqlite3
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
import os

DB_PATH = "ac_telemetry.db"
CSV_PATH = "ac_telemetry.csv"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# Global current reading dictionary
current_sample = {
    "timestamp": None,
    "indoor_temp": None,
    "indoor_hum": None,
    "outdoor_temp": None,
    "outdoor_hum": None,
    "comp_temp": None,
    "vibration": "NORMAL",
    "air_quality": None
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ac_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            indoor_temp REAL,
            indoor_hum REAL,
            outdoor_temp REAL,
            outdoor_hum REAL,
            comp_temp REAL,
            vibration TEXT,
            air_quality REAL
        )
    ''')
    conn.commit()
    conn.close()
    
    # Initialize CSV header if not exists
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w') as f:
            f.write("timestamp,indoor_temp,indoor_hum,outdoor_temp,outdoor_hum,comp_temp,vibration,air_quality\n")
    print(f"[LOGGER] Database initialized at {DB_PATH}")

def log_sample(sample):
    if sample["indoor_temp"] is None or sample["comp_temp"] is None:
        return # Skip incomplete initial samples
    
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample["timestamp"] = ts
    
    # Insert to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO ac_telemetry (timestamp, indoor_temp, indoor_hum, outdoor_temp, outdoor_hum, comp_temp, vibration, air_quality)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ts, sample["indoor_temp"], sample["indoor_hum"], sample["outdoor_temp"],
        sample["outdoor_hum"], sample["comp_temp"], sample["vibration"], sample["air_quality"]
    ))
    conn.commit()
    conn.close()

    # Append to CSV
    with open(CSV_PATH, 'a') as f:
        f.write(f"{ts},{sample['indoor_temp']},{sample['indoor_hum']},{sample['outdoor_temp']},{sample['outdoor_hum']},{sample['comp_temp']},{sample['vibration']},{sample['air_quality']}\n")
    
    print(f"[SAVED] {ts} -> InT:{sample['indoor_temp']}°C | OutT:{sample['outdoor_temp']}°C | CompT:{sample['comp_temp']}°C | Vib:{sample['vibration']} | AQI:{sample['air_quality']}%")

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected to Mosquitto broker (rc={rc})")
    client.subscribe("ac/#")
    print("[MQTT] Subscribed to topic: ac/#")

def on_message(client, userdata, msg):
    global current_sample
    topic = msg.topic
    payload = msg.payload.decode('utf-8')

    try:
        if topic == "ac/indoor/temperature":
            current_sample["indoor_temp"] = float(payload)
        elif topic == "ac/indoor/humidity":
            current_sample["indoor_hum"] = float(payload)
        elif topic == "ac/outdoor/temperature":
            current_sample["outdoor_temp"] = float(payload)
        elif topic == "ac/outdoor/humidity":
            current_sample["outdoor_hum"] = float(payload)
        elif topic == "ac/compressor/temp":
            current_sample["comp_temp"] = float(payload)
        elif topic == "ac/vibration":
            current_sample["vibration"] = payload.strip()
        elif topic == "ac/airquality":
            current_sample["air_quality"] = float(payload)
            # When full cycle finishes, log snapshot
            log_sample(current_sample)
    except Exception as e:
        print(f"[ERROR] Failed to process message on {topic}: {e}")

if __name__ == "__main__":
    init_db()
    client = mqtt.Client(client_id="Python_AC_DataLogger")
    client.on_connect = on_connect
    client.on_message = on_message
    
    print(f"[LOGGER] Connecting to {MQTT_BROKER}:{MQTT_PORT}...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[LOGGER] Stopping data logger.")
    except Exception as ex:
        print(f"[ERROR] Could not connect: {ex}")
