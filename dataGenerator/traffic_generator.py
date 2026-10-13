"""
AURA — Traffic & Parking Dataset Generator
Facility: HOSPITAL_001
Module: Traffic & Parking Intelligence

Generates 15-minute interval readings for 5 hospital traffic/parking zones
over 90 days. Includes realistic time-of-day, weekday/weekend patterns,
and controlled anomaly periods.

This is synthetic operational decision-support data only.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

FACILITY_ID = "HOSPITAL_001"
SOURCE = "synthetic"

START_DATE = datetime(2026, 1, 1, 0, 0, 0)
DAYS_TO_SIMULATE = 90
END_DATE = START_DATE + timedelta(days=DAYS_TO_SIMULATE)

INTERVAL_MINUTES = 15  # one reading every 15 minutes

ZONES = [
    "MAIN_GATE",
    "EMERGENCY_GATE",
    "VISITOR_PARKING",
    "STAFF_PARKING",
    "SERVICE_ENTRY",
]

VALID_TRAFFIC_STATUS = {"NORMAL", "BUSY", "CONGESTED"}
VALID_OPERATIONAL_STATUS = {"NORMAL", "MAINTENANCE", "REDUCED_OPERATION", "EMERGENCY"}

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "traffic.csv"

ANOMALY_WINDOWS = [
    (12, 9, 4, {"MAIN_GATE", "VISITOR_PARKING"}),
    (38, 14, 6, {"EMERGENCY_GATE", "MAIN_GATE"}),
    (71, 8, 5, {"STAFF_PARKING", "SERVICE_ENTRY"}),
]

GATE_ZONES = {"MAIN_GATE", "EMERGENCY_GATE"}

ZONE_CONFIG = {
    "MAIN_GATE":       {"max_vehicles": 35, "max_occupancy": 0,   "max_wait": 12},
    "EMERGENCY_GATE":  {"max_vehicles": 20, "max_occupancy": 0,   "max_wait": 5},
    "VISITOR_PARKING": {"max_vehicles": 10, "max_occupancy": 100, "max_wait": 15},
    "STAFF_PARKING":   {"max_vehicles": 8,  "max_occupancy": 100, "max_wait": 8},
    "SERVICE_ENTRY":   {"max_vehicles": 8,  "max_occupancy": 60,  "max_wait": 10},
}


def _build_anomaly_set(start_date):
    anomaly_map = {}
    for (day_offset, start_hour, duration_hours, zones) in ANOMALY_WINDOWS:
        window_start = start_date + timedelta(days=day_offset, hours=start_hour)
        steps = int(duration_hours * 60 / INTERVAL_MINUTES)
        for i in range(steps):
            ts = window_start + timedelta(minutes=i * INTERVAL_MINUTES)
            if ts not in anomaly_map:
                anomaly_map[ts] = set()
            anomaly_map[ts].update(zones)
    return anomaly_map


def _time_of_day_factor(hour, zone):
    if zone == "MAIN_GATE":
        if 8 <= hour < 10: return 1.0
        elif 16 <= hour < 18: return 0.9
        elif 10 <= hour < 16: return 0.6
        elif 6 <= hour < 8 or 18 <= hour < 20: return 0.4
        else: return 0.1
    elif zone == "EMERGENCY_GATE":
        if 2 <= hour < 6: return 0.5
        elif 8 <= hour < 20: return 0.85
        else: return 0.7
    elif zone == "VISITOR_PARKING":
        if 10 <= hour < 13: return 1.0
        elif 16 <= hour < 19: return 0.9
        elif 13 <= hour < 16: return 0.5
        elif 8 <= hour < 10 or 19 <= hour < 21: return 0.3
        else: return 0.05
    elif zone == "STAFF_PARKING":
        if 7 <= hour < 9: return 1.0
        elif 9 <= hour < 17: return 0.8
        elif 17 <= hour < 19: return 0.6
        elif 5 <= hour < 7: return 0.2
        else: return 0.1
    elif zone == "SERVICE_ENTRY":
        if 7 <= hour < 12: return 0.9
        elif 12 <= hour < 15: return 0.5
        elif 15 <= hour < 18: return 0.3
        else: return 0.05
    return 0.5


def _weekday_factor(weekday, zone):
    is_weekend = weekday >= 5
    if zone == "STAFF_PARKING":
        return 0.25 if is_weekend else 1.0
    elif zone == "SERVICE_ENTRY":
        if weekday == 6: return 0.2
        elif weekday == 5: return 0.5
        return 1.0
    elif zone == "VISITOR_PARKING":
        return 1.1 if is_weekend else 1.0
    elif zone == "MAIN_GATE":
        return 0.7 if is_weekend else 1.0
    elif zone == "EMERGENCY_GATE":
        return 1.0
    return 1.0


def generate_traffic_data():
    print("=" * 70)
    print("AURA: Generating Synthetic Traffic & Parking Dataset (HOSPITAL_001)")
    print(f"Horizon: ~{DAYS_TO_SIMULATE} days (15-min Interval Time-Series)")
    print(f"Zones: {', '.join(ZONES)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    anomaly_map = _build_anomaly_set(START_DATE)

    total_intervals = DAYS_TO_SIMULATE * 24 * (60 // INTERVAL_MINUTES)
    timestamps = [
        START_DATE + timedelta(minutes=i * INTERVAL_MINUTES)
        for i in range(total_intervals)
    ]

    records = []

    for ts in timestamps:
        hour = ts.hour
        weekday = ts.weekday()
        is_anomaly_window = ts in anomaly_map

        for zone in ZONES:
            cfg = ZONE_CONFIG[zone]
            tod_factor = _time_of_day_factor(hour, zone)
            wd_factor  = _weekday_factor(weekday, zone)
            base_factor = tod_factor * wd_factor

            is_zone_anomalous = is_anomaly_window and (zone in anomaly_map[ts])

            max_v = cfg["max_vehicles"]
            noise = np.random.uniform(0.85, 1.15)
            v_count_float = base_factor * max_v * noise
            if is_zone_anomalous:
                v_count_float *= np.random.uniform(1.4, 1.8)
            vehicle_count = max(0, int(round(v_count_float)))

            if zone in GATE_ZONES:
                parking_occ = 0.0
            else:
                max_occ = cfg["max_occupancy"]
                occ_noise = np.random.uniform(0.90, 1.10)
                occ = base_factor * max_occ * occ_noise
                if is_zone_anomalous:
                    occ *= np.random.uniform(1.2, 1.4)
                parking_occ = round(float(np.clip(occ, 0, 100)), 1)

            max_wait = cfg["max_wait"]
            wait_factor = base_factor * np.random.uniform(0.7, 1.3)
            wait_time = max_wait * wait_factor
            if is_zone_anomalous:
                wait_time *= np.random.uniform(1.5, 2.5)
            average_wait_time = round(float(max(0, wait_time)), 1)

            if zone in GATE_ZONES:
                load = vehicle_count / max(cfg["max_vehicles"], 1)
            else:
                load = (parking_occ / 100.0) if parking_occ > 0 else (vehicle_count / max(cfg["max_vehicles"], 1))
            if is_zone_anomalous:
                load = min(load * 1.3, 1.0)

            if load >= 0.85:
                traffic_status = "CONGESTED"
            elif load >= 0.55:
                traffic_status = "BUSY"
            else:
                traffic_status = "NORMAL"

            rand_op = np.random.random()
            if is_zone_anomalous:
                if rand_op < 0.15:
                    operational_status = "EMERGENCY"
                elif rand_op < 0.25:
                    operational_status = "REDUCED_OPERATION"
                else:
                    operational_status = "NORMAL"
            else:
                if rand_op < 0.005:
                    operational_status = "MAINTENANCE"
                elif rand_op < 0.015:
                    operational_status = "REDUCED_OPERATION"
                else:
                    operational_status = "NORMAL"

            anomaly_flag = 1 if is_zone_anomalous else 0

            records.append({
                "timestamp":                  ts,
                "facility_id":                FACILITY_ID,
                "zone_id":                    zone,
                "vehicle_count":              vehicle_count,
                "parking_occupancy_percent":  parking_occ,
                "average_wait_time_min":      average_wait_time,
                "traffic_status":             traffic_status,
                "operational_status":         operational_status,
                "source":                     SOURCE,
                "anomaly_flag":               anomaly_flag,
            })

    df = pd.DataFrame(records)
    return df


def validate_traffic_data(df):
    checks = []

    checks.append(("DataFrame is not empty", len(df) > 0))

    expected_cols = [
        "timestamp", "facility_id", "zone_id", "vehicle_count",
        "parking_occupancy_percent", "average_wait_time_min",
        "traffic_status", "operational_status", "source", "anomaly_flag"
    ]
    checks.append(("Exact expected columns present", list(df.columns) == expected_cols))
    checks.append(("No extra columns", set(df.columns) == set(expected_cols)))
    checks.append(("No missing values", df.isnull().sum().sum() == 0))
    checks.append(("No duplicate rows", df.duplicated().sum() == 0))
    checks.append(("Timestamp is datetime", pd.api.types.is_datetime64_any_dtype(df["timestamp"])))

    day_range = (df["timestamp"].max() - df["timestamp"].min()).days
    checks.append((f"~90-day coverage (got {day_range} days)", 85 <= day_range <= 95))

    expected_count = DAYS_TO_SIMULATE * 24 * (60 // INTERVAL_MINUTES) * len(ZONES)
    actual_count = len(df)
    checks.append((f"Expected ~43,200 records (got {actual_count})", abs(actual_count - expected_count) <= 200))

    checks.append(("facility_id is HOSPITAL_001", (df["facility_id"] == "HOSPITAL_001").all()))
    checks.append(("zone_id values are valid", set(df["zone_id"].unique()) == set(ZONES)))
    checks.append(("vehicle_count >= 0", (df["vehicle_count"] >= 0).all()))
    checks.append(("parking_occupancy_percent in [0, 100]", df["parking_occupancy_percent"].between(0, 100).all()))
    checks.append(("average_wait_time_min >= 0", (df["average_wait_time_min"] >= 0).all()))
    checks.append(("traffic_status values valid", set(df["traffic_status"].unique()).issubset(VALID_TRAFFIC_STATUS)))
    checks.append(("operational_status values valid", set(df["operational_status"].unique()).issubset(VALID_OPERATIONAL_STATUS)))
    checks.append(("source is always 'synthetic'", (df["source"] == "synthetic").all()))
    checks.append(("anomaly_flag contains only 0/1", set(df["anomaly_flag"].unique()).issubset({0, 1})))

    anomaly_rows = df[df["anomaly_flag"] == 1]
    normal_rows  = df[df["anomaly_flag"] == 0]
    checks.append(("Anomaly rows have higher avg vehicle_count than normal",
                   anomaly_rows["vehicle_count"].mean() > normal_rows["vehicle_count"].mean()))

    congested_pct = (df["traffic_status"] == "CONGESTED").mean()
    checks.append((f"CONGESTED < 25% of rows (got {congested_pct:.1%})", congested_pct < 0.25))

    zone_df = df[df["zone_id"] == "MAIN_GATE"].sort_values("timestamp")
    diffs = zone_df["timestamp"].diff().dropna()
    checks.append(("15-min interval consistent for MAIN_GATE", (diffs == pd.Timedelta(minutes=15)).all()))

    passed = 0
    failed = 0
    for desc, result in checks:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {desc}")
        if result: passed += 1
        else: failed += 1

    total = len(checks)
    if failed == 0:
        print(f"\nAll {total} Traffic & Parking Data Quality Validation checks PASSED successfully!")
    else:
        print(f"\n{failed} check(s) FAILED ({passed}/{total} passed)")
    return failed == 0


def print_summary(df):
    anomaly_count = (df["anomaly_flag"] == 1).sum()
    anomaly_pct   = anomaly_count / len(df) * 100
    print("\n" + "=" * 70)
    print("TRAFFIC & PARKING DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Records:              {len(df):,}")
    print(f"Total Columns:              {len(df.columns)}")
    print(f"Schema Columns:             {list(df.columns)}")
    print(f"First Timestamp:            {df['timestamp'].min()}")
    print(f"Last Timestamp:             {df['timestamp'].max()}")
    print(f"\nRecords by Zone:")
    for zone, cnt in df.groupby("zone_id")["timestamp"].count().items():
        print(f"  {zone:<20}: {cnt:,}")
    print(f"\nTraffic Status Distribution:")
    for status, cnt in df["traffic_status"].value_counts().items():
        print(f"  {status:<15}: {cnt:,}  ({cnt/len(df)*100:.1f}%)")
    print(f"\nAvg Vehicle Count by Zone:")
    for zone, avg in df.groupby("zone_id")["vehicle_count"].mean().items():
        print(f"  {zone:<20}: {avg:.1f}")
    print(f"\nAvg Parking Occupancy % by Zone:")
    for zone, avg in df.groupby("zone_id")["parking_occupancy_percent"].mean().items():
        print(f"  {zone:<20}: {avg:.1f}%")
    print(f"\nAvg Wait Time:              {df['average_wait_time_min'].mean():.1f} min")
    print(f"Controlled Anomaly Records: {anomaly_count:,} ({anomaly_pct:.1f}%)")
    print(f"Output File Path:           {OUTPUT_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    df = generate_traffic_data()
    print("\nRunning Traffic & Parking Data Quality Validation...")
    all_passed = validate_traffic_data(df)
    if all_passed:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nDataset saved successfully to: {OUTPUT_FILE}")
    else:
        print("\nValidation failed — dataset NOT saved.")
    print_summary(df)
