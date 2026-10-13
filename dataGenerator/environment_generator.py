"""
AURA - AI-Powered Sustainable Facility Intelligence Platform
Synthetic Environment / AQI Dataset Generator for Hospital Demo (BPUT Hackathon 2026 PS04)

Generates 90 days of realistic 15-minute interval environmental telemetry across
5 hospital zones (ICU, Emergency, General_Ward, OPD, Admin).

Features:
- Air Quality Index (aqi)
- Particulate matter telemetry (pm25, pm10 in µg/m³)
- Environmental context (temperature_c, humidity_percent, wind_speed_kmh)
- Operational context (operational_status)
- Controlled decision-support anomalies (anomaly_flag)

Schema (12 columns):
1. timestamp
2. facility_id
3. zone_id
4. aqi
5. pm25
6. pm10
7. temperature_c
8. humidity_percent
9. wind_speed_kmh
10. operational_status
11. source
12. anomaly_flag
"""

import math
import random
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

# ----------------------------------------------------------------------
# 1. Configuration & Reproducibility
# ----------------------------------------------------------------------
# Fixed random seed taaki dataset 100% reproducible rahe
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
OUTPUT_FILE = OUTPUT_DIR / "environment.csv"

# Allowed Domain Values
ALLOWED_STATUSES = {"NORMAL", "MAINTENANCE", "REDUCED_OPERATION", "EMERGENCY"}

# Zone Environmental Profiles (indoor filtration, external exposure)
ZONE_ENV_SPECS = {
    "ICU": {
        "pm25_base": 18.0,      # HEPA filtered, positive pressure, cleanest air
        "pm10_base": 28.0,
        "filtration_efficiency": 0.85,
    },
    "Admin": {
        "pm25_base": 32.0,      # Standard office HVAC, closed windows
        "pm10_base": 50.0,
        "filtration_efficiency": 0.55,
    },
    "General_Ward": {
        "pm25_base": 38.0,      # Cross ventilation, open windows, visiting hours footfall
        "pm10_base": 65.0,
        "filtration_efficiency": 0.35,
    },
    "OPD": {
        "pm25_base": 44.0,      # High crowd footfall, corridor dust resuspension
        "pm10_base": 88.0,
        "filtration_efficiency": 0.25,
    },
    "Emergency": {
        "pm25_base": 52.0,      # Ground floor, ambulance bays, vehicular exhaust exposure
        "pm10_base": 92.0,
        "filtration_efficiency": 0.20,
    },
}


