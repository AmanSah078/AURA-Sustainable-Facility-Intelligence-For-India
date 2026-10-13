# AURA — MySQL Database Design (Energy Intelligence Phase)
**Platform:** AURA — AI-Powered Sustainable Facility Intelligence Platform  
**Target Facility:** HOSPITAL_001 (Government Hospital, Multi-Facility Ready)  
**Module:** Core Facilities & Energy Intelligence  
**Document Status:** Architecture Design & Engineering Specification  

---

## 1. Purpose

The purpose of this document is to design a clean, normalized, and high-performance **MySQL Relational Database Schema** for AURA. 

Currently, AURA's data and machine learning prototypes operate directly on flat CSV files (`data/energy.csv`, `data/processed_energy_features.csv`). For an enterprise-grade hackathon prototype and production system, AURA requires persistent, structured storage capable of handling concurrent telemetry ingestion, fast time-series analytical queries, and seamless integration with the **Spring Boot** backend and **React** frontend.

```
┌─────────────────────────────────────────────────────────────┐
│                       AURA Architecture                     │
└─────────────────────────────────────────────────────────────┘
                             React UI
                                │
                                ▼
                       Spring Boot Backend
                       (Sole Owner of Data)
                         │             │
        (JPA / Hibernate)│             │ (HTTP REST / JSON)
                         ▼             ▼
                   MySQL Database    FastAPI AI Engine
                   (Persistence)     (Stateless ML Inference)
```

---

## 2. Why MySQL is Needed (Simple English + Hinglish)

Abhi tak hamara prototype flat CSV files par chal raha tha. But production ya real hospital facility mein CSV use karne ke drawbacks hain:
1. **Concurrency & File Locks:** Agar do alag devices ya processes ek sath CSV likhenge, toh file lock ya data corruption hoga. MySQL ACID compliance aur row-level locking deta hai.
2. **Slow Queries on Growing Data:** 90 din ka data ~43,200 rows hai. 1 saal ka data 1,75,000+ rows ho jayega. CSV ko har bar memory mein read karke filter karna extremely slow hai, jabki MySQL B-Tree indexes se microsecond range queries deta hai.
3. **Structured Relationships:** Facility details (naam, address, facility type) aur continuous sensor readings ko cleanly link karne ke liye relational database zaroori hai.
4. **Spring Boot Native Ecosystem:** Spring Boot + Spring Data JPA (Hibernate) MySQL ke sath out-of-the-box perfectly integrate hote hain (entity mapping, connection pooling with HikariCP, repository methods).

---

## 3. Proposed Entities & Why Each Exists

Hum over-engineering avoid karenge aur strictly **3 clean tables** propose kar rahe hain:

```
┌─────────────────┐       1 : N       ┌───────────────────────┐
│   facilities    │ ────────────────< │    energy_readings    │
│  (Facility Info)│                   │   (Raw Telemetry)     │
└────────┬────────┘                   └───────────────────────┘
         │
         │ 1 : N                      ┌───────────────────────┐
         └──────────────────────────< │  energy_intelligence  │
                                      │  (AI Inference Audit) │
                                      └───────────────────────┘
```

### Table 1: `facilities`
- **What it represents:** Ek physical ya organizational facility (e.g., Hospital, University, Commercial Tech Park, Municipal Office).
- **Why it exists:** PS04 hackathon requirement hai ki AURA ek *configurable facility platform* ho. Hum har facility type (Hospital, College, Company) ke liye alag alag databases nahi banayenge. `facility_type` column as configuration act karega.
- **Who writes to it:** Super Admin / System Setup script (one-time initialization or facility onboarding).
- **Who reads from it:** Spring Boot (facility metadata load karne ke liye), React Dashboard (facility header & multi-tenant dropdown ke liye).

### Table 2: `energy_readings`
- **What it represents:** Physical energy meters ka 15-minute telemetry data.
- **Why it exists:** Raw ground-level facts ko store karta hai (energy kWh, room occupancy, temperature, power source).
- **Who writes to it:** Spring Boot telemetry ingestion service / scheduled synthetic feeder.
- **Who reads from it:** Spring Boot dashboard queries (historical charts, daily consumption aggregates, peak load trends) aur ML training batch jobs.

