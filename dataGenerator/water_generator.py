"""
AURA - AI-Powered Sustainable Facility Intelligence Platform
Synthetic Water Dataset Generator for Hospital Demo (BPUT Hackathon 2026 PS04)

Generates 90 days of realistic 15-minute interval water telemetry across
5 hospital zones (ICU, Emergency, General_Ward, OPD, Admin).

Schema (10 columns):
1. timestamp
2. facility_id
3. zone_id
4. water_litres
5. occupancy_percent
6. temperature_c
7. operational_status
8. water_source
9. source
10. anomaly_flag
"""

import math
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# 1. Configuration & Reproducibility
# ----------------------------------------------------------------------
# Fixed seed taaki har run pe exactly same data generate ho (Java me Random(42) jaisa)
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

FACILITY_ID = "H001"
HOSPITAL_ZONES = ["ICU", "Emergency", "General_Ward", "OPD", "Admin"]

START_DATE = datetime(2026, 1, 1, 0, 0, 0)
DAYS_TO_SIMULATE = 90
INTERVAL_MINUTES = 15
INTERVALS_PER_DAY = (24 * 60) // INTERVAL_MINUTES  # 96 readings har din per zone
TOTAL_INTERVALS = DAYS_TO_SIMULATE * INTERVALS_PER_DAY  # 8,640 intervals
EXPECTED_TOTAL_ROWS = TOTAL_INTERVALS * len(HOSPITAL_ZONES)  # 43,200 rows

# File paths safely resolve relative to project root
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "water.csv"

# Allowed Domain Values
ALLOWED_STATUSES = {"NORMAL", "MAINTENANCE", "REDUCED_OPERATION", "EMERGENCY"}
ALLOWED_WATER_SOURCES = {"MUNICIPAL", "BOREWELL", "RECYCLED"}

# Zone-wise baseline specs (Litres per 15-minute interval)
ZONE_WATER_SPECS = {
    "General_Ward": {
        "base_litres": 110.0,   # Sabse zyada pani wards me lagta hai (toilets, baths, cleaning)
        "occ_factor": 0.8,
        "is_24_7": True,
    },
    "ICU": {
        "base_litres": 85.0,    # Continuous water for dialysis, sterilizers, hygiene scrub stations
        "occ_factor": 0.4,
        "is_24_7": True,
    },
    "Emergency": {
        "base_litres": 75.0,    # Trauma wash, sanitation, 24/7 staff and patient needs
        "occ_factor": 0.5,
        "is_24_7": True,
    },
    "OPD": {
        "base_litres": 35.0,    # Daytime public washrooms, coolers; night me near-zero
        "occ_factor": 0.9,
        "is_24_7": False,
    },
    "Admin": {
        "base_litres": 20.0,    # Office staff washrooms, pantry; night/weekend idle
        "occ_factor": 0.7,
        "is_24_7": False,
    },
}


# ----------------------------------------------------------------------
# 2. Environmental Simulation (Ambient Temperature in °C)
# ----------------------------------------------------------------------
def get_ambient_temperature(dt: datetime) -> float:
    """
    Simulates outdoor temperature in Celsius (°C).
    Subah 05:00 AM par minimum ~22°C, dopahar 14:00 par maximum ~36°C.
    """
    day_fraction = (dt.hour * 60 + dt.minute) / 1440.0
    day_of_year = dt.timetuple().tm_yday

    diurnal_cycle = -math.cos(2 * math.pi * (day_fraction - 0.21))
    seasonal_drift = 25.0 + (day_of_year / 90.0) * 5.0
    amplitude = 6.5
    noise = random.uniform(-0.7, 0.7)

    temp_c = seasonal_drift + (amplitude * diurnal_cycle) + noise
    return round(temp_c, 1)


