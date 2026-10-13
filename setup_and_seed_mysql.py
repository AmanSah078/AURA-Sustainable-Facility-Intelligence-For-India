"""
AURA MySQL Schema Setup & Sample Seeding Script
Executes DDL, seeds representative samples, and runs verification queries.
"""

import sys
from pathlib import Path
import pandas as pd
import pymysql

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ENERGY_CSV = DATA_DIR / "energy.csv"
ANOMALY_CSV = DATA_DIR / "energy_anomaly_results.csv"
FORECAST_CSV = DATA_DIR / "energy_forecast_results.csv"

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "AURA@MySQL2026",
    "charset": "utf8mb4"
}

def main():
    print("=" * 75)
    print("AURA MYSQL SCHEMA INITIALIZATION & VERIFICATION")
    print("=" * 75)

    # 1. Connect to MySQL server and check database existence
    print("\n1. Connecting to MySQL server...")
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("SHOW DATABASES LIKE 'aura_db'")
    existing_db = cursor.fetchone()
    if existing_db:
        print("   Database 'aura_db' already exists. Using existing database (NO DROP DATABASE).")
    else:
        print("   Database 'aura_db' does not exist. Creating 'aura_db'...")
        cursor.execute("CREATE DATABASE IF NOT EXISTS aura_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("   [OK] Database 'aura_db' created successfully.")

    cursor.execute("USE aura_db")

    # 2. Create tables
    print("\n2. Creating tables (facilities, energy_readings, energy_intelligence)...")
    
    # Table 1: facilities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facilities (
        facility_id VARCHAR(32) NOT NULL,
        name VARCHAR(128) NOT NULL,
        facility_type VARCHAR(32) NOT NULL DEFAULT 'HOSPITAL',
        location VARCHAR(255) NULL,
        total_floors INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (facility_id)
    ) ENGINE=InnoDB;
    """)
    print("   [OK] Table 'facilities' verified.")

    # Table 2: energy_readings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS energy_readings (
        id BIGINT AUTO_INCREMENT NOT NULL,
        facility_id VARCHAR(32) NOT NULL,
        zone_id VARCHAR(32) NOT NULL,
        timestamp DATETIME NOT NULL,
        energy_kwh DECIMAL(10, 2) NOT NULL,
        occupancy_percent DECIMAL(5, 2) DEFAULT 0.00,
        temperature_c DECIMAL(5, 2) NULL,
        operational_status VARCHAR(32) DEFAULT 'NORMAL',
        energy_source VARCHAR(32) DEFAULT 'GRID',
        source VARCHAR(32) DEFAULT 'synthetic',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        CONSTRAINT fk_readings_facility FOREIGN KEY (facility_id)
            REFERENCES facilities (facility_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
        INDEX idx_energy_zone_time (facility_id, zone_id, timestamp DESC),
        INDEX idx_energy_timestamp (timestamp)
    ) ENGINE=InnoDB;
    """)
    print("   [OK] Table 'energy_readings' verified.")

    # Table 3: energy_intelligence
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS energy_intelligence (
        id BIGINT AUTO_INCREMENT NOT NULL,
        facility_id VARCHAR(32) NOT NULL,
        zone_id VARCHAR(32) NOT NULL,
        timestamp DATETIME NOT NULL,
        current_energy_kwh DECIMAL(10, 2) NOT NULL,
        anomaly_detected BOOLEAN NOT NULL,
        anomaly_score DECIMAL(6, 3) NOT NULL,
        forecast_energy_kwh DECIMAL(10, 2) NOT NULL,
        forecast_horizon VARCHAR(32) DEFAULT 'next_1_hour',
        recommendation TEXT NOT NULL,
        source VARCHAR(32) DEFAULT 'synthetic',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        CONSTRAINT fk_intel_facility FOREIGN KEY (facility_id)
            REFERENCES facilities (facility_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
        INDEX idx_intel_zone_time (facility_id, zone_id, timestamp DESC),
        INDEX idx_intel_anomaly (facility_id, anomaly_detected, timestamp DESC)
    ) ENGINE=InnoDB;
    """)
    print("   [OK] Table 'energy_intelligence' verified.")

    conn.commit()

    # 3. Seed facilities table
    print("\n3. Seeding 'facilities' table...")
    cursor.execute("SELECT COUNT(*) FROM facilities WHERE facility_id = 'H001'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO facilities (facility_id, name, facility_type, location, total_floors)
        VALUES ('H001', 'Government Hospital', 'HOSPITAL', 'Bhubaneswar', 5)
        """)
        conn.commit()
        print("   [OK] Inserted primary facility 'H001' (Government Hospital, Bhubaneswar).")
    else:
        print("   [OK] Facility 'H001' already present.")

    # 4. Seed energy_readings (sample 300 records across all 5 zones)
    print("\n4. Seeding representative sample for 'energy_readings' (300 records)...")
    cursor.execute("SELECT COUNT(*) FROM energy_readings")
    current_readings_count = cursor.fetchone()[0]
    if current_readings_count == 0:
        df_energy = pd.read_csv(ENERGY_CSV)
        # Take 60 sample records from each of the 5 hospital zones
        sample_records = []
        for zone in ['Admin', 'Emergency', 'General_Ward', 'ICU', 'OPD']:
            sub = df_energy[df_energy['zone_id'] == zone].head(60)
            sample_records.append(sub)
        sample_df = pd.concat(sample_records, ignore_index=True)

        insert_sql = """
        INSERT INTO energy_readings 
        (facility_id, zone_id, timestamp, energy_kwh, occupancy_percent, temperature_c, operational_status, energy_source, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        rows_to_insert = []
        for _, row in sample_df.iterrows():
            # Format timestamp from DD-MM-YYYY HH:MM to YYYY-MM-DD HH:MM:SS
            dt = pd.to_datetime(row['timestamp'], dayfirst=True)
            formatted_ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            rows_to_insert.append((
                str(row['facility_id']),
                str(row['zone_id']),
                formatted_ts,
                float(row['energy_kwh']),
                float(row['occupancy_percent']),
                float(row['temperature_c']) if not pd.isna(row['temperature_c']) else None,
                str(row['operational_status']),
                str(row['energy_source']),
                'synthetic'
            ))

        cursor.executemany(insert_sql, rows_to_insert)
        conn.commit()
        print(f"   [OK] Inserted {len(rows_to_insert)} representative energy readings.")
    else:
        print(f"   [OK] 'energy_readings' already contains {current_readings_count} records.")

    # 5. Seed energy_intelligence (sample 250 records: normal + actual anomalies)
    print("\n5. Seeding representative sample for 'energy_intelligence' (250 records)...")
    cursor.execute("SELECT COUNT(*) FROM energy_intelligence")
    current_intel_count = cursor.fetchone()[0]
    if current_intel_count == 0:
        df_anom = pd.read_csv(ANOMALY_CSV)
        df_fcst = pd.read_csv(FORECAST_CSV)

        # Merge with forecast if available on timestamp and zone_id
        df_merged = df_anom.merge(
            df_fcst[['timestamp', 'zone_id', 'predicted_energy_kwh']],
            on=['timestamp', 'zone_id'],
            how='left'
        )
        df_merged['forecast_energy_kwh'] = df_merged['predicted_energy_kwh'].fillna(df_merged['energy_kwh'])

        # Include all 5 zones: 40 normal records + 10 anomaly records per zone
        intel_samples = []
        for zone in ['Admin', 'Emergency', 'General_Ward', 'ICU', 'OPD']:
            normal_sample = df_merged[(df_merged['zone_id'] == zone) & (df_merged['predicted_anomaly'] == 0)].head(40)
            anom_sample = df_merged[(df_merged['zone_id'] == zone) & (df_merged['predicted_anomaly'] == 1)].head(10)
            intel_samples.append(normal_sample)
            intel_samples.append(anom_sample)
        sample_intel_df = pd.concat(intel_samples, ignore_index=True)

        insert_intel_sql = """
        INSERT INTO energy_intelligence 
        (facility_id, zone_id, timestamp, current_energy_kwh, anomaly_detected, anomaly_score, forecast_energy_kwh, forecast_horizon, recommendation, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        intel_rows = []
        for _, row in sample_intel_df.iterrows():
            dt = pd.to_datetime(row['timestamp'], dayfirst=True)
            formatted_ts = dt.strftime('%Y-%m-%d %H:%M:%S')
            intel_rows.append((
                str(row['facility_id']),
                str(row['zone_id']),
                formatted_ts,
                float(row['energy_kwh']),
                bool(row['predicted_anomaly'] == 1),
                float(row['anomaly_score']),
                float(row['forecast_energy_kwh']),
                'next_1_hour',
                str(row['recommendation']),
                'synthetic'
            ))

        cursor.executemany(insert_intel_sql, intel_rows)
        conn.commit()
        print(f"   [OK] Inserted {len(intel_rows)} representative intelligence records (including anomalies).")
    else:
        print(f"   [OK] 'energy_intelligence' already contains {current_intel_count} records.")

    # 6. Verification queries
    print("\n" + "=" * 75)
    print("MYSQL DATABASE VERIFICATION QUERY RESULTS")
    print("=" * 75)

    # Query 1: Total facilities
    cursor.execute("SELECT facility_id, name, facility_type, location, total_floors FROM facilities")
    facs = cursor.fetchall()
    print(f"\n[QUERY 1] Total Facilities: {len(facs)}")
    for f in facs:
        print(f"   ID: {f[0]} | Name: {f[1]} | Type: {f[2]} | Location: {f[3]} | Floors: {f[4]}")

    # Query 2: Total energy readings by zone
    cursor.execute("SELECT zone_id, COUNT(*), MIN(energy_kwh), MAX(energy_kwh), AVG(energy_kwh) FROM energy_readings GROUP BY zone_id")
    readings_by_zone = cursor.fetchall()
    print(f"\n[QUERY 2] Energy Readings Distribution across Zones:")
    for r in readings_by_zone:
        print(f"   Zone: {r[0]:<15} | Count: {r[1]:3d} | Min: {r[2]:6.2f} kWh | Max: {r[3]:6.2f} kWh | Avg: {r[4]:6.2f} kWh")

    # Query 3: Latest Energy reading
    cursor.execute("SELECT facility_id, zone_id, timestamp, energy_kwh, occupancy_percent, operational_status, source FROM energy_readings ORDER BY timestamp DESC, id DESC LIMIT 1")
    latest_reading = cursor.fetchone()
    print(f"\n[QUERY 3] Latest Energy Reading in Database:")
    print(f"   Facility: {latest_reading[0]} | Zone: {latest_reading[1]} | Time: {latest_reading[2]} | Load: {latest_reading[3]} kWh | Status: {latest_reading[5]} | Source: {latest_reading[6]}")

    # Query 4: Recent readings for Emergency zone
    cursor.execute("SELECT timestamp, energy_kwh, occupancy_percent, operational_status FROM energy_readings WHERE zone_id = 'Emergency' ORDER BY timestamp DESC LIMIT 3")
    em_readings = cursor.fetchall()
    print(f"\n[QUERY 4] Recent Readings for Emergency Zone:")
    for er in em_readings:
        print(f"   Time: {er[0]} | Load: {er[1]:6.2f} kWh | Occupancy: {er[2]:.1f}% | Status: {er[3]}")

    # Query 5: Intelligence distribution & latest anomaly
    cursor.execute("""
    SELECT anomaly_detected, COUNT(*) FROM energy_intelligence GROUP BY anomaly_detected
    """)
    intel_counts = cursor.fetchall()
    print(f"\n[QUERY 5] Intelligence Records Breakdown:")
    for ic in intel_counts:
        status_label = "[ANOMALY]" if ic[0] else "[NORMAL]"
        print(f"   {status_label}: {ic[1]} records")

    cursor.execute("""
    SELECT zone_id, timestamp, current_energy_kwh, anomaly_score, recommendation 
    FROM energy_intelligence 
    WHERE anomaly_detected = TRUE 
    ORDER BY timestamp DESC 
    LIMIT 1
    """)
    latest_anomaly = cursor.fetchone()
    if latest_anomaly:
        print(f"\n[QUERY 6] Sample Detected Anomaly in MySQL:")
        print(f"   Zone: {latest_anomaly[0]} | Time: {latest_anomaly[1]} | Load: {latest_anomaly[2]} kWh | Score: {latest_anomaly[3]}")
        print(f"   Recommendation: \"{latest_anomaly[4]}\"")

    # Query 7: Index verification
    print(f"\n[QUERY 7] Index Verification on Tables:")
    for tbl in ['facilities', 'energy_readings', 'energy_intelligence']:
        cursor.execute(f"SHOW INDEX FROM {tbl}")
        indexes = cursor.fetchall()
        idx_names = sorted(list(set(idx[2] for idx in indexes)))
        print(f"   Table '{tbl}': Indexes = {idx_names}")

    conn.close()
    print("\n" + "=" * 75)
    print("ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY.")
    print("=" * 75)


if __name__ == "__main__":
    main()
