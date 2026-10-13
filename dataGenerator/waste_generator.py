"""
AURA - AI-Powered Sustainable Facility Intelligence Platform
Synthetic Waste Dataset Generator for Hospital Demo (BPUT Hackathon 2026 PS04)

Generates 90 days of realistic 15-minute interval waste telemetry across
5 hospital zones (ICU, Emergency, General_Ward, OPD, Admin).

Features:
- Waste generation per interval (waste_kg)
- Bin capacity tracking (bin_capacity_kg)
- Realistic saw-tooth accumulation and collection cycles (bin_fill_percent)
- Material classification (waste_category: GENERAL, RECYCLABLE, ORGANIC)
- Ground-truth controlled anomaly injection (anomaly_flag)

Schema (11 columns):
1. timestamp
2. facility_id
3. zone_id
4. waste_kg
5. bin_capacity_kg
6. bin_fill_percent
7. waste_category
8. occupancy_percent
9. operational_status
10. source
11. anomaly_flag
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# 1. Configuration & Reproducibility
# ----------------------------------------------------------------------
# Fixed random seed taaki dataset reproducible rahe
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

FACILITY_ID = "H001"
HOSPITAL_ZONES = ["ICU", "Emergency", "General_Ward", "OPD", "Admin"]

START_DATE = datetime(2026, 1, 1, 0, 0, 0)
DAYS_TO_SIMULATE = 90
INTERVAL_MINUTES = 15
INTERVALS_PER_DAY = (24 * 60) // INTERVAL_MINUTES  # 96 readings har din
TOTAL_INTERVALS = DAYS_TO_SIMULATE * INTERVALS_PER_DAY  # 8,640 intervals
EXPECTED_TOTAL_ROWS = TOTAL_INTERVALS * len(HOSPITAL_ZONES)  # 43,200 rows

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "waste.csv"

# Allowed Domain Values
ALLOWED_STATUSES = {"NORMAL", "MAINTENANCE", "REDUCED_OPERATION", "EMERGENCY"}
ALLOWED_CATEGORIES = {"GENERAL", "RECYCLABLE", "ORGANIC"}

# Zone-wise waste baselines (kg generated per 15-min) and bin capacities (kg)
ZONE_WASTE_SPECS = {
    "General_Ward": {
        "base_kg": 2.4,        # Highest volume: patient food, packaging, consumables
        "bin_capacity_kg": 140.0,
        "occ_factor": 0.75,
        "is_24_7": True,
    },
    "Emergency": {
        "base_kg": 1.9,        # Trauma packs, procedural packaging, gloves, gauze
        "bin_capacity_kg": 100.0,
        "occ_factor": 0.55,
        "is_24_7": True,
    },
    "ICU": {
        "base_kg": 1.5,        # Life-support disposables, sterile wraps, patient hygiene
        "bin_capacity_kg": 120.0,
        "occ_factor": 0.40,
        "is_24_7": True,
    },
    "OPD": {
        "base_kg": 1.2,        # Daytime outpatient footfall, clinic wrappers, registration paper
        "bin_capacity_kg": 80.0,
        "occ_factor": 0.85,
        "is_24_7": False,
    },
    "Admin": {
        "base_kg": 0.6,        # Office paper, cafeteria disposables, packaging cartons
        "bin_capacity_kg": 50.0,
        "occ_factor": 0.70,
        "is_24_7": False,
    },
}


# ----------------------------------------------------------------------
# 2. Operational Status Simulation
# ----------------------------------------------------------------------
def get_operational_status(zone: str, dt: datetime) -> str:
    """
    Returns zone status: NORMAL, MAINTENANCE, REDUCED_OPERATION, EMERGENCY.
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    # Acute emergency surge (~0.3% chance in Emergency/ICU)
    if zone in ["Emergency", "ICU"] and random.random() < 0.003:
        return "EMERGENCY"

    # Deep sanitation / deep cleaning maintenance window (Sunday mornings 06:00-09:00)
    if is_sunday and 6.0 <= hour <= 9.0 and random.random() < 0.20:
        return "MAINTENANCE"

    # Night off-hours me reduced operation
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
# 3. Occupancy Simulation
# ----------------------------------------------------------------------
def get_zone_occupancy(zone: str, dt: datetime, status: str) -> float:
    """
    Calculates realistic zone occupancy percentage (0.0 to 100.0%).
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    if status == "REDUCED_OPERATION":
        if zone in ["OPD", "Admin"]:
            return round(random.uniform(0.0, 4.0), 1)
        elif zone == "General_Ward":
            return round(random.uniform(50.0, 62.0), 1)

    if zone == "ICU":
        base = 85.0 + random.uniform(-8.0, 7.0)
        return round(max(60.0, min(100.0, base)), 1)

    elif zone == "Emergency":
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
                base -= 15.0
        else:
            base = random.uniform(0.0, 5.0)
        return round(max(0.0, min(100.0, base)), 1)

    return 50.0


# ----------------------------------------------------------------------
# 4. Waste Category Assignment
# ----------------------------------------------------------------------
def pick_waste_category(zone: str, dt: datetime) -> str:
    """
    Assigns category: GENERAL, RECYCLABLE, ORGANIC based on zone characteristics.
    """
    roll = random.random()
    hour = dt.hour + (dt.minute / 60.0)

    # Meal hours (08:00-09:30, 12:30-14:00, 19:30-21:00) me wards aur admin me ORGANIC peak
    is_meal_time = (8.0 <= hour <= 9.5) or (12.5 <= hour <= 14.0) or (19.5 <= hour <= 21.0)

    if zone == "General_Ward":
        if is_meal_time and roll < 0.60:
            return "ORGANIC"
        elif roll < 0.55:
            return "GENERAL"
        elif roll < 0.80:
            return "ORGANIC"
        else:
            return "RECYCLABLE"

    elif zone == "Admin":
        if is_meal_time and roll < 0.40:
            return "ORGANIC"
        elif roll < 0.50:
            return "RECYCLABLE"  # Office files, print papers, packaging
        elif roll < 0.80:
            return "GENERAL"
        else:
            return "ORGANIC"

    elif zone in ["ICU", "Emergency"]:
        # Medical disposables and procedural packaging
        if roll < 0.65:
            return "GENERAL"
        elif roll < 0.88:
            return "RECYCLABLE"  # Medicine cartons, plastic wraps
        else:
            return "ORGANIC"     # Dietary feed / staff meals

    elif zone == "OPD":
        if roll < 0.50:
            return "GENERAL"
        elif roll < 0.80:
            return "RECYCLABLE"  # Outpatient prescriptions, leaflets, bottles
        else:
            return "ORGANIC"

    return "GENERAL"


# ----------------------------------------------------------------------
# 5. Waste Generation & Anomaly Logic
# ----------------------------------------------------------------------
def compute_waste_kg(
    zone: str,
    occupancy: float,
    status: str,
    category: str,
    dt: datetime
) -> tuple[float, int]:
    """
    Computes waste (kg) generated in the 15-minute interval.
    Returns: (waste_kg, anomaly_flag)
    """
    spec = ZONE_WASTE_SPECS[zone]
    base_kg = spec["base_kg"]
    hour = dt.hour + (dt.minute / 60.0)

    # 1. Diurnal meal and routine generation surges
    diurnal_multiplier = 1.0
    if (8.0 <= hour <= 9.5) or (12.5 <= hour <= 14.0) or (19.5 <= hour <= 21.0):
        diurnal_multiplier = 1.40  # Meal/canteen times
    elif 0.0 <= hour <= 5.0 and zone in ["OPD", "Admin", "General_Ward"]:
        diurnal_multiplier = 0.20  # Night rest / closed clinics

    # 2. Occupancy contribution
    occ_load = (occupancy / 100.0) * (base_kg * 0.40) * spec["occ_factor"]

    # 3. Status multiplier
    status_multiplier = 1.0
    if status == "REDUCED_OPERATION":
        status_multiplier = 0.25
    elif status == "EMERGENCY":
        status_multiplier = 1.35
    elif status == "MAINTENANCE":
        status_multiplier = 1.20  # Deep clean discard

    # 4. Natural stochastic variation (+/- 8%)
    noise = random.uniform(-0.08, 0.08) * base_kg

    normal_waste = (base_kg * diurnal_multiplier + occ_load) * status_multiplier + noise
    normal_waste = max(0.05, normal_waste)

    # ------------------------------------------------------------------
    # Controlled Anomaly Injection (~0.6% probability)
    # ------------------------------------------------------------------
    anomaly_roll = random.random()

    # Pattern A: Bulk discard / cleanout packaging surge (3x to 4x surge)
    if anomaly_roll < 0.003:
        spike_multiplier = random.uniform(3.0, 4.2)
        anomaly_val = normal_waste * spike_multiplier
        return round(anomaly_val, 2), 1

    # Pattern B: Off-hours dumping in closed zone (OPD / Admin at midnight)
    elif anomaly_roll < 0.005 and zone in ["OPD", "Admin"] and status == "REDUCED_OPERATION":
        dump_kg = random.uniform(6.0, 12.0)  # Large bulk package dumped in empty corridor
        return round(normal_waste + dump_kg, 2), 1

    # Pattern C: Acute 
    # ward disposable surge
    elif anomaly_roll < 0.007 and zone == "General_Ward":
        procedure_waste = random.uniform(5.0, 9.0)
        return round(normal_waste + procedure_waste, 2), 1

    return round(normal_waste, 2), 0


# ----------------------------------------------------------------------
# 6. Bin Accumulation & Collection Tracking
# ----------------------------------------------------------------------
class ZoneBinTracker:
    """
    Tracks cumulative waste weight and simulates realistic collection rounds.
    Creates realistic saw-tooth bin_fill_percent curves.
    """
    def __init__(self, capacity_kg: float):
        self.capacity_kg = capacity_kg
        # Start at a realistic partial fill (20% to 40%)
        self.current_weight_kg = capacity_kg * random.uniform(0.20, 0.40)

    def add_waste(self, waste_kg: float, dt: datetime, is_anomaly: bool) -> float:
        """
        Adds interval waste, triggers collection rounds if scheduled or full,
        and returns the current bin_fill_percent.
        """
        self.current_weight_kg += waste_kg

        hour = dt.hour
        minute = dt.minute

        # Scheduled Collection Rounds in hospital:
        # Round 1: 06:00 AM (subah ki safai)
        # Round 2: 14:00 PM (shift handover)
        # Round 3: 22:00 PM (raat ki safai)
        is_collection_hour = (hour in [6, 14, 22]) and (minute == 0)

        # Threshold-based urgent collection if bin >= 88% full
        is_overflow_urgent = (self.current_weight_kg / self.capacity_kg) >= 0.88

        # In case of anomaly, occasionally simulate a MISSED collection round (overflow approaching 98%)
        if is_anomaly and (self.current_weight_kg / self.capacity_kg) > 0.80:
            # Skip emptying to let fill rise high for overflow risk detection training
            pass
        elif is_collection_hour or is_overflow_urgent:
            # Bin collected: empties down to liner weight (~4% to 12% capacity)
            self.current_weight_kg = self.capacity_kg * random.uniform(0.04, 0.12)

        # Calculate fill percentage bounded between 0 and 100%
        fill_percent = (self.current_weight_kg / self.capacity_kg) * 100.0
        return round(max(0.0, min(100.0, fill_percent)), 1)


# ----------------------------------------------------------------------
# 7. Dataset Generation Routine
# ----------------------------------------------------------------------
def generate_waste_dataset() -> pd.DataFrame:
    """
    Generates exactly 43,200 records covering 90 days of 15-minute readings
    for the 5 designated hospital zones.
    """
    records = []
    current_time = START_DATE

    # Initialize stateful bin trackers for each zone
    bin_trackers = {
        zone: ZoneBinTracker(ZONE_WASTE_SPECS[zone]["bin_capacity_kg"])
        for zone in HOSPITAL_ZONES
    }

    for _ in range(TOTAL_INTERVALS):
        for zone in HOSPITAL_ZONES:
            spec = ZONE_WASTE_SPECS[zone]
            status = get_operational_status(zone, current_time)
            occ_pct = get_zone_occupancy(zone, current_time, status)
            category = pick_waste_category(zone, current_time)

            waste_kg, anomaly_flag = compute_waste_kg(
                zone, occ_pct, status, category, current_time
            )

            bin_cap = spec["bin_capacity_kg"]
            fill_pct = bin_trackers[zone].add_waste(
                waste_kg, current_time, anomaly_flag == 1
            )

            records.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "facility_id": FACILITY_ID,
                "zone_id": zone,
                "waste_kg": waste_kg,
                "bin_capacity_kg": bin_cap,
                "bin_fill_percent": fill_pct,
                "waste_category": category,
                "occupancy_percent": occ_pct,
                "operational_status": status,
                "source": "synthetic",
                "anomaly_flag": anomaly_flag,
            })

        current_time += timedelta(minutes=INTERVAL_MINUTES)

    return pd.DataFrame(records)


# ----------------------------------------------------------------------
# 8. Data Quality Validation (16 Mandatory Rules)
# ----------------------------------------------------------------------
def validate_waste_dataset(df: pd.DataFrame) -> None:
    """
    Validates data quality before saving to CSV.
    Raises ValueError with a clear explanation if any rule is broken.
    """
    print("\nRunning Waste Data Quality Validation...")

    # Rule 1: Exactly 43,200 rows
    if len(df) != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"Rule 1 Failed: Expected {EXPECTED_TOTAL_ROWS} rows, got {len(df)}")

    # Rule 2: Exactly 5 zones
    actual_zones = set(df["zone_id"].unique())
    expected_zones = set(HOSPITAL_ZONES)
    if actual_zones != expected_zones:
        raise ValueError(f"Rule 2 Failed: Expected zones {expected_zones}, got {actual_zones}")

    # Rule 3: No missing/null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(f"Rule 3 Failed: Missing values detected:\n{null_counts[null_counts > 0]}")

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
        raise ValueError("Rule 5 Failed: Timestamp series is not strictly 15-minute steps")

    total_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0
    if not (89.9 <= total_days <= 90.0):
        raise ValueError(f"Rule 6 Failed: Timespan must cover 90 days, got {total_days:.2f} days")

    # Rule 7: occupancy_percent between 0 and 100
    if not df["occupancy_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 7 Failed: occupancy_percent out of bounds [0, 100]")

    # Rule 8: waste_kg is strictly non-negative
    if not (df["waste_kg"] >= 0).all():
        raise ValueError("Rule 8 Failed: Negative waste_kg detected")

    # Rule 9: bin_capacity_kg is strictly positive
    if not (df["bin_capacity_kg"] > 0).all():
        raise ValueError("Rule 9 Failed: Non-positive bin_capacity_kg detected")

    # Rule 10: bin_fill_percent between 0 and 100
    if not df["bin_fill_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 10 Failed: bin_fill_percent out of bounds [0, 100]")

    # Rule 11: source is consistently 'synthetic'
    if not (df["source"] == "synthetic").all():
        raise ValueError("Rule 10 Failed: Inconsistent source values")

    # Rule 12: anomaly_flag is only 0 or 1
    if not df["anomaly_flag"].isin([0, 1]).all():
        raise ValueError("Rule 12 Failed: anomaly_flag contains values other than 0 and 1")

    # Rule 13: Controlled anomaly rate (0.3% - 2.0%)
    anomaly_rate = df["anomaly_flag"].mean()
    if not (0.003 <= anomaly_rate <= 0.02):
        raise ValueError(f"Rule 13 Failed: Anomaly rate ({anomaly_rate:.2%}) outside bounds (0.3% - 2.0%)")

    # Rule 14: operational_status in allowed values
    invalid_statuses = set(df["operational_status"].unique()) - ALLOWED_STATUSES
    if invalid_statuses:
        raise ValueError(f"Rule 14 Failed: Invalid operational_status: {invalid_statuses}")

    # Rule 15: waste_category in allowed values
    invalid_cats = set(df["waste_category"].unique()) - ALLOWED_CATEGORIES
    if invalid_cats:
        raise ValueError(f"Rule 15 Failed: Invalid waste_category: {invalid_cats}")

    # Rule 16: facility_id is strictly H001
    if not (df["facility_id"] == FACILITY_ID).all():
        raise ValueError(f"Rule 16 Failed: facility_id contains values other than {FACILITY_ID}")

    print("All 16 Waste Data Quality Validation checks PASSED successfully!")


# ----------------------------------------------------------------------
# 9. Main Execution Routine
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AURA: Generating Synthetic Waste Dataset for Hospital (H001)")
    print(f"Horizon: {DAYS_TO_SIMULATE} days @ 15-min intervals")
    print(f"Hospital Zones: {', '.join(HOSPITAL_ZONES)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    # 1. Generate records
    df = generate_waste_dataset()

    # 2. Validate data
    validate_waste_dataset(df)

    # 3. Save CSV safely (handling Excel file-lock)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{OUTPUT_FILE}'.")
        print("Please close Microsoft Excel or any program holding 'waste.csv' open and re-run.")
        exit(1)

    # 4. Print structured summary
    anomaly_count = int(df["anomaly_flag"].sum())
    anomaly_pct = (anomaly_count / len(df)) * 100.0

    print("\n" + "=" * 70)
    print("WASTE DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Generated:     {len(df):,}")
    print(f"Total Columns:           {len(df.columns)}")
    print(f"Schema Columns:          {list(df.columns)}")
    print(f"First Timestamp:         {df['timestamp'].min()}")
    print(f"Last Timestamp:          {df['timestamp'].max()}")
    print(f"Hospital Zones:          {list(df['zone_id'].unique())}")
    print(f"Waste Categories:        {dict(df['waste_category'].value_counts())}")
    print(f"Operational Statuses:    {dict(df['operational_status'].value_counts())}")
    print(f"Avg Bin Fill Percent:    {df['bin_fill_percent'].mean():.1f}%")
    print(f"Total Anomalies Injected:{anomaly_count:,} ({anomaly_pct:.2f}%)")
    print(f"Output File Path:        {OUTPUT_FILE}")
    print("=" * 70)
