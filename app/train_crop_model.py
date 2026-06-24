import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

DATA_PATH = "data_for_training/Crop_recommendation.csv"
MODEL_PATH = "crop_model.pkl"
FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

# ponytail: manual curation step for Philippine relevance, cross-referenced
# against DA-BSWM/PhilRice crop coverage — not derived from additional
# training data. Update this list if PH-relevant labels are missing/extra.
PH_CROP_WHITELIST = {
    "rice", "maize", "banana", "coconut", "cotton", "jute",
    "mango", "watermelon", "muskmelon", "papaya", "orange",
    "mungbean", "blackgram", "lentil", "chickpea", "kidneybeans",
    "pigeonpeas", "mothbeans",
}

# ponytail: below this, the best PH-relevant match is a guess, not a
# recommendation — surface that honestly instead of returning a confident-
# looking low-probability label
MIN_CONFIDENCE = 0.3


def train_and_save():
    df = pd.read_csv(DATA_PATH)
    X = df.drop("label", axis=1)
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(random_state=42)
    model.fit(X_train, y_train)

    print(f"Test accuracy: {model.score(X_test, y_test):.4f}")
    print(f"Unique crop labels ({len(model.classes_)}): {sorted(model.classes_)}")

    joblib.dump(model, MODEL_PATH)
    return model


def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    model = joblib.load(MODEL_PATH)
    whitelist = PH_CROP_WHITELIST & set(model.classes_)
    row = pd.DataFrame([[N, P, K, temperature, humidity, ph, rainfall]], columns=FEATURES)
    probs = model.predict_proba(row)[0]
    ranked = sorted(zip(model.classes_, probs), key=lambda x: -x[1])

    for crop, conf in ranked:
        if crop in whitelist:
            if conf < MIN_CONFIDENCE:
                return {"crop": None, "confidence": round(float(conf), 4), "filtered": True,
                        "message": "No confident PH-relevant match for this reading."}
            filtered = crop != ranked[0][0]
            return {"crop": crop, "confidence": round(float(conf), 4), "filtered": filtered}

    return {"crop": None, "confidence": 0.0, "filtered": True,
            "message": "No confident PH-relevant match for this reading."}


if __name__ == "__main__":
    train_and_save()

    examples = [
        (90, 42, 43, 20.9, 82.0, 6.5, 202.9),
        (20, 60, 20, 25.0, 60.0, 6.0, 100.0),
        (70, 30, 30, 28.0, 70.0, 6.8, 150.0),
    ]
    print("\nExample predictions:")
    for N, P, K, t, h, ph, r in examples:
        result = predict_crop(N, P, K, t, h, ph, r)
        print(f"  N={N} P={P} K={K} temp={t} hum={h} ph={ph} rain={r} -> {result}")
