"""
AURA — AI-Powered Sustainable Facility Intelligence Platform
Module: Energy Anomaly Intelligence & Decision Support

Architecture Flow:
  1. Energy Data Ingestion (Telemetry: timestamp, zone, energy_kwh, occupancy, temp)
  2. Anomaly Detection (Dynamic Zone+Hour Baseline Z-Score & Residual Analysis)
  3. Zone Localization ([LOCATION] Pinpoint exact hospital block)
  4. Natural Language Explanation ([ANALYSIS] Simple Hinglish + Plain English root cause)
  5. Actionable Recommendation ([RECOMMENDATION] Simple steps anyone can understand and execute)
  6. Facility Team Action ([FACILITY ACTION] Ticket tracking: review, verify, resolve)
"""

from pathlib import Path
import pandas as pd
import numpy as np

# Hospital zone contextual knowledge base
ZONE_PROFILES = {
    "Admin": {
        "full_name": "Administration & Executive Wing",
        "primary_loads": "Office lighting, workstations, split ACs, conference room chillers",
        "normal_operating_hours": "08:00 to 18:00 (Mon - Fri)",
        "expected_offpeak_kwh": 10.0,
        "contact_team": "Facility Electrician & Office Admin Head"
    },
    "OPD": {
        "full_name": "Outpatient Consultation Clinics",
        "primary_loads": "Consultation room lighting, diagnostic screens, clinic ACs, waiting area fans",
        "normal_operating_hours": "08:30 to 17:00 (Mon - Sat)",
        "expected_offpeak_kwh": 18.0,
        "contact_team": "Clinical Support & HVAC Maintenance"
    },
    "General_Ward": {
        "full_name": "General Inpatient Wards (Wings A & B)",
        "primary_loads": "Bed lighting, patient monitoring displays, water heaters, ventilation fans",
        "normal_operating_hours": "24x7 continuous (Quiet hours 22:00 to 06:00)",
        "expected_offpeak_kwh": 70.0,
        "contact_team": "Duty Nurse In-charge & Ward Maintenance Staff"
    },
    "Emergency": {
        "full_name": "Emergency & Trauma Resuscitation Unit",
        "primary_loads": "Trauma lights, portable ultrasound, life monitors, defibrillators, crash carts",
        "normal_operating_hours": "24x7 emergency readiness",
        "expected_offpeak_kwh": 150.0,
        "contact_team": "Emergency Duty Officer & Biomedical Engineering"
    },
    "ICU": {
        "full_name": "Intensive Care Unit (Critical Care)",
        "primary_loads": "Ventilators, continuous vitals telemetry, HEPA positive-pressure HVAC, blood warmers",
        "normal_operating_hours": "24x7 mission-critical",
        "expected_offpeak_kwh": 190.0,
        "contact_team": "Chief Biomedical Engineer & Electrical Superintendant"
    }
}