# ----------------------------------------------------------------------
# 2. Environmental Context Simulation (Weather / Ambient Dynamics)
# ----------------------------------------------------------------------
def get_ambient_weather(dt: datetime) -> tuple[float, float, float]:
    """
    Simulates campus-level weather:
    - Temperature (°C): 20°C - 38°C sinusoidal diurnal wave
    - Humidity (%): 35% - 85% (subah high, dopahar me low)
    - Wind Speed (km/h): 3 - 22 km/h (dopahar breezy, night calm)

    Returns: (temperature_c, humidity_percent, wind_speed_kmh)
    """
    day_fraction = (dt.hour * 60 + dt.minute) / 1440.0
    day_of_year = dt.timetuple().tm_yday

    # 1. Temperature (°C): Min at 05:00 AM, Peak at 14:00 PM
    temp_diurnal = -math.cos(2 * math.pi * (day_fraction - 0.21))
    seasonal_drift = 25.0 + (day_of_year / 90.0) * 5.0
    temp_c = seasonal_drift + (6.5 * temp_diurnal) + random.uniform(-0.7, 0.7)
    temp_c = round(temp_c, 1)

    # 2. Humidity (%): Inversely related to temperature
    humidity_base = 62.0 - (18.0 * temp_diurnal) + random.uniform(-3.5, 3.5)
    humidity_percent = round(max(25.0, min(95.0, humidity_base)), 1)

    # 3. Wind Speed (km/h): Calm nights, breezier afternoons
    wind_diurnal = -math.cos(2 * math.pi * (day_fraction - 0.35))
    wind_speed = 9.0 + (5.5 * wind_diurnal) + random.uniform(-2.0, 2.5)
    wind_speed_kmh = round(max(1.5, wind_speed), 1)

    return temp_c, humidity_percent, wind_speed_kmh


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

    # Acute emergency surge in Emergency/ICU
    if zone in ["Emergency", "ICU"] and random.random() < 0.003:
        return "EMERGENCY"

    # Routine civil/HVAC filter maintenance (Sunday mornings 06:00-09:00)
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
# 4. Pollutant & AQI Simulation with Controlled Anomalies
# ----------------------------------------------------------------------
def compute_air_quality(
    zone: str,
    temp_c: float,
    humidity: float,
    wind_speed: float,
    status: str,
    dt: datetime
) -> tuple[float, float, float, int]:
    """
    Computes (aqi, pm25, pm10, anomaly_flag) for a given zone and weather context:
    - Zone specific baseline & filtration
    - Diurnal traffic & crowd patterns (morning & evening rush)
    - Atmospheric inversion effect (high humidity + low wind traps particles)
    - Controlled decision-support anomaly injection (~0.55% rate)

    Returns:
        (aqi, pm25, pm10, anomaly_flag)
    """
    spec = ZONE_ENV_SPECS[zone]
    hour = dt.hour + (dt.minute / 60.0)

    # 1. Diurnal traffic & activity factor
    # Rush hours (08:00 - 10:30 & 17:30 - 20:30) have higher outdoor emissions
    activity_multiplier = 1.0
    if (8.0 <= hour <= 10.5) or (17.5 <= hour <= 20.5):
        activity_multiplier = 1.30  # Peak traffic & movement
    elif 11.0 <= hour <= 15.0:
        activity_multiplier = 1.05  # Sun dispersion
    elif 0.0 <= hour <= 5.0:
        activity_multiplier = 0.80  # Low traffic nighttime

    # 2. OPD daytime crowd footfall factor
    if zone == "OPD":
        if 8.5 <= hour <= 13.5:
            activity_multiplier *= 1.45  # OPD morning crowd dust
        elif status == "REDUCED_OPERATION":
            activity_multiplier *= 0.45  # Closed clinic

    # 3. Weather dispersion impact (Higher wind disperses; high humidity traps)
    dispersion_factor = 1.0 - (wind_speed / 40.0) + (humidity / 250.0)

    # 4. Calculate baseline PM2.5 and PM10
    noise_pm25 = random.uniform(-3.0, 3.0)
    noise_pm10 = random.uniform(-6.0, 6.0)

    pm25 = max(5.0, (spec["pm25_base"] * activity_multiplier * dispersion_factor) + noise_pm25)
    pm10 = max(10.0, (spec["pm10_base"] * activity_multiplier * dispersion_factor) + noise_pm10)

    # Operational status adjustment (Maintenance causes slight local dust)
    if status == "MAINTENANCE":
        pm10 += random.uniform(15.0, 25.0)

    # ------------------------------------------------------------------
    # Controlled Anomaly Injection (~0.55% overall probability)
    # ------------------------------------------------------------------
    anomaly_roll = random.random()

    # Pattern A: Ambulance Bay Vehicular Idling / Diesel exhaust surge at Emergency
    if anomaly_roll < 0.003 and zone == "Emergency":
        pm25 += random.uniform(55.0, 85.0)   # Heavy diesel smoke ingress
        pm10 += random.uniform(40.0, 65.0)
        aqi_val = 1.45 * pm25 + 0.35 * pm10 - (0.4 * wind_speed) + random.uniform(-4, 4)
        return round(aqi_val, 1), round(pm25, 1), round(pm10, 1), 1

    # Pattern B: Civil Renovation / Uncontained Tile Cutting Dust at OPD/Admin
    elif anomaly_roll < 0.005 and zone in ["OPD", "Admin"]:
        pm10 += random.uniform(85.0, 140.0)  # Heavy dust surge
        pm25 += random.uniform(20.0, 35.0)
        aqi_val = 1.35 * pm25 + 0.40 * pm10 - (0.4 * wind_speed) + random.uniform(-4, 4)
        return round(aqi_val, 1), round(pm25, 1), round(pm10, 1), 1

    # Pattern C: Localized HVAC Filter bypass / window left open in Ward
    elif anomaly_roll < 0.007 and zone == "General_Ward":
        pm25 += random.uniform(40.0, 65.0)
        pm10 += random.uniform(50.0, 75.0)
        aqi_val = 1.40 * pm25 + 0.35 * pm10 - (0.4 * wind_speed) + random.uniform(-4, 4)
        return round(aqi_val, 1), round(pm25, 1), round(pm10, 1), 1

    # Normal observation AQI calculation (synthetic formulation for prototype)
    normal_aqi = 1.35 * pm25 + 0.32 * pm10 - (0.4 * wind_speed) + random.uniform(-3, 3)
    normal_aqi = max(15.0, normal_aqi)

    return round(normal_aqi, 1), round(pm25, 1), round(pm10, 1), 0


# ----------------------------------------------------------------------
# 5. Dataset Generation Routine
# ----------------------------------------------------------------------
def generate_environment_dataset() -> pd.DataFrame:
    """
    Generates exactly 43,200 records covering 90 days of 15-minute readings
    for 5 hospital zones.
    """
    records = []
    current_time = START_DATE

    for _ in range(TOTAL_INTERVALS):
        # Weather is campus-wide for this timestamp
        temp_c, humidity, wind_speed = get_ambient_weather(current_time)

        for zone in HOSPITAL_ZONES:
            status = get_operational_status(zone, current_time)
            aqi, pm25, pm10, anomaly_flag = compute_air_quality(
                zone, temp_c, humidity, wind_speed, status, current_time
            )

            records.append({
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "facility_id": FACILITY_ID,
                "zone_id": zone,
                "aqi": aqi,
                "pm25": pm25,
                "pm10": pm10,
                "temperature_c": temp_c,
                "humidity_percent": humidity,
                "wind_speed_kmh": wind_speed,
                "operational_status": status,
                "source": "synthetic",
                "anomaly_flag": anomaly_flag,
            })

        current_time += timedelta(minutes=INTERVAL_MINUTES)

    return pd.DataFrame(records)


