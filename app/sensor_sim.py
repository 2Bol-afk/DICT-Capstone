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


def simulate_sensor_values(df: pd.DataFrame, crop: str | None = None) -> dict:
    """Sample realistic sensor values for a PH-relevant crop.

    If crop is omitted, pick one at random. Callers simulating multiple
    sensors on the same farm should pass the same crop for all of them —
    otherwise each sensor samples an unrelated crop and the farm-wide
    average (used for the whole-farm recommendation) blends incompatible
    profiles into a low-confidence mush that the model correctly rejects.
    """
    # ponytail: only sample PH-relevant crops — real PH farms wouldn't be
    # growing coffee/grapes, so simulating them just produces noise
    ph_labels = PH_CROP_WHITELIST & set(df["label"].unique())
    if crop is None:
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
