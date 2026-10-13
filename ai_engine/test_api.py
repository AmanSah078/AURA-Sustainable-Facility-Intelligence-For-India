"""
Test suite for AURA Energy Intelligence FastAPI Layer.
Validates:
1. /health endpoint
2. Single-zone intelligence endpoint (/api/v1/energy/intelligence?zone_id=EMERGENCY)
3. All-zone intelligence endpoint (/api/v1/energy/intelligence)
4. Energy Intelligence Contract compliance (required fields present, internal features absent)
5. Zero dependency on synthetic ground-truth 'anomaly_flag'
6. Recommendation text is simple, clear English
7. Error handling on invalid zone_id
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Required Contract fields
EXPECTED_CONTRACT_FIELDS = {
    "facility_id",
    "zone_id",
    "timestamp",
    "current_energy_kwh",
    "anomaly_detected",
    "anomaly_score",
    "forecast_energy_kwh",
    "forecast_horizon",
    "recommendation",
    "source"
}

# Strictly forbidden internal ML features
FORBIDDEN_INTERNAL_FEATURES = {
    "hour_sin",
    "hour_cos",
    "energy_lag_1",
    "energy_lag_4",
    "energy_lag_96",
    "rolling_res_mean",
    "rolling_res_std",
    "residual",
    "anomaly_flag",
    "datetime"
}


def run_tests():
    from fastapi.testclient import TestClient
    from ai_engine.api import app

    client = TestClient(app)
    print("=" * 75)
    print("AURA FASTAPI ENERGY INTELLIGENCE LAYER - VALIDATION TEST SUITE")
    print("=" * 75)

    # Test 1: Health check
    print("\n[TEST 1] Testing GET /health...")
    resp = client.get("/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    assert resp.json() == {"status": "ok"}, f"Unexpected health payload: {resp.json()}"
    print("  --> PASSED: Status 200, Payload: {'status': 'ok'}")

    # Test 2: Single-zone query (EMERGENCY)
    print("\n[TEST 2] Testing GET /api/v1/energy/intelligence?zone_id=EMERGENCY...")
    resp = client.get("/api/v1/energy/intelligence?zone_id=EMERGENCY")
    assert resp.status_code == 200, f"Single zone failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert isinstance(data, dict), "Expected dictionary response"
    
    # Contract field validation
    assert set(data.keys()) == EXPECTED_CONTRACT_FIELDS, (
        f"Contract mismatch! Found: {set(data.keys())}, Expected: {EXPECTED_CONTRACT_FIELDS}"
    )
    
    # Check forbidden fields
    for field in FORBIDDEN_INTERNAL_FEATURES:
        assert field not in data, f"Internal feature leaked in response: {field}"
        
    assert data["zone_id"] == "Emergency", f"Zone mismatch: {data['zone_id']}"
    assert isinstance(data["anomaly_detected"], bool), "anomaly_detected must be boolean"
    assert isinstance(data["anomaly_score"], (int, float)), "anomaly_score must be numeric"
    assert isinstance(data["forecast_energy_kwh"], (int, float)), "forecast must be numeric"
    assert data["forecast_horizon"] == "next_1_hour", "forecast_horizon must be 'next_1_hour'"
    assert "Review" in data["recommendation"] or "Normal" in data["recommendation"]
    print("  --> PASSED: Valid Contract payload returned:")
    print(f"      Zone: {data['zone_id']} | Load: {data['current_energy_kwh']} kWh | Score: {data['anomaly_score']}")
    print(f"      Recommendation: \"{data['recommendation']}\"")

    # Test 3: Specific historical anomaly event (Emergency at 03-01-2026 08:00)
    print("\n[TEST 3] Testing known anomaly record (Emergency at 03-01-2026 08:00)...")
    resp = client.get("/api/v1/energy/intelligence?zone_id=Emergency&timestamp=03-01-2026%2008:00")
    assert resp.status_code == 200
    anomaly_data = resp.json()
    assert anomaly_data["anomaly_detected"] is True, "Expected anomaly_detected = True"
    assert anomaly_data["anomaly_score"] >= 3.0, "Expected Z-score >= 3.0"
    assert "Unusual energy usage detected in the Emergency zone" in anomaly_data["recommendation"]
    print("  --> PASSED: Anomaly correctly flagged with recommendation:")
    print(f"      Score: {anomaly_data['anomaly_score']} | Alert: {anomaly_data['anomaly_detected']}")
    print(f"      Recommendation: \"{anomaly_data['recommendation']}\"")

    # Test 4: All-zones query (/api/v1/energy/intelligence)
    print("\n[TEST 4] Testing GET /api/v1/energy/intelligence (All Zones)...")
    resp = client.get("/api/v1/energy/intelligence")
    assert resp.status_code == 200, f"All zones failed: {resp.status_code}"
    all_data = resp.json()
    assert isinstance(all_data, list), "Expected list response"
    assert len(all_data) == 5, f"Expected 5 hospital zones, found: {len(all_data)}"
    
    returned_zones = {item["zone_id"] for item in all_data}
    expected_zones = {"Admin", "Emergency", "General_Ward", "ICU", "OPD"}
    assert returned_zones == expected_zones, f"Zones mismatch: {returned_zones}"

    for item in all_data:
        assert set(item.keys()) == EXPECTED_CONTRACT_FIELDS
        for field in FORBIDDEN_INTERNAL_FEATURES:
            assert field not in item
    print(f"  --> PASSED: All 5 hospital zones returned ({', '.join(sorted(returned_zones))})")

    # Test 5: Error handling on invalid zone_id
    print("\n[TEST 5] Testing error handling with invalid zone_id ('CARDIOLOGY')...")
    resp = client.get("/api/v1/energy/intelligence?zone_id=CARDIOLOGY")
    assert resp.status_code == 400, f"Expected 400 status, got: {resp.status_code}"
    err_detail = resp.json().get("detail", "")
    assert "Unknown zone_id" in err_detail, f"Unexpected error detail: {err_detail}"
    print(f"  --> PASSED: HTTP 400 with clear message: \"{err_detail}\"")

    print("\n" + "=" * 75)
    print("ALL 5 TESTS PASSED SUCCESSFULLY! FASTAPI LAYER IS VERIFIED.")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
