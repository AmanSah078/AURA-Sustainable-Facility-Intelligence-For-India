# AURA — Energy Intelligence Output Contract
**Platform:** AURA — AI-Powered Sustainable Facility Intelligence Platform  
**Target Facility:** HOSPITAL_001 (Government Hospital)  
**Module:** Energy Intelligence  
**Document Status:** Approved Architecture Design  

---

## 1. Purpose

The purpose of this document is to define a clean, formal, and stable **Output Contract** for the AURA Energy Intelligence module. 

This contract establishes the exact JSON schema that the Python AI/Analytics engine will produce for downstream consumption by the Spring Boot backend and the React operational dashboard. It bridges mathematical machine learning with practical facility operations.

```
┌─────────────────────────────────┐
│   Python AI / Analytics Layer   │  (Anomaly Detection + Forecasting)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   Energy Intelligence Contract  │  (Standardized, Decoupled JSON Schema)
└────────────────┬────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│  Future API  │   │ Spring Boot  │  (Enterprise Orchestration & Persistence)
└──────────────┘   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │  React UI    │  (Facility Administrator Dashboard)
                   └──────────────┘
```

---

## 2. Why the Contract is Needed (Simple English + Hinglish)

Jab hum Jupyter Notebooks ya Python scripts mein ML models build karte hain, toh code ke andar bohot saare **internal calculation features** create hote hain (jaise `energy_lag_1`, `energy_lag_96`, `hour_sin`, `hour_cos`, rolling statistics, Z-scores).

Agar hum seedha API banana shuru kar dein bina contract define kiye, toh:
1. **Tight Coupling Risk:** Agar kal ko hum ML model change karte hain (e.g. Seasonal-Naive se Ridge Regression ya Random Forest), toh bina stable contract ke Spring Boot aur React UI code break ho jayega.
2. **Information Overload:** Hospital facility managers ko trigonometric cyclic encodings (`hour_sin`) ya dataframe index se koi matlab nahi hota. Unhe operational clarity chahiye.
3. **Clear Boundary Between Math & Operations:** ML layer ka kaam hai patterns detect karna; Dashboard ka kaam hai decision support dikhana. Contract in dono ke beech ek "firewall/agreement" banata hai.
4. **Consistency Across Modules:** Ye contract aage chalke Water, Waste, Environment, Equipment, Safety aur Traffic intelligence ke liye standard architectural blueprint banega.

---

## 3. High-Level Data Flow

```
1. 15-Minute Sensor Telemetry Ingestion (energy_kwh, timestamp, zone_id)
                       ↓
2. Feature Transformation (Internal Lags, Diurnal Windows)
                       ↓
3. Seasonal Baseline Comparison (t - 96 interval reference)
                       ↓
4. Anomaly Scoring (Residual deviation vs 7-day rolling std)
                       ↓
5. Short-Term Forecast Projection (Upcoming 1-hour expected load)
                       ↓
6. Actionable Recommendation Synthesizer (Operational rule heuristics)
                       ↓
7. [ENERGY INTELLIGENCE CONTRACT JSON] ──> Dispatched to Spring Boot / React
```

---

## 4. Field Definitions

The contract exposes exactly **10 well-defined fields**. Each field addresses a specific operational requirement:

| # | Field Name | Data Type | Example Value | Description & Ground-Level Utility |
|---|---|---|---|---|
| 1 | `facility_id` | String | `"HOSPITAL_001"` | Facility identifier. Multi-tenant AURA deployment ko support karta hai. |
| 2 | `zone_id` | String | `"EMERGENCY"` | Hospital zone (`ICU`, `EMERGENCY`, `GENERAL_WARD`, `OPD`, `ADMIN`). Pinpoints exact physical location of load. |
| 3 | `timestamp` | String (ISO-8601) | `"2026-03-20T14:30:00"` | Timestamp of telemetry reading. Time-series sync aur event logging ke liye zaroori hai. |
| 4 | `current_energy_kwh` | Float | `850.4` | Actual observed energy consumption during this 15-minute interval. |
| 5 | `anomaly_detected` | Boolean | `true` | Binary indicator (`true`/`false`). Dashboard par visual alert card/badge trigger karta hai. |
| 6 | `anomaly_score` | Float | `3.21` | Normalized statistical severity score (Z-score). Alert priority rank karne ke kaam aata hai. |
| 7 | `forecast_energy_kwh` | Float | `870.2` | Expected energy consumption for the upcoming near-term horizon based on historical baseline. |
| 8 | `forecast_horizon` | String | `"next_1_hour"` | Forecast validity duration. Administrator ko planning window batata hai. |
| 9 | `recommendation` | String | `"Review high-usage equipment and operating schedule."` | Plain-language, non-prescriptive guidance for the duty engineer or administrator. |
| 10 | `source` | String | `"synthetic"` | Data provenance (`"synthetic"` for prototype testing, `"telemetry"` for real IoT hardware meters). |

---

## 5. Example JSON Payload

### Scenario A: Anomaly Detected in Critical Ward (Elevated Load)
```json
{
  "facility_id": "HOSPITAL_001",
  "zone_id": "EMERGENCY",
  "timestamp": "2026-03-20T14:30:00",
  "current_energy_kwh": 850.4,
  "anomaly_detected": true,
  "anomaly_score": 3.21,
  "forecast_energy_kwh": 870.2,
  "forecast_horizon": "next_1_hour",
  "recommendation": "Review high-usage equipment and operating schedule.",
  "source": "synthetic"
}
```