# ----------------------------------------------------------------------
# 3. Operational Status Simulation
# ----------------------------------------------------------------------
def get_operational_status(zone: str, dt: datetime) -> str:
    """
    Returns zone status: NORMAL, MAINTENANCE, REDUCED_OPERATION, EMERGENCY.
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    # 1. Acute emergency surge (~0.3% chance in Emergency/ICU)
    if zone in ["Emergency", "ICU"] and random.random() < 0.003:
        return "EMERGENCY"

    # 2. Routine plumbing/tank maintenance (Sunday mornings 06:00-09:00)
    if is_sunday and 6.0 <= hour <= 9.0 and random.random() < 0.20:
        return "MAINTENANCE"

    # 3. Night off-hours me reduced operation
    if zone == "OPD":
        if is_sunday or hour < 7.5 or hour > 18.0:
            return "REDUCED_OPERATION"
    elif zone == "Admin":
        if is_weekend or hour < 8.0 or hour > 19.0:
            return "REDUCED_OPERATION"
    elif zone == "General_Ward":
        if 23.0 <= hour or hour <= 5.0:
            return "REDUCED_OPERATION"

    return "NORMAL"


# ----------------------------------------------------------------------
# 4. Water Source Simulation
# ----------------------------------------------------------------------
def get_water_source(zone: str, dt: datetime) -> str:
    """
    Simulates water source: MUNICIPAL (~70%), BOREWELL (~22%), RECYCLED (~8%).
    Admin aur OPD non-potable flush systems me treated recycled water use karte hain.
    """
    hour = dt.hour + (dt.minute / 60.0)
    roll = random.random()

    # Recycled treated greywater used for flushing in Admin/OPD
    if zone in ["Admin", "OPD"] and 8.0 <= hour <= 18.0 and roll < 0.25:
        return "RECYCLED"

    # Morning high-demand time (06:00 - 10:00) me borewell pumps auxiliary support dete hain
    if 6.0 <= hour <= 10.0 and roll < 0.40:
        return "BOREWELL"

    # General background borewell usage
    if roll < 0.18:
        return "BOREWELL"

    # Primary main feed
    return "MUNICIPAL"


# ----------------------------------------------------------------------
# 5. Occupancy Simulation
# ----------------------------------------------------------------------
def get_zone_occupancy(zone: str, dt: datetime, status: str) -> float:
    """
    Calculates realistic zone occupancy percentage (0.0 to 100.0%).
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    # Agar zone night me band hai
    if status == "REDUCED_OPERATION":
        if zone in ["OPD", "Admin"]:
            return round(random.uniform(0.0, 4.0), 1)
        elif zone == "General_Ward":
            return round(random.uniform(50.0, 62.0), 1)

    if zone == "ICU":
        # 24/7 high continuous occupancy (75% to 95%)
        base = 85.0 + random.uniform(-8.0, 7.0)
        return round(max(60.0, min(100.0, base)), 1)

    elif zone == "Emergency":
        # Evening, night aur weekend me trauma surge
        if 18 <= hour <= 23 or 0 <= hour <= 3:
            base = 76.0 + random.uniform(-10.0, 14.0)
        elif 9 <= hour < 18:
            base = 62.0 + random.uniform(-10.0, 10.0)
        else:
            base = 48.0 + random.uniform(-10.0, 10.0)

        if is_weekend:
            base += 8.0
        if status == "EMERGENCY":
            base = min(100.0, base + 20.0)
        return round(max(20.0, min(100.0, base)), 1)

    elif zone == "General_Ward":
        # Visiting hours (16:00 - 19:00) me relatives aate hain
        if 16 <= hour <= 19:
            base = 88.0 + random.uniform(-5.0, 9.0)
        elif 8 <= hour < 22:
            base = 72.0 + random.uniform(-8.0, 8.0)
        else:
            base = 56.0 + random.uniform(-5.0, 5.0)

        if is_sunday:
            base -= 6.0
        return round(max(30.0, min(100.0, base)), 1)

    elif zone == "OPD":
        # OPD working hours me open rehta hai
        if is_sunday:
            return round(random.uniform(0.0, 3.0), 1)

        if 8.5 <= hour <= 13.5:
            base = 85.0 + random.uniform(-10.0, 12.0)
        elif 13.5 < hour <= 17.0:
            base = 52.0 + random.uniform(-12.0, 10.0)
        else:
            base = random.uniform(0.0, 4.0)

        if dt.weekday() == 5 and hour > 13.0:
            base = random.uniform(0.0, 5.0)
        return round(max(0.0, min(100.0, base)), 1)

    elif zone == "Admin":
        if is_weekend:
            return round(random.uniform(0.0, 4.0), 1)

        if 9.0 <= hour <= 18.0:
            base = 78.0 + random.uniform(-10.0, 12.0)
            if 13.0 <= hour <= 14.0:
                base -= 15.0  # Lunch break
        else:
            base = random.uniform(0.0, 5.0)
        return round(max(0.0, min(100.0, base)), 1)

    return 50.0


