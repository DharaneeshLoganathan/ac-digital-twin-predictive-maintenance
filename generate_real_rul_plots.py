"""
=============================================================================
PROJECT : Digital Twin for Predictive Maintenance of Air Conditioner
MODULE  : 100% Empirical RUL Model Evaluation & Feature Importance Generator
FILE    : generate_real_rul_plots.py
=============================================================================
This script:
1. Loads the actual 100,000-sample dataset ('ac_realistic_twin_dataset_100k.csv').
2. Loads the trained Random Forest Regressor ('ac_rul_regressor.joblib') and features.
3. Computes:
   - Real feature importances directly from `rul_model.feature_importances_`.
   - Real predictions on the 20,000 hold-out test set (`rul_model.predict(X_test)`).
   - Exact empirical R², MAE, and RMSE.
4. Generates publication-ready figures (300 DPI):
   - 'ml_rul_feature_importance.png' (Empirical feature importances)
   - 'ml_rul_regression_fit.png'     (Empirical Actual vs Predicted scatter fit)
=============================================================================
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import os
import shutil

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def main():
    print("=" * 75)
    print("RUNNING 100% EMPIRICAL EVALUATION FOR RUL REGRESSOR & FEATURE IMPORTANCE...")
    print("=" * 75)

    # 1. Load Data & Trained Model
    df = pd.read_csv("ac_realistic_twin_dataset_100k.csv")
    feature_cols = [
        'indoor_temp', 'indoor_hum', 'outdoor_temp', 'outdoor_hum',
        'comp_temp', 'temp_lift', 'cooling_delta',
        'voltage_v', 'current_amp', 'power_watts', 'power_factor',
        'air_quality_pct'
    ]
    X = df[feature_cols]
    y_rul = df['rul_hours']
    y_clf = df['fault_category']

    # Stratified split to get identical 20,000 test samples
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_rul, test_size=0.20, random_state=42, stratify=y_clf
    )

    rul_model = joblib.load("ac_rul_regressor.joblib")
    
    # Run real prediction on the test set
    y_pred = rul_model.predict(X_test)

    # Calculate exact empirical metrics
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"\n--- EMPIRICAL RUL REGRESSOR TEST METRICS (N = {len(y_test):,} Samples) ---")
    print(f"R² Score : {r2:.4f} ({r2*100:.2f}% Variance Explained)")
    print(f"MAE      : {mae:.2f} Hours")
    print(f"RMSE     : {rmse:.2f} Hours")

    # Feature Importance
    importances = rul_model.feature_importances_
    feat_imp_df = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': importances * 100
    }).sort_values(by='Importance', ascending=True)

    print("\n--- EMPIRICAL FEATURE IMPORTANCES ---")
    for _, row in feat_imp_df.iloc[::-1].iterrows():
        print(f"  {row['Feature']:20s}: {row['Importance']:.2f}%")

    artifact_dir = r"C:\Users\dhara\.gemini\antigravity\brain\c4f01390-3f83-4fce-991b-ef3ce6ce975c"

    # =========================================================================
    # 2. PLOT: EMPIRICAL RUL FEATURE IMPORTANCE (ml_rul_feature_importance.png)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(9, 6), dpi=300, facecolor='#FFFFFF')
    
    # Feature readable name mapping
    feat_names_clean = {
        'temp_lift': 'Temperature Lift (ΔT_lift)',
        'air_quality_pct': 'Air Quality Index (AQI)',
        'indoor_temp': 'Room Temperature (T_indoor)',
        'current_amp': 'Motor Current (I_rms)',
        'outdoor_temp': 'Outdoor Temperature (T_ambient)',
        'comp_temp': 'Compressor Temp (T_comp)',
        'power_watts': 'Active Power (Watts)',
        'power_factor': 'Power Factor (PF)',
        'indoor_hum': 'Indoor Humidity (%)',
        'outdoor_hum': 'Outdoor Humidity (%)',
        'voltage_v': 'Mains Voltage (V)',
        'cooling_delta': 'Cooling Delta (ΔT_cooling)'
    }

    plot_df = feat_imp_df.copy()
    plot_df['CleanName'] = plot_df['Feature'].map(feat_names_clean).fillna(plot_df['Feature'])

    # Pick colors based on importance tier
    colors = []
    for imp in plot_df['Importance']:
        if imp >= 50:
            colors.append('#EF4444') # Red for dominant driver
        elif imp >= 5:
            colors.append('#F59E0B') # Amber
        elif imp >= 2.5:
            colors.append('#3B82F6') # Blue
        else:
            colors.append('#64748B') # Slate gray

    bars = ax1.barh(plot_df['CleanName'], plot_df['Importance'], color=colors, height=0.62, edgecolor='#1E293B', linewidth=0.8, zorder=3)
    ax1.set_xlim(0, 95)
    ax1.set_xlabel('Empirical Feature Importance Score (%)', fontweight='bold', fontsize=11, color='#0F172A')
    ax1.set_title('Empirical Random Forest RUL Feature Importance\n(Extracted directly from 60 Ensemble Decision Trees)', 
                  fontweight='bold', fontsize=12, pad=14, color='#0F172A')
    ax1.grid(axis='x', linestyle='--', alpha=0.5, zorder=0)

    for bar in bars:
        width = bar.get_width()
        ax1.annotate(f"{width:.1f}%",
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(6, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=9.5, fontweight='bold', color='#0F172A')

    # Dominance callout
    top_feature = feat_imp_df.iloc[-1]
    ax1.text(42, 1.8, f"★ {feat_names_clean.get(top_feature['Feature'], top_feature['Feature'])} Dominates ({top_feature['Importance']:.1f}%)\nThermodynamic heat-transfer bottleneck\nserves as the primary physical degradation driver.", 
             fontsize=9, style='italic', color='#7F1D1D',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#FEF2F2", edgecolor="#F87171", linewidth=1.1))

    fig1.savefig("ml_rul_feature_importance.png", dpi=300, bbox_inches='tight')
    if os.path.exists(artifact_dir):
        shutil.copy("ml_rul_feature_importance.png", os.path.join(artifact_dir, "ml_rul_feature_importance.png"))
    plt.close(fig1)
    print("[SUCCESS] Exported: ml_rul_feature_importance.png")

    # =========================================================================
    # 3. PLOT: EMPIRICAL ACTUAL VS PREDICTED RUL (ml_rul_regression_fit.png)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(8.5, 6.5), dpi=300, facecolor='#FFFFFF')

    # Subsample 1,000 points from the 20,000 test set for clean scatter density visibility
    np.random.seed(42)
    sample_indices = np.random.choice(len(y_test), size=1000, replace=False)
    y_test_sub = np.array(y_test)[sample_indices]
    y_pred_sub = y_pred[sample_indices]

    ax2.scatter(y_test_sub, y_pred_sub, color='#0284C7', alpha=0.45, edgecolors='none', s=24, 
                label=f'Hold-Out Test Data (1,000 Sample Subset of {len(y_test):,})', zorder=3)
    
    # Plot Ideal fit line y = x
    max_val = max(y_test.max(), y_pred.max()) + 100
    ax2.plot([0, max_val], [0, max_val], 'r--', linewidth=2.0, label='Ideal Perfect Prediction (y = x)', zorder=4)

    # MAE Confidence Band
    ax2.fill_between([0, max_val], [-mae, max_val - mae], [mae, max_val + mae], 
                     color='#BAE6FD', alpha=0.40, label=f'MAE Error Margin (±{mae:.2f} h)', zorder=2)

    ax2.set_xlim(0, 2600)
    ax2.set_ylim(0, 2600)
    ax2.set_xlabel('Ground Truth Remaining Useful Life (Hours)', fontweight='bold', fontsize=11, color='#0F172A')
    ax2.set_ylabel('Model Predicted Remaining Useful Life (Hours)', fontweight='bold', fontsize=11, color='#0F172A')
    ax2.set_title(f'Empirical RUL Regressor — Actual vs. Predicted Performance\n(Evaluated on {len(y_test):,} Hold-Out Test Samples | R² = {r2:.4f})', 
                  fontweight='bold', fontsize=12, pad=14, color='#0F172A')
    ax2.grid(True, linestyle='--', alpha=0.5, zorder=0)
    ax2.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=9.5)

    fit_box = (
        f"Empirical Test Evaluation Metrics:\n"
        f"• Coefficient of Det. (R²) = {r2:.4f} ({r2*100:.2f}%)\n"
        f"• Mean Absolute Error (MAE)  = {mae:.2f} Hours\n"
        f"• Root Mean Sq. Error (RMSE) = {rmse:.2f} Hours"
    )
    ax2.text(0.55, 0.08, fit_box, transform=ax2.transAxes, fontsize=9.5, color='#065F46',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0FDF4", edgecolor="#10B981", linewidth=1.2))

    fig2.savefig("ml_rul_regression_fit.png", dpi=300, bbox_inches='tight')
    if os.path.exists(artifact_dir):
        shutil.copy("ml_rul_regression_fit.png", os.path.join(artifact_dir, "ml_rul_regression_fit.png"))
    plt.close(fig2)
    print("[SUCCESS] Exported: ml_rul_regression_fit.png")
    print("=" * 75)

if __name__ == "__main__":
    main()
