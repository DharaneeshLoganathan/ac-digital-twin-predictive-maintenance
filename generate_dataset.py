"""
=============================================================================
PROJECT : Digital Twin for Predictive Maintenance of Air Conditioner
MODULE  : Physics-Calibrated Synthetic Degradation Dataset Generator
FILE    : generate_dataset.py
OUTPUT  : ac_realistic_twin_dataset.csv (3,000 samples)
=============================================================================
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_ac_digital_twin_dataset(n_samples=3000, seed=42):
    np.random.seed(seed)
    
    # 1. Base Time Grid (5-minute intervals starting June 1, 2026)
    start_time = datetime(2026, 6, 1, 8, 0, 0)
    timestamps = [start_time + timedelta(minutes=5 * i) for i in range(n_samples)]
    time_steps = np.linspace(0, 100, n_samples)
    
    # 2. Ambient Environmental Baseline (Diurnal Cycle: 28°C night to 38°C peak afternoon)
    day_cycle = np.sin(2 * np.pi * time_steps / 10.0) # Periodic day/night oscillations
    outdoor_temp = 32.0 + 4.5 * day_cycle + np.random.normal(0, 0.4, n_samples)
    outdoor_hum = 65.0 - 10.0 * day_cycle + np.random.normal(0, 1.2, n_samples)
    
    # 3. Indoor Room Conditions
    indoor_temp = 24.0 + 1.2 * day_cycle + np.random.normal(0, 0.3, n_samples)
    indoor_hum = 50.0 + 2.0 * np.random.normal(0, 0.8, n_samples)
    
    # 4. Degradation Stage Allocation across 3,000 samples:
    # 0 to 1000   : Nominal Baseline
    # 1001 to 1600 : Indoor Filter Clogging
    # 1601 to 2100 : Condenser Thermal Runaway
    # 2101 to 2600 : Mechanical Damper / Vibration Wear
    # 2601 to 3000 : Compound Catastrophic Failure
    
    comp_temp = np.zeros(n_samples)
    vibration_state = []
    vibration_pulses = np.zeros(n_samples, dtype=int)
    air_quality_pct = np.zeros(n_samples)
    health_score = np.zeros(n_samples, dtype=int)
    rul_hours = np.zeros(n_samples)
    fault_category = []
    
    for i in range(n_samples):
        # Progress parameter (0.0 at start, 1.0 at end of life)
        t_prog = i / float(n_samples)
        
        # Base nominal compressor heat lift (~13°C above outdoor temp)
        c_base = outdoor_temp[i] + 13.0 + np.random.normal(0, 0.6)
        aqi_base = 15.0 + np.random.normal(0, 1.5)
        vib_is_active = 0
        
        if i < 1000:
            # STAGE 1: NOMINAL HEALTHY
            c_val = c_base
            aqi_val = aqi_base
            vib_is_active = 0
            h_val = 100
            rul_val = 2500.0 - (i * 0.83)
            cat = "NOMINAL_HEALTHY"
            
        elif i < 1500:
            # STAGE 2: INDOOR FILTER DUST CLOGGING
            clog_factor = (i - 1000) / 500.0
            c_val = c_base + (clog_factor * 3.0)
            aqi_val = aqi_base + (clog_factor * 48.0) # AQI rises to ~65%
            indoor_temp[i] += (clog_factor * 4.5) # Room gets warmer
            vib_is_active = 0
            h_val = int(100 - (clog_factor * 25)) # Drops to 75%
            rul_val = 1666.0 - ((i - 1000) * 0.83)
            cat = "INDOOR_FILTER_CLOGGED"
            
        elif i < 2100:
            # STAGE 3: CONDENSER FOULING & THERMAL RUNAWAY
            heat_factor = (i - 1500) / 600.0
            c_val = c_base + (heat_factor * 30.0) # Comp temp rises to 78°C+
            aqi_val = aqi_base
            vib_is_active = 0
            h_val = int(75 - (heat_factor * 30)) # Drops to 45%
            rul_val = 1250.0 - ((i - 1500) * 0.83)
            cat = "CONDENSER_FOULING_OVERHEATING"
            
        elif i < 2600:
            # STAGE 4: FAN BEARING & MECHANICAL VIBRATION WEAR
            vib_factor = (i - 2100) / 500.0
            c_val = c_base + (vib_factor * 8.0)
            aqi_val = aqi_base
            vib_is_active = 1 if np.random.rand() > 0.15 else 0 # 85% vibration active
            h_val = int(45 - (vib_factor * 25)) # Drops to 20%
            rul_val = 750.0 - ((i - 2100) * 0.83)
            cat = "FAN_BEARING_MECHANICAL_WEAR"
            
        else:
            # STAGE 5: CRITICAL COMPOUND FAILURE
            crit_factor = (i - 2600) / 400.0
            c_val = outdoor_temp[i] + 36.0 + (crit_factor * 8.0) # Overheating > 78°C
            aqi_val = 60.0 + (crit_factor * 10.0)
            indoor_temp[i] += 4.5
            vib_is_active = 1
            h_val = int(max(5, 20 - (crit_factor * 15))) # Drops to 5%
            rul_val = max(0.0, 333.0 - ((i - 2600) * 0.83))
            cat = "CRITICAL_COMPRESSOR_FAILURE"
            
        comp_temp[i] = round(c_val, 2)
        air_quality_pct[i] = round(max(5.0, min(95.0, aqi_val)), 1)
        vibration_state.append("DETECTED" if vib_is_active else "NORMAL")
        vibration_pulses[i] = int(np.random.randint(4, 18)) if vib_is_active else 0
        health_score[i] = max(5, min(100, h_val))
        rul_hours[i] = round(max(0.0, rul_val), 1)
        fault_category.append(cat)
        
    # Derived Physical Thermodynamic Features
    temp_lift = np.round(comp_temp - outdoor_temp, 2)
    cooling_delta = np.round(outdoor_temp - indoor_temp, 2)
    
    df = pd.DataFrame({
        "timestamp": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
        "indoor_temp": np.round(indoor_temp, 2),
        "indoor_hum": np.round(indoor_hum, 1),
        "outdoor_temp": np.round(outdoor_temp, 2),
        "outdoor_hum": np.round(outdoor_hum, 1),
        "comp_temp": comp_temp,
        "temp_lift": temp_lift,
        "cooling_delta": cooling_delta,
        "vibration_pulses": vibration_pulses,
        "vibration_state": vibration_state,
        "air_quality_pct": air_quality_pct,
        "health_score": health_score,
        "rul_hours": rul_hours,
        "fault_category": fault_category
    })
    
    return df

if __name__ == "__main__":
    df = generate_ac_digital_twin_dataset(3000)
    out_file = "ac_realistic_twin_dataset.csv"
    df.to_csv(out_file, index=False)
    print(f"Generated {len(df)} samples successfully in {out_file}.")
