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
    readings = get_db().collection("readings").where("plot_id", ">=", f"{farm_id}-").where("plot_id", "<", f"{farm_id}.").stream()
    for r in readings:
        r.reference.delete()


def insert_farmer(farmer: dict) -> dict:
    raise NotImplementedError("migrated in Task 3")


def get_farmer(farmer_id: str) -> dict | None:
    raise NotImplementedError("migrated in Task 3")


def get_farmer_by_name(name: str) -> dict | None:
    raise NotImplementedError("migrated in Task 3")


def get_all_farmers() -> list[dict]:
    raise NotImplementedError("migrated in Task 3")


def update_farmer(farmer_id: str, name: str) -> dict | None:
    raise NotImplementedError("migrated in Task 3")


def delete_farmer(farmer_id: str):
    raise NotImplementedError("migrated in Task 3")


def set_farmer_password(farmer_id: str, password_hash: str):
    raise NotImplementedError("migrated in Task 3")


def assign_farm_to_farmer(farm_id: str, farmer_id: str | None):
    raise NotImplementedError("migrated in Task 3")


def insert_reading(row: dict) -> dict:
    raise NotImplementedError("migrated in Task 4")


def get_reading_by_id(row_id) -> dict | None:
    raise NotImplementedError("migrated in Task 4")


def get_all_readings() -> list[dict]:
    raise NotImplementedError("migrated in Task 4")


def get_readings_for_plot(plot_id: str) -> list[dict]:
    raise NotImplementedError("migrated in Task 4")


def get_latest_per_plot() -> list[dict]:
    raise NotImplementedError("migrated in Task 4")


def get_latest_for_farm(farm_id: str) -> list[dict]:
    raise NotImplementedError("migrated in Task 4")
