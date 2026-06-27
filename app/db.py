from firestore_client import get_db

FARMS = "farms"


def init_db():
    get_db()  # ponytail: Firestore has no schema to create — just confirm connectivity


def insert_farm(farm: dict) -> dict:
    db = get_db()
    db.collection(FARMS).document(farm["farm_id"]).set({
        "farm_name": farm["farm_name"],
        "owner_name": farm["owner_name"],
        "hectares": farm["hectares"],
        "polygon": farm["polygon"],
        "created_at": farm["created_at"],
        "farmer_id": farm.get("farmer_id"),
    })
    return get_farm(farm["farm_id"])


def get_farm(farm_id: str) -> dict | None:
    doc = get_db().collection(FARMS).document(farm_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["farm_id"] = doc.id
    return data


def get_farm_by_name(farm_name: str) -> dict | None:
    docs = list(get_db().collection(FARMS).where("farm_name", "==", farm_name).limit(1).stream())
    if not docs:
        return None
    data = docs[0].to_dict()
    data["farm_id"] = docs[0].id
    return data


def get_all_farms() -> list[dict]:
    results = []
    for doc in get_db().collection(FARMS).order_by("created_at", direction="DESCENDING").stream():
        data = doc.to_dict()
        data["farm_id"] = doc.id
        results.append(data)
    return results


def update_farm(farm_id: str, farm_name: str, owner_name: str | None, hectares: float, polygon: str) -> dict | None:
    get_db().collection(FARMS).document(farm_id).update({
        "farm_name": farm_name,
        "owner_name": owner_name,
        "hectares": hectares,
        "polygon": polygon,
    })
    return get_farm(farm_id)


def delete_farm(farm_id: str):
    get_db().collection(FARMS).document(farm_id).delete()
    # Cascade-delete this farm's readings via a string range query: plot_ids follow the
    # "{farm_id}-S{n}" convention, and "-" (0x2D) sorts immediately before "." (0x2E) in
    # Firestore's string ordering, so [f"{farm_id}-", f"{farm_id}.") tightly bounds every
    # plot_id belonging to this farm without matching farm_ids that share a prefix.
    readings = get_db().collection("readings").where("plot_id", ">=", f"{farm_id}-").where("plot_id", "<", f"{farm_id}.").stream()
    for r in readings:
        r.reference.delete()


FARMERS = "farmers"


def insert_farmer(farmer: dict) -> dict:
    get_db().collection(FARMERS).document(farmer["id"]).set({
        "name": farmer["name"],
        "created_at": farmer["created_at"],
        "password_hash": farmer.get("password_hash"),
        "role": farmer.get("role", "farmer"),
    })
    return get_farmer(farmer["id"])


def get_farmer(farmer_id: str) -> dict | None:
    doc = get_db().collection(FARMERS).document(farmer_id).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def get_farmer_by_name(name: str) -> dict | None:
    docs = list(get_db().collection(FARMERS).where("name", "==", name).limit(1).stream())
    if not docs:
        return None
    data = docs[0].to_dict()
    data["id"] = docs[0].id
    return data


def get_all_farmers() -> list[dict]:
    results = []
    for doc in get_db().collection(FARMERS).order_by("created_at", direction="DESCENDING").stream():
        data = doc.to_dict()
        data["id"] = doc.id
        farm_count = len(list(get_db().collection(FARMS).where("farmer_id", "==", doc.id).stream()))
        data["farm_count"] = farm_count
        results.append(data)
    return results


def update_farmer(farmer_id: str, name: str) -> dict | None:
    get_db().collection(FARMERS).document(farmer_id).update({"name": name})
    return get_farmer(farmer_id)


def delete_farmer(farmer_id: str):
    farms = get_db().collection(FARMS).where("farmer_id", "==", farmer_id).stream()
    for f in farms:
        f.reference.update({"farmer_id": None})
    get_db().collection(FARMERS).document(farmer_id).delete()


def set_farmer_password(farmer_id: str, password_hash: str):
    get_db().collection(FARMERS).document(farmer_id).update({"password_hash": password_hash})


def assign_farm_to_farmer(farm_id: str, farmer_id: str | None):
    get_db().collection(FARMS).document(farm_id).update({"farmer_id": farmer_id})


READINGS = "readings"


def insert_reading(row: dict) -> dict:
    doc_ref = get_db().collection(READINGS).document()
    doc_ref.set({
        "plot_id": row["plot_id"], "owner_name": row["owner_name"],
        "lat": row["lat"], "lng": row["lng"], "timestamp": row["timestamp"],
        "soil_n": row["soil_n"], "soil_p": row["soil_p"], "soil_k": row["soil_k"],
        "soil_ph": row["soil_ph"], "air_temp_c": row["air_temp_c"],
        "humidity_pct": row["humidity_pct"], "rainfall_mm": row["rainfall_mm"],
        "soil_moisture_pct": row["soil_moisture_pct"],
        "predicted_crop": row["predicted_crop"], "confidence": row["confidence"],
        "filtered": bool(row["filtered"]),
    })
    return get_reading_by_id(doc_ref.id)


def get_reading_by_id(row_id: str) -> dict | None:
    doc = get_db().collection(READINGS).document(str(row_id)).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def get_all_readings() -> list[dict]:
    results = []
    for doc in get_db().collection(READINGS).order_by("timestamp", direction="DESCENDING").stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def get_readings_for_plot(plot_id: str) -> list[dict]:
    results = []
    query = (
        get_db().collection(READINGS)
        .where("plot_id", "==", plot_id)
        .order_by("timestamp", direction="DESCENDING")
    )
    for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def _latest_by_plot(readings: list[dict]) -> list[dict]:
    # ponytail: Firestore has no SQL-style GROUP BY/MAX JOIN — reduce in Python.
    # Fine at co-op scale (hundreds of readings, not millions).
    latest: dict[str, dict] = {}
    for r in readings:
        existing = latest.get(r["plot_id"])
        if existing is None or r["timestamp"] > existing["timestamp"]:
            latest[r["plot_id"]] = r
    return list(latest.values())


def get_latest_per_plot() -> list[dict]:
    return _latest_by_plot(get_all_readings())


def get_latest_for_farm(farm_id: str) -> list[dict]:
    all_readings = get_all_readings()
    for_farm = [r for r in all_readings if r["plot_id"].startswith(f"{farm_id}-")]
    return _latest_by_plot(for_farm)
