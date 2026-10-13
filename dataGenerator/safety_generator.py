"""
AURA - AI-Powered Sustainable Facility Intelligence Platform
Synthetic Safety Incident Dataset Generator for Hospital Demo (BPUT Hackathon 2026 PS04)

Event-based incident reporting across 5 hospital zones:
- ICU, EMERGENCY, GENERAL_WARD, OPD, ADMIN

Schema (10 columns):
1. timestamp
2. facility_id
3. zone_id
4. incident_type
5. severity_level
6. response_time_min
7. occupancy_percent
8. operational_status
9. source
10. anomaly_flag
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# 1. Configuration & Reproducibility
# ----------------------------------------------------------------------
# Fixed random seed for complete reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

FACILITY_ID = "HOSPITAL_001"
HOSPITAL_ZONES = ["ICU", "EMERGENCY", "GENERAL_WARD", "OPD", "ADMIN"]

START_DATE = datetime(2026, 1, 1, 0, 0, 0)
DAYS_TO_SIMULATE = 90
END_DATE = START_DATE + timedelta(days=DAYS_TO_SIMULATE)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = OUTPUT_DIR / "safety.csv"

# Allowed Domain Values
ALLOWED_INCIDENT_TYPES = {
    "SLIP_FALL",
    "EQUIPMENT_INCIDENT",
    "FIRE_ALERT",
    "SECURITY_INCIDENT",
    "MEDICAL_EMERGENCY",
    "POWER_RELATED",
    "OTHER",
}
ALLOWED_SEVERITIES = {"LOW", "MEDIUM", "HIGH"}
ALLOWED_STATUSES = {"NORMAL", "MAINTENANCE", "REDUCED_OPERATION", "EMERGENCY"}

# Zone-wise baseline daily incident frequency tendencies (mean events per day)
ZONE_INCIDENT_WEIGHTS = {
    "EMERGENCY": 6.5,     # Highest activity: rapid intake, security, acute medical calls
    "GENERAL_WARD": 5.5,  # High patient movement, slip/falls, nurse call button alarms
    "OPD": 3.8,           # Daytime crowd footfall, queues, security alerts
    "ICU": 2.8,           # Controlled access: equipment alarms, acute interventions
    "ADMIN": 1.2,         # Low risk office floor: slips, power trips, minor facility calls
}

# Incident Type distribution probabilities by zone
INCIDENT_TYPE_PROBS = {
    "EMERGENCY": [
        ("MEDICAL_EMERGENCY", 0.35),
        ("SECURITY_INCIDENT", 0.20),
        ("EQUIPMENT_INCIDENT", 0.18),
        ("SLIP_FALL", 0.12),
        ("POWER_RELATED", 0.08),
        ("FIRE_ALERT", 0.02),
        ("OTHER", 0.05),
    ],
    "GENERAL_WARD": [
        ("SLIP_FALL", 0.32),
        ("MEDICAL_EMERGENCY", 0.25),
        ("EQUIPMENT_INCIDENT", 0.20),
        ("SECURITY_INCIDENT", 0.08),
        ("POWER_RELATED", 0.07),
        ("FIRE_ALERT", 0.02),
        ("OTHER", 0.06),
    ],
    "OPD": [
        ("SECURITY_INCIDENT", 0.30),
        ("SLIP_FALL", 0.28),
        ("MEDICAL_EMERGENCY", 0.15),
        ("EQUIPMENT_INCIDENT", 0.10),
        ("POWER_RELATED", 0.08),
        ("FIRE_ALERT", 0.02),
        ("OTHER", 0.07),
    ],
    "ICU": [
        ("EQUIPMENT_INCIDENT", 0.40),
        ("MEDICAL_EMERGENCY", 0.35),
        ("POWER_RELATED", 0.12),
        ("SLIP_FALL", 0.05),
        ("FIRE_ALERT", 0.02),
        ("SECURITY_INCIDENT", 0.02),
        ("OTHER", 0.04),
    ],
    "ADMIN": [
        ("SLIP_FALL", 0.30),
        ("POWER_RELATED", 0.25),
        ("SECURITY_INCIDENT", 0.18),
        ("FIRE_ALERT", 0.08),
        ("EQUIPMENT_INCIDENT", 0.07),
        ("MEDICAL_EMERGENCY", 0.04),
        ("OTHER", 0.08),
    ],
}


# ----------------------------------------------------------------------
# 2. Controlled Anomaly Window Definitions
# ----------------------------------------------------------------------
# Specific dates where localized facility distress/surges happen
ANOMALY_PERIODS = [
    {
        "name": "Emergency Mass-Casualty / Trauma Surge",
        "start_day": 24,
        "end_day": 27,
        "zone": "EMERGENCY",
        "freq_multiplier": 3.2,
    },
    {
        "name": "General Ward Plumbing Leak / Wet-Floor Hazard",
        "start_day": 58,
        "end_day": 61,
        "zone": "GENERAL_WARD",
        "freq_multiplier": 2.8,
    },
    {
        "name": "OPD Heavy Crowd / Queue Agitation Cluster",
        "start_day": 76,
        "end_day": 78,
        "zone": "OPD",
        "freq_multiplier": 3.0,
    },
]


# ----------------------------------------------------------------------
# 3. Helper Functions for Realism
# ----------------------------------------------------------------------
def pick_incident_type(zone: str) -> str:
    """Samples realistic incident type according to zone profile."""
    probs = INCIDENT_TYPE_PROBS[zone]
    types, weights = zip(*probs)
    return random.choices(types, weights=weights, k=1)[0]


def pick_severity_level(incident_type: str, is_anomaly: bool) -> str:
    """
    Samples severity: LOW (~60%), MEDIUM (~30%), HIGH (~10%).
    HIGH severity is intentionally rare for realism.
    """
    if incident_type in ["FIRE_ALERT", "MEDICAL_EMERGENCY"]:
        # Higher baseline severity for fire alarms and medical emergencies
        weights = [0.35, 0.45, 0.20] if not is_anomaly else [0.25, 0.45, 0.30]
    elif incident_type == "SLIP_FALL":
        weights = [0.65, 0.28, 0.07]
    elif incident_type == "SECURITY_INCIDENT":
        weights = [0.55, 0.35, 0.10]
    else:
        weights = [0.68, 0.26, 0.06]

    return random.choices(["LOW", "MEDIUM", "HIGH"], weights=weights, k=1)[0]


def compute_response_time(severity: str, zone: str) -> float:
    """
    Computes realistic operational staff response time in minutes:
    - HIGH severity: Rapid dispatch (2.0 - 8.5 min)
    - MEDIUM severity: Standard operational priority (5.5 - 18.0 min)
    - LOW severity: Routine maintenance / housekeeping response (12.0 - 35.0 min)
    """
    if severity == "HIGH":
        base = random.uniform(2.5, 7.5)
        if zone in ["ICU", "EMERGENCY"]:
            base = max(1.5, base - 1.2)  # Critical zones respond even faster
    elif severity == "MEDIUM":
        base = random.uniform(6.0, 16.5)
    else:  # LOW
        base = random.uniform(12.0, 32.0)

    return round(base, 1)


def get_occupancy_and_status(zone: str, dt: datetime, is_anomaly: bool) -> tuple[float, str]:
    """
    Generates realistic occupancy percent and operational status
    at the time of the reported safety event.
    """
    hour = dt.hour + (dt.minute / 60.0)
    is_weekend = dt.weekday() >= 5
    is_sunday = dt.weekday() == 6

    # Operational status
    if is_anomaly and zone == "EMERGENCY":
        status = "EMERGENCY"
    elif is_sunday and 6.0 <= hour <= 9.0 and random.random() < 0.25:
        status = "MAINTENANCE"
    elif zone in ["OPD", "ADMIN"] and (is_weekend or hour < 8.0 or hour > 18.5):
        status = "REDUCED_OPERATION"
    elif zone == "GENERAL_WARD" and (hour >= 23.0 or hour <= 5.0):
        status = "REDUCED_OPERATION"
    else:
        status = "NORMAL"

    # Occupancy percent
    if status == "REDUCED_OPERATION":
        if zone in ["OPD", "ADMIN"]:
            occ = random.uniform(0.0, 6.0)
        else:
            occ = random.uniform(50.0, 62.0)
    elif zone == "ICU":
        occ = random.uniform(75.0, 95.0)
    elif zone == "EMERGENCY":
        occ = random.uniform(60.0, 92.0) if not is_anomaly else random.uniform(85.0, 100.0)
    elif zone == "GENERAL_WARD":
        occ = random.uniform(65.0, 88.0)
    elif zone == "OPD":
        if 8.5 <= hour <= 14.0:
            occ = random.uniform(75.0, 98.0)
        else:
            occ = random.uniform(25.0, 55.0)
    elif zone == "ADMIN":
        occ = random.uniform(60.0, 85.0) if (9.0 <= hour <= 18.0) else random.uniform(2.0, 8.0)
    else:
        occ = 50.0

    return round(max(0.0, min(100.0, occ)), 1), status


# ----------------------------------------------------------------------
# 4. Main Event-Based Incident Generation Routine
# ----------------------------------------------------------------------
def generate_safety_dataset() -> pd.DataFrame:
    """
    Generates event-based incident reports across 90 days.
    Produces roughly 1,500 - 2,200 incident records.
    """
    records = []

    for day_idx in range(DAYS_TO_SIMULATE):
        day_date = START_DATE + timedelta(days=day_idx)

        for zone in HOSPITAL_ZONES:
            # Check if this zone is currently in a controlled anomaly window
            is_in_anomaly_period = False
            anomaly_multiplier = 1.0

            for window in ANOMALY_PERIODS:
                if window["zone"] == zone and (window["start_day"] <= day_idx <= window["end_day"]):
                    is_in_anomaly_period = True
                    anomaly_multiplier = window["freq_multiplier"]
                    break

            base_rate = ZONE_INCIDENT_WEIGHTS[zone]

            # Day of week adjustment (Sunday has slightly fewer OPD/Admin calls, slightly more Emergency calls)
            if day_date.weekday() == 6:
                if zone in ["OPD", "ADMIN"]:
                    base_rate *= 0.25
                elif zone == "EMERGENCY":
                    base_rate *= 1.25

            # Calculate daily incident count using Poisson-like randomized sampling
            mean_events = base_rate * anomaly_multiplier
            event_count = max(0, int(round(random.gauss(mean_events, mean_events * 0.25))))

            for _ in range(event_count):
                # Sample random time of day for this incident
                # Daytime hours have higher reporting likelihood
                if random.random() < 0.72:
                    # Daytime between 07:00 and 21:00
                    rand_seconds = random.randint(7 * 3600, 21 * 3600)
                else:
                    # Nighttime
                    rand_seconds = random.randint(0, 86399)

                incident_dt = day_date + timedelta(seconds=rand_seconds)

                # Incident characteristics
                inc_type = pick_incident_type(zone)
                severity = pick_severity_level(inc_type, is_in_anomaly_period)
                resp_time = compute_response_time(severity, zone)
                occ_pct, status = get_occupancy_and_status(zone, incident_dt, is_in_anomaly_period)

                anomaly_flag = 1 if is_in_anomaly_period else 0

                records.append({
                    "timestamp": incident_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "facility_id": FACILITY_ID,
                    "zone_id": zone,
                    "incident_type": inc_type,
                    "severity_level": severity,
                    "response_time_min": resp_time,
                    "occupancy_percent": occ_pct,
                    "operational_status": status,
                    "source": "synthetic",
                    "anomaly_flag": anomaly_flag,
                })

    df = pd.DataFrame(records)

    # Sort strictly chronologically by timestamp
    df["dt_temp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("dt_temp").drop(columns=["dt_temp"]).reset_index(drop=True)

    return df


# ----------------------------------------------------------------------
# 5. Data Quality Validation (16 Rules)
# ----------------------------------------------------------------------
def validate_safety_dataset(df: pd.DataFrame) -> None:
    """
    Validates data quality before saving to CSV.
    Raises ValueError with explanation if any rule is broken.
    """
    print("\nRunning Safety Intelligence Data Quality Validation...")

    # Rule 1: Expected record count range (roughly 1,000 - 3,000 records)
    total_records = len(df)
    if not (1000 <= total_records <= 3000):
        raise ValueError(
            f"Rule 1 Failed: Expected between 1,000 and 3,000 incident records, got {total_records}"
        )

    # Rule 2: Expected columns exist exactly
    expected_cols = [
        "timestamp",
        "facility_id",
        "zone_id",
        "incident_type",
        "severity_level",
        "response_time_min",
        "occupancy_percent",
        "operational_status",
        "source",
        "anomaly_flag",
    ]
    if list(df.columns) != expected_cols:
        raise ValueError(f"Rule 2 Failed: Columns mismatch.\nExpected: {expected_cols}\nGot: {list(df.columns)}")

    # Rule 3: No missing/null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        raise ValueError(f"Rule 3 Failed: Missing values detected:\n{null_counts[null_counts > 0]}")

    # Rule 4: No duplicate rows
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        raise ValueError(f"Rule 4 Failed: Found {duplicates} exact duplicate rows")

    # Rule 5: 90-day coverage
    ts = pd.to_datetime(df["timestamp"])
    total_days = (ts.max() - ts.min()).total_seconds() / 86400.0
    if not (88.0 <= total_days <= 91.0):
        raise ValueError(f"Rule 5 Failed: Timespan must cover ~90 days, got {total_days:.2f} days")

    # Rule 6: facility_id is correct
    if not (df["facility_id"] == FACILITY_ID).all():
        raise ValueError(f"Rule 6 Failed: Inconsistent facility_id found")

    # Rule 7: Only allowed zones
    actual_zones = set(df["zone_id"].unique())
    expected_zones = set(HOSPITAL_ZONES)
    if not actual_zones.issubset(expected_zones):
        raise ValueError(f"Rule 7 Failed: Unexpected zones {actual_zones - expected_zones}")

    # Rule 8: Only allowed incident types
    actual_types = set(df["incident_type"].unique())
    if not actual_types.issubset(ALLOWED_INCIDENT_TYPES):
        raise ValueError(f"Rule 8 Failed: Unexpected incident types: {actual_types - ALLOWED_INCIDENT_TYPES}")

    # Rule 9: Only allowed severities
    actual_sevs = set(df["severity_level"].unique())
    if not actual_sevs.issubset(ALLOWED_SEVERITIES):
        raise ValueError(f"Rule 9 Failed: Unexpected severity levels: {actual_sevs - ALLOWED_SEVERITIES}")

    # Rule 10: response_time_min is positive
    if not (df["response_time_min"] > 0).all():
        raise ValueError("Rule 10 Failed: Non-positive response_time_min detected")

    # Rule 11: occupancy_percent between 0 and 100
    if not df["occupancy_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 11 Failed: occupancy_percent out of bounds [0, 100]")

    # Rule 12: operational_status in allowed values
    actual_statuses = set(df["operational_status"].unique())
    if not actual_statuses.issubset(ALLOWED_STATUSES):
        raise ValueError(f"Rule 12 Failed: Unexpected operational_status: {actual_statuses - ALLOWED_STATUSES}")

    # Rule 13: source is consistently 'synthetic'
    if not (df["source"] == "synthetic").all():
        raise ValueError("Rule 13 Failed: Inconsistent source values")

    # Rule 14: anomaly_flag contains only 0 or 1
    if not df["anomaly_flag"].isin([0, 1]).all():
        raise ValueError("Rule 14 Failed: anomaly_flag contains values other than 0 and 1")

    # Rule 15: HIGH severity incidents are reasonably rare (< 25% of all incidents)
    high_sev_pct = (df["severity_level"] == "HIGH").mean()
    if high_sev_pct > 0.25:
        raise ValueError(f"Rule 15 Failed: HIGH severity incidents unrealistically common ({high_sev_pct:.1%})")

    # Rule 16: Anomaly rate is controlled (between 3% and 18% of incident events)
    anomaly_rate = df["anomaly_flag"].mean()
    if not (0.03 <= anomaly_rate <= 0.18):
        raise ValueError(f"Rule 16 Failed: Anomaly rate ({anomaly_rate:.1%}) outside realistic window [3%, 18%]")

    print("All 16 Safety Intelligence Data Quality Validation checks PASSED successfully!")


# ----------------------------------------------------------------------
# 6. Main Execution Routine
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AURA: Generating Synthetic Safety Incident Dataset (HOSPITAL_001)")
    print(f"Horizon: ~{DAYS_TO_SIMULATE} days (Event-Based Incident Telemetry)")
    print(f"Hospital Zones: {', '.join(HOSPITAL_ZONES)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    # 1. Generate records
    df = generate_safety_dataset()

    # 2. Validate data
    validate_safety_dataset(df)

    # 3. Save CSV safely (handling Excel file-lock)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{OUTPUT_FILE}'.")
        print("Please close Microsoft Excel or any program holding 'safety.csv' open and re-run.")
        exit(1)

    # 4. Print structured summary
    anomaly_count = int(df["anomaly_flag"].sum())
    anomaly_pct = (anomaly_count / len(df)) * 100.0

    print("\n" + "=" * 70)
    print("SAFETY DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Incident Records:   {len(df):,}")
    print(f"Total Columns:           {len(df.columns)}")
    print(f"Schema Columns:          {list(df.columns)}")
    print(f"First Incident Timestamp:{df['timestamp'].min()}")
    print(f"Last Incident Timestamp: {df['timestamp'].max()}")
    print(f"Incidents by Zone:       {dict(df['zone_id'].value_counts())}")
    print(f"Incidents by Type:       {dict(df['incident_type'].value_counts())}")
    print(f"Severity Distribution:   {dict(df['severity_level'].value_counts())}")
    print(f"Avg Response Time:       {df['response_time_min'].mean():.1f} minutes")
    print(f"Controlled Anomalies:    {anomaly_count:,} ({anomaly_pct:.1f}%)")
    print(f"Output File Path:        {OUTPUT_FILE}")
    print("=" * 70)
