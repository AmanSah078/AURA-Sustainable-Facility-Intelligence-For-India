"""
AURA - AI-Powered Sustainable Facility Intelligence Platform
Synthetic Equipment / Asset Utilization Dataset Generator (BPUT Hackathon 2026 PS04)

Generates 90 days of realistic hourly telemetry across 10 hospital equipment assets:
- Medical Equipment: Ventilators, Patient Monitors
- Facility Utilities: HVAC Units, Utility Pumps

Features:
- Asset utilization tracking (utilization_percent)
- Equipment operating time in 1-hour interval (runtime_hours: 0.0 to 1.0)
- Operating state (operational_status: RUNNING, IDLE, MAINTENANCE, OFFLINE)
- Service scheduling state (maintenance_status: NORMAL, DUE_SOON, OVERDUE)
- Controlled decision-su
pport anomalies (anomaly_flag)

Schema (11 columns):
1. timestamp
2. facility_id
3. equipment_id
4. equipment_type
5. zone_id
6. utilization_percent
7. runtime_hours
8. operational_status
9. maintenance_status
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
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

FACILITY_ID = "H001"

START_DATE = datetime(2026, 1, 1, 0, 0, 0)
DAYS_TO_SIMULATE = 90
INTERVAL_HOURS = 1
TOTAL_HOURLY_INTERVALS = DAYS_TO_SIMULATE * 24  # 2,160 hours

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "equipment.csv"

# Allowed Domain Values
ALLOWED_OPERATIONAL_STATUSES = {"RUNNING", "IDLE", "MAINTENANCE", "OFFLINE"}
ALLOWED_MAINTENANCE_STATUSES = {"NORMAL", "DUE_SOON", "OVERDUE"}
ALLOWED_EQUIPMENT_TYPES = {"VENTILATOR", "PATIENT_MONITOR", "HVAC", "PUMP"}

# ----------------------------------------------------------------------
# 2. Representative Equipment Inventory (10 Assets)
# ----------------------------------------------------------------------
EQUIPMENT_INVENTORY = [
    {
        "id": "VENT-001",
        "type": "VENTILATOR",
        "zone": "ICU",
        "base_util": 82.0,      # Critical life support: continuous high demand
        "is_24_7": True,
        "service_interval_hrs": 600,
    },
    {
        "id": "VENT-002",
        "type": "VENTILATOR",
        "zone": "Emergency",
        "base_util": 50.0,      # Variable trauma stabilization
        "is_24_7": True,
        "service_interval_hrs": 600,
    },
    {
        "id": "MON-001",
        "type": "PATIENT_MONITOR",
        "zone": "ICU",
        "base_util": 88.0,      # High continuous ICU vitals tracking
        "is_24_7": True,
        "service_interval_hrs": 720,
    },
    {
        "id": "MON-002",
        "type": "PATIENT_MONITOR",
        "zone": "General_Ward",
        "base_util": 58.0,      # Inpatient monitoring; moderate night dip
        "is_24_7": True,
        "service_interval_hrs": 720,
    },
    {
        "id": "MON-003",
        "type": "PATIENT_MONITOR",
        "zone": "OPD",
        "base_util": 22.0,      # Underutilized asset: used only 09:00-14:00
        "is_24_7": False,
        "service_interval_hrs": 720,
    },
    {
        "id": "HVAC-001",
        "type": "HVAC",
        "zone": "ICU",
        "base_util": 92.0,      # 24/7 continuous HEPA climate filtration
        "is_24_7": True,
        "service_interval_hrs": 500,
    },
    {
        "id": "HVAC-002",
        "type": "HVAC",
        "zone": "Admin",
        "base_util": 45.0,      # Office hours only (08:30-18:00); idle nights/weekends
        "is_24_7": False,
        "service_interval_hrs": 500,
    },
    {
        "id": "PUMP-001",
        "type": "PUMP",
        "zone": "Emergency",
        "base_util": 38.0,      # Trauma infusion / suction pump; intermittent
        "is_24_7": True,
        "service_interval_hrs": 450,
    },
    {
        "id": "PUMP-002",
        "type": "PUMP",
        "zone": "General_Ward",
        "base_util": 48.0,      # Inpatient IV infusion pump; cyclic usage
        "is_24_7": True,
        "service_interval_hrs": 450,
    },
    {
        "id": "PUMP-003",
        "type": "PUMP",
        "zone": "Admin",
        "base_util": 18.0,      # Central utility standby pump; underutilized
        "is_24_7": False,
        "service_interval_hrs": 450,
    },
]

EXPECTED_TOTAL_ROWS = TOTAL_HOURLY_INTERVALS * len(EQUIPMENT_INVENTORY)  # 21,600 rows


# ----------------------------------------------------------------------
# 3. State Tracker for Equipment Asset Runtime & Maintenance
# ----------------------------------------------------------------------
class EquipmentStateTracker:
    """
    Maintains cumulative operating hours and service schedule state.
    Transitions: NORMAL -> DUE_SOON -> OVERDUE -> (Serviced) -> NORMAL.
    """
    def __init__(self, asset_spec: dict):
        self.asset = asset_spec
        self.interval_limit = asset_spec["service_interval_hrs"]
        # Start at a realistic initial runtime into the service cycle
        self.cumulative_runtime = random.uniform(100.0, self.interval_limit * 0.70)

    def step(self, runtime_this_hour: float, dt: datetime) -> str:
        self.cumulative_runtime += runtime_this_hour

        # Determine maintenance status based on accumulated runtime
        ratio = self.cumulative_runtime / self.interval_limit

        if ratio >= 1.05:
            current_maint_status = "OVERDUE"
        elif ratio >= 0.85:
            current_maint_status = "DUE_SOON"
        else:
            current_maint_status = "NORMAL"

        # Preventive Maintenance reset (routine service round when due)
        # Scheduled Sunday morning (06:00 - 08:00)
        is_sunday_service = (dt.weekday() == 6) and (dt.hour == 7)
        if (current_maint_status in ["DUE_SOON", "OVERDUE"]) and is_sunday_service and (random.random() < 0.65):
            self.cumulative_runtime = random.uniform(0.0, 30.0)  # Serviced & reset
            current_maint_status = "NORMAL"

        return current_maint_status


# ----------------------------------------------------------------------
# 4. Telemetry Computation per Hour
# ----------------------------------------------------------------------
def compute_equipment_telemetry(
    asset: dict,
    dt: datetime,
    maint_status: str
) -> tuple[float, float, str, int]:
    """
    Computes (utilization_percent, runtime_hours, operational_status, anomaly_flag)
    for a 1-hour observation window.
    """
    hour = dt.hour
    is_weekend = dt.weekday() >= 5
    is_24_7 = asset["is_24_7"]
    base_util = asset["base_util"]

    # 1. Operational Status Assignment
    roll = random.random()

    # Maintenance state: low probability during scheduled Sunday service
    if dt.weekday() == 6 and hour in [6, 7] and roll < 0.08:
        return 0.0, 0.0, "MAINTENANCE", 0

    # Offline state: occasional turnover, cleaning, or sensor calibration
    if roll < 0.015:
        return 0.0, 0.0, "OFFLINE", 0

    # Non-24/7 assets (OPD / Admin) become IDLE outside working hours
    if not is_24_7:
        if is_weekend or hour < 8 or hour > 18:
            # Standby IDLE
            if roll < 0.85:
                return 0.0, 0.0, "IDLE", 0
            else:
                # Minimal standby tick (5-10%)
                return round(random.uniform(2.0, 8.0), 1), round(random.uniform(0.05, 0.15), 2), "RUNNING", 0

    # 2. Daytime & shift variation for active equipment
    diurnal_factor = 1.0
    if 9 <= hour <= 16:
        diurnal_factor = 1.15  # Peak clinical / shift activity
    elif 0 <= hour <= 5 and not is_24_7:
        diurnal_factor = 0.20
    elif 0 <= hour <= 5 and is_24_7:
        diurnal_factor = 0.90  # Night life-support remains steady

    # 3. Calculate normal utilization (%)
    noise = random.uniform(-4.5, 4.5)
    normal_util = (base_util * diurnal_factor) + noise
    normal_util = max(5.0, min(95.0, normal_util))

    # 4. Runtime (hours) in this 1-hour interval
    # Correlated with utilization: higher utilization = equipment ran more of that hour
    normal_runtime = min(1.0, max(0.1, (normal_util / 100.0) * random.uniform(0.92, 1.05)))

    # ------------------------------------------------------------------
    # Controlled Anomaly Injection (~0.50% overall probability)
    # ------------------------------------------------------------------
    anomaly_roll = random.random()

    # Pattern A: Critical Overutilization / 98-100% continuous strain when maintenance is DUE
    if anomaly_roll < 0.025 and maint_status in ["DUE_SOON", "OVERDUE"]:
        anom_util = round(random.uniform(97.0, 100.0), 1)
        anom_runtime = 1.0  # Ran continuous full hour
        return anom_util, anom_runtime, "RUNNING", 1

    # Pattern B: Unplanned mid-shift drop / stall during active daytime clinical hours
    elif anomaly_roll < 0.0035 and 9 <= hour <= 17 and is_24_7:
        return round(random.uniform(0.0, 5.0), 1), 0.05, "IDLE", 1

    # Pattern C: Pump continuous dry-run / stuck run
    elif anomaly_roll < 0.0020 and asset["type"] == "PUMP":
        return round(random.uniform(92.0, 98.0), 1), 0.98, "RUNNING", 1

    # Normal running state
    return round(normal_util, 1), round(normal_runtime, 2), "RUNNING", 0


# ----------------------------------------------------------------------
# 5. Dataset Generation Routine
# ----------------------------------------------------------------------
def generate_equipment_dataset() -> pd.DataFrame:
    """
    Generates exactly 21,600 records covering 90 days of 1-hour telemetry
    across the 10 defined hospital equipment assets.
    """
    records = []
    current_time = START_DATE

    # Initialize state trackers for each equipment asset
    trackers = {asset["id"]: EquipmentStateTracker(asset) for asset in EQUIPMENT_INVENTORY}

    for _ in range(TOTAL_HOURLY_INTERVALS):
        for asset in EQUIPMENT_INVENTORY:
            asset_id = asset["id"]
            tracker = trackers[asset_id]

            # 1. Determine baseline maintenance status before step
            current_maint_status = tracker.step(0.0, current_time)

            # 2. Compute telemetry
            util_pct, runtime_hrs, op_status, anomaly_flag = compute_equipment_telemetry(
                asset, current_time, current_maint_status
            )

            # 3. Update tracker with actual runtime this hour
            maint_status = tracker.step(runtime_hrs, current_time)

            records.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "facility_id": FACILITY_ID,
                "equipment_id": asset_id,
                "equipment_type": asset["type"],
                "zone_id": asset["zone"],
                "utilization_percent": util_pct,
                "runtime_hours": runtime_hrs,
                "operational_status": op_status,
                "maintenance_status": maint_status,
                "source": "synthetic",
                "anomaly_flag": anomaly_flag,
            })

        current_time += timedelta(hours=INTERVAL_HOURS)

    return pd.DataFrame(records)


# ----------------------------------------------------------------------
# 6. Data Quality Validation (16 Mandatory Rules)
# ----------------------------------------------------------------------
def validate_equipment_dataset(df: pd.DataFrame) -> None:
    """
    Validates data quality across 16 mandatory integrity rules.
    Raises ValueError with explanation if any rule is violated.
    """
    print("\nRunning Equipment / Asset Utilization Data Quality Validation...")

    # Rule 1: Exactly 21,600 rows (10 assets * 2,160 hours)
    if len(df) != EXPECTED_TOTAL_ROWS:
        raise ValueError(f"Rule 1 Failed: Expected {EXPECTED_TOTAL_ROWS} rows, got {len(df)}")

    # Rule 2: Exactly 10 assets
    actual_assets = set(df["equipment_id"].unique())
    expected_assets = {a["id"] for a in EQUIPMENT_INVENTORY}
    if actual_assets != expected_assets:
        raise ValueError(f"Rule 2 Failed: Expected assets {expected_assets}, got {actual_assets}")

    # Rule 3: No missing/null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(f"Rule 3 Failed: Missing values detected:\n{null_counts[null_counts > 0]}")

    # Rule 4: No duplicate records
    duplicates = df.duplicated(subset=["timestamp", "facility_id", "equipment_id"]).sum()
    if duplicates > 0:
        raise ValueError(f"Rule 4 Failed: Found {duplicates} duplicate records")

    # Rule 5 & 6: Hourly intervals and 90-day span
    timestamps = pd.to_datetime(df["timestamp"].drop_duplicates().sort_values())
    if len(timestamps) != TOTAL_HOURLY_INTERVALS:
        raise ValueError(f"Rule 5 Failed: Expected {TOTAL_HOURLY_INTERVALS} hourly timestamps, got {len(timestamps)}")
    diffs = timestamps.diff().dropna()
    expected_delta = pd.Timedelta(hours=INTERVAL_HOURS)
    if not (diffs == expected_delta).all():
        raise ValueError("Rule 5 Failed: Timestamp series is not strictly 1-hour steps")

    total_days = (timestamps.max() - timestamps.min()).total_seconds() / 86400.0
    if not (89.9 <= total_days <= 90.0):
        raise ValueError(f"Rule 6 Failed: Timespan must cover 90 days, got {total_days:.2f} days")

    # Rule 7: utilization_percent between 0 and 100
    if not df["utilization_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 7 Failed: utilization_percent out of bounds [0, 100]")

    # Rule 8: runtime_hours between 0 and 1.0 (for 1-hour intervals)
    if not df["runtime_hours"].between(0.0, 1.0).all():
        raise ValueError("Rule 8 Failed: runtime_hours out of bounds [0.0, 1.0]")

    # Rule 9: operational_status in allowed values
    invalid_op = set(df["operational_status"].unique()) - ALLOWED_OPERATIONAL_STATUSES
    if invalid_op:
        raise ValueError(f"Rule 9 Failed: Invalid operational_status: {invalid_op}")

    # Rule 10: maintenance_status in allowed values
    invalid_maint = set(df["maintenance_status"].unique()) - ALLOWED_MAINTENANCE_STATUSES
    if invalid_maint:
        raise ValueError(f"Rule 10 Failed: Invalid maintenance_status: {invalid_maint}")

    # Rule 11: equipment_type in allowed values
    invalid_types = set(df["equipment_type"].unique()) - ALLOWED_EQUIPMENT_TYPES
    if invalid_types:
        raise ValueError(f"Rule 11 Failed: Invalid equipment_type: {invalid_types}")

    # Rule 12: source is consistently 'synthetic'
    if not (df["source"] == "synthetic").all():
        raise ValueError("Rule 12 Failed: Inconsistent source values")

    # Rule 13: anomaly_flag is only 0 or 1
    if not df["anomaly_flag"].isin([0, 1]).all():
        raise ValueError("Rule 13 Failed: anomaly_flag contains values other than 0 and 1")

    # Rule 14: Controlled anomaly rate (0.2% - 1.5%)
    anomaly_rate = df["anomaly_flag"].mean()
    if not (0.002 <= anomaly_rate <= 0.015):
        raise ValueError(f"Rule 14 Failed: Anomaly rate ({anomaly_rate:.2%}) outside bounds (0.2% - 1.5%)")

    # Rule 15: If status is MAINTENANCE or OFFLINE, utilization should be 0.0
    inactive_mask = df["operational_status"].isin(["MAINTENANCE", "OFFLINE"])
    if (df.loc[inactive_mask, "utilization_percent"] > 0).any():
        raise ValueError("Rule 15 Failed: Inactive equipment has non-zero utilization")

    # Rule 16: facility_id is strictly H001
    if not (df["facility_id"] == FACILITY_ID).all():
        raise ValueError(f"Rule 16 Failed: facility_id contains values other than {FACILITY_ID}")

    print("All 16 Equipment Data Quality Validation checks PASSED successfully!")


# ----------------------------------------------------------------------
# 7. Main Execution Routine
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AURA: Generating Synthetic Equipment / Asset Dataset (H001)")
    print(f"Horizon: {DAYS_TO_SIMULATE} days @ 1-hour intervals")
    print(f"Total Equipment Assets: {len(EQUIPMENT_INVENTORY)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    # 1. Generate records
    df = generate_equipment_dataset()

    # 2. Validate data
    validate_equipment_dataset(df)

    # 3. Save CSV safely (handling Excel file-lock)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{OUTPUT_FILE}'.")
        print("Please close Microsoft Excel or any program holding 'equipment.csv' open and re-run.")
        exit(1)

    # 4. Print structured summary
    anomaly_count = int(df["anomaly_flag"].sum())
    anomaly_pct = (anomaly_count / len(df)) * 100.0

    print("\n" + "=" * 70)
    print("EQUIPMENT DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Generated:     {len(df):,}")
    print(f"Total Columns:           {len(df.columns)}")
    print(f"Schema Columns:          {list(df.columns)}")
    print(f"First Timestamp:         {df['timestamp'].min()}")
    print(f"Last Timestamp:          {df['timestamp'].max()}")
    print(f"Equipment Types:         {list(df['equipment_type'].unique())}")
    print(f"Equipment Assets (10):   {list(df['equipment_id'].unique())}")
    print(f"Operational Statuses:    {dict(df['operational_status'].value_counts())}")
    print(f"Maintenance Statuses:    {dict(df['maintenance_status'].value_counts())}")
    print(f"Avg Overall Utilization: {df['utilization_percent'].mean():.1f}%")
    print(f"Total Anomalies Injected:{anomaly_count:,} ({anomaly_pct:.2f}%)")
    print(f"Output File Path:        {OUTPUT_FILE}")
    print("=" * 70)
