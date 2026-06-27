"""Full backend smoke test. Hits every endpoint and asserts sane responses.

STANDALONE SCRIPT, NOT A PYTEST TEST: this module executes top-level code at import
time against a live server, so it is NOT picked up automatically by `pytest` and does
NOT use the Firestore emulator fixture in conftest.py. To run it safely against
Firestore without touching production data: set FIRESTORE_EMULATOR_HOST=localhost:8080
and GOOGLE_CLOUD_PROJECT=bukid-ac67d, start the Firestore emulator, then start the live
server with `python -m uvicorn main:app` (from app/) on port 8000, then run this script
directly with `python test_full.py`.
"""
import requests, sys

API = "http://127.0.0.1:8000"
passed, failed = 0, []

def check(name, cond):
    global passed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed.append(name)
        print(f"  FAIL  {name}")

print("\n=== FARMS ===")
r = requests.get(f"{API}/farms")
check("GET /farms returns 200", r.status_code == 200)
farms = r.json()
check("at least one farm exists", len(farms) >= 1)
farm = farms[0]
fid = farm["farm_id"]
check("farm has farm_id", "farm_id" in farm)
check("farm has polygon list", isinstance(farm.get("polygon"), list))
check("farm has farmer_id field", "farmer_id" in farm)

print("\n=== PLOTS / SENSORS ===")
r = requests.get(f"{API}/plots")
check("GET /plots returns 200", r.status_code == 200)
plots = r.json()
sensor_plots = [p for p in plots if p["plot_id"].startswith(fid)]
check("farm has sensor sub-plots", len(sensor_plots) >= 1)

print("\n=== SIMULATE READING ===")
if sensor_plots:
    pid = sensor_plots[0]["plot_id"]
    r = requests.post(f"{API}/readings/simulate", params={"plot_id": pid})
    check("POST /readings/simulate returns 200", r.status_code == 200)
    rd = r.json()
    check("simulated reading has predicted_crop", "predicted_crop" in rd)
    check("simulated reading has soil_n", rd.get("soil_n") is not None)

print("\n=== FARM PREDICT ===")
r = requests.get(f"{API}/farms/{fid}/predict")
check("GET /farms/{id}/predict returns 200", r.status_code == 200)
pred = r.json()
check("predict returns crop", "crop" in pred)
check("predict returns sensor_count", "sensor_count" in pred)

print("\n=== FARMERS CRUD ===")
r = requests.post(f"{API}/farmers", json={"name": "_test_farmer_xyz"})
check("POST /farmers returns 200", r.status_code == 200)
frm = r.json()
fmid = frm["id"]
r = requests.post(f"{API}/farmers", json={"name": "_test_farmer_xyz"})
check("duplicate farmer name returns 409", r.status_code == 409)
r = requests.get(f"{API}/farmers")
check("GET /farmers returns list with farm_count", all("farm_count" in f for f in r.json()))
r = requests.put(f"{API}/farmers/{fmid}", json={"name": "_test_renamed_xyz"})
check("PUT /farmers/{id} rename returns 200", r.status_code == 200)

print("\n=== FARM ASSIGNMENT ===")
r = requests.put(f"{API}/farms/{fid}/farmer", json={"farmer_id": fmid})
check("PUT /farms/{id}/farmer assign returns 200", r.status_code == 200)
r = requests.get(f"{API}/farmers/by-name/_test_renamed_xyz")
check("GET /farmers/by-name returns farmer", r.status_code == 200)
check("farmer has farms[] with assigned farm", any(f["farm_id"] == fid for f in r.json().get("farms", [])))
# unassign + cleanup
requests.put(f"{API}/farms/{fid}/farmer", json={"farmer_id": None})
r = requests.delete(f"{API}/farmers/{fmid}")
check("DELETE /farmers/{id} returns 200", r.status_code == 200)

print("\n=== ERROR HANDLING ===")
r = requests.get(f"{API}/farmers/by-name/does_not_exist_zzz")
check("unknown farmer returns 404", r.status_code == 404)
r = requests.get(f"{API}/farms/FAKE-ID/predict")
check("unknown farm predict returns 404", r.status_code == 404)

print(f"\n{'='*40}\nRESULT: {passed} passed, {len(failed)} failed")
if failed:
    print("FAILURES:", failed)
    sys.exit(1)
print("ALL BACKEND TESTS PASSED")
