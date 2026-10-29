import json
import os

phases = [
    # Phase 1: Nominal Healthy (Steps 1-5, 5 seconds)
    {
        "phase": 1,
        "name": "NOMINAL_HEALTHY",
        "samples": [
            {"indoor_temp": 23.58, "indoor_hum": 54.0, "outdoor_temp": 33.32, "outdoor_hum": 73.9, "comp_temp": 47.41, "voltage_v": 230.0, "current_amp": 4.29, "power_watts": 907.5, "power_factor": 0.92, "air_quality_pct": 19.0, "fault_category": "NOMINAL_HEALTHY", "health_score": 100, "rul_hours": 2500.0, "remediation_action": "System operating optimally. Routine preventive maintenance in 180 days."},
            {"indoor_temp": 23.80, "indoor_hum": 53.5, "outdoor_temp": 33.50, "outdoor_hum": 72.0, "comp_temp": 47.80, "voltage_v": 229.5, "current_amp": 4.32, "power_watts": 912.0, "power_factor": 0.92, "air_quality_pct": 19.5, "fault_category": "NOMINAL_HEALTHY", "health_score": 100, "rul_hours": 2500.0, "remediation_action": "System operating optimally. Routine preventive maintenance in 180 days."},
            {"indoor_temp": 23.65, "indoor_hum": 52.8, "outdoor_temp": 33.40, "outdoor_hum": 71.5, "comp_temp": 47.60, "voltage_v": 230.5, "current_amp": 4.25, "power_watts": 899.8, "power_factor": 0.92, "air_quality_pct": 19.2, "fault_category": "NOMINAL_HEALTHY", "health_score": 100, "rul_hours": 2500.0, "remediation_action": "System operating optimally. Routine preventive maintenance in 180 days."},
            {"indoor_temp": 23.70, "indoor_hum": 52.0, "outdoor_temp": 33.60, "outdoor_hum": 70.8, "comp_temp": 47.90, "voltage_v": 229.0, "current_amp": 4.35, "power_watts": 916.4, "power_factor": 0.92, "air_quality_pct": 19.8, "fault_category": "NOMINAL_HEALTHY", "health_score": 100, "rul_hours": 2500.0, "remediation_action": "System operating optimally. Routine preventive maintenance in 180 days."},
            {"indoor_temp": 23.90, "indoor_hum": 51.5, "outdoor_temp": 33.80, "outdoor_hum": 70.0, "comp_temp": 48.20, "voltage_v": 230.0, "current_amp": 4.38, "power_watts": 926.8, "power_factor": 0.92, "air_quality_pct": 20.2, "fault_category": "NOMINAL_HEALTHY", "health_score": 100, "rul_hours": 2500.0, "remediation_action": "System operating optimally. Routine preventive maintenance in 180 days."}
        ]
    },
    # Phase 2: Indoor Filter Clog (Steps 6-10, 5 seconds)
    {
        "phase": 2,
        "name": "INDOOR_FILTER_CLOG",
        "samples": [
            {"indoor_temp": 26.80, "indoor_hum": 54.0, "outdoor_temp": 33.00, "outdoor_hum": 68.0, "comp_temp": 51.00, "voltage_v": 230.0, "current_amp": 4.60, "power_watts": 973.4, "power_factor": 0.92, "air_quality_pct": 68.0, "fault_category": "INDOOR_FILTER_CLOG", "health_score": 65, "rul_hours": 600.0, "remediation_action": "Remove, wash with warm water, and thoroughly dry the indoor mesh filter."},
            {"indoor_temp": 27.00, "indoor_hum": 53.5, "outdoor_temp": 33.20, "outdoor_hum": 67.5, "comp_temp": 51.50, "voltage_v": 229.5, "current_amp": 4.68, "power_watts": 988.2, "power_factor": 0.92, "air_quality_pct": 72.0, "fault_category": "INDOOR_FILTER_CLOG", "health_score": 65, "rul_hours": 580.0, "remediation_action": "Remove, wash with warm water, and thoroughly dry the indoor mesh filter."},
            {"indoor_temp": 27.20, "indoor_hum": 53.0, "outdoor_temp": 33.40, "outdoor_hum": 66.0, "comp_temp": 52.00, "voltage_v": 230.0, "current_amp": 4.72, "power_watts": 998.6, "power_factor": 0.92, "air_quality_pct": 76.0, "fault_category": "INDOOR_FILTER_CLOG", "health_score": 60, "rul_hours": 550.0, "remediation_action": "Remove, wash with warm water, and thoroughly dry the indoor mesh filter."},
            {"indoor_temp": 27.40, "indoor_hum": 52.5, "outdoor_temp": 33.50, "outdoor_hum": 65.0, "comp_temp": 52.50, "voltage_v": 228.5, "current_amp": 4.78, "power_watts": 1004.8, "power_factor": 0.92, "air_quality_pct": 80.0, "fault_category": "INDOOR_FILTER_CLOG", "health_score": 58, "rul_hours": 520.0, "remediation_action": "Remove, wash with warm water, and thoroughly dry the indoor mesh filter."},
            {"indoor_temp": 27.60, "indoor_hum": 52.0, "outdoor_temp": 33.60, "outdoor_hum": 64.0, "comp_temp": 53.00, "voltage_v": 229.0, "current_amp": 4.82, "power_watts": 1015.4, "power_factor": 0.92, "air_quality_pct": 84.0, "fault_category": "INDOOR_FILTER_CLOG", "health_score": 58, "rul_hours": 500.0, "remediation_action": "Remove, wash with warm water, and thoroughly dry the indoor mesh filter."}
        ]
    },
    # Phase 3: Condenser Fouling (Steps 11-15, 5 seconds)
    {
        "phase": 3,
        "name": "CONDENSER_FOULING",
        "samples": [
            {"indoor_temp": 26.50, "indoor_hum": 49.0, "outdoor_temp": 35.00, "outdoor_hum": 58.0, "comp_temp": 73.00, "voltage_v": 229.0, "current_amp": 7.05, "power_watts": 1485.4, "power_factor": 0.92, "air_quality_pct": 21.0, "fault_category": "CONDENSER_FOULING", "health_score": 55, "rul_hours": 250.0, "remediation_action": "Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow."},
            {"indoor_temp": 26.80, "indoor_hum": 48.5, "outdoor_temp": 35.20, "outdoor_hum": 57.0, "comp_temp": 75.00, "voltage_v": 228.5, "current_amp": 7.20, "power_watts": 1513.7, "power_factor": 0.92, "air_quality_pct": 22.0, "fault_category": "CONDENSER_FOULING", "health_score": 50, "rul_hours": 220.0, "remediation_action": "Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow."},
            {"indoor_temp": 27.00, "indoor_hum": 48.0, "outdoor_temp": 35.40, "outdoor_hum": 56.5, "comp_temp": 76.50, "voltage_v": 228.0, "current_amp": 7.35, "power_watts": 1541.7, "power_factor": 0.92, "air_quality_pct": 23.0, "fault_category": "CONDENSER_FOULING", "health_score": 48, "rul_hours": 200.0, "remediation_action": "Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow."},
            {"indoor_temp": 27.20, "indoor_hum": 47.5, "outdoor_temp": 35.60, "outdoor_hum": 56.0, "comp_temp": 78.00, "voltage_v": 227.5, "current_amp": 7.45, "power_watts": 1559.3, "power_factor": 0.92, "air_quality_pct": 23.5, "fault_category": "CONDENSER_FOULING", "health_score": 45, "rul_hours": 190.0, "remediation_action": "Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow."},
            {"indoor_temp": 27.40, "indoor_hum": 47.0, "outdoor_temp": 35.80, "outdoor_hum": 55.5, "comp_temp": 79.20, "voltage_v": 227.0, "current_amp": 7.55, "power_watts": 1576.8, "power_factor": 0.92, "air_quality_pct": 24.0, "fault_category": "CONDENSER_FOULING", "health_score": 45, "rul_hours": 180.0, "remediation_action": "Clean outdoor condenser fins with foaming coil cleaner; verify outdoor fan exhaust airflow."}
        ]
    },
    # Phase 4: Refrigerant Undercharge (Steps 16-20, 5 seconds)
    {
        "phase": 4,
        "name": "REFRIGERANT_UNDERCHARGE",
        "samples": [
            {"indoor_temp": 32.00, "indoor_hum": 68.0, "outdoor_temp": 33.80, "outdoor_hum": 65.0, "comp_temp": 64.00, "voltage_v": 230.0, "current_amp": 3.80, "power_watts": 804.1, "power_factor": 0.92, "air_quality_pct": 20.5, "fault_category": "REFRIGERANT_UNDERCHARGE", "health_score": 50, "rul_hours": 300.0, "remediation_action": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A."},
            {"indoor_temp": 32.40, "indoor_hum": 69.0, "outdoor_temp": 34.00, "outdoor_hum": 64.5, "comp_temp": 65.50, "voltage_v": 229.5, "current_amp": 3.72, "power_watts": 785.4, "power_factor": 0.92, "air_quality_pct": 21.0, "fault_category": "REFRIGERANT_UNDERCHARGE", "health_score": 48, "rul_hours": 270.0, "remediation_action": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A."},
            {"indoor_temp": 32.80, "indoor_hum": 70.0, "outdoor_temp": 34.20, "outdoor_hum": 64.0, "comp_temp": 66.80, "voltage_v": 229.0, "current_amp": 3.65, "power_watts": 769.0, "power_factor": 0.92, "air_quality_pct": 21.5, "fault_category": "REFRIGERANT_UNDERCHARGE", "health_score": 45, "rul_hours": 250.0, "remediation_action": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A."},
            {"indoor_temp": 33.10, "indoor_hum": 71.0, "outdoor_temp": 34.40, "outdoor_hum": 63.5, "comp_temp": 67.50, "voltage_v": 229.0, "current_amp": 3.58, "power_watts": 754.2, "power_factor": 0.92, "air_quality_pct": 22.0, "fault_category": "REFRIGERANT_UNDERCHARGE", "health_score": 45, "rul_hours": 240.0, "remediation_action": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A."},
            {"indoor_temp": 33.40, "indoor_hum": 71.5, "outdoor_temp": 34.50, "outdoor_hum": 63.0, "comp_temp": 68.20, "voltage_v": 228.5, "current_amp": 3.50, "power_watts": 735.8, "power_factor": 0.92, "air_quality_pct": 22.5, "fault_category": "REFRIGERANT_UNDERCHARGE", "health_score": 42, "rul_hours": 230.0, "remediation_action": "Perform electronic/bubble leak check on flare joints, seal leak, pull deep vacuum, and recharge rated R32/R410A."}
        ]
    },
    # Phase 5: Grid Voltage Anomaly (Steps 21-25, 5 seconds)
    {
        "phase": 5,
        "name": "GRID_VOLTAGE_ANOMALY",
        "samples": [
            {"indoor_temp": 24.80, "indoor_hum": 52.0, "outdoor_temp": 33.20, "outdoor_hum": 66.0, "comp_temp": 55.40, "voltage_v": 198.5, "current_amp": 7.85, "power_watts": 1433.6, "power_factor": 0.92, "air_quality_pct": 20.0, "fault_category": "GRID_VOLTAGE_ANOMALY", "health_score": 60, "rul_hours": 450.0, "remediation_action": "Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS)."},
            {"indoor_temp": 25.00, "indoor_hum": 52.5, "outdoor_temp": 33.30, "outdoor_hum": 65.5, "comp_temp": 56.00, "voltage_v": 197.8, "current_amp": 7.92, "power_watts": 1441.1, "power_factor": 0.92, "air_quality_pct": 20.5, "fault_category": "GRID_VOLTAGE_ANOMALY", "health_score": 60, "rul_hours": 440.0, "remediation_action": "Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS)."},
            {"indoor_temp": 25.20, "indoor_hum": 53.0, "outdoor_temp": 33.40, "outdoor_hum": 65.0, "comp_temp": 56.80, "voltage_v": 197.0, "current_amp": 8.00, "power_watts": 1449.9, "power_factor": 0.92, "air_quality_pct": 20.8, "fault_category": "GRID_VOLTAGE_ANOMALY", "health_score": 58, "rul_hours": 430.0, "remediation_action": "Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS)."},
            {"indoor_temp": 25.40, "indoor_hum": 53.5, "outdoor_temp": 33.50, "outdoor_hum": 64.5, "comp_temp": 57.50, "voltage_v": 196.5, "current_amp": 8.08, "power_watts": 1460.6, "power_factor": 0.92, "air_quality_pct": 21.0, "fault_category": "GRID_VOLTAGE_ANOMALY", "health_score": 58, "rul_hours": 420.0, "remediation_action": "Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS)."},
            {"indoor_temp": 25.60, "indoor_hum": 54.0, "outdoor_temp": 33.60, "outdoor_hum": 64.0, "comp_temp": 58.20, "voltage_v": 196.0, "current_amp": 8.15, "power_watts": 1469.6, "power_factor": 0.92, "air_quality_pct": 21.5, "fault_category": "GRID_VOLTAGE_ANOMALY", "health_score": 55, "rul_hours": 400.0, "remediation_action": "Inspect electrical distribution board; verify breaker connections and install an Automatic Voltage Stabilizer (AVS)."}
        ]
    },
    # Phase 6: Dual Compound - Indoor Filter + Outdoor Condenser (Steps 26-30, 5 seconds)
    {
        "phase": 6,
        "name": "FILTER_AND_CONDENSER_FAULT",
        "samples": [
            {"indoor_temp": 28.50, "indoor_hum": 56.0, "outdoor_temp": 35.00, "outdoor_hum": 60.0, "comp_temp": 76.50, "voltage_v": 228.0, "current_amp": 7.20, "power_watts": 1510.3, "power_factor": 0.92, "air_quality_pct": 74.0, "fault_category": "FILTER_AND_CONDENSER_FAULT", "health_score": 35, "rul_hours": 120.0, "remediation_action": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger."},
            {"indoor_temp": 28.80, "indoor_hum": 56.5, "outdoor_temp": 35.20, "outdoor_hum": 59.5, "comp_temp": 77.20, "voltage_v": 227.5, "current_amp": 7.30, "power_watts": 1528.1, "power_factor": 0.92, "air_quality_pct": 76.0, "fault_category": "FILTER_AND_CONDENSER_FAULT", "health_score": 35, "rul_hours": 115.0, "remediation_action": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger."},
            {"indoor_temp": 29.00, "indoor_hum": 57.0, "outdoor_temp": 35.40, "outdoor_hum": 59.0, "comp_temp": 78.00, "voltage_v": 227.0, "current_amp": 7.38, "power_watts": 1541.2, "power_factor": 0.92, "air_quality_pct": 78.0, "fault_category": "FILTER_AND_CONDENSER_FAULT", "health_score": 32, "rul_hours": 110.0, "remediation_action": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger."},
            {"indoor_temp": 29.30, "indoor_hum": 57.5, "outdoor_temp": 35.60, "outdoor_hum": 58.5, "comp_temp": 78.80, "voltage_v": 226.5, "current_amp": 7.45, "power_watts": 1552.4, "power_factor": 0.92, "air_quality_pct": 80.0, "fault_category": "FILTER_AND_CONDENSER_FAULT", "health_score": 30, "rul_hours": 105.0, "remediation_action": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger."},
            {"indoor_temp": 29.50, "indoor_hum": 58.0, "outdoor_temp": 35.80, "outdoor_hum": 58.0, "comp_temp": 79.50, "voltage_v": 226.0, "current_amp": 7.52, "power_watts": 1563.6, "power_factor": 0.92, "air_quality_pct": 82.0, "fault_category": "FILTER_AND_CONDENSER_FAULT", "health_score": 30, "rul_hours": 100.0, "remediation_action": "Perform dual-side maintenance: wash indoor filter mesh and chemically wash outdoor condenser heat exchanger."}
        ]
    },
    # Phase 7: Dual Compound - Refrigerant Leak + Outdoor Condenser (Steps 31-35, 5 seconds)
    {
        "phase": 7,
        "name": "REFRIGERANT_LEAK_AND_CONDENSER_FAULT",
        "samples": [
            {"indoor_temp": 33.20, "indoor_hum": 70.0, "outdoor_temp": 35.50, "outdoor_hum": 58.0, "comp_temp": 82.50, "voltage_v": 227.0, "current_amp": 6.80, "power_watts": 1419.8, "power_factor": 0.92, "air_quality_pct": 22.0, "fault_category": "REFRIGERANT_LEAK_AND_CONDENSER_FAULT", "health_score": 25, "rul_hours": 48.0, "remediation_action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out."},
            {"indoor_temp": 33.50, "indoor_hum": 70.5, "outdoor_temp": 35.60, "outdoor_hum": 57.5, "comp_temp": 83.20, "voltage_v": 226.5, "current_amp": 6.90, "power_watts": 1437.8, "power_factor": 0.92, "air_quality_pct": 22.5, "fault_category": "REFRIGERANT_LEAK_AND_CONDENSER_FAULT", "health_score": 25, "rul_hours": 45.0, "remediation_action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out."},
            {"indoor_temp": 33.80, "indoor_hum": 71.0, "outdoor_temp": 35.80, "outdoor_hum": 57.0, "comp_temp": 84.00, "voltage_v": 226.0, "current_amp": 6.98, "power_watts": 1451.3, "power_factor": 0.92, "air_quality_pct": 23.0, "fault_category": "REFRIGERANT_LEAK_AND_CONDENSER_FAULT", "health_score": 22, "rul_hours": 40.0, "remediation_action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out."},
            {"indoor_temp": 34.00, "indoor_hum": 71.5, "outdoor_temp": 36.00, "outdoor_hum": 56.5, "comp_temp": 84.80, "voltage_v": 225.5, "current_amp": 7.05, "power_watts": 1462.6, "power_factor": 0.92, "air_quality_pct": 23.5, "fault_category": "REFRIGERANT_LEAK_AND_CONDENSER_FAULT", "health_score": 20, "rul_hours": 36.0, "remediation_action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out."},
            {"indoor_temp": 34.20, "indoor_hum": 72.0, "outdoor_temp": 36.20, "outdoor_hum": 56.0, "comp_temp": 85.50, "voltage_v": 225.0, "current_amp": 7.12, "power_watts": 1473.8, "power_factor": 0.92, "air_quality_pct": 24.0, "fault_category": "REFRIGERANT_LEAK_AND_CONDENSER_FAULT", "health_score": 20, "rul_hours": 32.0, "remediation_action": "Immediate attention: Clean condenser fins, repair refrigerant leak, and top up refrigerant charge to prevent compressor burn-out."}
        ]
    },
    # Phase 8: Dual Compound - Indoor Filter + Refrigerant Leak (Steps 36-40, 5 seconds)
    {
        "phase": 8,
        "name": "FILTER_AND_REFRIGERANT_FAULT",
        "samples": [
            {"indoor_temp": 32.50, "indoor_hum": 72.0, "outdoor_temp": 34.00, "outdoor_hum": 62.0, "comp_temp": 68.00, "voltage_v": 230.0, "current_amp": 4.10, "power_watts": 867.6, "power_factor": 0.92, "air_quality_pct": 78.0, "fault_category": "FILTER_AND_REFRIGERANT_FAULT", "health_score": 30, "rul_hours": 100.0, "remediation_action": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge."},
            {"indoor_temp": 32.80, "indoor_hum": 72.5, "outdoor_temp": 34.20, "outdoor_hum": 61.5, "comp_temp": 68.80, "voltage_v": 229.5, "current_amp": 4.15, "power_watts": 876.2, "power_factor": 0.92, "air_quality_pct": 80.0, "fault_category": "FILTER_AND_REFRIGERANT_FAULT", "health_score": 30, "rul_hours": 95.0, "remediation_action": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge."},
            {"indoor_temp": 33.10, "indoor_hum": 73.0, "outdoor_temp": 34.40, "outdoor_hum": 61.0, "comp_temp": 69.50, "voltage_v": 229.0, "current_amp": 4.20, "power_watts": 884.8, "power_factor": 0.92, "air_quality_pct": 82.0, "fault_category": "FILTER_AND_REFRIGERANT_FAULT", "health_score": 28, "rul_hours": 90.0, "remediation_action": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge."},
            {"indoor_temp": 33.40, "indoor_hum": 73.5, "outdoor_temp": 34.60, "outdoor_hum": 60.5, "comp_temp": 70.20, "voltage_v": 228.5, "current_amp": 4.25, "power_watts": 893.4, "power_factor": 0.92, "air_quality_pct": 84.0, "fault_category": "FILTER_AND_REFRIGERANT_FAULT", "health_score": 25, "rul_hours": 85.0, "remediation_action": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge."},
            {"indoor_temp": 33.70, "indoor_hum": 74.0, "outdoor_temp": 34.80, "outdoor_hum": 60.0, "comp_temp": 71.00, "voltage_v": 228.0, "current_amp": 4.30, "power_watts": 901.9, "power_factor": 0.92, "air_quality_pct": 86.0, "fault_category": "FILTER_AND_REFRIGERANT_FAULT", "health_score": 25, "rul_hours": 80.0, "remediation_action": "Clean indoor filter mesh, defrost evaporator coil, and top up refrigerant charge."}
        ]
    },
    # Phase 9: Triple Compound Multi-Point Fault (Steps 41-45, 5 seconds)
    {
        "phase": 9,
        "name": "CRITICAL_COMPOUND_MULTI_FAULT",
        "samples": [
            {"indoor_temp": 34.00, "indoor_hum": 75.0, "outdoor_temp": 36.00, "outdoor_hum": 55.0, "comp_temp": 88.50, "voltage_v": 225.0, "current_amp": 7.80, "power_watts": 1614.6, "power_factor": 0.92, "air_quality_pct": 85.0, "fault_category": "CRITICAL_COMPOUND_MULTI_FAULT", "health_score": 10, "rul_hours": 24.0, "remediation_action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."},
            {"indoor_temp": 34.40, "indoor_hum": 75.5, "outdoor_temp": 36.20, "outdoor_hum": 54.5, "comp_temp": 89.50, "voltage_v": 224.5, "current_amp": 7.95, "power_watts": 1642.0, "power_factor": 0.92, "air_quality_pct": 87.0, "fault_category": "CRITICAL_COMPOUND_MULTI_FAULT", "health_score": 10, "rul_hours": 20.0, "remediation_action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."},
            {"indoor_temp": 34.70, "indoor_hum": 76.0, "outdoor_temp": 36.50, "outdoor_hum": 54.0, "comp_temp": 90.80, "voltage_v": 224.0, "current_amp": 8.10, "power_watts": 1669.6, "power_factor": 0.92, "air_quality_pct": 89.0, "fault_category": "CRITICAL_COMPOUND_MULTI_FAULT", "health_score": 8, "rul_hours": 16.0, "remediation_action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."},
            {"indoor_temp": 35.00, "indoor_hum": 76.5, "outdoor_temp": 36.80, "outdoor_hum": 53.5, "comp_temp": 91.80, "voltage_v": 223.5, "current_amp": 8.25, "power_watts": 1696.3, "power_factor": 0.92, "air_quality_pct": 91.0, "fault_category": "CRITICAL_COMPOUND_MULTI_FAULT", "health_score": 5, "rul_hours": 12.0, "remediation_action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."},
            {"indoor_temp": 35.30, "indoor_hum": 77.0, "outdoor_temp": 37.00, "outdoor_hum": 53.0, "comp_temp": 93.00, "voltage_v": 223.0, "current_amp": 8.40, "power_watts": 1723.3, "power_factor": 0.92, "air_quality_pct": 93.0, "fault_category": "CRITICAL_COMPOUND_MULTI_FAULT", "health_score": 5, "rul_hours": 8.0, "remediation_action": "Critical multi-point failure! Shut down AC immediately. Overhaul refrigerant circuit, clean all coils, and inspect compressor windings."}
        ]
    }
]

flat_samples = []
for p in phases:
    for s in p["samples"]:
        flat_samples.append(s)

out_file = r"C:\Users\dhara\.gemini\antigravity\scratch\ac_digital_twin\nodered_flows\curated_replay_dataset.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(flat_samples, f, indent=2)

print(f"Generated {len(flat_samples)} curated replay samples across {len(phases)} phases ({len(phases)*5} seconds playback).")
