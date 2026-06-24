import json
import subprocess
import time
from datetime import datetime, timezone

import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import db
from train_crop_model import FEATURES, MIN_CONFIDENCE, MODEL_PATH, PH_CROP_WHITELIST

CROP_FIL = {
    "rice": "palay", "maize": "mais", "chickpea": "garbanzos", "kidneybeans": "habichuelas",
    "pigeonpeas": "kadyos", "mothbeans": "paayap", "mungbean": "monggo", "blackgram": "itim na munggo",
    "lentil": "lentil", "pomegranate": "granada", "banana": "saging", "mango": "mangga",
    "grapes": "ubas", "watermelon": "pakwan", "muskmelon": "melon", "apple": "mansanas",
    "orange": "dalandan", "papaya": "papaya", "coconut": "niyog", "cotton": "bulak",
    "jute": "yute", "coffee": "kape",
}

def _localize_crop(text: str, crop_en: str, lang: str) -> str:
    if lang != "fil" or not crop_en:
        return text
    fil = CROP_FIL.get(crop_en.lower())
    if fil:
        import re
        text = re.sub(re.escape(crop_en), fil, text, flags=re.IGNORECASE)
    return text
from sensor_sim import simulate_sensor_values
from explain import explain_reading
from translate import translate
from geometry import sensor_count_for, suggest_sensor_points
import pandas as pd
import requests
from fastapi import HTTPException

CROP_DATA_PATH = "data_for_training/Crop_recommendation.csv"
_crop_df = None  # loaded once at startup, used for simulated readings

