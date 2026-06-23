import random

import pandas as pd

from train_crop_model import PH_CROP_WHITELIST

DATA_PATH = "data_for_training/Crop_recommendation.csv"
SOIL_MOISTURE_RANGE = (15, 45)


def sample_reading(df: pd.DataFrame, crop: str) -> dict:
    crop_rows = df[df["label"] == crop]
    values = {}
    for col in ["N", "P", "K", "ph", "temperature", "humidity", "rainfall"]:
        lo, hi = crop_rows[col].min(), crop_rows[col].max()
        values[col] = round(random.uniform(lo, hi), 2)
    return values


def simulate_sensor_values(df: pd.DataFrame) -> dict:
    """Pick a random PH-relevant crop and sample realistic sensor values for it."""
    # ponytail: only sample PH-relevant crops — real PH farms wouldn't be
    # growing coffee/grapes, so simulating them just produces noise
    ph_labels = PH_CROP_WHITELIST & set(df["label"].unique())
    crop = random.choice(sorted(ph_labels))
    sampled = sample_reading(df, crop)
    return {
        "soil_n": sampled["N"],
        "soil_p": sampled["P"],
        "soil_k": sampled["K"],
        "soil_ph": sampled["ph"],
        "air_temp_c": sampled["temperature"],
        "humidity_pct": sampled["humidity"],
        "rainfall_mm": sampled["rainfall"],
        "soil_moisture_pct": round(random.uniform(*SOIL_MOISTURE_RANGE), 1),
        "_source_crop": crop,
    }
