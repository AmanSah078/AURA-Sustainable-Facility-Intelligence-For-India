"""
AURA - AI-Powered Sustainable Facility Intelligence Platform
Synthetic Energy Dataset Generator for Hospital Demo (BPUT Hackathon 2026 PS04)

Generates 90 days of realistic 15-minute interval energy telemetry across
5 hospital zones (ICU, Emergency, General_Ward, OPD, Admin).

Schema (10 columns):
1. timestamp
2. facility_id
3. zone_id
4. energy_kwh
5. occupancy_percent
6. temperature_c
7. operational_status
8. energy_source
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
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

FACILITY_ID = "H001"
HOSPITAL_ZONES = ["ICU", "Emergency", "General_Ward", "OPD", "Admin"]

START_DATE = datetime(2026, 1, 1, 0, 0, 0)
DAYS_TO_SIMULATE = 90
INTERVAL_MINUTES = 15
INTERVALS_PER_DAY = (24 * 60) // INTERVAL_MINUTES  # 96 readings/day/zone
TOTAL_INTERVALS = DAYS_TO_SIMULATE * INTERVALS_PER_DAY  # 8,640 intervals
EXPECTED_TOTAL_ROWS = TOTAL_INTERVALS * len(HOSPITAL_ZONES)  # 43,200 rows

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "energy.csv"

# Allowed Domain Values
ALLOWED_STATUSES = {"NORMAL", "MAINTENANCE", "REDUCED_OPERATION", "EMERGENCY"}
ALLOWED_ENERGY_SOURCES = {"GRID", "SOLAR", "BACKUP_GENERATOR"}

# Zone Baseline Parameters (kWh per 15-min interval, sensitivity multipliers)
ZONE_SPECS = {
    "ICU": {
        "base_kwh": 180.0,      # High 24/7 life-support baseload
        "hvac_factor": 2.2,     # Strict continuous climate control (target 21°C)
        "occ_factor": 0.4,
        "is_24_7": True,
    },
    "Emergency": {
        "base_kwh": 140.0,      # Triage, diagnostics, trauma readiness
        "hvac_factor": 1.8,
        "occ_factor": 0.5,
        "is_24_7": True,
    },
    "General_Ward": {
        "base_kwh": 90.0,       # Inpatient lighting, monitoring, HVAC
        "hvac_factor": 1.5,
        "occ_factor": 0.6,
        "is_24_7": True,
    },
    "OPD": {
        "base_kwh": 25.0,       # Daytime outpatient clinic; low standby at night
        "hvac_factor": 1.4,
        "occ_factor": 0.8,
        "is_24_7": False,
    },
    "Admin": {
        "base_kwh": 15.0,       # Office computers, admin servers; idle nights/weekends
        "hvac_factor": 1.1,
        "occ_factor": 0.7,
        "is_24_7": False,
    },
}


# ----------------------------------------------------------------------
# 2. Environmental Simulation (Indian Context Diurnal Temperature)
# ----------------------------------------------------------------------
def get_ambient_temperature(dt: datetime) -> float:
    """
    Simulates realistic outdoor temperature in Celsius (°C).
    Daily minimum ~22°C at 05:00 AM, daily peak ~36°C at 14:00.
    Includes slight seasonal progression across 90 days.
    """
    day_fraction = (dt.hour * 60 + dt.minute) / 1440.0
    day_of_year = dt.timetuple().tm_yday

    # Peak temperature occurs around 14:00 (14/24 ~ 0.583)
    diurnal_cycle = -math.cos(2 * math.pi * (day_fraction - 0.21))

    # Seasonal drift from Jan winter to March pre-summer
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
    Determines operational status: NORMAL, MAINTENANCE, REDUCED_OPERATION, EMERGENCY.
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    # 1. Rare acute hospital emergency surge (~0.3% probability in Emergency/ICU)
    if zone in ["Emergency", "ICU"] and random.random() < 0.003:
        return "EMERGENCY"

    # 2. Scheduled maintenance window (Sunday mornings 06:00-09:00 for Admin/OPD/Wards)
    if is_sunday and 6.0 <= hour <= 9.0 and random.random() < 0.25:
        return "MAINTENANCE"

    # 3. Off-hours / Night reduced operation
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
# 4. Energy Source Simulation
# ----------------------------------------------------------------------
def get_energy_source(zone: str, dt: datetime, temp_c: float) -> str:
    """
    Determines energy source: GRID, SOLAR, or BACKUP_GENERATOR.
    Hospital has rooftop solar generating during sunny daytime (09:30-15:30).
    Rare backup diesel generator (DG) switchovers occur during grid interruption drills.
    """
    hour = dt.hour + (dt.minute / 60.0)

    # Backup generator switchover / test drill (~0.4% chance, critical zones prioritize)
    if random.random() < 0.004:
        return "BACKUP_GENERATOR"

    # Rooftop solar generation during sunny peak hours (09:30 to 15:30)
    # Higher contribution on clear warm days
    if 9.5 <= hour <= 15.5 and temp_c >= 26.0:
        # Non-critical and daytime zones readily utilize solar
        if zone in ["OPD", "Admin", "General_Ward"]:
            if random.random() < 0.55:
                return "SOLAR"
        elif random.random() < 0.25:
            return "SOLAR"

    return "GRID"


# ----------------------------------------------------------------------
# 5. Occupancy Simulation
# ----------------------------------------------------------------------
def get_zone_occupancy(zone: str, dt: datetime, status: str) -> float:
    """
    Returns realistic occupancy percentage (0.0 to 100.0%).
    Respects zone operational status, daytime/night, and weekends.
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    if status == "REDUCED_OPERATION":
        # Skeleton night staff or closed clinics
        if zone in ["OPD", "Admin"]:
            return round(random.uniform(0.0, 4.0), 1)
        elif zone == "General_Ward":
            return round(random.uniform(50.0, 62.0), 1)

    if zone == "ICU":
        # 24/7 high continuous occupancy (75% - 95%)
        base = 85.0 + random.uniform(-8.0, 7.0)
        return round(max(60.0, min(100.0, base)), 1)

    elif zone == "Emergency":
        # 24/7 active; surges in evening, night, and weekends
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
        # Daytime baseline + visiting hour spikes (16:00 - 19:00)
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
        # Active 08:30 to 17:00 on weekdays; closed on Sundays
        if is_sunday:
            return round(random.uniform(0.0, 3.0), 1)

        if 8.5 <= hour <= 13.5:
            base = 85.0 + random.uniform(-10.0, 12.0)
        elif 13.5 < hour <= 17.0:
            base = 52.0 + random.uniform(-12.0, 10.0)
        else:
            base = random.uniform(0.0, 4.0)

        if dt.weekday() == 5 and hour > 13.0:  # Saturday afternoon
            base = random.uniform(0.0, 5.0)
        return round(max(0.0, min(100.0, base)), 1)

    elif zone == "Admin":
        # Office hours 09:00 to 18:00, Monday to Friday
        if is_weekend:
            return round(random.uniform(0.0, 4.0), 1)

        if 9.0 <= hour <= 18.0:
            base = 78.0 + random.uniform(-10.0, 12.0)
            if 13.0 <= hour <= 14.0:
                base -= 15.0  # Lunch break dip
        else:
            base = random.uniform(0.0, 5.0)
        return round(max(0.0, min(100.0, base)), 1)

    return 50.0


