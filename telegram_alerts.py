"""
=============================================================================
PROJECT: Digital Twin for Predictive Maintenance of Air Conditioner
MODULE : Telegram Push Notification & Critical Alert Dispatcher
=============================================================================
This module provides automated real-time Telegram alerts when:
1. Live Hardware Telemetry detects Critical Overheat, Gas Leak, or SW-420 Vibration.
2. Prototype Dataset Replay reaches a Critical Compound Failure state.
3. Manual Injection / Simulation Sliders force a Critical Fault condition.
4. ESP32 Microcontroller or Sensor hardware watchdog goes Offline.
=============================================================================
"""

import json
import os
import time
import urllib.request
import urllib.parse
from datetime import datetime

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "telegram_config.json")

# Default Configuration Template
DEFAULT_CONFIG = {
    "enabled": True,
    "bot_token": "8933462238:AAG5JO7iRPeNZxstzA-yRph8FGh3MyfkC-U",
    "chat_id": "-5466215213, 1448262676",  # Telegram Group & Direct User Chat
    "cooldown_seconds": 30,  # Minimum seconds between repeated alerts for the same fault location
    "alert_on_warning": True,
    "alert_on_critical": True,
    "alert_on_offline": True
}

# In-memory alert state tracking for debouncing
last_alert_timestamps = {}
last_severity_state = "OPTIMAL"

def load_config():
    """Loads Telegram configuration from file or initializes default settings."""
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception as e:
        print(f"[TELEGRAM] Error loading config: {e}")
        return DEFAULT_CONFIG

def save_config(token, chat_id, enabled=True, cooldown=30):
    """Saves updated Telegram bot token and target chat IDs."""
    config = load_config()
    config["bot_token"] = token.strip()
    config["chat_id"] = str(chat_id).strip()
    config["enabled"] = enabled
    config["cooldown_seconds"] = cooldown
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    print(f"[TELEGRAM] Configuration saved successfully to {CONFIG_PATH}")