### Scenario B: Normal Operations (Steady Load)
```json
{
  "facility_id": "HOSPITAL_001",
  "zone_id": "ICU",
  "timestamp": "2026-03-20T14:30:00",
  "current_energy_kwh": 224.5,
  "anomaly_detected": false,
  "anomaly_score": 0.32,
  "forecast_energy_kwh": 223.8,
  "forecast_horizon": "next_1_hour",
  "recommendation": "Energy consumption is within expected operational limits.",
  "source": "synthetic"
}
```

---

## 6. Internal ML Data vs. User-Facing Facility Information

To maintain a clean separation of concerns, the contract strictly filters out mathematical artifacts:

| Category | Field / Variable | Layer | Why It Stays Internal or Becomes Public |
|---|---|---|---|
| **Internal ML Feature** | `hour_sin`, `hour_cos` | Python Only | Cyclic numerical encoding. Dashboard user ke liye meaningless hai. |
| **Internal ML Feature** | `energy_lag_1`, `energy_lag_4` | Python Only | Immediate momentum lags used by algorithms. |
| **Internal ML Feature** | `energy_lag_96` | Python Only | 24-hr historical index. Used to compute `forecast_energy_kwh`. |
| **Internal ML Feature** | `rolling_res_mean`, `rolling_res_std` | Python Only | Intermediate calibration stats for Z-score computation. |
| **Internal Ground Truth**| `anomaly_flag` | Python Only | Synthetic ground truth label. Strictly for evaluation, never exposed as input. |
| **User-Facing Info** | `current_energy_kwh` | Exposed | Facility team needs to see actual current draw. |
| **User-Facing Info** | `anomaly_detected` | Exposed | Essential for alert banners and push notifications. |
| **User-Facing Info** | `anomaly_score` | Exposed | Used to sort alerts by severity (High / Medium / Low). |
| **User-Facing Info** | `forecast_energy_kwh` | Exposed | Provides operational heads-up for load shedding / DG readiness. |
| **User-Facing Info** | `recommendation` | Exposed | Practical action item for duty supervisor. |

---

## 7. Recommendation Rules & User-Facing Language

### Tone and Phrasing Guidelines:
- **Decision Support, Not Diagnosis:** AURA telemetry-based anomaly flag karta hai, physical fault verify nahi karta.
- **Allowed Words:** `"expected"`, `"estimated"`, `"likely"`, `"based on recent pattern"`, `"consider reviewing"`.
- **Strictly Avoided Words:** 
  - ❌ *"Equipment is faulty."*
  - ❌ *"HVAC caused the anomaly."*
  - ❌ *"There is definitely an electrical short-circuit."*

### Recommendation Decision Matrix:

```
                              ┌────────────────────────┐
                              │    Anomaly Detected?   │
                              └───────────┬────────────┘
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
                 [ YES ]                                     [ NO ]
                    │                                           │
         Upcoming Forecast Trend?                    Upcoming Forecast Trend?
         ┌──────────┴──────────┐                     ┌──────────┴──────────┐
         ▼                     ▼                     ▼                     ▼
    [ Elevated ]         [ Normalizing ]         [ High Peak ]          [ Steady ]
         │                     │                     │                     │
    Recommendation:       Recommendation:       Recommendation:       Recommendation:
"Review high-usage    "Unusual surge        "Upcoming load is     "Energy consumption
equipment and         observed; verify if   estimated to rise;    is within expected
operating schedule    transient procedure   consider shedding     operational
in this zone."        load has concluded." deferrable loads."    limits."
```

---

## 8. Assumptions

1. **Interval Frequency:** Readings arrive at a regular 15-minute interval (96 intervals/day).
2. **Timezone:** Timestamps follow local facility standard time (ISO-8601 formatted string).
3. **Telemetry Units:** Energy values are normalized in kilowatt-hours (`kWh`) per 15-minute interval.
4. **Data Reliability:** Telemetry meter ID maps reliably to one of the 5 designated hospital zones.
5. **Decoupled Architecture:** Spring Boot handles authentication, role-based access, and alert logging without needing to understand the underlying ML model code.

---

## 9. Limitations

1. **Synthetic Data Context:** Current threshold calibration (`Z >= 3.0`) is derived from synthetic prototype data for hackathon simulation; it must be recalibrated when connected to physical smart meters.
2. **Single-Metric Horizon:** Short-term forecast relies on a 24-hour diurnal seasonal baseline; extreme weather shifts or unannounced emergency triage surges cannot be anticipated 24 hours in advance.
3. **No Automated Actuation:** The contract outputs advisory recommendations only; it does not directly trigger circuit breakers, BMS switches, or DG starts.

---

## 10. Future Extension Notes

This contract is designed to be easily extensible across all other AURA intelligence modules:

- **Water Intelligence (`data/water.csv`):**
  - Replace `current_energy_kwh` with `current_flow_liters`.
  - Replace `forecast_energy_kwh` with `forecast_flow_liters`.
  - Recommendation example: *"Review supply valves and check for possible line leakage."*

- **Environment Intelligence (`data/environment.csv`):**
  - Add `temperature_c`, `humidity_percent`, `air_quality_aqi`.
  - Recommendation example: *"Inspect zone ventilation and HEPA filtration cycle."*

- **Equipment Intelligence (`data/equipment.csv`):**
  - Add `equipment_id`, `runtime_hours`, `vibration_mm_s`.
  - Recommendation example: *"Schedule preventative lubrication inspection."*

- **Traffic Intelligence (`data/traffic.csv`):**
  - Add `vehicle_count`, `parking_occupancy_percent`.
  - Recommendation example: *"Divert visitor parking to auxiliary lot B."*

The core structure (`facility_id`, `zone_id`, `timestamp`, `current_metric`, `anomaly_detected`, `anomaly_score`, `forecast_metric`, `recommendation`, `source`) remains constant across the entire platform.