### Table 3: `energy_intelligence`
- **What it represents:** AURA Python AI engine ke dwara generate kiya gaya output contract (anomaly score, detection status, near-term forecast, recommendation).
- **Why it exists:** 
  - **Pros of storing:** 
    1. *Historical Audit Trail:* Hospital administrator 1 mahine baad audit kar sakta hai: *"Last month kitne alerts aaye aur recommendation kya thi?"*
    2. *Fast Dashboard Loading:* React UI ko historical alerts dekhne ke liye bar-bar Python ML run nahi karna padta; direct MySQL se instant render ho jata hai.
    3. *Facility Ticket Integration:* Alert ko maintenance work-order ke sath link karne ke liye unique intelligence record ID milta hai.
  - **Cons:** Extra disk storage (~few MBs per month).
  - **Decision:** **YES, store it.** Storing intelligence results in MySQL creates a complete historical operational log for administrators.

---

## 4. Table Columns & Data Types

### 4.1. Table: `facilities`

| Column Name | SQL Data Type | Constraints | Description |
|---|---|---|---|
| `facility_id` | `VARCHAR(32)` | **PRIMARY KEY** | Unique facility code (e.g. `'H001'` or `'HOSPITAL_001'`). |
| `name` | `VARCHAR(128)` | `NOT NULL` | Human-readable name (e.g. `'BPUT Government General Hospital'`). |
| `facility_type` | `VARCHAR(32)` | `NOT NULL` | Facility category (`'HOSPITAL'`, `'COLLEGE'`, `'MUNICIPAL'`, `'COMMERCIAL'`). |
| `location` | `VARCHAR(255)` | `NULL` | Physical address or city (e.g. `'Rourkela, Odisha'`). |
| `total_floors` | `INT` | `DEFAULT 1` | Operational structure configuration. |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Record onboarding timestamp. |

---

### 4.2. Table: `energy_readings`

