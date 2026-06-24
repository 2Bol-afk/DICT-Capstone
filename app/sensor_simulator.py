"""Imitates field sensors pushing live readings to the backend.

Every INTERVAL seconds it re-fetches the list of sensor sub-plots from the API
and posts one fresh simulated reading per sensor via /readings/simulate. It
re-fetches every cycle, so farms/sensors added during the demo start reporting
automatically with no restart.

All sensors on the same farm are pinned to the same crop profile (picked once
per farm, cached for the life of this process). Real sensors on one farm are
reading the same soil/climate, so this keeps each farm internally consistent —
otherwise the whole-farm recommendation (which averages all of a farm's
sensors) blends unrelated crop profiles and the model rejects the low-
confidence result, showing "no match" even though every sensor has data.

Run (server must already be up):
    py sensor_simulator.py                 # default 15s interval
    py sensor_simulator.py --interval 10   # every 10s
    py sensor_simulator.py --once          # one cycle then exit (for testing)
"""
import argparse
import random
import time
from datetime import datetime

import requests

from train_crop_model import PH_CROP_WHITELIST

API = "http://127.0.0.1:8000"
_farm_crop_cache: dict[str, str] = {}


def sensor_plot_ids() -> list[str]:
    """Every sub-plot whose id looks like FARM-...-S<n> (the auto-placed sensors)."""
    plots = requests.get(f"{API}/plots", timeout=10).json()
    return sorted(p["plot_id"] for p in plots if "-S" in p["plot_id"])


def farm_id_of(plot_id: str) -> str:
    return plot_id.rsplit("-S", 1)[0]


def crop_for_farm(farm_id: str) -> str:
    """Same crop for every sensor on a farm, picked once and cached."""
    if farm_id not in _farm_crop_cache:
        _farm_crop_cache[farm_id] = random.choice(sorted(PH_CROP_WHITELIST))
    return _farm_crop_cache[farm_id]


def push_one(plot_id: str, crop: str) -> dict | None:
    r = requests.post(f"{API}/readings/simulate",
                      params={"plot_id": plot_id, "crop": crop}, timeout=10)
    if r.status_code != 200:
        return None
    return r.json()


def run_cycle() -> int:
    ids = sensor_plot_ids()
    if not ids:
        print(f"[{_now()}] no sensors yet — add a farm in the admin dashboard, "
              "then sensors will appear here automatically.")
        return 0
    ok = 0
    for pid in ids:
        crop = crop_for_farm(farm_id_of(pid))
        reading = push_one(pid, crop)
        if reading:
            ok += 1
            pred_crop = reading.get("predicted_crop") or "—"
            conf = reading.get("confidence")
            conf_s = f"{conf:.0%}" if conf else "—"
            print(f"[{_now()}] {pid:<24} (sim={crop:<12}) N={reading['soil_n']:>6.1f} "
                  f"pH={reading['soil_ph']:>4.1f} -> {pred_crop} ({conf_s})")
        else:
            print(f"[{_now()}] {pid:<24} FAILED to push reading")
    print(f"[{_now()}] cycle done: {ok}/{len(ids)} sensors reported\n")
    return ok


def _now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def main():
    ap = argparse.ArgumentParser(description="Imitate field sensors sending live data.")
    ap.add_argument("--interval", type=int, default=15,
                    help="seconds between cycles (default 15)")
    ap.add_argument("--once", action="store_true", help="run one cycle then exit")
    args = ap.parse_args()

    # fail fast if the server isn't running
    try:
        requests.get(f"{API}/farms", timeout=5)
    except requests.RequestException:
        print(f"Cannot reach the backend at {API}. Start it first:\n"
              "    py -m uvicorn main:app --reload")
        return

    print(f"Sensor simulator started. Pushing every {args.interval}s. Ctrl+C to stop.\n")
    if args.once:
        run_cycle()
        return
    try:
        while True:
            run_cycle()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
