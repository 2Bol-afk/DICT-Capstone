import random

import pandas as pd
import requests

from sensor_sim import simulate_sensor_values

DATA_PATH = "data_for_training/Crop_recommendation.csv"
API_URL = "http://127.0.0.1:8000/readings"
NUM_PLOTS = 10

PH_LAT_RANGE = (5.0, 19.0)
PH_LNG_RANGE = (117.0, 127.0)
OWNER_NAMES = [
    "Juan Dela Cruz", "Maria Santos", "Pedro Reyes", "Ana Garcia",
    "Jose Ramos", "Rosa Flores", "Carlos Mendoza", "Liza Bautista",
    "Antonio Cruz", "Elena Torres",
]


def build_plot_reading(plot_num: int, df: pd.DataFrame) -> dict:
    sampled = simulate_sensor_values(df)
    source_crop = sampled.pop("_source_crop")
    return {
        "plot_id": f"FARM-{plot_num:03d}",
        "owner_name": random.choice(OWNER_NAMES),
        "lat": round(random.uniform(*PH_LAT_RANGE), 4),
        "lng": round(random.uniform(*PH_LNG_RANGE), 4),
        **sampled,
        "_source_crop": source_crop,
    }


def main():
    df = pd.read_csv(DATA_PATH)

    print(f"Simulating {NUM_PLOTS} plots and posting to {API_URL}\n")
    for i in range(1, NUM_PLOTS + 1):
        reading = build_plot_reading(i, df)
        source_crop = reading.pop("_source_crop")

        response = requests.post(API_URL, json=reading)
        response.raise_for_status()
        result = response.json()

        print(
            f"{result['plot_id']} ({reading['owner_name']}) "
            f"sampled-from={source_crop} -> "
            f"predicted={result['predicted_crop']} "
            f"(confidence={result['confidence']}, filtered={bool(result['filtered'])})"
        )


if __name__ == "__main__":
    main()