# ----------------------------------------------------------------------
# 6. Energy Computation & Controlled Anomaly Injection
# ----------------------------------------------------------------------
def compute_energy(
    zone: str,
    occupancy: float,
    temperature_c: float,
    status: str,
    dt: datetime
) -> tuple[float, int]:
    """
    Computes energy consumption (kWh) based on:
    - Baseload of medical/zone equipment
    - HVAC cooling demand when ambient temp > 23°C
    - Occupancy-driven load (lighting, monitors, plug loads)
    - Operational status modifier (REDUCED_OPERATION vs EMERGENCY)
    - Natural stochastic variation (+/- 3%)
    - Controlled anomaly injection (~0.8% rate)

    Returns:
        (energy_kwh, anomaly_flag)
    """
    spec = ZONE_SPECS[zone]
    base_kwh = spec["base_kwh"]

    # Cooling degree demand (Hospital indoor target ~23°C)
    cooling_delta = max(0.0, temperature_c - 23.0)
    hvac_load = cooling_delta * spec["hvac_factor"]

    # Occupancy contribution
    occ_load = (occupancy / 100.0) * (base_kwh * 0.45) * spec["occ_factor"]

    # Status multiplier
    status_multiplier = 1.0
    if status == "REDUCED_OPERATION":
        status_multiplier = 0.70
    elif status == "EMERGENCY":
        status_multiplier = 1.25
    elif status == "MAINTENANCE":
        status_multiplier = 0.90

    # Natural unmetered variance (+/- 3%)
    noise = random.uniform(-0.03, 0.03) * base_kwh

    normal_energy = (base_kwh + hvac_load + occ_load) * status_multiplier + noise
    normal_energy = max(5.0, normal_energy)

    # ------------------------------------------------------------------
    # Controlled Anomaly Injection (~0.8% overall probability)
    # ------------------------------------------------------------------
    anomaly_roll = random.random()
    hour = dt.hour

    # Pattern 1: HVAC Chiller / Compressor fault during hot daytime
    if anomaly_roll < 0.003 and temperature_c > 31.0:
        spike_multiplier = random.uniform(1.50, 1.85)
        energy_val = normal_energy * spike_multiplier
        return round(energy_val, 2), 1

    # Pattern 2: Equipment / AC left running in empty zone during off-hours
    elif anomaly_roll < 0.006 and zone in ["OPD", "Admin"] and status == "REDUCED_OPERATION":
        phantom_load = random.uniform(50.0, 90.0)
        energy_val = normal_energy + phantom_load
        return round(energy_val, 2), 1

    # Pattern 3: Power quality spike / equipment power leakage
    elif anomaly_roll < 0.008:
        spike_multiplier = random.uniform(1.35, 1.65)
        energy_val = normal_energy * spike_multiplier
        return round(energy_val, 2), 1

    # Normal observation
    return round(normal_energy, 2), 0


