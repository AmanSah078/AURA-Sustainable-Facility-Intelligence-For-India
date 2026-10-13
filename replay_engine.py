"""
AURA — AI-Powered Sustainable Facility Intelligence Platform
Module: Dataset Replay & Synthetic Sensor Simulation Engine

Purpose:
  Simulates a real IoT smart meter sending 15-minute telemetry packets
  to Spring Boot's ingestion API (POST /api/v1/energy/ingest).

Usage:
  python replay_engine.py --speed 3.0 --zone Emergency
"""

import csv
import json
import time
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Paths & Defaults
PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_PATH = PROJECT_ROOT / "data" / "energy.csv"
DEFAULT_INGEST_URL = "http://localhost:8080/api/v1/energy/ingest"

# Default Deterministic Window: Normal -> Anomaly Spike -> Normal Recovery
DEFAULT_ZONE = "Emergency"
DEFAULT_DATE = "06-01-2026"
DEFAULT_START_TIME = "14:00"
DEFAULT_END_TIME = "17:00"


def load_window_records(csv_path: Path, zone: str, date_str: str, start_time: str, end_time: str):
    """
    Reads the validated dataset and extracts the deterministic demo window.
    Does NOT modify the original CSV file.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {csv_path}")

    records = []
    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_zone = row.get("zone_id", "").strip()
            row_ts = row.get("timestamp", "").strip()

            if row_zone.lower() == zone.lower() and row_ts.startswith(date_str):
                time_part = row_ts.split(" ")[1] if " " in row_ts else ""
                if start_time <= time_part <= end_time:
                    records.append({
                        "facility_id": row.get("facility_id", "H001"),
                        "zone_id": row.get("zone_id", zone),
                        "timestamp": row_ts,
                        "energy_kwh": float(row.get("energy_kwh", 0.0)),
                        "occupancy_percent": float(row.get("occupancy_percent", 0.0)) if row.get("occupancy_percent") else None,
                        "temperature_c": float(row.get("temperature_c", 0.0)) if row.get("temperature_c") else None,
                        "operational_status": row.get("operational_status", "NORMAL"),
                        "energy_source": row.get("energy_source", "GRID"),
                        "source": "replay_sensor",
                        "anomaly_flag": row.get("anomaly_flag", "0")
                    })

    # Sort chronologically
    records.sort(key=lambda r: r["timestamp"])
    return records


def post_reading(ingest_url: str, record: dict) -> tuple[int, dict]:
    """
    Sends reading packet through Spring Boot HTTP Ingestion API.
    Does NOT write directly to MySQL.
    """
    payload = {
        "facility_id": record["facility_id"],
        "zone_id": record["zone_id"],
        "timestamp": record["timestamp"],
        "energy_kwh": record["energy_kwh"],
        "occupancy_percent": record.get("occupancy_percent"),
        "temperature_c": record.get("temperature_c"),
        "operational_status": record.get("operational_status", "NORMAL"),
        "energy_source": record.get("energy_source", "GRID"),
        "source": "replay_sensor"
    }

    req = urllib.request.Request(
        ingest_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            return response.status, res_body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return e.code, {"error": err_body}
    except Exception as e:
        return 0, {"error": str(e)}


def run_replay(speed: float, zone: str, date_str: str, start_time: str, end_time: str, ingest_url: str):
    """
    Main replay loop simulating sensor telemetry stream.
    """
    print("=" * 80)
    print("AURA — SYNTHETIC SENSOR REPLAY ENGINE")
    print("=" * 80)
    print(f"Target Ingestion URL : {ingest_url}")
    print(f"Monitored Ward       : {zone}")
    print(f"Replay Window        : {date_str} ({start_time} to {end_time})")
    print(f"Replay Interval      : {speed:.1f} seconds / packet")
    print("=" * 80)

    try:
        records = load_window_records(DATASET_PATH, zone, date_str, start_time, end_time)
    except Exception as e:
        print(f"[ERROR] Failed to load replay records: {e}")
        return

    if not records:
        print("[WARNING] No records matched the specified window.")
        return

    print(f"Loaded {len(records)} chronological records from validated dataset.")
    print("Starting sensor replay stream...\n")

    for idx, rec in enumerate(records, start=1):
        ts = rec["timestamp"]
        kwh = rec["energy_kwh"]
        is_spike = kwh > 250.0 or rec.get("anomaly_flag") == "1"

        status_tag = ">>> ANOMALY SPIKE <<<" if is_spike else "NORMAL LOAD"

        status_code, res = post_reading(ingest_url, rec)

        if status_code in (200, 201):
            print(f"[{idx:02d}/{len(records):02d}] {ts} | Load: {kwh:6.2f} kWh | {status_tag:<22} -> [HTTP {status_code}] Saved to MySQL (ID: {res.get('id')})")
        else:
            print(f"[{idx:02d}/{len(records):02d}] {ts} | Load: {kwh:6.2f} kWh | FAILED -> [HTTP {status_code}] {res.get('error')}")

        if idx < len(records):
            time.sleep(speed)

    print("\n" + "=" * 80)
    print("REPLAY STREAM COMPLETED SUCCESSFULLY (All records processed).")
    print("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA Synthetic Sensor Replay Engine")
    parser.add_argument("--speed", type=float, default=3.0, help="Seconds between telemetry packets (default: 3.0)")
    parser.add_argument("--zone", type=str, default=DEFAULT_ZONE, help="Hospital Ward (default: Emergency)")
    parser.add_argument("--date", type=str, default=DEFAULT_DATE, help="Dataset Date (default: 06-01-2026)")
    parser.add_argument("--start-time", type=str, default=DEFAULT_START_TIME, help="Start time (default: 14:00)")
    parser.add_argument("--end-time", type=str, default=DEFAULT_END_TIME, help="End time (default: 17:00)")
    parser.add_argument("--url", type=str, default=DEFAULT_INGEST_URL, help="Spring Boot Ingestion URL")

    args = parser.parse_args()
    run_replay(
        speed=args.speed,
        zone=args.zone,
        date_str=args.date,
        start_time=args.start_time,
        end_time=args.end_time,
        ingest_url=args.url
    )