| Column Name | SQL Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT AUTO_INCREMENT` | **PRIMARY KEY** | Unique reading record sequence ID. |
| `facility_id` | `VARCHAR(32)` | `NOT NULL`, **FK** | References `facilities(facility_id)`. |
| `zone_id` | `VARCHAR(32)` | `NOT NULL` | Hospital zone (`'ICU'`, `'EMERGENCY'`, `'GENERAL_WARD'`, `'OPD'`, `'ADMIN'`). |
| `timestamp` | `DATETIME` | `NOT NULL` | Exact reading interval (YYYY-MM-DD HH:MM:SS). |
| `energy_kwh` | `DECIMAL(10,2)` | `NOT NULL` | Active electrical consumption during interval. |
| `occupancy_percent` | `DECIMAL(5,2)` | `DEFAULT 0.00` | Room/zone occupancy percentage during interval. |
| `temperature_c` | `DECIMAL(5,2)` | `NULL` | Ambient indoor temperature in Celsius. |
| `operational_status` | `VARCHAR(32)` | `DEFAULT 'NORMAL'` | Operational state (`'NORMAL'`, `'SURGE'`, `'OFF_HOURS'`). |
| `energy_source` | `VARCHAR(32)` | `DEFAULT 'GRID'` | Power supply source (`'GRID'`, `'SOLAR'`, `'BACKUP_DG'`). |
| `source` | `VARCHAR(32)` | `DEFAULT 'synthetic'` | Data provenance (`'synthetic'` for hackathon prototype, `'telemetry'` for physical IoT meters). |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Database insertion timestamp. |

---

### 4.3. Table: `energy_intelligence`

| Column Name | SQL Data Type | Constraints | Description |
|---|---|---|---|
| `id` | `BIGINT AUTO_INCREMENT` | **PRIMARY KEY** | Unique intelligence event sequence ID. |
| `facility_id` | `VARCHAR(32)` | `NOT NULL`, **FK** | References `facilities(facility_id)`. |
| `zone_id` | `VARCHAR(32)` | `NOT NULL` | Hospital zone identifier. |
| `timestamp` | `DATETIME` | `NOT NULL` | Timestamp corresponding to the telemetry interval. |
| `current_energy_kwh` | `DECIMAL(10,2)` | `NOT NULL` | Observed consumption value. |
| `anomaly_detected` | `BOOLEAN` | `NOT NULL` | `TRUE` if anomaly score exceeds threshold, else `FALSE`. |
| `anomaly_score` | `DECIMAL(6,3)` | `NOT NULL` | Standardized Z-Score deviation. |
| `forecast_energy_kwh` | `DECIMAL(10,2)` | `NOT NULL` | Estimated energy consumption for near-term horizon. |
| `forecast_horizon` | `VARCHAR(32)` | `DEFAULT 'next_1_hour'` | Forecast validity duration. |
| `recommendation` | `TEXT` | `NOT NULL` | Ground-level actionable guidance in simple English. |
| `source` | `VARCHAR(32)` | `DEFAULT 'synthetic'` | Data provenance indicator. |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Time intelligence was generated and stored. |

---

## 5. Primary Keys, Foreign Keys, & Relationships

1. **`facilities` is the Master Entity:**
   - Primary Key: `facility_id`
2. **`energy_readings` Child Entity:**
   - Foreign Key: `facility_id` $\to$ references `facilities(facility_id)` on delete cascade or restrict.
   - Relationship: One Facility has many Energy Readings ($1 : N$).
3. **`energy_intelligence` Child Entity:**
   - Foreign Key: `facility_id` $\to$ references `facilities(facility_id)`.
   - Relationship: One Facility has many Intelligence Evaluations ($1 : N$).
4. **Logical Link between Readings and Intelligence:**
   - Both share `(facility_id, zone_id, timestamp)` as a natural business key, allowing simple `JOIN` queries without synthetic composite keys.

---

## 6. Useful Indexes (No Over-Indexing)

AURA queries dashboard data along 3 primary dimensions: **Facility**, **Zone**, and **Time**.

### Indexes on `energy_readings`:
1. **`idx_energy_zone_time (facility_id, zone_id, timestamp DESC)`:**
   - *Why:* Sabse critical index. Jab React dashboard ICU ya Emergency ka last 24-hour ya 7-day trend maangta hai, toh MySQL instant index range scan karega (O(log N)).
2. **`idx_energy_timestamp (timestamp)`:**
   - *Why:* Facility-wide hourly aggregations (e.g. *"Poore hospital ka subah 9 baje total load kitna tha?"*).

### Indexes on `energy_intelligence`:
1. **`idx_intel_zone_time (facility_id, zone_id, timestamp DESC)`:**
   - *Why:* Zone specific alert history and latest intelligence lookup.
2. **`idx_intel_anomaly (facility_id, anomaly_detected, timestamp DESC)`:**
   - *Why:* React alert feed ke liye: *"Sirf wahi records dikhao jahan anomaly_detected = TRUE"* filter queries ko instant scan karega.

---

## 7. Architecture Decision: Who Owns Database Access?

### Question:
**Should FastAPI directly connect to MySQL, OR should Spring Boot own the database access?**

### Decision & Rationale:
**Spring Boot MUST own all direct MySQL access. FastAPI remains a stateless AI compute engine.**

```
[BAD / ANTI-PATTERN] Tight Coupled:
FastAPI ──── (Direct DB Connection) ────┐
                                        ▼
                                   MySQL Database
                                        ▲
Spring Boot ── (Direct DB Connection) ──┘
(Split ownership, dual connection pools, schema synchronization headaches)

=============================================================================

[RECOMMENDED / CLEAN ARCHITECTURE] Decoupled:
React Dashboard
      │
      ▼ (REST)
Spring Boot (Single Source of Truth, Auth, JPA, Connection Pools, DB Migrations)
      │
      ├─── Reads/Writes ───> MySQL Database
      │
      └─── Calls (HTTP) ───> FastAPI AI Engine (Stateless ML Inference)
