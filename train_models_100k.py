"""
=============================================================================
PROJECT : Digital Twin for Predictive Maintenance of Air Conditioner
MODULE  : Model Training, Anti-Overfitting Validation & Export (100k Dataset)
FILE    : train_models_100k.py
=============================================================================
This script:
1. Loads the 100,000-sample Smart Plug + IoT multi-fault dataset.
2. Performs an 80/20 Stratified Train-Test Split (80,000 Train, 20,000 Test).
3. Performs 5-Fold Cross-Validation to verify zero overfitting / underfitting.
4. Trains a Regularized Multi-Class Decision Tree Fault Classifier (9 Classes).
5. Trains a Regularized Random Forest RUL Regressor.
6. Evaluates and prints comprehensive metrics (Confusion Matrix, Precision,
   Recall, F1, R², RMSE, MAE, Train vs Test gap).
7. Exports updated models to 'ac_fault_classifier.joblib' and 'ac_rul_regressor.joblib'.
=============================================================================
"""

import pandas as pd
import numpy as np
import joblib
import time
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    r2_score, mean_squared_error, mean_absolute_error
)

def train_and_validate():
    print("=" * 75)
    print("   AC DIGITAL TWIN ML TRAINING & OVERFIT/UNDERFIT VALIDATION PIPELINE")
    print("   Dataset: 100,000 Samples (Smart Plug + Multi-Fault Permutations)")
    print("=" * 75)
    
    t0 = time.time()
    df = pd.read_csv("ac_realistic_twin_dataset_100k.csv")
    print(f"[DATA] Loaded dataset shape: {df.shape}")
    
    # Feature columns (Smart Plug Power + Environmental + Compressor Telemetry, NO MPU-6050)
    feature_cols = [
        'indoor_temp', 'indoor_hum', 'outdoor_temp', 'outdoor_hum',
        'comp_temp', 'temp_lift', 'cooling_delta',
        'voltage_v', 'current_amp', 'power_watts', 'power_factor',
        'air_quality_pct'
    ]
    
    X = df[feature_cols]
    y_clf = df['fault_category']
    y_rul = df['rul_hours']
    
    print("\n[CLASS DISTRIBUTION (9 Multi-Location Operational States)]")
    print(df['fault_category'].value_counts(normalize=True).apply(lambda x: f"{x*100:.1f}%"))
    
    # -------------------------------------------------------------------------
    # 1. TRAIN / TEST SPLIT (80% Train = 80,000, 20% Test = 20,000)
    # -------------------------------------------------------------------------
    X_train, X_test, y_train_clf, y_test_clf, y_train_rul, y_test_rul = train_test_split(
        X, y_clf, y_rul, test_size=0.20, random_state=42, stratify=y_clf
    )
    print(f"\n[SPLIT] Training Set: {len(X_train):,} samples | Hold-out Test Set: {len(X_test):,} samples")
    
    # -------------------------------------------------------------------------
    # 2. MODEL 1: MULTI-CLASS FAULT CLASSIFIER (REGULARIZED DECISION TREE)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("1. TRAINING MULTI-CLASS FAULT CLASSIFIER (9 Operational Classes)")
    print("-" * 75)
    
    # Regularization parameters to prevent overfitting:
    # - max_depth=8 handles 9-class boundary depth without memorizing noise
    # - min_samples_split=20 requires cluster mass
    # - min_samples_leaf=10 prevents leaf memorization
    clf_model = DecisionTreeClassifier(
        criterion='entropy',
        max_depth=8,
        min_samples_split=20,
        min_samples_leaf=10,
        random_state=42
    )
    
    # 5-Fold Stratified Cross-Validation on Training Data
    cv_kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(clf_model, X_train, y_train_clf, cv=cv_kfold, scoring='accuracy')
    print(f"5-Fold Cross-Validation Accuracy: Mean = {cv_scores.mean()*100:.2f}% (Std: ±{cv_scores.std()*100:.3f}%)")
    
    # Fit on full 80k training set
    clf_model.fit(X_train, y_train_clf)
    
    # Evaluation on Train vs Test (Checks Overfit vs Underfit)
    train_acc = accuracy_score(y_train_clf, clf_model.predict(X_train))
    test_acc = accuracy_score(y_test_clf, clf_model.predict(X_test))
    
    print(f"\n[OVERFIT CHECK - CLASSIFIER]")
    print(f"  Training Set Accuracy : {train_acc*100:.2f}%")
    print(f"  Hold-out Test Accuracy: {test_acc*100:.2f}%")
    acc_gap = abs(train_acc - test_acc) * 100
    print(f"  Generalization Gap    : {acc_gap:.2f}% -> " + ("[PASS] ZERO OVERFITTING (Gap < 1.0%)" if acc_gap < 1.0 else "[WARNING] Check parameters"))
    
    y_pred_clf = clf_model.predict(X_test)
    print(f"\n[HOLD-OUT TEST SET CLASSIFICATION REPORT (20,000 Samples)]")
    print(classification_report(y_test_clf, y_pred_clf, digits=4))
    
    print("[FEATURE IMPORTANCES - CLASSIFIER]")
    for feat, imp in zip(feature_cols, clf_model.feature_importances_):
        print(f"  {feat:20s}: {imp:.4f} ({imp*100:.1f}%)")
        
    # -------------------------------------------------------------------------
    # 3. MODEL 2: REMAINING USEFUL LIFE (RUL) REGRESSOR (RANDOM FOREST)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("2. TRAINING REMAINING USEFUL LIFE (RUL) REGRESSOR (Random Forest)")
    print("-" * 75)
    
    # Regularized Random Forest Regressor:
    # - n_estimators=60 for ensemble diversity
    # - max_depth=12 for smooth multi-fault RUL estimation
    # - min_samples_leaf=6 for smooth regression boundaries
    rul_model = RandomForestRegressor(
        n_estimators=60,
        max_depth=12,
        min_samples_leaf=6,
        n_jobs=-1,
        random_state=42
    )
    
    rul_model.fit(X_train, y_train_rul)
    
    y_train_rul_pred = rul_model.predict(X_train)
    y_test_rul_pred = rul_model.predict(X_test)
    
    train_r2 = r2_score(y_train_rul, y_train_rul_pred)
    test_r2 = r2_score(y_test_rul, y_test_rul_pred)
    test_mae = mean_absolute_error(y_test_rul, y_test_rul_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test_rul, y_test_rul_pred))
    
    print(f"\n[OVERFIT CHECK - RUL REGRESSOR]")
    print(f"  Training R^2 Score : {train_r2:.4f} ({train_r2*100:.2f}% Variance Explained)")
    print(f"  Hold-out Test R^2  : {test_r2:.4f} ({test_r2*100:.2f}% Variance Explained)")
    print(f"  Test Mean Abs Error (MAE) : {test_mae:.2f} Hours")
    print(f"  Test Root Mean Sq Error (RMSE): {test_rmse:.2f} Hours")
    r2_gap = abs(train_r2 - test_r2)
    print(f"  Generalization Gap        : {r2_gap:.4f} -> " + ("[PASS] ZERO OVERFITTING (R^2 Gap < 0.02)" if r2_gap < 0.02 else "[WARNING] Check regularization"))
    
    print("\n[FEATURE IMPORTANCES - RUL REGRESSOR]")
    for feat, imp in zip(feature_cols, rul_model.feature_importances_):
        print(f"  {feat:20s}: {imp:.4f} ({imp*100:.1f}%)")
        
    # -------------------------------------------------------------------------
    # 4. EXPORT TRAINED MODELS & FEATURE LIST
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("3. EXPORTING RETRAINED INDUSTRIAL MODELS")
    print("-" * 75)
    joblib.dump(clf_model, "ac_fault_classifier.joblib", compress=3)
    joblib.dump(rul_model, "ac_rul_regressor.joblib", compress=3)
    joblib.dump(feature_cols, "model_features.joblib", compress=3)
    
    total_time = time.time() - t0
    print(f"Saved: ac_fault_classifier.joblib & ac_rul_regressor.joblib & model_features.joblib")
    print(f"Total Pipeline Execution Time: {total_time:.2f} seconds.")
    print("=" * 75)
if __name__ == "__main__":
    train_and_validate()
