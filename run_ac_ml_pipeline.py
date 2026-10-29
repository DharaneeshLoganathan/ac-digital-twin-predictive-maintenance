#!/usr/bin/env python
"""
ac_digital_twin: Complete ML Pipeline
1. Generates 100,000-sample dataset
2. Trains Decision Tree Classifier & Random Forest REGRESSOR
3. Saves joblibs
4. Loads & Tests 3x Live Inference Samples
"""

import numpy as np
import pandas as pd
import joblib
import time

# 1. Load existing dataset or generate if not present
import os
if not os.path.exists('ac_realistic_twin_dataset_100k.csv'):
    print("[DATA] Generating 100,000-sample dataset...")
    from generate_100k_dataset import generate_100k_ac_dataset
    df = generate_100k_ac_dataset(100000)
    df.to_csv('ac_realistic_twin_dataset_100k.csv', index=False)
else:
    print("[1/4] Loading 100,000-sample dataset...")
    df = pd.read_csv('ac_realistic_twin_dataset_100k.csv')

# 2. Train Models
print("\n[2/4] Training & Validating Models...")
from train_models_100k import train_and_validate
train_and_validate()

# 3. Test Pretrained Models on Live Samples
print("\n[3/4] Loading Pretrained Models from Disk...")
clf = joblib.load('ac_fault_classifier.joblib')
rul = joblib.load('ac_rul_regressor.joblib')
features = joblib.load('model_features.joblib')

print("\n=============================================================================")
print("               LIVE PRETRAINED MODEL TESTING RESULTS")
print("============================================================================")

s1 = pd.DataFrame([{'indoor_temp': 24.0, 'indoor_hum': 50.0, 'outdoor_temp': 32.0, 'outdoor_hum': 60.0, 'comp_temp': 45.0, 'temp_lift': 13.0, 'cooling_delta': 8.0, 'voltage_v': 230.0, 'current_amp': 4.2, 'power_watts': 880.0, 'power_factor': 0.91, 'air_quality_pct': 18.0}])[features]
print(f"\n[TEST 1: NORMMAL HEALTHY AC]")
print(f"  -> Predicted Fault : {clf.predict(s1)[0]}")
print(f"  -> Predicted RUL   : {rul.predict(s1)[0]:.1f} Hours")

s2 = pd.DataFrame([{'indoor_temp': 27.5, 'indoor_hum': 55.0, 'outdoor_temp': 34.0, 'outdoor_hum': 60.0, 'comp_temp': 52.0, 'temp_lift': 18.0, 'cooling_delta': 6.5, 'voltage_v': 228.0, 'current_amp': 4.8, 'power_watts': 990.0, 'power_factor': 0.90, 'air_quality_pct': 82.0}])[features]
print(f"\n[TEST 2: INDOOR FILTER CLOG ( AQI = 82% )]")
print(f"  -> Predicted Fault : {clf.predict(s2)[0]}")
print(f"  -> Predicted RUL   : {rul.predict(s2)[0]:.1f} Hours")

s3 = pd.DataFrame([{'indoor_temp': 31.0, 'indoor_hum': 60.0, 'outdoor_temp': 38.0, 'outdoor_hum': 50.0, 'comp_temp': 86.5, 'temp_lift': 48.5, 'cooling_delta': 7.0, 'voltage_v': 226.0, 'current_amp': 7.8, 'power_watts': 1520.0, 'power_factor': 0.86, 'air_quality_pct': 30.0}])[features]
print(f"\n[TEST 3: REFRIGERANT LEAK + CONDENSER FOULING]")
print(f"  -> Predicted Fault : {clf.predict(s3)[0]}")
print(f"  -> Predicted RUL   : {rul.predict(s3)[0]:.1f} Hours")
print("=" * 75)
