# Final Fix Report

## Fix 1: admin.html — sensor count always shows 0

**Problem:** `loadDashboard` and `loadFarmsTab` both called `GET /readings/{farm_id}` with a farm ID. That endpoint expects a sensor plot ID, so it always returned empty, causing sensor counts to show 0.

**Fix applied:**
- In `loadDashboard` (stat counter): replaced the `/readings/${farm_id}` fetch with `/farms/${farm_id}/predict`, summing `pred.sensor_count` across all farms.
- In `loadDashboard` (overview table rows): merged the two separate fetches (one for readings count, one for predict) into a single `/farms/${farm_id}/predict` call that provides both `sensor_count` and `crop`.
- In `loadFarmsTab`: removed the per-farm `/readings/${farm_id}` fetch entirely and replaced the sensor column with `—` (this tab is for farmer assignment, not sensor monitoring).

## Fix 2: main.py — route order for /farms/by-name

**Problem:** FastAPI registers routes in declaration order. `GET /farms/{farm_id}/predict` was declared before `GET /farms/by-name/{farm_name}`, so a request to `/farms/by-name/SomeFarm` matched `{farm_id}` = `"by-name"` instead of the intended route.

**Fix applied:** Moved `GET /farms/by-name/{farm_name}` to appear before `GET /farms/{farm_id}/predict` and `GET /farms/{farm_id}/explain`.

## Minor fix: import uuid moved to top-level

Moved `import uuid` from inside the `create_farmer()` function body to the top-level import block in `main.py`.

## Files changed
- `frontend/admin.html`
- `main.py`