# ----------------------------------------------------------------------
# 6. Water Computation & Controlled Anomaly Injection
# ----------------------------------------------------------------------
def compute_water(
    zone: str,
    occupancy: float,
    temperature_c: float,
    status: str,
    dt: datetime
) -> tuple[float, int]:
    """
    Computes water consumption (Litres) per 15-minute interval:
    - Baseload of hospital zone
    - Morning diurnal hygiene spike (06:00 - 09:30) & evening visiting surge (16:30 - 19:00)
    - Occupancy-driven demand
    - Temperature effect (garmi me thoda extra consumption)
    - Status multiplier (REDUCED_OPERATION vs EMERGENCY)
    - Natural stochastic variance (+/- 4%)
    - Controlled anomaly injection (~0.8% rate)

    Returns:
        (water_litres, anomaly_flag)
    """
    spec = ZONE_WATER_SPECS[zone]
    base_l = spec["base_litres"]
    hour = dt.hour + (dt.minute / 60.0)

    # 1. Diurnal water spike pattern (Morning baths/cleaning & Evening visiting hours)
    diurnal_multiplier = 1.0
    if zone in ["General_Ward", "Emergency"]:
        if 6.0 <= hour <= 9.5:
            diurnal_multiplier = 1.45  # Subah ke time toilets aur floor cleaning peak
        elif 16.5 <= hour <= 19.0:
            diurnal_multiplier = 1.25  # Evening visiting hours
        elif 0.0 <= hour <= 5.0:
            diurnal_multiplier = 0.60  # Raat ko log so rahe hote hain
    elif zone == "OPD":
        if 8.5 <= hour <= 14.0:
            diurnal_multiplier = 1.35
        elif 14.0 < hour <= 17.5:
            diurnal_multiplier = 1.0
        else:
            diurnal_multiplier = 0.10  # Night me OPD band hai

    # 2. Occupancy load contribution
    occ_load = (occupancy / 100.0) * (base_l * 0.50) * spec["occ_factor"]

    # 3. Hot weather hydration & sanitation effect (if temp > 30°C)
    temp_factor = 1.0 + max(0.0, (temperature_c - 30.0) * 0.012)

    # 4. Operational status adjustment
    status_multiplier = 1.0
    if status == "REDUCED_OPERATION":
        status_multiplier = 0.55
    elif status == "EMERGENCY":
        status_multiplier = 1.30
    elif status == "MAINTENANCE":
        status_multiplier = 0.85

    # 5. Natural random fluctuation (+/- 4%)
    noise = random.uniform(-0.04, 0.04) * base_l

    normal_water = (base_l * diurnal_multiplier + occ_load) * temp_factor * status_multiplier + noise
    normal_water = max(1.0, normal_water)

    # ------------------------------------------------------------------
    # Controlled Anomaly Injection (~0.8% overall probability)
    # ------------------------------------------------------------------
    anomaly_roll = random.random()

    # Pattern A: Major Pipe Burst / Main Valve Leak (+120% to +180% sudden flow)
    if anomaly_roll < 0.003:
        spike_multiplier = random.uniform(2.2, 2.8)
        anomaly_val = normal_water * spike_multiplier
        return round(anomaly_val, 2), 1

    # Pattern B: Unattended running tap / toilet flush stuck during night in empty zone
    elif anomaly_roll < 0.006 and zone in ["OPD", "Admin"] and status == "REDUCED_OPERATION":
        leakage_flow = random.uniform(65.0, 120.0)  # Empty clinic me continuous tap open
        anomaly_val = normal_water + leakage_flow
        return round(anomaly_val, 2), 1

    # Pattern C: Ward flush valve stuck / acute pressure surge
    elif anomaly_roll < 0.008 and zone == "General_Ward":
        valve_leak = random.uniform(80.0, 140.0)
        anomaly_val = normal_water + valve_leak
        return round(anomaly_val, 2), 1

    return round(normal_water, 2), 0