# ----------------------------------------------------------------------
# 7. Dataset Generation Routine
# ----------------------------------------------------------------------
def generate_energy_dataset() -> pd.DataFrame:
    """
    Generates exactly 43,200 records covering 90 days of 15-minute readings
    for the 5 designated hospital zones.
    """
    records = []
    current_time = START_DATE

    for _ in range(TOTAL_INTERVALS):
        # Environmental temperature is campus-wide for this timestamp
        temp_c = get_ambient_temperature(current_time)

        for zone in HOSPITAL_ZONES:
            status = get_operational_status(zone, current_time)
            energy_source = get_energy_source(zone, current_time, temp_c)
            occ_pct = get_zone_occupancy(zone, current_time, status)
            energy_kwh, anomaly_flag = compute_energy(
                zone, occ_pct, temp_c, status, current_time
            )

            records.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "facility_id": FACILITY_ID,
                "zone_id": zone,
                "energy_kwh": energy_kwh,
                "occupancy_percent": occ_pct,
                "temperature_c": temp_c,
                "operational_status": status,
                "energy_source": energy_source,
                "source": "synthetic",
                "anomaly_flag": anomaly_flag,
            })

        current_time += timedelta(minutes=INTERVAL_MINUTES)

    return pd.DataFrame(records)


# ----------------------------------------------------------------------
# 8. Data Quality Validation (15 Mandatory Rules)
# ----------------------------------------------------------------------
def validate_energy_dataset(df: pd.DataFrame) -> None:
    """
    Validates data quality across 15 mandatory integrity rules.
    Raises ValueError with a descriptive message if any check fails.
    """
    print("\nRunning comprehensive data quality validation...")

    # Rule 1: Exactly 43,200 rows
    if len(df) != EXPECTED_TOTAL_ROWS:
        raise ValueError(
            f"Rule 1 Failed: Expected {EXPECTED_TOTAL_ROWS} rows, but got {len(df)}"
        )

    # Rule 2: Exactly the expected 5 zones
    actual_zones = set(df["zone_id"].unique())
    expected_zones = set(HOSPITAL_ZONES)
    if actual_zones != expected_zones:
        raise ValueError(
            f"Rule 2 Failed: Expected zones {expected_zones}, got {actual_zones}"
        )

    # Rule 3: No missing/null values in any column
    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(
            f"Rule 3 Failed: Missing values detected:\n{null_counts[null_counts > 0]}"
        )

    # Rule 4: No duplicate combinations of (timestamp + facility_id + zone_id)
    duplicates = df.duplicated(subset=["timestamp", "facility_id", "zone_id"]).sum()
    if duplicates > 0:
        raise ValueError(
            f"Rule 4 Failed: Found {duplicates} duplicate (timestamp, facility_id, zone_id) rows"
        )

    # Rule 5 & 6: 15-minute interval check and exactly 90 days span
    timestamps = pd.to_datetime(df["timestamp"].drop_duplicates().sort_values())
    if len(timestamps) != TOTAL_INTERVALS:
        raise ValueError(
            f"Rule 5 Failed: Expected {TOTAL_INTERVALS} unique timestamps, got {len(timestamps)}"
        )
    diffs = timestamps.diff().dropna()
    expected_delta = pd.Timedelta(minutes=INTERVAL_MINUTES)
    if not (diffs == expected_delta).all():
        raise ValueError("Rule 5 Failed: Timestamp series is not strictly 15-minute steps")

    total_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0
    # 8,640 intervals of 15 min spans 8,639 * 15 min = 89.989 days (exactly 90 days of readings)
    if not (89.9 <= total_days <= 90.0):
        raise ValueError(f"Rule 6 Failed: Timespan must cover 90 days, got {total_days:.2f} days")

    # Rule 7: occupancy_percent between 0 and 100
    if not df["occupancy_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 7 Failed: occupancy_percent out of [0, 100] bounds")

    # Rule 8: energy_kwh is strictly positive
    if not (df["energy_kwh"] > 0).all():
        raise ValueError("Rule 8 Failed: Non-positive energy_kwh detected")

    # Rule 9: temperature_c within plausible synthetic range (15°C to 45°C)
    if not df["temperature_c"].between(15.0, 45.0).all():
        raise ValueError("Rule 9 Failed: temperature_c outside plausible range (15-45°C)")

    # Rule 10: source is consistently 'synthetic'
    if not (df["source"] == "synthetic").all():
        raise ValueError("Rule 10 Failed: Inconsistent source values found")

    # Rule 11: anomaly_flag contains only 0 or 1
    if not df["anomaly_flag"].isin([0, 1]).all():
        raise ValueError("Rule 11 Failed: anomaly_flag contains values other than 0 and 1")

    # Rule 12: Anomalies are limited and intentional (between 0.3% and 2.0%)
    anomaly_rate = df["anomaly_flag"].mean()
    if not (0.003 <= anomaly_rate <= 0.02):
        raise ValueError(
            f"Rule 12 Failed: Anomaly rate ({anomaly_rate:.2%}) is outside controlled bounds (0.3% - 2.0%)"
        )

    # Rule 13: facility_id is correctly populated as 'H001'
    if not (df["facility_id"] == FACILITY_ID).all():
        raise ValueError(f"Rule 13 Failed: facility_id contains values other than {FACILITY_ID}")

    # Rule 14: operational_status contains only allowed values
    invalid_statuses = set(df["operational_status"].unique()) - ALLOWED_STATUSES
    if invalid_statuses:
        raise ValueError(f"Rule 14 Failed: Invalid operational_status: {invalid_statuses}")

    # Rule 15: energy_source contains only allowed values
    invalid_sources = set(df["energy_source"].unique()) - ALLOWED_ENERGY_SOURCES
    if invalid_sources:
        raise ValueError(f"Rule 15 Failed: Invalid energy_source: {invalid_sources}")

    print("All 15 Data Quality Validation checks PASSED successfully!")