class EnergyAnomalyIntelligenceEngine:
    """
    End-to-End AURA Energy Intelligence Engine.
    Detects anomalies, localizes zones, generates plain-language explanations,
    and produces actionable facility maintenance recommendations.
    """
    def __init__(self, z_threshold: float = 3.0, min_deviation_pct: float = 30.0):
        self.z_threshold = z_threshold
        self.min_deviation_pct = min_deviation_pct
        self.baselines = None

    def fit_baselines(self, df: pd.DataFrame):
        """
        Learn zone-specific hourly baseline profiles (Mean, Std, Median)
        from historical telemetry to establish normal facility rhythm.
        """
        # Group by zone and hour to learn diurnal baseline patterns
        self.baselines = df.groupby(["zone_id", "hour"])["energy_kwh"].agg(
            baseline_mean="mean",
            baseline_std="std",
            baseline_median="median"
        ).reset_index()
        return self

    def detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Evaluate energy telemetry against zone baselines.
        Flags anomalous records and calculates deviation metrics.
        """
        if self.baselines is None:
            self.fit_baselines(df)

        scored = df.merge(self.baselines, on=["zone_id", "hour"], how="left")
        
        # Calculate dynamic Z-Score and percentage deviation from baseline
        scored["z_score"] = (scored["energy_kwh"] - scored["baseline_mean"]) / scored["baseline_std"].replace(0, 1.0)
        scored["deviation_pct"] = ((scored["energy_kwh"] - scored["baseline_mean"]) / scored["baseline_mean"]) * 100.0

        # Anomaly condition: Significant statistical deviation AND practical percentage surge
        scored["is_detected_anomaly"] = (
            (scored["z_score"] >= self.z_threshold) & 
            (scored["deviation_pct"] >= self.min_deviation_pct)
        )

        # Severity categorization
        def assign_severity(row):
            if not row["is_detected_anomaly"]:
                return "NORMAL"
            if row["z_score"] >= 5.0 or row["deviation_pct"] >= 100.0:
                return "CRITICAL"
            elif row["z_score"] >= 3.5 or row["deviation_pct"] >= 50.0:
                return "HIGH"
            else:
                return "MEDIUM"

        scored["severity"] = scored.apply(assign_severity, axis=1)
        return scored

    def generate_explanation(self, row: pd.Series) -> str:
        """
        Explain WHAT was observed in simple Hinglish + plain English.
        Zero academic jargon — easily readable by doctors, electricians, and facility heads.
        """
        zone = row["zone_id"]
        actual_kwh = row["energy_kwh"]
        expected_kwh = row["baseline_mean"]
        dev_pct = row["deviation_pct"]
        hour = int(row["hour"])
        occupancy = row["occupancy_percent"]
        op_status = row.get("operational_status", "NORMAL")

        time_str = f"{hour:02d}:00"
        profile = ZONE_PROFILES.get(zone, {})
        zone_title = profile.get("full_name", zone)

        # Contextual explanation logic
        if zone in ["Admin", "OPD"] and (hour >= 20 or hour < 6):
            return (
                f"[ALERT] [Off-Hours Spike] {zone_title} mein raat ke {time_str} baje energy consumption "
                f"achanak {actual_kwh:.1f} kWh ho gaya, jabki normal baseline sirf {expected_kwh:.1f} kWh hota hai "
                f"(+{dev_pct:.0f}% extra power). Is time occupancy sirf {occupancy:.0f}% hai (area lagbhag khali hai), "
                f"isliye itni zyada power draw hona abnormal hai."
            )
        elif zone == "ICU":
            return (
                f"[ALERT] [Critical Care High Load] ICU Unit mein {time_str} baje massive electrical surge detect hua: "
                f"{actual_kwh:.1f} kWh consume ho raha hai (Expected: {expected_kwh:.1f} kWh, deviation: +{dev_pct:.0f}%). "
                f"ICU mein life-support systems lage hain. Current occupancy {occupancy:.0f}% aur facility status '{op_status}' hai. "
                f"High-draw heating/cooling ya medical compressors continuous overload par chal rahe ho sakte hain."
            )
        elif zone == "Emergency":
            return (
                f"[ALERT] [Emergency Trauma Surge] Emergency block mein {time_str} baje consumption {actual_kwh:.1f} kWh tak pahunch gaya "
                f"(Baseline: {expected_kwh:.1f} kWh, deviation: +{dev_pct:.0f}%). Occupancy level {occupancy:.0f}% hai. "
                f"Trauma diagnostic devices aur portable imaging machinery ke continuous usage se power spike aaya hai."
            )
        else:
            return (
                f"[ALERT] [Unusual Load Surge] {zone_title} mein {time_str} baje energy consumption {actual_kwh:.1f} kWh observe hua, "
                f"jo normal expected baseline ({expected_kwh:.1f} kWh) se +{dev_pct:.0f}% zyada hai. "
                f"Occupancy {occupancy:.0f}% ke hisaab se power consumption out of range hai."
            )

    def generate_recommendation(self, row: pd.Series) -> str:
        """
        Generate actionable recommendations that anyone can understand and execute.
        Provides direct, concrete checklist steps.
        """
        zone = row["zone_id"]
        hour = int(row["hour"])
        profile = ZONE_PROFILES.get(zone, {})
        team = profile.get("contact_team", "Duty Facility Staff")

        if zone == "Admin":
            if hour >= 19 or hour < 7:
                return (
                    f"[RECOMMENDATION] Step 1: Night guard ya duty electrician turant Admin 2nd floor aur conference room bhejein.\n"
                    f"[RECOMMENDATION] Step 2: Check karein ki meeting room ke central AC chillers aur computer lab strips galti se ON toh nahi reh gaye.\n"
                    f"[RECOMMENDATION] Step 3: Unoccupied cabins ke switches aur decorative hallway lighting ko OFF karein."
                )
            else:
                return (
                    f"[RECOMMENDATION] Step 1: Admin block ke HVAC thermostat setting ko 24°C par set karein.\n"
                    f"[RECOMMENDATION] Step 2: Unused meeting rooms ke split ACs band karein aur electrical sub-panel A-1 check karein."
                )
        elif zone == "OPD":
            return (
                f"[RECOMMENDATION] Step 1: Outpatient clinic ke consultation blocks 1, 2, aur 3 inspect karein.\n"
                f"[RECOMMENDATION] Step 2: Check karein ki ultrasound warming tables ya heavy diagnostic screens standby mode ke bajay full ON toh nahi hain.\n"
                f"[RECOMMENDATION] Step 3: OPD waiting corridor ke exhaust fans aur AC units ko off-peak mode par dalein."
            )
        elif zone == "ICU":
            return (
                f"[RECOMMENDATION] Step 1: Biomedical engineering team ({team}) ko turant notify karein.\n"
                f"[RECOMMENDATION] Step 2: ICU Main Distribution Panel (MDP-ICU) par phase balance aur voltage sag check karein.\n"
                f"[RECOMMENDATION] Step 3: Positive-pressure HVAC chiller unit aur backup UPS load balance verify karein taaki equipment trip na ho."
            )
        elif zone == "Emergency":
            return (
                f"[RECOMMENDATION] Step 1: Emergency duty technician trauma bay ke secondary portable imaging machines ka load check karein.\n"
                f"[RECOMMENDATION] Step 2: Ensure karein ki Dedicated Emergency Diesel Generator (DG) standby mode mein ready hai agar grid voltage drop ho.\n"
                f"[RECOMMENDATION] Step 3: Non-critical triage rooms ki excess lighting aur secondary cooling ko optimize karein."
            )
        else: # General_Ward
            return (
                f"[RECOMMENDATION] Step 1: Ward in-charge nurse station aur patient wings ke water geyser timer circuits inspect karein.\n"
                f"[RECOMMENDATION] Step 2: Check karein ki pantry microwave ya food warming cabinets continuous loop par toh nahi chal rahe.\n"
                f"[RECOMMENDATION] Step 3: Hallway lighting ko 50% power-saving night mode par switch karein."
            )

    def create_facility_ticket(self, row: pd.Series, ticket_id: str) -> dict:
        """
        Creates a structured Facility Action Ticket for the maintenance team.
        """
        zone = row["zone_id"]
        profile = ZONE_PROFILES.get(zone, {})
        
        return {
            "ticket_id": ticket_id,
            "timestamp": str(row["timestamp"]),
            "zone_id": zone,
            "zone_name": profile.get("full_name", zone),
            "severity": row["severity"],
            "metrics": {
                "observed_energy_kwh": round(float(row["energy_kwh"]), 2),
                "expected_baseline_kwh": round(float(row["baseline_mean"]), 2),
                "excess_energy_kwh": round(float(row["energy_kwh"] - row["baseline_mean"]), 2),
                "deviation_percentage": f"+{row['deviation_pct']:.1f}%",
                "room_occupancy": f"{row['occupancy_percent']:.1f}%"
            },
            "root_cause_explanation": self.generate_explanation(row),
            "action_recommendation": self.generate_recommendation(row),
            "assigned_team": profile.get("contact_team", "General Maintenance"),
            "status": "PENDING_FACILITY_REVIEW",
            "action_taken": None,
            "verified_by": None
        }


# Quick demonstration runner
if __name__ == "__main__":
    data_path = Path(__file__).resolve().parent.parent / "data" / "processed_energy_features.csv"
    if not data_path.exists():
        data_path = Path(__file__).resolve().parent.parent / "data" / "energy.csv"

    print("Loading data from:", data_path)
    df = pd.read_csv(data_path)
    if "hour" not in df.columns:
        df["datetime"] = pd.to_datetime(df["timestamp"], dayfirst=True)
        df["hour"] = df["datetime"].dt.hour

    engine = EnergyAnomalyIntelligenceEngine(z_threshold=3.0, min_deviation_pct=30.0)
    scored_df = engine.detect_anomalies(df)

    anomalies = scored_df[scored_df["is_detected_anomaly"]].copy()
    print(f"\n[OK] Total Anomalies Detected: {len(anomalies):,}")
    print("\nSeverity Breakdown:\n", anomalies["severity"].value_counts())
    print("\nZone Breakdown:\n", anomalies["zone_id"].value_counts())

    # Generate 1 sample ticket from Admin and 1 from ICU
    print("\n" + "=" * 75)
    print("SAMPLE FACILITY ACTION TICKETS GENERATED BY AURA")
    print("=" * 75)

    sample_admin = anomalies[anomalies["zone_id"] == "Admin"].iloc[0]
    ticket_1 = engine.create_facility_ticket(sample_admin, "AURA-ENG-2026-001")
    
    sample_icu = anomalies[anomalies["zone_id"] == "ICU"].iloc[0]
    ticket_2 = engine.create_facility_ticket(sample_icu, "AURA-ENG-2026-002")

    for t in [ticket_1, ticket_2]:
        print(f"\n[TICKET: {t['ticket_id']}] | SEVERITY: {t['severity']}")
        print(f"Timestamp:   {t['timestamp']}")
        print(f"[LOCATION] Zone:     {t['zone_name']} ({t['zone_id']})")
        print(f"[METRICS] Metrics:  Observed={t['metrics']['observed_energy_kwh']} kWh vs Baseline={t['metrics']['expected_baseline_kwh']} kWh ({t['metrics']['deviation_percentage']})")
        print(f"\n[ANALYSIS] Observation & Root Cause:")
        print(f"   {t['root_cause_explanation']}")
        print(f"\n[RECOMMENDATION] Actionable Recommendation:")
        for line in t['action_recommendation'].split('\n'):
            print(f"   {line}")
        print(f"\n[FACILITY ACTION] Facility Review Status:")
        print(f"   Assigned: {t['assigned_team']}")
        print(f"   Status:   {t['status']}")
        print("-" * 75)
