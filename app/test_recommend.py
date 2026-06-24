"""Quick smoke test for crop recommendation endpoint."""
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
