"""Reset the DB and seed a presentable demo dataset via the live API.

ponytail: Firestore data is ephemeral/safe to wipe via the Firebase Console or
emulator — this seeds fresh demo data via the live API regardless of what's
already there.
"""
import random
import time

import requests

API = "http://127.0.0.1:8000"
READINGS_PER_PLOT = 3
NUM_PLOTS = 8

PH_LAT_RANGE = (5.0, 19.0)
PH_LNG_RANGE = (117.0, 127.0)
OWNER_NAMES = [
    "Juan Dela Cruz", "Maria Santos", "Pedro Reyes", "Ana Garcia",
    "Jose Ramos", "Rosa Flores", "Carlos Mendoza", "Liza Bautista",
]


def main():
    # NOTE: this seeds via the live API and is safe to re-run any time — Firestore
    # data can simply be wiped via the Firebase Console or emulator if you want a
    # clean slate first.
    for i, owner in enumerate(OWNER_NAMES[:NUM_PLOTS], start=1):
        plot_id = f"FARM-{i:03d}"
        plot = {
            "plot_id": plot_id,
            "owner_name": owner,
            "lat": round(random.uniform(*PH_LAT_RANGE), 4),
            "lng": round(random.uniform(*PH_LNG_RANGE), 4),
        }
        requests.post(f"{API}/plots", json=plot).raise_for_status()
        print(f"Created {plot_id} ({owner})")

        for _ in range(READINGS_PER_PLOT):
            res = requests.post(f"{API}/readings/simulate", params={"plot_id": plot_id})
            res.raise_for_status()
            r = res.json()
            print(f"  reading -> predicted={r['predicted_crop']} confidence={r['confidence']}")
            time.sleep(0.05)  # keeps timestamps distinct for history ordering

    print(f"\nSeeded {NUM_PLOTS} plots with {READINGS_PER_PLOT} readings each.")


if __name__ == "__main__":
    main()