app = FastAPI(title="Crop Recommendation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None  # loaded once at startup


def _ensure_ollama_running():
    """Auto-launch the Ollama server if it isn't already running, so the offline
    AI explain feature is self-contained instead of depending on the user
    manually starting the Ollama app first."""
    try:
        requests.get("http://localhost:11434/api/tags", timeout=1)
        return
    except requests.RequestException:
        pass
    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except FileNotFoundError:
        return  # ponytail: ollama.exe not on PATH — explain endpoint will just 503
    for _ in range(20):
        time.sleep(0.5)
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            return
        except requests.RequestException:
            continue


@app.on_event("startup")
def startup():
    global model, _crop_df
    db.init_db()
    model = joblib.load(MODEL_PATH)
    _crop_df = pd.read_csv(CROP_DATA_PATH)
    _ensure_ollama_running()


def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
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


class ReadingIn(BaseModel):
    plot_id: str
    owner_name: str | None = None
    lat: float
    lng: float
    soil_n: float
    soil_p: float
    soil_k: float
    soil_ph: float
    air_temp_c: float
    humidity_pct: float
    rainfall_mm: float
    soil_moisture_pct: float | None = None


@app.post("/readings")
def create_reading(reading: ReadingIn):
    prediction = predict_crop(
        reading.soil_n, reading.soil_p, reading.soil_k,
        reading.air_temp_c, reading.humidity_pct, reading.soil_ph, reading.rainfall_mm,
    )
    row = reading.model_dump()
    row["timestamp"] = datetime.now(timezone.utc).isoformat()
    row["predicted_crop"] = prediction["crop"]
    row["confidence"] = prediction["confidence"]
    row["filtered"] = prediction["filtered"]
    return db.insert_reading(row)


class PlotIn(BaseModel):
    plot_id: str
    owner_name: str | None = None
    lat: float
    lng: float


@app.post("/plots")
def create_plot(plot: PlotIn):
    """Register a plot with no sensor reading yet."""
    row = plot.model_dump()
    row.update(
        soil_n=None, soil_p=None, soil_k=None, soil_ph=None,
        air_temp_c=None, humidity_pct=None, rainfall_mm=None,
        soil_moisture_pct=None, predicted_crop=None, confidence=None,
        filtered=False,
    )
    row["timestamp"] = datetime.now(timezone.utc).isoformat()
    return db.insert_reading(row)


@app.post("/readings/simulate")
def simulate_reading(plot_id: str):
    """Generate one realistic reading for an existing plot and predict on it."""
    existing = db.get_readings_for_plot(plot_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Unknown plot_id: {plot_id}")
    latest = existing[0]

    sampled = simulate_sensor_values(_crop_df)
    sampled.pop("_source_crop")
    prediction = predict_crop(
        sampled["soil_n"], sampled["soil_p"], sampled["soil_k"],
        sampled["air_temp_c"], sampled["humidity_pct"], sampled["soil_ph"], sampled["rainfall_mm"],
    )

    row = {
        "plot_id": plot_id,
        "owner_name": latest["owner_name"],
        "lat": latest["lat"],
        "lng": latest["lng"],
        **sampled,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "predicted_crop": prediction["crop"],
        "confidence": prediction["confidence"],
        "filtered": prediction["filtered"],
    }
    return db.insert_reading(row)


@app.get("/readings/{reading_id}/explain")
def explain(reading_id: int, lang: str = "en"):
    """Ask the local offline LLM (Ollama) to explain a specific reading's prediction,
    then translate it offline (NLLB-200) if lang is 'fil' or 'hil'."""
    reading = db.get_reading_by_id(reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail=f"Unknown reading id: {reading_id}")
    try:
        explanation = explain_reading(reading)
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Offline AI model (Ollama) is not reachable.")
    try:
        explanation = translate(explanation, lang)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    explanation = _localize_crop(explanation, reading.get("predicted_crop"), lang)
    return {"explanation": explanation}


@app.get("/readings")
def list_readings():
    return db.get_all_readings()


@app.get("/readings/{plot_id}")
def list_readings_for_plot(plot_id: str):
    return db.get_readings_for_plot(plot_id)


@app.get("/plots")
def list_plots():
    return db.get_latest_per_plot()


class FarmIn(BaseModel):
    farm_name: str
    owner_name: str | None = None
    hectares: float
    polygon: list[list[float]]  # [[lat, lng], ...] drawn shape vertices


class FarmUpdate(BaseModel):
    farm_name: str
    owner_name: str | None = None
    hectares: float
    polygon: list[list[float]]


class FarmerIn(BaseModel):
    name: str


class FarmAssignIn(BaseModel):
    farmer_id: str | None = None


@app.post("/farms")
def create_farm(farm: FarmIn):
    """Register a farm boundary and auto-place sensor sub-plots inside it
    (5 sensors/hectare, min 1, max 30). farm_name doubles as the farmer's
    login identifier on farmer.html, so it must be unique."""
    if db.get_farm_by_name(farm.farm_name):
        raise HTTPException(status_code=409, detail=f"Farm name already taken: {farm.farm_name}")

    farm_id = "FARM-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    sensor_count = sensor_count_for(farm.hectares)
    points = suggest_sensor_points(farm.polygon, sensor_count)

    db.insert_farm({
        "farm_id": farm_id,
        "farm_name": farm.farm_name,
        "owner_name": farm.owner_name,
        "hectares": farm.hectares,
        "polygon": json.dumps(farm.polygon),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    sensors = []
    for i, (lat, lng) in enumerate(points, start=1):
        row = {
            "plot_id": f"{farm_id}-S{i}", "owner_name": farm.owner_name, "lat": lat, "lng": lng,
            "soil_n": None, "soil_p": None, "soil_k": None, "soil_ph": None,
            "air_temp_c": None, "humidity_pct": None, "rainfall_mm": None,
            "soil_moisture_pct": None, "predicted_crop": None, "confidence": None, "filtered": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sensors.append(db.insert_reading(row))

    return {"farm_id": farm_id, "farm_name": farm.farm_name, "hectares": farm.hectares,
            "sensor_count": sensor_count, "sensors": sensors}


@app.get("/farms")
def list_farms():
    farms = db.get_all_farms()
    for f in farms:
        f["polygon"] = json.loads(f["polygon"])
    return farms


@app.put("/farms/{farm_id}")
def edit_farm(farm_id: str, body: FarmUpdate):
    existing = db.get_farm(farm_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Unknown farm_id: {farm_id}")
    other = db.get_farm_by_name(body.farm_name)
    if other and other["farm_id"] != farm_id:
        raise HTTPException(status_code=409, detail=f"Farm name already taken: {body.farm_name}")
    farm = db.update_farm(farm_id, body.farm_name, body.owner_name, body.hectares, json.dumps(body.polygon))
    farm["polygon"] = json.loads(farm["polygon"])
    return farm


@app.delete("/farms/{farm_id}")
def remove_farm(farm_id: str):
    if not db.get_farm(farm_id):
        raise HTTPException(status_code=404, detail=f"Unknown farm_id: {farm_id}")
    db.delete_farm(farm_id)
    return {"deleted": farm_id}


@app.get("/farms/{farm_id}/predict")
def predict_farm(farm_id: str):
    """Average all sensors' latest readings in the farm and predict one best crop for the whole farm."""
    if not db.get_farm(farm_id):
        raise HTTPException(status_code=404, detail=f"Unknown farm_id: {farm_id}")
    sensors = [s for s in db.get_latest_for_farm(farm_id) if s["soil_n"] is not None]
    if not sensors:
        raise HTTPException(status_code=400, detail="No sensor readings yet for this farm.")

    fields = ["soil_n", "soil_p", "soil_k", "soil_ph", "air_temp_c", "humidity_pct", "rainfall_mm"]
    avg = {f: sum(s[f] for s in sensors) / len(sensors) for f in fields}
    prediction = predict_crop(
        avg["soil_n"], avg["soil_p"], avg["soil_k"],
        avg["air_temp_c"], avg["humidity_pct"], avg["soil_ph"], avg["rainfall_mm"],
    )
    return {"farm_id": farm_id, "sensor_count": len(sensors), "averaged_readings": avg, **prediction}


@app.get("/farms/{farm_id}/explain")
def explain_farm(farm_id: str, lang: str = "en"):
    if not db.get_farm(farm_id):
        raise HTTPException(status_code=404, detail=f"Unknown farm_id: {farm_id}")
    sensors = [s for s in db.get_latest_for_farm(farm_id) if s["soil_n"] is not None]
    if not sensors:
        raise HTTPException(status_code=400, detail="No sensor readings yet for this farm.")
    fields = ["soil_n", "soil_p", "soil_k", "soil_ph", "air_temp_c", "humidity_pct", "rainfall_mm"]
    avg = {f: sum(s[f] for s in sensors) / len(sensors) for f in fields}
    prediction = predict_crop(avg["soil_n"], avg["soil_p"], avg["soil_k"],
                              avg["air_temp_c"], avg["humidity_pct"], avg["soil_ph"], avg["rainfall_mm"])
    reading = {**avg, "predicted_crop": prediction["crop"], "confidence": prediction["confidence"]}
    try:
        explanation = explain_reading(reading)
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Offline AI model (Ollama) is not reachable.")
    try:
        explanation = translate(explanation, lang)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    explanation = _localize_crop(explanation, prediction["crop"], lang)
    return {"explanation": explanation}


@app.get("/farms/by-name/{farm_name}")
def farm_by_name(farm_name: str):
    """Farmer login: look up a farm (and its sensor sub-plots) by name, no password."""
    farm = db.get_farm_by_name(farm_name)
    if not farm:
        raise HTTPException(status_code=404, detail=f"Unknown farm name: {farm_name}")
    farm["polygon"] = json.loads(farm["polygon"])
    farm["sensors"] = db.get_latest_for_farm(farm["farm_id"])
    return farm


@app.get("/farmers")
def list_farmers():
    return db.get_all_farmers()


@app.post("/farmers")
def create_farmer(body: FarmerIn):
    import uuid
    if db.get_farmer_by_name(body.name):
        raise HTTPException(status_code=409, detail=f"Farmer name already taken: {body.name}")
    return db.insert_farmer({
        "id": str(uuid.uuid4()),
        "name": body.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


@app.put("/farmers/{farmer_id}")
def update_farmer(farmer_id: str, body: FarmerIn):
    if not db.get_farmer(farmer_id):
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {farmer_id}")
    existing = db.get_farmer_by_name(body.name)
    if existing and existing["id"] != farmer_id:
        raise HTTPException(status_code=409, detail=f"Name already taken: {body.name}")
    return db.update_farmer(farmer_id, body.name)


@app.delete("/farmers/{farmer_id}")
def remove_farmer(farmer_id: str):
    if not db.get_farmer(farmer_id):
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {farmer_id}")
    db.delete_farmer(farmer_id)
    return {"deleted": farmer_id}


@app.get("/farmers/by-name/{name}")
def farmer_by_name(name: str):
    farmer = db.get_farmer_by_name(name)
    if not farmer:
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {name}")
    farms = [f for f in db.get_all_farms() if f.get("farmer_id") == farmer["id"]]
    for f in farms:
        f["polygon"] = json.loads(f["polygon"]) if isinstance(f["polygon"], str) else f["polygon"]
        f["sensors"] = db.get_latest_for_farm(f["farm_id"])
    return {**farmer, "farms": farms}


@app.put("/farms/{farm_id}/farmer")
def assign_farmer(farm_id: str, body: FarmAssignIn):
    if not db.get_farm(farm_id):
        raise HTTPException(status_code=404, detail=f"Unknown farm: {farm_id}")
    if body.farmer_id and not db.get_farmer(body.farmer_id):
        raise HTTPException(status_code=404, detail=f"Unknown farmer: {body.farmer_id}")
    db.assign_farm_to_farmer(farm_id, body.farmer_id)
    return {"farm_id": farm_id, "farmer_id": body.farmer_id}


# ponytail: mounted last so API routes above always win over static files of the same path
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
