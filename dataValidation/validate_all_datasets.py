"""
AURA — Central Data Validation Suite
Facility: HOSPITAL_001 / H001
Module: Multi-Dataset Pre-EDA / Pre-ML Validation Layer

Validates all 7 synthetic facility datasets:
  1. energy.csv
  2. water.csv
  3. waste.csv
  4. environment.csv
  5. equipment.csv
  6. safety.csv
  7. traffic.csv

Ensures structure, schema, constraints, domain values,
time-series consistency, and anomaly labels are fully valid.
"""

from pathlib import Path
import pandas as pd
import sys

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Standard Allowed Facility IDs across generation iterations
VALID_FACILITY_IDS = {"H001", "HOSPITAL_001"}

# Standard Hospital Zones
HOSPITAL_ZONES_TITLE = {"ICU", "Emergency", "General_Ward", "OPD", "Admin"}
HOSPITAL_ZONES_UPPER = {"ICU", "EMERGENCY", "GENERAL_WARD", "OPD", "ADMIN"}
TRAFFIC_ZONES = {"MAIN_GATE", "EMERGENCY_GATE", "VISITOR_PARKING", "STAFF_PARKING", "SERVICE_ENTRY"}

# Operational Status allowed across modules
FACILITY_OPERATIONAL_STATUS = {"NORMAL", "REDUCED_OPERATION", "EMERGENCY", "MAINTENANCE"}
EQUIPMENT_OPERATIONAL_STATUS = {"RUNNING", "IDLE", "OFFLINE", "MAINTENANCE"}
EQUIPMENT_MAINTENANCE_STATUS = {"NORMAL", "DUE_SOON", "OVERDUE"}
EQUIPMENT_TYPES = {"VENTILATOR", "PATIENT_MONITOR", "HVAC", "PUMP"}

def parse_timestamps(series):
    """
    Parse timestamps safely.
    Handles ISO (%Y-%m-%d) or Indian/European (%d-%m-%Y) formats without date distortion.
    """
    first_val = str(series.dropna().iloc[0]).strip()
    if first_val[:4].isdigit() and "-" in first_val[:5]:
        # ISO format (e.g. 2026-01-01 00:00:00)
        return pd.to_datetime(series, errors="coerce")
    else:
        # Day-first format (e.g. 01-01-2026 00:00)
        return pd.to_datetime(series, dayfirst=True, errors="coerce")


