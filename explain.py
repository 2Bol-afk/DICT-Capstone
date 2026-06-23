import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
# ponytail: qwen2.5:3b is what's actually pulled on this machine; swap to a
# Gemma tag (e.g. "gemma2:2b") once pulled — endpoint/prompt don't change.
MODEL = "qwen2.5:3b"

PROMPT_TEMPLATE = """You are an agricultural advisor for a Filipino farmer cooperative.
Explain briefly (2-3 sentences, simple English) why the recommended crop fits this plot's
sensor readings. Be concrete about which readings support the choice.

Recommended crop: {crop}
Confidence: {confidence:.0%}
Soil N: {soil_n} mg/kg, P: {soil_p} mg/kg, K: {soil_k} mg/kg
Soil pH: {soil_ph}
Air temperature: {air_temp_c}°C
Humidity: {humidity_pct}%
Rainfall: {rainfall_mm} mm
"""


def explain_reading(reading: dict) -> str:
    """Ask the local Ollama model to explain a prediction. Raises requests.RequestException if Ollama is unreachable."""
    if not reading.get("predicted_crop"):
        return "No confident crop match for this reading, so there's nothing to explain yet."

    prompt = PROMPT_TEMPLATE.format(
        crop=reading["predicted_crop"],
        confidence=reading["confidence"] or 0,
        soil_n=reading["soil_n"], soil_p=reading["soil_p"], soil_k=reading["soil_k"],
        soil_ph=reading["soil_ph"], air_temp_c=reading["air_temp_c"],
        humidity_pct=reading["humidity_pct"], rainfall_mm=reading["rainfall_mm"],
    )
    resp = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["response"].strip()


if __name__ == "__main__":
    demo_reading = {
        "predicted_crop": "rice", "confidence": 0.92,
        "soil_n": 90, "soil_p": 42, "soil_k": 43, "soil_ph": 6.5,
        "air_temp_c": 20.9, "humidity_pct": 82.0, "rainfall_mm": 202.9,
    }
    print(explain_reading(demo_reading))
