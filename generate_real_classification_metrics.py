"""
=============================================================================
PROJECT : Digital Twin for Predictive Maintenance of Air Conditioner
MODULE  : Actual Empirical Machine Learning Evaluation & Real Metric Plots
FILE    : generate_real_classification_metrics.py
=============================================================================
This script:
1. Loads the actual 100,000-sample dataset ('ac_realistic_twin_dataset_100k.csv').
2. Loads the trained Decision Tree Classifier ('ac_fault_classifier.joblib').
3. Runs inference on the actual 20,000-sample hold-out test set.
4. Directly extracts scikit-learn empirical metrics:
   - Real Confusion Matrix
   - Real Classification Report (Precision, Recall, F1-Score, Support per class)
5. Plots and saves 100% real, empirical figures (300 DPI):
   - 'ml_classification_metrics.png' (Empirical Per-Class & Overall Metrics)
   - 'ml_confusion_matrix.png'       (Empirical 9x9 Confusion Matrix)
   - 'ml_classification_report.png'  (Formatted Empirical Scientific Report Table)
=============================================================================
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_recall_fscore_support
)
import os
import shutil

# Set clean scientific plotting style
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10

def main():
    print("=" * 75)
    print("RUNNING EMPIRICAL ML EVALUATION ON TEST SET (20,000 SAMPLES)...")
    print("=" * 75)

    # 1. Load Dataset
    df = pd.read_csv("ac_realistic_twin_dataset_100k.csv")
    feature_cols = [
        'indoor_temp', 'indoor_hum', 'outdoor_temp', 'outdoor_hum',
        'comp_temp', 'temp_lift', 'cooling_delta',
        'voltage_v', 'current_amp', 'power_watts', 'power_factor',
        'air_quality_pct'
    ]
    X = df[feature_cols]
    y_clf = df['fault_category']

    # 2. Split exactly matching train_models_100k.py
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_clf, test_size=0.20, random_state=42, stratify=y_clf
    )

    # 3. Load Model & Predict
    clf = joblib.load("ac_fault_classifier.joblib")
    y_pred = clf.predict(X_test)

    # 4. Compute Empirical Metrics
    acc = accuracy_score(y_test, y_pred)
    report_dict = classification_report(y_test, y_pred, digits=4, output_dict=True)
    report_text = classification_report(y_test, y_pred, digits=4)
    cm = confusion_matrix(y_test, y_pred)

    print("\n--- RAW SCIKIT-LEARN EVALUATION OUTPUT ---")
    print(f"Overall Accuracy: {acc*100:.2f}%\n")
    print(report_text)

    classes = sorted(list(y_test.unique()))
    
    # Class abbreviation for clean display
    class_labels_short = [
        'Condenser Foul',
        'Crit Multi-Fault',
        'Filter+Condenser',
        'Filter+Refrigerant',
        'Grid Sag Anomaly',
        'Indoor Filter Clog',
        'Nominal Healthy',
        'Refrig+Condenser',
        'Refrigerant Leak'
    ]

    artifact_dir = r"C:\Users\dhara\.gemini\antigravity\brain\c4f01390-3f83-4fce-991b-ef3ce6ce975c"

    # =========================================================================
    # PLOT 1: EMPIRICAL PER-CLASS CLASSIFICATION METRICS (ml_classification_metrics.png)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(11, 6), dpi=300, facecolor='#FFFFFF')
    
    class_names = [c for c in classes]
    precisions = [report_dict[c]['precision'] * 100 for c in class_names]
    recalls = [report_dict[c]['recall'] * 100 for c in class_names]
    f1_scores = [report_dict[c]['f1-score'] * 100 for c in class_names]

    x = np.arange(len(class_names))
    width = 0.26

    rects1 = ax1.bar(x - width, precisions, width, label='Precision (%)', color='#2563EB', edgecolor='#1E293B', linewidth=0.8)
    rects2 = ax1.bar(x, recalls, width, label='Recall (%)', color='#0D9488', edgecolor='#1E293B', linewidth=0.8)
    rects3 = ax1.bar(x + width, f1_scores, width, label='F1-Score (%)', color='#7C3AED', edgecolor='#1E293B', linewidth=0.8)

    ax1.set_ylabel('Empirical Metric Score (%)', fontweight='bold', fontsize=11, color='#0F172A')
    ax1.set_title(f'Empirical Per-Class Classification Performance\n(Evaluated on {len(y_test):,} Hold-Out Test Samples | Overall Accuracy: {acc*100:.2f}%)', 
                  fontweight='bold', fontsize=12, pad=14, color='#0F172A')
    ax1.set_xticks(x)
    ax1.set_xticklabels(class_labels_short, rotation=22, ha='right', fontsize=9.5, fontweight='medium')
    ax1.set_ylim(80, 103)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    ax1.legend(loc='lower right', frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=10)

    # Overall Summary Badge
    summary_box = (
        f"Overall Model Performance:\n"
        f"• Accuracy : {acc*100:.2f}%\n"
        f"• Macro F1 : {report_dict['macro avg']['f1-score']:.4f}\n"
        f"• Wtd F1   : {report_dict['weighted avg']['f1-score']:.4f}"
    )
    ax1.text(0.02, 0.96, summary_box, transform=ax1.transAxes, fontsize=9.5, va='top',
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0FDF4", edgecolor="#10B981", linewidth=1.2))

    fig1.savefig("ml_classification_metrics.png", dpi=300, bbox_inches='tight')
    if os.path.exists(artifact_dir):
        shutil.copy("ml_classification_metrics.png", os.path.join(artifact_dir, "ml_classification_metrics.png"))
    plt.close(fig1)
    print("[SUCCESS] Exported: ml_classification_metrics.png")

    # =========================================================================
    # PLOT 2: EMPIRICAL 9x9 CONFUSION MATRIX (ml_confusion_matrix.png)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(10, 8.5), dpi=300, facecolor='#FFFFFF')
    
    # Normalize confusion matrix
    cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    im = ax2.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
    cbar = ax2.figure.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel('Normalized Accuracy Proportion', rotation=-90, va="bottom", fontsize=10, fontweight='bold')

    ax2.set(xticks=np.arange(cm.shape[1]),
            yticks=np.arange(cm.shape[0]),
            xticklabels=class_labels_short,
            yticklabels=class_labels_short,
            ylabel='Ground Truth True Class',
            xlabel='Model Predicted Class')

    plt.setp(ax2.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor", fontsize=9)
    plt.setp(ax2.get_yticklabels(), fontsize=9)

    ax2.set_title(f'Empirical 9x9 Fault Classification Confusion Matrix\n(Test Set N = {len(y_test):,} Samples | Accuracy = {acc*100:.2f}%)', 
                  fontweight='bold', fontsize=12, pad=16, color='#0F172A')

    # Annotate counts and percentages in each cell
    thresh = cm_norm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val_text = f"{cm[i, j]:,}\n({cm_norm[i, j]*100:.1f}%)" if cm[i, j] > 0 else "0"
            ax2.text(j, i, val_text,
                     ha="center", va="center", fontsize=7.5,
                     color="white" if cm_norm[i, j] > thresh else "#0F172A",
                     fontweight='bold' if i == j else 'normal')

    fig2.savefig("ml_confusion_matrix.png", dpi=300, bbox_inches='tight')
    if os.path.exists(artifact_dir):
        shutil.copy("ml_confusion_matrix.png", os.path.join(artifact_dir, "ml_confusion_matrix.png"))
    plt.close(fig2)
    print("[SUCCESS] Exported: ml_confusion_matrix.png")

    # =========================================================================
    # PLOT 3: SCIENTIFIC CLASSIFICATION REPORT TABLE (ml_classification_report.png)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(10, 6), dpi=300, facecolor='#FFFFFF')
    ax3.axis('off')

    table_data = []
    for c, short in zip(classes, class_labels_short):
        table_data.append([
            short,
            f"{report_dict[c]['precision']*100:.2f}%",
            f"{report_dict[c]['recall']*100:.2f}%",
            f"{report_dict[c]['f1-score']*100:.2f}%",
            f"{int(report_dict[c]['support']):,}"
        ])
    
    table_data.append(["---", "---", "---", "---", "---"])
    table_data.append([
        "Overall Accuracy", "", "", f"{acc*100:.2f}%", f"{len(y_test):,}"
    ])
    table_data.append([
        "Macro Average",
        f"{report_dict['macro avg']['precision']*100:.2f}%",
        f"{report_dict['macro avg']['recall']*100:.2f}%",
        f"{report_dict['macro avg']['f1-score']*100:.2f}%",
        f"{len(y_test):,}"
    ])
    table_data.append([
        "Weighted Average",
        f"{report_dict['weighted avg']['precision']*100:.2f}%",
        f"{report_dict['weighted avg']['recall']*100:.2f}%",
        f"{report_dict['weighted avg']['f1-score']*100:.2f}%",
        f"{len(y_test):,}"
    ])

    col_labels = ["Operational State / Fault Class", "Precision", "Recall", "F1-Score", "Test Support"]
    table = ax3.table(cellText=table_data, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1.1, 1.4)

    # Style Header
    for j in range(len(col_labels)):
        table[(0, j)].set_facecolor('#1E3A8A')
        table[(0, j)].set_text_props(color='white', fontweight='bold')
    
    # Highlight summary rows
    for row_idx in [len(table_data)-2, len(table_data)-1, len(table_data)]:
        for col_idx in range(len(col_labels)):
            table[(row_idx, col_idx)].set_facecolor('#F1F5F9')
            table[(row_idx, col_idx)].set_text_props(fontweight='bold')

    ax3.set_title(f"Empirical Classification Report Table (Scikit-Learn Output on N = {len(y_test):,} Samples)", 
                  fontweight='bold', fontsize=12, pad=12, color='#0F172A')

    fig3.savefig("ml_classification_report.png", dpi=300, bbox_inches='tight')
    if os.path.exists(artifact_dir):
        shutil.copy("ml_classification_report.png", os.path.join(artifact_dir, "ml_classification_report.png"))
    plt.close(fig3)
    print("[SUCCESS] Exported: ml_classification_report.png")
    print("=" * 75)

if __name__ == "__main__":
    main()
