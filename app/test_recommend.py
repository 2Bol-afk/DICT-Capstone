"""Quick smoke test for crop recommendation endpoint.

STANDALONE SCRIPT, NOT A PYTEST TEST: this module executes top-level code at import
time against a live server, so it is NOT picked up automatically by `pytest` and does
NOT use the Firestore emulator fixture in conftest.py. To run it safely against
Firestore without touching production data: set FIRESTORE_EMULATOR_HOST=localhost:8080
and GOOGLE_CLOUD_PROJECT=bukid-ac67d, start the Firestore emulator, then start the live
server with `python -m uvicorn main:app` (from app/) on port 8000, then run this script
directly with `python test_recommend.py`.
"""
import requests

BASE = "http://127.0.0.1:8000"

# Typical rice-growing conditions
payload = {
    "plot_id": "test-plot-001",
    "soil_n": 90,
    "soil_p": 42,
    "soil_k": 43,
    "air_temp_c": 25.0,
    "humidity_pct": 82.0,
    "soil_ph": 6.5,
    "rainfall_mm": 200.0,
    "lat": 8.0,
    "lng": 124.0,
}

print("Sending reading...")
r = requests.post(f"{BASE}/readings", json=payload)
print(f"Status: {r.status_code}")
data = r.json()
print(f"Predicted crop : {data.get('predicted_crop')}")
print(f"Confidence     : {data.get('confidence'):.2%}" if data.get('confidence') else "Confidence: N/A")
print(f"Filtered       : {data.get('filtered')}")
print(f"Full response  : {data}")