class DatasetValidator:
    """
    Validates a single dataset with general and module-specific rules.
    Collects failures and generates clean report.
    """
    def __init__(self, name, filename, expected_cols):
        self.name = name
        self.filename = filename
        self.file_path = DATA_DIR / filename
        self.expected_cols = expected_cols
        self.df = None
        self.parsed_ts = None
        self.failures = []  # list of (column, problem, invalid_count)

    def record_failure(self, column, problem, invalid_count):
        self.failures.append((column, problem, invalid_count))

    def load_and_run_general_checks(self):
        # 1. File exists
        if not self.file_path.exists():
            self.record_failure("FILE", f"File not found at {self.file_path}", 1)
            return False

        # 2. Can load CSV
        try:
            self.df = pd.read_csv(self.file_path)
        except Exception as e:
            self.record_failure("FILE", f"Failed to parse CSV: {e}", 1)
            return False

        if len(self.df) == 0:
            self.record_failure("ROWS", "Dataset is empty (0 rows)", 0)
            return False

        # 3 & 4. Column checks
        actual_cols = list(self.df.columns)
        if actual_cols != self.expected_cols:
            missing = set(self.expected_cols) - set(actual_cols)
            extra = set(actual_cols) - set(self.expected_cols)
            if missing:
                self.record_failure("COLUMNS", f"Missing expected columns: {missing}", len(missing))
            if extra:
                self.record_failure("COLUMNS", f"Unexpected extra columns: {extra}", len(extra))

        # 5. Missing values
        null_counts = self.df.isnull().sum()
        for col, count in null_counts.items():
            if count > 0:
                self.record_failure(col, "Contains missing/NaN values", int(count))

        # 6. Duplicate rows
        dup_count = int(self.df.duplicated().sum())
        if dup_count > 0:
            self.record_failure("ROWS", "Duplicate rows detected", dup_count)

        # 7 & 8. Timestamp parsing & range
        if "timestamp" in self.df.columns:
            ts = parse_timestamps(self.df["timestamp"])
            null_ts = int(ts.isna().sum())
            if null_ts > 0:
                self.record_failure("timestamp", "Unparseable timestamp values", null_ts)
            else:
                self.parsed_ts = ts
                min_ts = ts.min()
                max_ts = ts.max()
                day_span = (max_ts - min_ts).days
                if day_span < 80 or day_span > 100:
                    self.record_failure("timestamp", f"Expected ~90 days coverage, got {day_span} days ({min_ts} to {max_ts})", 1)

        # 9. facility_id valid
        if "facility_id" in self.df.columns:
            invalid_facility = (~self.df["facility_id"].isin(VALID_FACILITY_IDS)).sum()
            if invalid_facility > 0:
                self.record_failure("facility_id", f"Contains invalid facility_id (allowed: {VALID_FACILITY_IDS})", int(invalid_facility))

        # 10. source is always 'synthetic'
        if "source" in self.df.columns:
            invalid_source = (self.df["source"] != "synthetic").sum()
            if invalid_source > 0:
                self.record_failure("source", "Source is not strictly 'synthetic'", int(invalid_source))

        # 11. anomaly_flag binary (0 or 1)
        if "anomaly_flag" in self.df.columns:
            invalid_anomaly = (~self.df["anomaly_flag"].isin({0, 1})).sum()
            if invalid_anomaly > 0:
                self.record_failure("anomaly_flag", "anomaly_flag must contain only 0 or 1", int(invalid_anomaly))

        return True

    def validate_specific(self):
        """Module-specific validations implemented by subclasses/handlers"""
        pass

    def run(self):
        ok = self.load_and_run_general_checks()
        if ok:
            self.validate_specific()
        return len(self.failures) == 0

    def print_report(self):
        total_rows = len(self.df) if self.df is not None else 0
        anomaly_count = int(self.df["anomaly_flag"].sum()) if (self.df is not None and "anomaly_flag" in self.df.columns) else 0
        anomaly_pct = (anomaly_count / total_rows * 100) if total_rows > 0 else 0

        ts_info = "N/A"
        if self.parsed_ts is not None and not self.parsed_ts.empty:
            ts_info = f"{self.parsed_ts.min()} to {self.parsed_ts.max()} ({(self.parsed_ts.max() - self.parsed_ts.min()).days} days)"

        status = "PASS" if len(self.failures) == 0 else "FAIL"

        print(f"\n{'-'*60}")
        print(f"[{status}] DATASET: {self.name.upper()} ({self.filename})")
        print(f"{'-'*60}")
        print(f"  Total Rows:         {total_rows:,}")
        print(f"  Date Range:         {ts_info}")
        print(f"  Anomaly Records:    {anomaly_count:,} ({anomaly_pct:.1f}%)")
        print(f"  Missing Values:     {'PASS (0)' if not any(f[1] == 'Contains missing/NaN values' for f in self.failures) else 'FAIL'}")
        print(f"  Duplicate Rows:     {'PASS (0)' if not any(f[1] == 'Duplicate rows detected' for f in self.failures) else 'FAIL'}")

        if len(self.failures) == 0:
            print(f"  Module Constraints: PASS (All schema & domain checks met)")
            print(f"  Validation Result:  >>> PASS <<<")
        else:
            print(f"  Validation Result:  >>> FAIL ({len(self.failures)} issues found) <<<")
            print("  Failure Details:")
            for col, prob, count in self.failures:
                print(f"    * Column: [{col}] -> {prob} (Affected records: {count})")


# -------------------------------------------------------------
# SPECIFIC MODULE VALIDATORS
# -------------------------------------------------------------