# ----------------------------------------------------------------------
# 9. Main Execution Flow
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AURA: Generating Synthetic Energy Dataset for Hospital (H001)")
    print(f"Horizon: {DAYS_TO_SIMULATE} days @ 15-min intervals")
    print(f"Hospital Zones: {', '.join(HOSPITAL_ZONES)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    # 1. Generate records
    df = generate_energy_dataset()

    # 2. Validate data quality
    validate_energy_dataset(df)

    # 3. Ensure output directory exists and save CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{OUTPUT_FILE}'.")
        print("Please close Microsoft Excel or any program holding 'energy.csv' open and re-run.")
        exit(1)

    # 4. Print structured summary information
    anomaly_count = int(df["anomaly_flag"].sum())
    anomaly_pct = (anomaly_count / len(df)) * 100.0

    print("\n" + "=" * 70)
    print("DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Generated:     {len(df):,}")
    print(f"Total Columns:           {len(df.columns)}")
    print(f"Schema Columns:          {list(df.columns)}")
    print(f"First Timestamp:         {df['timestamp'].min()}")
    print(f"Last Timestamp:          {df['timestamp'].max()}")
    print(f"Hospital Zones:          {list(df['zone_id'].unique())}")
    print(f"Operational Statuses:    {dict(df['operational_status'].value_counts())}")
    print(f"Energy Sources:          {dict(df['energy_source'].value_counts())}")
    print(f"Total Anomalies Injected:{anomaly_count:,} ({anomaly_pct:.2f}%)")
    print(f"Output File Path:        {OUTPUT_FILE}")
    print("=" * 70)