def send_telegram_message(message_text, specific_chat_id=None):
    """
    Sends a formatted Markdown message to Telegram group and direct chats via HTTP POST.
    Supports comma-separated chat IDs (e.g. '-5466215213, 1448262676').
    """
    config = load_config()
    if not config.get("enabled", False):
        return False, "Telegram alerts disabled in config."

    token = config.get("bot_token", "").strip()
    raw_chat_ids = specific_chat_id or config.get("chat_id", "")

    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        return False, "Telegram Bot Token not configured."

    # Parse target chat IDs (supports group IDs like -5466215213 and direct user IDs)
    target_chats = [c.strip() for c in str(raw_chat_ids).split(",") if c.strip() and c.strip() != "YOUR_TELEGRAM_CHAT_ID_HERE"]
    if not target_chats:
        return False, "No valid Telegram Chat IDs configured."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    delivery_results = []
    overall_success = False

    for cid in target_chats:
        payload = {
            "chat_id": cid,
            "text": message_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_json = json.loads(response.read().decode("utf-8"))
                if res_json.get("ok"):
                    delivery_results.append(f"Chat {cid}: OK")
                    overall_success = True
                else:
                    delivery_results.append(f"Chat {cid}: Failed ({res_json.get('description')})")
        except Exception as e:
            delivery_results.append(f"Chat {cid}: Error ({e})")

    summary = " | ".join(delivery_results)
    return overall_success, summary

def format_critical_alert(twin_state):
    """
    Constructs a rich, high-visibility engineering alert message for Telegram groups.
    Accurately handles Live Hardware, Prototype Replay, and Manual Injection scenarios.
    """
    # 1. Determine Telemetry Origin
    data_source = twin_state.get("data_source", "")
    is_replaying = twin_state.get("is_replaying", False)
    manual_override = twin_state.get("manual_override_active", False)

    if manual_override or data_source == "MANUAL SIMULATION OVERRIDE":
        origin_badge = "🎛️ *MANUAL FAULT INJECTION (Test Deck)*"
    elif is_replaying or data_source == "PROTOTYPE DATASET REPLAY":
        rep_idx = twin_state.get("replay_index", 1)
        rep_tot = twin_state.get("replay_total", 45)
        origin_badge = f"🧪 *PROTOTYPE DATASET SIMULATION (Step {rep_idx}/{rep_tot})*"
    else:
        origin_badge = "📡 *LIVE HARDWARE TELEMETRY (ESP32 & Sensors)*"

    location = twin_state.get("fault_location", "UNKNOWN SUBSYSTEM")
    title = twin_state.get("fault_title", "Unspecified Fault Condition")
    severity = str(twin_state.get("fault_severity", "CRITICAL")).upper()
    health = twin_state.get("health_score")
    risk = twin_state.get("failure_risk")
    rul = twin_state.get("rul_hours")
    root_cause = twin_state.get("root_cause", "Anomaly detected in operating parameters.")
    action = twin_state.get("prescriptive_action", "Inspect subsystem and perform preventive maintenance.")

    # Sensor values with graceful disconnected / null handling
    comp_temp = twin_state.get("comp_temp")
    room_temp = twin_state.get("room_temp")
    ambient_temp = twin_state.get("ambient_temp")
    power_watts = twin_state.get("power_watts")
    current_amp = twin_state.get("current_amp")
    voltage_v = twin_state.get("voltage_v")
    aqi = twin_state.get("air_quality")
    vibration = twin_state.get("vibration", "NORMAL")
    temp_lift = twin_state.get("temp_lift")
    cooling_delta = twin_state.get("cooling_delta")

    # Formatted Metric Strings
    comp_str = f"`{comp_temp:.1f}°C`" if comp_temp is not None else "`NOT CONNECTED`"
    lift_str = f"`+{temp_lift:.1f}°C`" if temp_lift is not None else "`--`"
    room_str = f"`{room_temp:.1f}°C`" if room_temp is not None else "`NOT CONNECTED`"
    amb_str = f"`{ambient_temp:.1f}°C`" if ambient_temp is not None else "`NOT CONNECTED`"
    delta_str = f"`{cooling_delta:.1f}°C`" if cooling_delta is not None else "`--`"

    if power_watts is not None:
        pwr_str = f"`{round(power_watts)} W` (`{current_amp:.2f} A` / `{round(voltage_v)} V`)" if (current_amp is not None and voltage_v is not None) else f"`{round(power_watts)} W`"
    else:
        pwr_str = "`NOT CONNECTED`"

    aqi_str = f"`{round(aqi)}%`" if aqi is not None else "`NOT CONNECTED`"
    vib_str = f"`{vibration}`" if twin_state.get("vibration_sensor_connected", True) else "`NOT CONNECTED`"
    health_str = f"`{health}%`" if health is not None else "`--`"
    risk_str = f"`{risk}%`" if risk is not None else "`--`"
    rul_str = f"`{rul} Hours`" if rul is not None else "`--`"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    emoji = "🚨" if severity == "CRITICAL" else ("⚠️" if severity == "WARNING" else "ℹ️")

    msg = f"""
{emoji} *AIR CONDITIONER DIGITAL TWIN ALERT* {emoji}
━━━━━━━━━━━━━━━━━━━━
*Severity*: `{severity}`
*Operating Mode*: {origin_badge}
*Timestamp*: `{timestamp}`

📍 *FAULT LOCATION*:
*{location}*

📋 *FAULT TITLE*:
_{title}_

📊 *DIAGNOSTIC & SMART PLUG METRICS*:
• *Compressor Temp*: {comp_str} (Lift: {lift_str})
• *Room / Ambient*: {room_str} / {amb_str} (ΔT: {delta_str})
• *Smart Plug Power*: {pwr_str}
• *Indoor Air Quality (AQI)*: {aqi_str}
• *Vibration (SW-420)*: {vib_str}
• *System Health Score*: {health_str}
• *Failure Risk*: {risk_str}
• *Remaining Useful Life*: {rul_str}

🔍 *ROOT CAUSE*:
{root_cause}

🛠️ *PRESCRIPTIVE ACTION*:
{action}
━━━━━━━━━━━━━━━━━━━━
_Predictive Maintenance System - Digital Twin IoT_
"""
    return msg.strip()

def process_twin_state_for_alerts(twin_state):
    """
    Checks if an alert should be dispatched to Telegram group/bot based on:
    1. Live Hardware critical telemetry
    2. Prototype simulation / replay critical faults
    3. Manual injection critical test conditions
    4. Hardware watchdog offline state
    """
    global last_alert_timestamps, last_severity_state

    config = load_config()
    if not config.get("enabled", False):
        return False

    severity = twin_state.get("fault_severity", "OPTIMAL")
    esp_status = twin_state.get("esp_status", "ONLINE")
    is_replaying = twin_state.get("is_replaying", False)
    manual_override = twin_state.get("manual_override_active", False)
    cooldown = config.get("cooldown_seconds", 30)
    now = time.time()

    should_alert = False
    alert_key = ""

    # Rule 1: Microcontroller / Telemetry Watchdog Timeout
    if esp_status == "OFFLINE" and not is_replaying and not manual_override:
        if config.get("alert_on_offline", True):
            should_alert = True
            alert_key = "HARDWARE_OFFLINE"

    # Rule 2: Critical Fault (Live Hardware, Prototype Replay, or Manual Injection)
    elif severity == "CRITICAL" and config.get("alert_on_critical", True):
        should_alert = True
        alert_key = f"CRITICAL_{twin_state.get('fault_location', 'FAULT')}"

    # Rule 3: Warning Fault (Optional early advisory)
    elif severity == "WARNING" and config.get("alert_on_warning", True):
        if last_severity_state == "OPTIMAL" or last_severity_state == "OFFLINE":
            should_alert = True
            alert_key = f"WARNING_{twin_state.get('fault_location', 'FAULT')}"

    last_severity_state = severity

    if should_alert:
        last_time = last_alert_timestamps.get(alert_key, 0)
        # Dispatch immediately if fault location changed or cooldown elapsed
        if (now - last_time) >= cooldown:
            last_alert_timestamps[alert_key] = now
            msg_text = format_critical_alert(twin_state)
            success, detail = send_telegram_message(msg_text)
            if success:
                print(f"[TELEGRAM ALERT DISPATCHED] {alert_key} -> {detail}")
            else:
                print(f"[TELEGRAM ALERT SKIPPED/FAILED] {detail}")
            return success

    return False

if __name__ == "__main__":
    import sys
    print("=====================================================")
    print("   AC DIGITAL TWIN - TELEGRAM ALERT TEST UTILITY")
    print("=====================================================")
    
    config = load_config()
    token = config.get("bot_token", "")
    chat_id = config.get("chat_id", "")
    
    print(f"Current Config Path: {CONFIG_PATH}")
    print(f"Bot Token : {token[:10]}... (Total: {len(token)} chars)" if len(token) > 10 else f"Bot Token : {token}")
    print(f"Target Chat(s): {chat_id}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        new_token = input("Enter your Telegram Bot Token: ").strip()
        new_chat_id = input("Enter your Telegram Chat ID (or comma-separated group & user IDs): ").strip()
        save_config(new_token, new_chat_id)
        print("Setup complete! Run 'python telegram_alerts.py --test' to send a test alert.")

    elif len(sys.argv) > 1 and sys.argv[1] == "--test-live":
        print("\n[1/3] Testing LIVE HARDWARE Critical Telemetry Alert...")
        live_state = {
            "data_source": "REAL HARDWARE (ESP32 & SMART PLUG)",
            "esp_status": "ONLINE",
            "is_replaying": False,
            "manual_override_active": False,
            "fault_location": "📍 MECHANICAL SUBSYSTEM: ABNORMAL VIBRATION (1 Location)",
            "fault_title": "Excessive Compressor Mechanical Shock / Rotor Oscillation",
            "fault_severity": "CRITICAL",
            "health_score": 40,
            "failure_risk": 61.6,
            "rul_hours": 150.0,
            "comp_temp": 34.5,
            "room_temp": 32.2,
            "ambient_temp": 32.8,
            "power_watts": None,
            "current_amp": None,
            "voltage_v": None,
            "air_quality": 1.2,
            "vibration": "VIBRATION DETECTED",
            "vibration_sensor_connected": True,
            "root_cause": "SW-420 sensor on GPIO 27 detected abnormal mechanical oscillation or loose mounting grommets.",
            "prescriptive_action": "Inspect compressor anti-vibration rubber mounts and check outdoor fan balance."
        }
        success, res = send_telegram_message(format_critical_alert(live_state))
        print(f"Result: {res}")

    elif len(sys.argv) > 1 and sys.argv[1] == "--test-prototype":
        print("\n[2/3] Testing PROTOTYPE DATASET SIMULATION Critical Fault Alert...")
        prototype_state = {
            "data_source": "PROTOTYPE DATASET REPLAY",
            "esp_status": "ONLINE",
            "is_replaying": True,
            "replay_index": 42,
            "replay_total": 45,
            "manual_override_active": False,
            "fault_location": "📍 CRITICAL MULTI-POINT FAILURE: INDOOR + OUTDOOR + REFRIGERANT (3 Locations)",
            "fault_title": "Critical Multi-Subsystem Breakdown Alert",
            "fault_severity": "CRITICAL",
            "health_score": 10,
            "failure_risk": 90.4,
            "rul_hours": 24.0,
            "comp_temp": 88.5,
            "room_temp": 34.0,
            "ambient_temp": 36.0,
            "power_watts": 1615.0,
            "current_amp": 7.8,
            "voltage_v": 225.0,
            "air_quality": 85.0,
            "vibration": "VIBRATION DETECTED",
            "vibration_sensor_connected": True,
            "root_cause": "Simultaneous breakdown across all 3 key subsystems: Extreme compressor overheat, filter blocked, high current surge.",
            "prescriptive_action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit and clean all coils."
        }
        success, res = send_telegram_message(format_critical_alert(prototype_state))
        print(f"Result: {res}")

    elif len(sys.argv) > 1 and sys.argv[1] == "--test-manual":
        print("\n[3/3] Testing MANUAL FAULT INJECTION Test Deck Alert...")
        manual_state = {
            "data_source": "MANUAL SIMULATION OVERRIDE",
            "esp_status": "ONLINE",
            "is_replaying": False,
            "manual_override_active": True,
            "fault_location": "📍 COMPOUND FAULT: REFRIGERANT LEAK + CONDENSER FOULING (2 Locations)",
            "fault_title": "Severe Compressor Thermal Overload Hazard",
            "fault_severity": "CRITICAL",
            "health_score": 25,
            "failure_risk": 76.0,
            "rul_hours": 48.0,
            "comp_temp": 82.0,
            "room_temp": 32.5,
            "ambient_temp": 34.5,
            "power_watts": 1420.0,
            "current_amp": 6.8,
            "voltage_v": 227.0,
            "air_quality": 22.0,
            "vibration": "VIBRATION DETECTED",
            "vibration_sensor_connected": True,
            "root_cause": "Dangerous combination: dirty condenser coil plus loss of suction gas cooling causes severe compressor overheating.",
            "prescriptive_action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge."
        }
        success, res = send_telegram_message(format_critical_alert(manual_state))
        print(f"Result: {res}")

    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("\nSending All 3 Diagnostic Alert Scenarios to Telegram Group...")
        print("\n1. Testing Live Hardware Alert...")
        os.system("python telegram_alerts.py --test-live")
        time.sleep(1)
        print("\n2. Testing Prototype Simulation Alert...")
        os.system("python telegram_alerts.py --test-prototype")
        time.sleep(1)
        print("\n3. Testing Manual Injection Alert...")
        os.system("python telegram_alerts.py --test-manual")
    else:
        print("\nUsage:")
        print("  • Configure credentials            : python telegram_alerts.py --setup")
        print("  • Test all 3 alert scenarios       : python telegram_alerts.py --test")
        print("  • Test live hardware shock/overheat: python telegram_alerts.py --test-live")
        print("  • Test prototype replay fault      : python telegram_alerts.py --test-prototype")
        print("  • Test manual fault injection      : python telegram_alerts.py --test-manual")
