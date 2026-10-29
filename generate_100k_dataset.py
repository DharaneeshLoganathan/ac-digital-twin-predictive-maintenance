"""
=============================================================================
PROJECT : Digital Twin for Predictive Maintenance of Air Conditioner
MODULE  : 100,000-Sample Physics-Calibrated Multi-Fault Dataset Generator
FILE    : generate_100k_dataset.py
OUTPUT  : ac_realistic_twin_dataset_100k.csv (~100,000 samples, ~347 Days of 5-min IoT Data)
=============================================================================
Based on Research Foundations:
1. Rossi & Braun (1997) & Li & Braun (2004/2007) - Multi-Simultaneous HVAC Fault Dynamics
2. Kim et al. / NIST (2009) - Thermal Inertia & Steady-State Transitions
3. Han & Song (IEEE 2003) - Motor Electrical Signature Analysis (Current / Power)
4. Hosamo et al. (2022) - Digital Twin Non-Linear Degradation
=============================================================================
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time

def generate_100k_ac_dataset(n_samples=100000, seed=42):
    print(f"[DATASET GENERATOR] Generating {n_samples:,} physics-calibrated samples with Smart Plug power & multi-location faults...")
    start_time_gen = time.time()
    np.random.seed(seed)
    
    # 1. Temporal Index: 5-minute sampling interval spanning ~347.2 Days
    base_datetime = datetime(2025, 7, 1, 0, 0, 0)
    timestamps = [base_datetime + timedelta(minutes=5 * i) for i in range(n_samples)]
    day_indices = np.array([i / (12 * 24.0) for i in range(n_samples)])
    
    # 2. Multi-Seasonal Atmospheric Temperature Model
    # Annual Seasonality (Summer peak ~42°C, Winter low ~18°C) + Diurnal 24h Cycle (±4.5°C)
    annual_cycle = np.cos(2 * np.pi * day_indices / 365.25)
    seasonal_base_temp = 30.0 + 7.0 * annual_cycle
    diurnal_cycle = np.sin(2 * np.pi * day_indices - (np.pi / 3.0))
    
    # Random realistic weather front fluctuations (multi-day heatwaves / rainstorms)
    weather_noise = np.convolve(np.random.normal(0, 1.8, n_samples), np.ones(50)/50, mode='same')
    sensor_noise_outdoor = np.random.normal(0, 0.35, n_samples)
    
    outdoor_temp = np.clip(seasonal_base_temp + 4.5 * diurnal_cycle + weather_noise + sensor_noise_outdoor, 16.0, 48.0)
    outdoor_hum = np.clip(62.0 - 15.0 * diurnal_cycle - 5.0 * annual_cycle + np.random.normal(0, 2.5, n_samples), 25.0, 95.0)
    
    # 3. Indoor Building Thermal Model
    # Dynamic occupancy thermal load (1.2°C extra heat during 9 AM - 10 PM)
    room_occupancy_load = np.where((np.mod(day_indices * 24, 24) >= 9) & (np.mod(day_indices * 24, 24) <= 22), 1.2, 0.0)
    indoor_temp = 23.5 + 0.15 * (outdoor_temp - 30.0) + room_occupancy_load + np.random.normal(0, 0.3, n_samples)
    indoor_hum = np.clip(48.0 + 0.1 * (outdoor_hum - 50.0) + np.random.normal(0, 1.2, n_samples), 35.0, 75.0)
    
    # 4. Smart Plug Electrical Grid Model (Mains Voltage Fluctuation)
    # Nominal 230V AC with normal distribution ±3.5V and occasional industrial grid sag
    grid_voltage_base = 230.0 + np.random.normal(0, 3.2, n_samples)
    
    # Arrays for derived telemetry
    comp_temp = np.zeros(n_samples)
    voltage_v = np.zeros(n_samples)
    current_amp = np.zeros(n_samples)
    power_watts = np.zeros(n_samples)
    power_factor = np.zeros(n_samples)
    air_quality_pct = np.zeros(n_samples)
    health_score = np.zeros(n_samples, dtype=int)
    rul_hours = np.zeros(n_samples)
    fault_category = []
    remediation_action = []
    
    # Remediation Action Lookup Dictionary
    REMEDIATIONS = {
        "NOMINAL_HEALTHY": "System operating optimally. Perform regular scheduled preventive inspection.",
        "INDOOR_FILTER_CLOG": "Remove, wash with warm water, and dry the indoor nylon mesh filter.",
        "CONDENSER_FOULING": "Clean outdoor condenser coil fins with foaming coil cleaner; verify outdoor fan airflow.",
        "REFRIGERANT_UNDERCHARGE": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A.",
        "GRID_VOLTAGE_ANOMALY": "Inspect main electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS).",
        "FILTER_AND_CONDENSER_FAULT": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger.",
        "REFRIGERANT_LEAK_AND_CONDENSER_FAULT": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out.",
        "FILTER_AND_REFRIGERANT_FAULT": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge to nominal operating pressure.",
        "CRITICAL_COMPOUND_MULTI_FAULT": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."
    }
    
    # 10 full run-to-degradation lifecycle cycles (10,000 samples each = ~34.7 days per cycle)
    cycle_size = 10000
    
    for i in range(n_samples):
        cycle_pos = i % cycle_size
        cycle_id = i // cycle_size
        
        # Base healthy baseline operating values
        c_base = outdoor_temp[i] + 13.0 + np.random.normal(0, 0.6)
        aqi_base = 18.0 + 0.05 * indoor_temp[i] + np.random.normal(0, 1.2)
        v_base = grid_voltage_base[i]
        pf_base = 0.92 + np.random.normal(0, 0.015)
        
        # Determine operational phase across the 10,000-sample lifecycle:
        # Phase 0 (0-2500, 25%): NOMINAL HEALTHY
        # Phase 1 (2500-3500, 10%): INDOOR_FILTER_CLOG (1 location)
        # Phase 2 (3500-4500, 10%): CONDENSER_FOULING (1 location)
        # Phase 3 (4500-5500, 10%): REFRIGERANT_UNDERCHARGE (1 location)
        # Phase 4 (5500-6500, 10%): GRID_VOLTAGE_ANOMALY (1 location)
        # Phase 5 (6500-7500, 10%): FILTER_AND_CONDENSER_FAULT (2 locations)
        # Phase 6 (7500-8500, 10%): REFRIGERANT_LEAK_AND_CONDENSER_FAULT (2 locations)
        # Phase 7 (8500-9300, 8%):  FILTER_AND_REFRIGERANT_FAULT (2 locations)
        # Phase 8 (9300-10000, 7%): CRITICAL_COMPOUND_MULTI_FAULT (3 locations)
        
        if cycle_pos < 2500:
            # 1. NOMINAL HEALTHY (100% -> 90% Health)
            deg = cycle_pos / 2500.0
            cat = "NOMINAL_HEALTHY"
            c_val = c_base
            aqi_val = aqi_base
            v_val = v_base
            i_val = 4.2 + 0.04 * (outdoor_temp[i] - 30.0) + np.random.normal(0, 0.12)
            pf_val = pf_base
            h_val = int(100 - deg * 10)
            rul_val = 2500.0 - (cycle_pos * 0.35)
            
        elif cycle_pos < 3500:
            # 2. INDOOR_FILTER_CLOG (1 location: Indoor)
            deg = (cycle_pos - 2500) / 1000.0
            cat = "INDOOR_FILTER_CLOG"
            c_val = c_base + (deg * 3.5)
            aqi_val = aqi_base + (deg * 52.0) # AQI rises significantly
            indoor_temp[i] += (deg * 2.8) # Cooling capacity drops
            v_val = v_base
            i_val = 4.2 + (deg * 0.6) + np.random.normal(0, 0.12) # Slight blower strain
            pf_val = pf_base - (deg * 0.02)
            h_val = int(90 - deg * 20) # 90 -> 70%
            rul_val = 1625.0 - ((cycle_pos - 2500) * 0.45)
            
        elif cycle_pos < 4500:
            # 3. CONDENSER_FOULING (1 location: Outdoor)
            deg = (cycle_pos - 3500) / 1000.0
            cat = "CONDENSER_FOULING"
            c_val = c_base + (deg * 26.0) # Comp temp rises up to 78°C+
            aqi_val = aqi_base + (deg * 4.0)
            v_val = v_base
            # High discharge head pressure causes significant motor current rise (Han & Song / IEEE 2003)
            i_val = 4.5 + (deg * 2.8) + np.random.normal(0, 0.15) # 4.5A -> 7.3A
            pf_val = pf_base - (deg * 0.04)
            h_val = int(70 - deg * 22) # 70 -> 48%
            rul_val = 1175.0 - ((cycle_pos - 3500) * 0.45)
            
        elif cycle_pos < 5500:
            # 4. REFRIGERANT_UNDERCHARGE (1 location: Refrigerant circuit)
            deg = (cycle_pos - 4500) / 1000.0
            cat = "REFRIGERANT_UNDERCHARGE"
            # Lack of cooling suction gas raises compressor temp, but cooling delta drops to near 0 (Rossi & Braun 1997)
            c_val = c_base + (deg * 18.0)
            indoor_temp[i] += (deg * 5.2) # Severe under-cooling (ΔT collapses)
            aqi_val = aqi_base
            v_val = v_base
            # Lower mass flow of gas actually lightens motor compression load (Current drops slightly)
            i_val = max(3.1, 4.2 - (deg * 0.9) + np.random.normal(0, 0.12)) # 4.2A -> 3.3A
            pf_val = pf_base - (deg * 0.06)
            h_val = int(60 - deg * 25) # 60 -> 35%
            rul_val = 725.0 - ((cycle_pos - 4500) * 0.38)
            
        elif cycle_pos < 6500:
            # 5. GRID_VOLTAGE_ANOMALY (1 location: Electrical Grid)
            deg = (cycle_pos - 5500) / 1000.0
            cat = "GRID_VOLTAGE_ANOMALY"
            # Low voltage sag down to 192V causes motor current spike to deliver mechanical torque (P = V*I)
            v_val = v_base - (deg * 34.0) + np.random.normal(0, 1.5) # 230V -> 196V
            i_val = 4.4 + (deg * 3.4) + np.random.normal(0, 0.18) # 4.4A -> 7.8A spike
            c_val = c_base + (deg * 14.0) # Motor winding heating
            aqi_val = aqi_base
            pf_val = pf_base - (deg * 0.08)
            h_val = int(65 - deg * 25)
            rul_val = 550.0 - ((cycle_pos - 5500) * 0.25)
            
        elif cycle_pos < 7500:
            # 6. FILTER_AND_CONDENSER_FAULT (2 locations: Indoor Filter + Outdoor Condenser)
            deg = (cycle_pos - 6500) / 1000.0
            cat = "FILTER_AND_CONDENSER_FAULT"
            c_val = c_base + (deg * 28.0) # High comp temp > 80°C
            aqi_val = aqi_base + (deg * 48.0) # High AQI
            indoor_temp[i] += (deg * 4.0)
            v_val = v_base
            i_val = 4.6 + (deg * 3.1) + np.random.normal(0, 0.16) # Elevated current
            pf_val = pf_base - (deg * 0.05)
            h_val = int(50 - deg * 25) # 50 -> 25%
            rul_val = 400.0 - ((cycle_pos - 6500) * 0.22)
            
        elif cycle_pos < 8500:
            # 7. REFRIGERANT_LEAK_AND_CONDENSER_FAULT (2 locations: Refrigerant + Outdoor Condenser)
            deg = (cycle_pos - 7500) / 1000.0
            cat = "REFRIGERANT_LEAK_AND_CONDENSER_FAULT"
            # Deadly combination: dirty condenser coil + gas loss = extreme overheating
            c_val = outdoor_temp[i] + 32.0 + (deg * 16.0) # Overheat > 85°C
            indoor_temp[i] += 5.5 # Zero cooling
            aqi_val = aqi_base + (deg * 6.0)
            v_val = v_base
            i_val = 5.0 + (deg * 2.2) + np.random.normal(0, 0.15)
            pf_val = pf_base - (deg * 0.07)
            h_val = int(35 - deg * 20) # 35 -> 15%
            rul_val = 220.0 - ((cycle_pos - 7500) * 0.15)
            
        elif cycle_pos < 9300:
            # 8. FILTER_AND_REFRIGERANT_FAULT (2 locations: Indoor Filter + Refrigerant Leak)
            deg = (cycle_pos - 8500) / 800.0
            cat = "FILTER_AND_REFRIGERANT_FAULT"
            c_val = c_base + (deg * 16.0)
            aqi_val = aqi_base + (deg * 55.0) # High dust
            indoor_temp[i] += (deg * 5.0) # No cooling
            v_val = v_base
            i_val = max(3.2, 4.0 - (deg * 0.5) + np.random.normal(0, 0.12))
            pf_val = pf_base - (deg * 0.06)
            h_val = int(28 - deg * 15) # 28 -> 13%
            rul_val = 110.0 - ((cycle_pos - 8500) * 0.08)
            
        else:
            # 9. CRITICAL_COMPOUND_MULTI_FAULT (3 locations: Indoor + Outdoor + Refrigerant)
            deg = (cycle_pos - 9300) / 700.0
            cat = "CRITICAL_COMPOUND_MULTI_FAULT"
            c_val = outdoor_temp[i] + 38.0 + (deg * 14.0) # Extreme overheating > 92°C
            aqi_val = 65.0 + (deg * 25.0) # Severe filter block
            indoor_temp[i] += 6.5 # Rapid room temperature rise
            v_val = v_base - (deg * 15.0)
            i_val = 6.5 + (deg * 2.2) + np.random.normal(0, 0.20) # Current surge > 8.5A
            pf_val = 0.82 - (deg * 0.05)
            h_val = int(max(5, 15 - deg * 10)) # 15 -> 5%
            rul_val = max(0.0, 45.0 - ((cycle_pos - 9300) * 0.06))
            
        # Calculate Active Power: P (Watts) = V * I * cos(theta)
        v_final = round(float(np.clip(v_val, 185.0, 255.0)), 1)
        i_final = round(float(max(0.0, i_val)), 2)
        pf_final = round(float(np.clip(pf_val, 0.70, 0.98)), 3)
        p_final = round(v_final * i_final * pf_final, 1)
        
        comp_temp[i] = round(c_val, 2)
        voltage_v[i] = v_final
        current_amp[i] = i_final
        power_watts[i] = p_final
        power_factor[i] = pf_final
        air_quality_pct[i] = round(max(5.0, min(99.0, aqi_val)), 1)
        health_score[i] = max(5, min(100, h_val))
        rul_hours[i] = round(max(0.0, rul_val), 1)
        fault_category.append(cat)
        remediation_action.append(REMEDIATIONS[cat])
        
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
        "voltage_v": voltage_v,
        "current_amp": current_amp,
        "power_watts": power_watts,
        "power_factor": power_factor,
        "air_quality_pct": air_quality_pct,
        "health_score": health_score,
        "rul_hours": rul_hours,
        "fault_category": fault_category,
        "remediation_action": remediation_action
    })
    
    elapsed = time.time() - start_time_gen
    print(f"[DATASET GENERATOR] Successfully generated {len(df):,} samples in {elapsed:.2f} seconds.")
    print(f"[DATASET GENERATOR] Fault Class Distribution:\n{df['fault_category'].value_counts(normalize=True)*100}")
    return df

if __name__ == "__main__":
    df = generate_100k_ac_dataset(100000)
    out_file = "ac_realistic_twin_dataset_100k.csv"
    df.to_csv(out_file, index=False)
    
    # Also update ac_realistic_twin_dataset.csv
    df.to_csv("ac_realistic_twin_dataset.csv", index=False)
    print(f"\n[OK] Dataset saved to {out_file} and ac_realistic_twin_dataset.csv.")

