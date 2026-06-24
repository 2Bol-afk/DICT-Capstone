# Task 5 Report — Farmer SPA

## Status: DONE

## Changes
- **Replaced** `frontend/farmer.html` entirely with a new single-page app.
- Auth guard is the first inline `<script>` in `<head>`; redirects to `/` if `farmerAuth` is missing from `sessionStorage`.
- Four tabs: **tabMyFarms** (default), **tabSensors**, **tabHistory**, **tabSettings**.
- Fixed top header: farm logo, farmer name (from `farmerAuth.name`), language toggle button (`id="langToggle"`).
- Fixed bottom nav with 4 buttons; active state uses `#0d631b`.
- `CROP_FIL` dictionary covers all 22 crops.
- `applyLanguage(pref)` iterates `[data-fil]` elements and updates `langToggle` text.
- `cropLabel(en)` returns Tagalog name when `lang === "fil"`.
- My Farms: renders one card per `farmerAuth.farms` entry, fetches `GET /farms/{farm_id}/predict`, click → switches to Sensors tab and calls `loadSensors(farm_id)`.
- Sensors tab: farm selector dropdown, recommendation card with explain button, sensor buttons (green/gray by reading presence), 3-column readings grid (N, P, K, pH, Temp, Ulan).
- History tab: farm selector, fetches `GET /readings/{plot_id}` for each sensor, table rows sorted descending.
- Settings tab: language toggle (Tagalog/Ingles), theme toggle (Maliwanag/Madilim), logout button clears `sessionStorage` and redirects to `/`.
- All event listeners added via `addEventListener` — no `onclick` string interpolation.
- Dark mode CSS included.

## Concerns
- `showReading(sensor)` reads values directly from `farmerAuth.farms[].sensors[]` (the auth object snapshot). If live sensor data diverges from the login snapshot, the Sensors tab will show stale readings until re-login. The History tab fetches live from `GET /readings/{plot_id}` and is always fresh.
- `rainfall_mm` is mapped to the "Ulan" field; if the API returns a different field name (e.g. `rainfall`) the cell will show `—`. Check the sensor schema if this occurs.