```

### Why this is the best decision for our B.Tech Hackathon Architecture:
1. **Single Source of Truth:** Database connection pool (HikariCP), transactions (`@Transactional`), schema migrations (Flyway/Liquibase), aur enterprise security (JWT/Roles) Spring Boot ke paas rehti hai.
2. **Stateless AI Engine:** FastAPI ko database credentials ya SQL schemas janne ki zaroorat nahi hoti. FastAPI sirf input telemetry receive karta hai aur mathematically scored intelligence contract return karta hai.
3. **Zero DB Driver Conflicts:** Python aur Java dono se ek hi database par concurrent locks ya pooling issues nahi aate.
4. **Future Scalability:** Kal ko FastAPI ko Docker container mein cloud/edge par scale out kiya ja sakta hai bina database pooling bottlenecks ke.

---

## 8. Data Flow

```
1. Telemetry Ingestion:
   Synthetic Sensor Generator / Feeder
                 │ (Batch / Stream)
                 ▼
          Spring Boot Service
                 │
                 ├─── 1. Persists Telemetry ───> MySQL (`energy_readings`)
                 │
                 ├─── 2. Calls AI Service ─────> FastAPI (`GET /api/v1/energy/intelligence`)
                 │                                        │
                 │                                        ▼
                 │                               Compute Anomaly + Forecast + Recommendation
                 │                                        │
                 │ <── 3. Returns Contract JSON ──────────┘
                 │
                 ├─── 4. Persists Intelligence ─> MySQL (`energy_intelligence`)
                 │
                 ▼
2. User Dashboard Query:
   React Frontend Dashboard
                 │ (HTTP GET /api/dashboard/energy)
                 ▼
          Spring Boot Controller
                 │
                 ├─── Queries MySQL (`energy_readings` + `energy_intelligence`)
                 │
                 ▼
   Returns Rich Unified Facility Dashboard State to User
```

---

## 9. Synthetic Data Assumptions & Integrity

1. **Source Tracking:** `source` column always defaults to `'synthetic'` for the current prototype data. It clearly marks data as simulated operational prototype data, not actual hospital medical hardware.
2. **Data Consistency:** Facility ID in tables matches the source telemetry (`'H001'`).
3. **Internal ML Features Excluded:** Columns like `hour_sin`, `hour_cos`, `energy_lag_96`, `rolling_res_std`, aur synthetic `anomaly_flag` MySQL database schema mein **store nahi honge**. Database clean aur user-facing rahega.

---

## 10. Future Extension for Other Modules

Ye schema design extensible hai. Jab hum baki modules par move karenge:
- **`water_readings` & `water_intelligence`:** Same structure, `energy_kwh` replaced by `flow_liters`.
- **`waste_readings` & `waste_intelligence`:** Same structure, metrics replaced by `waste_kg`, `bin_fill_percent`.
- **`environment_readings`:** Same structure, metrics: `temperature_c`, `humidity_percent`, `air_quality_aqi`.
- **`equipment_readings`:** Adds `equipment_id`, `runtime_hours`, `vibration_mm_s`.
- **`traffic_readings`:** Adds `vehicle_count`, `parking_occupancy_percent`.

Baki sabhi tables `facilities(facility_id)` se link hongi, keeping the database architecture unified.

---

## 11. Final Recommended SQL DDL Schema

```sql
-- =============================================================================
-- AURA Facility Intelligence Platform — MySQL DDL Schema (Energy Phase)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS aura_facility_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE aura_facility_db;

-- -----------------------------------------------------------------------------
-- 1. Facilities Master Table
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS facilities (
    facility_id VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    facility_type VARCHAR(32) NOT NULL DEFAULT 'HOSPITAL',
    location VARCHAR(255) NULL,
    total_floors INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (facility_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 2. Energy Readings Telemetry Table
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- 3. Energy Intelligence Outputs Table
-- -----------------------------------------------------------------------------
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
```