class EnergyValidator(DatasetValidator):
    def validate_specific(self):
        # 1. occupancy_percent between 0 and 100
        inv_occ = (~self.df["occupancy_percent"].between(0, 100)).sum()
        if inv_occ > 0:
            self.record_failure("occupancy_percent", "Values outside [0, 100]", int(inv_occ))

        # 2. energy_kwh > 0
        inv_energy = (self.df["energy_kwh"] <= 0).sum()
        if inv_energy > 0:
            self.record_failure("energy_kwh", "Values must be strictly > 0", int(inv_energy))

        # 3. valid zones
        inv_zones = (~self.df["zone_id"].isin(HOSPITAL_ZONES_TITLE)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {HOSPITAL_ZONES_TITLE}", int(inv_zones))

        # 4. operational_status
        inv_op = (~self.df["operational_status"].isin(FACILITY_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {FACILITY_OPERATIONAL_STATUS}", int(inv_op))

        # 5. energy_source
        valid_sources = {"GRID", "BACKUP_GENERATOR", "SOLAR"}
        inv_source = (~self.df["energy_source"].isin(valid_sources)).sum()
        if inv_source > 0:
            self.record_failure("energy_source", f"Invalid energy source. Allowed: {valid_sources}", int(inv_source))

        # 6. 15-minute frequency check
        if self.parsed_ts is not None:
            sample_zone = self.df[self.df["zone_id"] == "ICU"].copy()
            sample_zone["parsed_ts"] = self.parsed_ts.loc[sample_zone.index]
            diffs = sample_zone.sort_values("parsed_ts")["parsed_ts"].diff().dropna()
            if not (diffs == pd.Timedelta(minutes=15)).all():
                self.record_failure("timestamp", "Timestamps do not follow consistent 15-minute intervals for ICU zone", 1)


class WaterValidator(DatasetValidator):
    def validate_specific(self):
        # 1. water_litres > 0
        inv_water = (self.df["water_litres"] <= 0).sum()
        if inv_water > 0:
            self.record_failure("water_litres", "Values must be strictly > 0", int(inv_water))

        # 2. occupancy_percent between 0 and 100
        inv_occ = (~self.df["occupancy_percent"].between(0, 100)).sum()
        if inv_occ > 0:
            self.record_failure("occupancy_percent", "Values outside [0, 100]", int(inv_occ))

        # 3. valid hospital zones
        inv_zones = (~self.df["zone_id"].isin(HOSPITAL_ZONES_TITLE)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {HOSPITAL_ZONES_TITLE}", int(inv_zones))

        # 4. operational_status
        inv_op = (~self.df["operational_status"].isin(FACILITY_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {FACILITY_OPERATIONAL_STATUS}", int(inv_op))

        # 5. water_source
        valid_sources = {"MUNICIPAL", "BOREWELL", "RECYCLED"}
        inv_source = (~self.df["water_source"].isin(valid_sources)).sum()
        if inv_source > 0:
            self.record_failure("water_source", f"Invalid water source. Allowed: {valid_sources}", int(inv_source))

        # 6. 15-minute interval check
        if self.parsed_ts is not None:
            sample_zone = self.df[self.df["zone_id"] == "ICU"].copy()
            sample_zone["parsed_ts"] = self.parsed_ts.loc[sample_zone.index]
            diffs = sample_zone.sort_values("parsed_ts")["parsed_ts"].diff().dropna()
            if not (diffs == pd.Timedelta(minutes=15)).all():
                self.record_failure("timestamp", "Timestamps do not follow 15-minute intervals", 1)


class WasteValidator(DatasetValidator):
    def validate_specific(self):
        # 1. waste_kg >= 0
        inv_kg = (self.df["waste_kg"] < 0).sum()
        if inv_kg > 0:
            self.record_failure("waste_kg", "Values must be >= 0", int(inv_kg))

        # 2. bin_capacity_kg > 0
        inv_cap = (self.df["bin_capacity_kg"] <= 0).sum()
        if inv_cap > 0:
            self.record_failure("bin_capacity_kg", "Values must be strictly > 0", int(inv_cap))

        # 3. bin_fill_percent between 0 and 100
        inv_fill = (~self.df["bin_fill_percent"].between(0, 100)).sum()
        if inv_fill > 0:
            self.record_failure("bin_fill_percent", "Values outside [0, 100]", int(inv_fill))

        # 4. valid waste_category
        valid_cats = {"GENERAL", "ORGANIC", "RECYCLABLE"}
        inv_cat = (~self.df["waste_category"].isin(valid_cats)).sum()
        if inv_cat > 0:
            self.record_failure("waste_category", f"Invalid category. Allowed: {valid_cats}", int(inv_cat))

        # 5. occupancy_percent between 0 and 100
        inv_occ = (~self.df["occupancy_percent"].between(0, 100)).sum()
        if inv_occ > 0:
            self.record_failure("occupancy_percent", "Values outside [0, 100]", int(inv_occ))

        # 6. valid hospital zones
        inv_zones = (~self.df["zone_id"].isin(HOSPITAL_ZONES_TITLE)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {HOSPITAL_ZONES_TITLE}", int(inv_zones))

        # 7. operational_status
        inv_op = (~self.df["operational_status"].isin(FACILITY_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {FACILITY_OPERATIONAL_STATUS}", int(inv_op))


class EnvironmentValidator(DatasetValidator):
    def validate_specific(self):
        # 1. aqi >= 0
        inv_aqi = (self.df["aqi"] < 0).sum()
        if inv_aqi > 0:
            self.record_failure("aqi", "Values must be >= 0", int(inv_aqi))

        # 2. pm25 >= 0
        inv_pm25 = (self.df["pm25"] < 0).sum()
        if inv_pm25 > 0:
            self.record_failure("pm25", "Values must be >= 0", int(inv_pm25))

        # 3. pm10 >= 0
        inv_pm10 = (self.df["pm10"] < 0).sum()
        if inv_pm10 > 0:
            self.record_failure("pm10", "Values must be >= 0", int(inv_pm10))

        # 4. humidity_percent between 0 and 100
        inv_hum = (~self.df["humidity_percent"].between(0, 100)).sum()
        if inv_hum > 0:
            self.record_failure("humidity_percent", "Values outside [0, 100]", int(inv_hum))

        # 5. valid hospital zones
        inv_zones = (~self.df["zone_id"].isin(HOSPITAL_ZONES_TITLE)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {HOSPITAL_ZONES_TITLE}", int(inv_zones))

        # 6. operational_status
        inv_op = (~self.df["operational_status"].isin(FACILITY_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {FACILITY_OPERATIONAL_STATUS}", int(inv_op))


class EquipmentValidator(DatasetValidator):
    def validate_specific(self):
        # 1. utilization_percent between 0 and 100
        inv_util = (~self.df["utilization_percent"].between(0, 100)).sum()
        if inv_util > 0:
            self.record_failure("utilization_percent", "Values outside [0, 100]", int(inv_util))

        # 2. runtime_hours >= 0
        inv_run = (self.df["runtime_hours"] < 0).sum()
        if inv_run > 0:
            self.record_failure("runtime_hours", "Values must be >= 0", int(inv_run))

        # 3. valid equipment_type
        inv_types = (~self.df["equipment_type"].isin(EQUIPMENT_TYPES)).sum()
        if inv_types > 0:
            self.record_failure("equipment_type", f"Invalid equipment type. Allowed: {EQUIPMENT_TYPES}", int(inv_types))

        # 4. valid operational_status
        inv_op = (~self.df["operational_status"].isin(EQUIPMENT_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {EQUIPMENT_OPERATIONAL_STATUS}", int(inv_op))

        # 5. valid maintenance_status
        inv_maint = (~self.df["maintenance_status"].isin(EQUIPMENT_MAINTENANCE_STATUS)).sum()
        if inv_maint > 0:
            self.record_failure("maintenance_status", f"Invalid maintenance status. Allowed: {EQUIPMENT_MAINTENANCE_STATUS}", int(inv_maint))

        # 6. valid hospital zones
        inv_zones = (~self.df["zone_id"].isin(HOSPITAL_ZONES_TITLE)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {HOSPITAL_ZONES_TITLE}", int(inv_zones))

        # 7. Hourly interval check per equipment
        if self.parsed_ts is not None:
            sample_eq = self.df[self.df["equipment_id"] == "VENT-001"].copy()
            sample_eq["parsed_ts"] = self.parsed_ts.loc[sample_eq.index]
            diffs = sample_eq.sort_values("parsed_ts")["parsed_ts"].diff().dropna()
            if not (diffs == pd.Timedelta(hours=1)).all():
                self.record_failure("timestamp", "Timestamps do not follow 1-hour intervals for equipment VENT-001", 1)


class SafetyValidator(DatasetValidator):
    def validate_specific(self):
        # 1. valid hospital zones (safety uses uppercase)
        inv_zones = (~self.df["zone_id"].isin(HOSPITAL_ZONES_UPPER)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {HOSPITAL_ZONES_UPPER}", int(inv_zones))

        # 2. incident_type
        allowed_incidents = {
            "EQUIPMENT_INCIDENT", "OTHER", "SECURITY_INCIDENT",
            "MEDICAL_EMERGENCY", "FIRE_ALERT", "SLIP_FALL", "POWER_RELATED"
        }
        inv_inc = (~self.df["incident_type"].isin(allowed_incidents)).sum()
        if inv_inc > 0:
            self.record_failure("incident_type", f"Invalid incident types. Allowed: {allowed_incidents}", int(inv_inc))

        # 3. severity_level (LOW, MEDIUM, HIGH)
        valid_severity = {"LOW", "MEDIUM", "HIGH"}
        inv_sev = (~self.df["severity_level"].isin(valid_severity)).sum()
        if inv_sev > 0:
            self.record_failure("severity_level", f"Invalid severity. Allowed: {valid_severity}", int(inv_sev))

        # 4. response_time_min > 0
        inv_resp = (self.df["response_time_min"] <= 0).sum()
        if inv_resp > 0:
            self.record_failure("response_time_min", "Response time must be strictly > 0", int(inv_resp))

        # 5. occupancy_percent between 0 and 100
        inv_occ = (~self.df["occupancy_percent"].between(0, 100)).sum()
        if inv_occ > 0:
            self.record_failure("occupancy_percent", "Values outside [0, 100]", int(inv_occ))

        # 6. operational_status
        inv_op = (~self.df["operational_status"].isin(FACILITY_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {FACILITY_OPERATIONAL_STATUS}", int(inv_op))

        # Note: Safety is event-based, so 15-minute frequency check is intentionally omitted.


class TrafficValidator(DatasetValidator):
    def validate_specific(self):
        # 1. valid traffic zones
        inv_zones = (~self.df["zone_id"].isin(TRAFFIC_ZONES)).sum()
        if inv_zones > 0:
            self.record_failure("zone_id", f"Invalid zones. Allowed: {TRAFFIC_ZONES}", int(inv_zones))

        # 2. vehicle_count >= 0
        inv_vc = (self.df["vehicle_count"] < 0).sum()
        if inv_vc > 0:
            self.record_failure("vehicle_count", "Values must be >= 0", int(inv_vc))

        # 3. parking_occupancy_percent between 0 and 100
        inv_occ = (~self.df["parking_occupancy_percent"].between(0, 100)).sum()
        if inv_occ > 0:
            self.record_failure("parking_occupancy_percent", "Values outside [0, 100]", int(inv_occ))

        # 4. average_wait_time_min >= 0
        inv_wait = (self.df["average_wait_time_min"] < 0).sum()
        if inv_wait > 0:
            self.record_failure("average_wait_time_min", "Values must be >= 0", int(inv_wait))

        # 5. traffic_status (NORMAL, BUSY, CONGESTED)
        valid_ts = {"NORMAL", "BUSY", "CONGESTED"}
        inv_ts = (~self.df["traffic_status"].isin(valid_ts)).sum()
        if inv_ts > 0:
            self.record_failure("traffic_status", f"Invalid status. Allowed: {valid_ts}", int(inv_ts))

        # 6. operational_status
        inv_op = (~self.df["operational_status"].isin(FACILITY_OPERATIONAL_STATUS)).sum()
        if inv_op > 0:
            self.record_failure("operational_status", f"Invalid status. Allowed: {FACILITY_OPERATIONAL_STATUS}", int(inv_op))

        # 7. expected approximately 43,200 records
        if abs(len(self.df) - 43200) > 200:
            self.record_failure("ROWS", f"Expected ~43,200 records, got {len(self.df)}", 1)

        # 8. 15-minute frequency check
        if self.parsed_ts is not None:
            sample_zone = self.df[self.df["zone_id"] == "MAIN_GATE"].copy()
            sample_zone["parsed_ts"] = self.parsed_ts.loc[sample_zone.index]
            diffs = sample_zone.sort_values("parsed_ts")["parsed_ts"].diff().dropna()
            if not (diffs == pd.Timedelta(minutes=15)).all():
                self.record_failure("timestamp", "Timestamps do not follow 15-minute intervals for MAIN_GATE", 1)


# =============================================================
# MAIN VALIDATION ORCHESTRATOR
# =============================================================

def validate_all():
    print("=" * 70)
    print("AURA: CENTRAL FACILITY DATA VALIDATION SUITE (7 DATASETS)")
    print("Facility: HOSPITAL_001")
    print(f"Data Directory: {DATA_DIR}")
    print("=" * 70)

    validators = [
        EnergyValidator(
            "Energy", "energy.csv",
            ['timestamp', 'facility_id', 'zone_id', 'energy_kwh', 'occupancy_percent', 'temperature_c', 'operational_status', 'energy_source', 'source', 'anomaly_flag']
        ),
        WaterValidator(
            "Water", "water.csv",
            ['timestamp', 'facility_id', 'zone_id', 'water_litres', 'occupancy_percent', 'temperature_c', 'operational_status', 'water_source', 'source', 'anomaly_flag']
        ),
        WasteValidator(
            "Waste", "waste.csv",
            ['timestamp', 'facility_id', 'zone_id', 'waste_kg', 'bin_capacity_kg', 'bin_fill_percent', 'waste_category', 'occupancy_percent', 'operational_status', 'source', 'anomaly_flag']
        ),
        EnvironmentValidator(
            "Environment", "environment.csv",
            ['timestamp', 'facility_id', 'zone_id', 'aqi', 'pm25', 'pm10', 'temperature_c', 'humidity_percent', 'wind_speed_kmh', 'operational_status', 'source', 'anomaly_flag']
        ),
        EquipmentValidator(
            "Equipment", "equipment.csv",
            ['timestamp', 'facility_id', 'equipment_id', 'equipment_type', 'zone_id', 'utilization_percent', 'runtime_hours', 'operational_status', 'maintenance_status', 'source', 'anomaly_flag']
        ),
        SafetyValidator(
            "Safety", "safety.csv",
            ['timestamp', 'facility_id', 'zone_id', 'incident_type', 'severity_level', 'response_time_min', 'occupancy_percent', 'operational_status', 'source', 'anomaly_flag']
        ),
        TrafficValidator(
            "Traffic", "traffic.csv",
            ['timestamp', 'facility_id', 'zone_id', 'vehicle_count', 'parking_occupancy_percent', 'average_wait_time_min', 'traffic_status', 'operational_status', 'source', 'anomaly_flag']
        ),
    ]

    all_passed = True
    passed_count = 0

    for validator in validators:
        passed = validator.run()
        validator.print_report()
        if passed:
            passed_count += 1
        else:
            all_passed = False

    print("\n" + "=" * 70)
    print("FINAL SUMMARY REPORT")
    print("=" * 70)
    print(f"Total Datasets Evaluated: {len(validators)}")
    print(f"Passed:                   {passed_count}/{len(validators)}")
    print(f"Failed:                   {len(validators) - passed_count}/{len(validators)}")

    if all_passed:
        print("\n>>> OVERALL STATUS: ALL 7 DATASETS PASSED VALIDATION! READY FOR EDA & ML. <<<")
        print("=" * 70)
        return 0
    else:
        print("\n>>> OVERALL STATUS: VALIDATION FAILED! Please inspect issues above. <<<")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    exit_code = validate_all()
    sys.exit(exit_code)