# ----------------------------------------------------------------------
# 7. Dataset Generation Routine
# ----------------------------------------------------------------------
def generate_water_dataset() -> pd.DataFrame:
    """
    Generates exactly 43,200 records covering 90 days of 15-minute readings
    for 5 hospital zones.
    """
    records = []
    current_time = START_DATE

    for _ in range(TOTAL_INTERVALS):
        temp_c = get_ambient_temperature(current_time)

        for zone in HOSPITAL_ZONES:
            status = get_operational_status(zone, current_time)
            w_source = get_water_source(zone, current_time)
            occ_pct = get_zone_occupancy(zone, current_time, status)
            water_litres, anomaly_flag = compute_water(
                zone, occ_pct, temp_c, status, current_time
            )

            records.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "facility_id": FACILITY_ID,
                "zone_id": zone,
                "water_litres": water_litres,
                "occupancy_percent": occ_pct,
                "temperature_c": temp_c,
                "operational_status": status,
                "water_source": w_source,
                "source": "synthetic",
                "anomaly_flag": anomaly_flag,
            })

        current_time += timedelta(minutes=INTERVAL_MINUTES)

    return pd.DataFrame(records)


# ----------------------------------------------------------------------
# 8. Data Quality Validation (14 Rules)
# ----------------------------------------------------------------------
def validate_water_dataset(df: pd.DataFrame) -> None:
    """
    Validates data quality before saving to CSV.
    Raises ValueError with explanation if any rule is violated.
    """
    print("\nRunning Water Data Quality Validation...")

    # Rule 1: Exactly 43,200 rows
    if len(df) != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"Rule 1 Failed: Expected {EXPECTED_TOTAL_ROWS} rows, got {len(df)}")

    # Rule 2: Exactly the expected 5 zones
    actual_zones = set(df["zone_id"].unique())
    expected_zones = set(HOSPITAL_ZONES)
    if actual_zones != expected_zones:
        raise ValueError(f"Rule 2 Failed: Expected zones {expected_zones}, got {actual_zones}")

    # Rule 3: No missing/null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(f"Rule 3 Failed: Missing values found:\n{null_counts[null_counts > 0]}")

    # Rule 4: No duplicate records
    duplicates = df.duplicated(subset=["timestamp", "facility_id", "zone_id"]).sum()
    if duplicates > 0:
        raise ValueError(f"Rule 4 Failed: Found {duplicates} duplicate records")

    # Rule 5 & 6: 15-minute interval check and 90-day span
    timestamps = pd.to_datetime(df["timestamp"].drop_duplicates().sort_values())
    if len(timestamps) != TOTAL_INTERVALS:
        raise ValueError(f"Rule 5 Failed: Expected {TOTAL_INTERVALS} unique timestamps, got {len(timestamps)}")
    diffs = timestamps.diff().dropna()
    expected_delta = pd.Timedelta(minutes=INTERVAL_MINUTES)
    if not (diffs == expected_delta).all():
        raise ValueError("Rule 5 Failed: Timestamp series is not strictly 15-minute intervals")

    total_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0
    if not (89.9 <= total_days <= 90.0):
        raise ValueError(f"Rule 6 Failed: Timespan must cover 90 days, got {total_days:.2f} days")

    # Rule 7: occupancy_percent between 0 and 100
    if not df["occupancy_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 7 Failed: occupancy_percent out of bounds [0, 100]")

    # Rule 8: water_litres is strictly positive
    if not (df["water_litres"] > 0).all():
        raise ValueError("Rule 8 Failed: Non-positive water_litres detected")

    # Rule 9: temperature_c within plausible synthetic range (15°C to 45°C)
    if not df["temperature_c"].between(15.0, 45.0).all():
        raise ValueError("Rule 9 Failed: temperature_c out of range (15-45°C)")

    # Rule 10: source is consistently 'synthetic'
    if not (df["source"] == "synthetic").all():
        raise ValueError("Rule 10 Failed: Inconsistent source values")

    # Rule 11: anomaly_flag is only 0 or 1
    if not df["anomaly_flag"].isin([0, 1]).all():
        raise ValueError("Rule 11 Failed: anomaly_flag contains values other than 0 and 1")

    # Rule 12: Controlled anomaly rate (0.3% - 2.0%)
    anomaly_rate = df["anomaly_flag"].mean()
    if not (0.003 <= anomaly_rate <= 0.02):
        raise ValueError(f"Rule 12 Failed: Anomaly rate ({anomaly_rate:.2%}) outside bounds (0.3% - 2.0%)")

    # Rule 13: operational_status in allowed values
    invalid_statuses = set(df["operational_status"].unique()) - ALLOWED_STATUSES
    if invalid_statuses:
        raise ValueError(f"Rule 13 Failed: Invalid operational_status: {invalid_statuses}")

    # Rule 14: water_source in allowed values
    invalid_sources = set(df["water_source"].unique()) - ALLOWED_WATER_SOURCES
    if invalid_sources:
        raise ValueError(f"Rule 14 Failed: Invalid water_source: {invalid_sources}")

    print("All 14 Water Data Quality Validation checks PASSED successfully!")