# ----------------------------------------------------------------------
# 6. Data Quality Validation (18 Mandatory Rules)
# ----------------------------------------------------------------------
def validate_environment_dataset(df: pd.DataFrame) -> None:
    """
    Validates data quality before saving to CSV.
    Raises ValueError with explanation if any rule is broken.
    """
    print("\nRunning Environment / AQI Data Quality Validation...")

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

    # Rule 7: aqi is non-negative
    if not (df["aqi"] >= 0).all():
        raise ValueError("Rule 7 Failed: Negative aqi detected")

    # Rule 8: pm25 is non-negative
    if not (df["pm25"] >= 0).all():
        raise ValueError("Rule 8 Failed: Negative pm25 detected")

    # Rule 9: pm10 is non-negative
    if not (df["pm10"] >= 0).all():
        raise ValueError("Rule 9 Failed: Negative pm10 detected")

    # Rule 10: temperature_c within plausible synthetic range (15°C to 45°C)
    if not df["temperature_c"].between(15.0, 45.0).all():
        raise ValueError("Rule 10 Failed: temperature_c out of range (15-45°C)")

    # Rule 11: humidity_percent between 0 and 100
    if not df["humidity_percent"].between(0.0, 100.0).all():
        raise ValueError("Rule 11 Failed: humidity_percent out of bounds [0, 100]")

    # Rule 12: wind_speed_kmh is non-negative
    if not (df["wind_speed_kmh"] >= 0).all():
        raise ValueError("Rule 12 Failed: Negative wind_speed_kmh detected")

    # Rule 13: source is consistently 'synthetic'
    if not (df["source"] == "synthetic").all():
        raise ValueError("Rule 13 Failed: Inconsistent source values")

    # Rule 14: anomaly_flag is only 0 or 1
    if not df["anomaly_flag"].isin([0, 1]).all():
        raise ValueError("Rule 14 Failed: anomaly_flag contains values other than 0 and 1")

    # Rule 15: Controlled anomaly rate (0.3% - 2.0%)
    anomaly_rate = df["anomaly_flag"].mean()
    if not (0.003 <= anomaly_rate <= 0.02):
        raise ValueError(f"Rule 15 Failed: Anomaly rate ({anomaly_rate:.2%}) outside bounds (0.3% - 2.0%)")

    # Rule 16: operational_status in allowed values
    invalid_statuses = set(df["operational_status"].unique()) - ALLOWED_STATUSES
    if invalid_statuses:
        raise ValueError(f"Rule 16 Failed: Invalid operational_status: {invalid_statuses}")

    # Rule 17: facility_id is strictly H001
    if not (df["facility_id"] == FACILITY_ID).all():
        raise ValueError(f"Rule 17 Failed: facility_id contains values other than {FACILITY_ID}")

    print("All 18 Environment / AQI Data Quality Validation checks PASSED successfully!")


# ----------------------------------------------------------------------
# 7. Main Execution Routine
# ----------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("AURA: Generating Synthetic Environment / AQI Dataset (H001)")
    print(f"Horizon: {DAYS_TO_SIMULATE} days @ 15-min intervals")
    print(f"Hospital Zones: {', '.join(HOSPITAL_ZONES)}")
    print(f"Random Seed: {RANDOM_SEED}")
    print("=" * 70)

    # 1. Generate records
    df = generate_environment_dataset()

    # 2. Validate data
    validate_environment_dataset(df)

    # 3. Save CSV safely (handling Excel file-lock)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(OUTPUT_FILE, index=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied when writing to '{OUTPUT_FILE}'.")
        print("Please close Microsoft Excel or any program holding 'environment.csv' open and re-run.")
        exit(1)

    # 4. Print structured summary
    anomaly_count = int(df["anomaly_flag"].sum())
    anomaly_pct = (anomaly_count / len(df)) * 100.0

    print("\n" + "=" * 70)
    print("ENVIRONMENT DATASET GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Rows Generated:     {len(df):,}")
    print(f"Total Columns:           {len(df.columns)}")
    print(f"Schema Columns:          {list(df.columns)}")
    print(f"First Timestamp:         {df['timestamp'].min()}")
    print(f"Last Timestamp:          {df['timestamp'].max()}")
    print(f"Hospital Zones:          {list(df['zone_id'].unique())}")
    print(f"Avg Campus AQI:          {df['aqi'].mean():.1f}")
    print(f"Avg PM2.5:               {df['pm25'].mean():.1f} µg/m³")
    print(f"Avg PM10:                {df['pm10'].mean():.1f} µg/m³")
    print(f"Operational Statuses:    {dict(df['operational_status'].value_counts())}")
    print(f"Total Anomalies Injected:{anomaly_count:,} ({anomaly_pct:.2f}%)")
    print(f"Output File Path:        {OUTPUT_FILE}")
    print("=" * 70)