# ----------------------------------------------------------------------
# 9. Main Execution Routine
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AURA: Generating Synthetic Water Dataset for Hospital (H001)")
    print(f"Horizon: {DAYS_TO_SIMULATE} days @ 15-min intervals")
    print(f"Hospital Zones: {', '.join(HOSPITAL_ZONES)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    # 1. Generate data
    df = generate_water_dataset()

    # 2. Validate data
    validate_water_dataset(df)

    # 3. Save CSV safely (handling Excel file-lock)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{OUTPUT_FILE}'.")
        print("Please close Microsoft Excel or any program holding 'water.csv' open and re-run.")
        exit(1)

    # 4. Print structured summary
    anomaly_count = int(df["anomaly_flag"].sum())
    anomaly_pct = (anomaly_count / len(df)) * 100.0

    print("\n" + "=" * 70)
    print("WATER DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Generated:     {len(df):,}")
    print(f"Total Columns:           {len(df.columns)}")
    print(f"Schema Columns:          {list(df.columns)}")
    print(f"First Timestamp:         {df['timestamp'].min()}")
    print(f"Last Timestamp:          {df['timestamp'].max()}")
    print(f"Hospital Zones:          {list(df['zone_id'].unique())}")
    print(f"Operational Statuses:    {dict(df['operational_status'].value_counts())}")
    print(f"Water Sources:           {dict(df['water_source'].value_counts())}")
    print(f"Total Anomalies Injected:{anomaly_count:,} ({anomaly_pct:.2f}%)")
    print(f"Output File Path:        {OUTPUT_FILE}")
    print("=" * 70)
