def test_emulator_starts():
    import os
    assert os.environ["FIRESTORE_EMULATOR_HOST"] == "localhost:8080"


def test_farm_crud(clear_firestore):
    import db
    db.init_db()

    farm = db.insert_farm({
        "farm_id": "FARM-1",
        "farm_name": "Test Farm",
        "owner_name": "Juan",
        "hectares": 3.0,
        "polygon": "[[0,0],[1,0],[1,1]]",
        "created_at": "2026-06-25T00:00:00Z",
    })
    assert farm["farm_id"] == "FARM-1"
    assert farm["farm_name"] == "Test Farm"

    fetched = db.get_farm("FARM-1")
    assert fetched["owner_name"] == "Juan"

    by_name = db.get_farm_by_name("Test Farm")
    assert by_name["farm_id"] == "FARM-1"

    all_farms = db.get_all_farms()
    assert len(all_farms) == 1

    updated = db.update_farm("FARM-1", "Renamed Farm", "Juan", 5.0, "[[0,0]]")
    assert updated["farm_name"] == "Renamed Farm"
    assert updated["hectares"] == 5.0

    db.delete_farm("FARM-1")
    assert db.get_farm("FARM-1") is None


def test_delete_farm_cascades_readings(clear_firestore):
    import db
    db.init_db()

    farm = db.insert_farm({
        "farm_id": "FARM-CASCADE",
        "farm_name": "Cascade Farm",
        "owner_name": "Juan",
        "hectares": 1.0,
        "polygon": "[]",
        "created_at": "2026-06-25T00:00:00Z",
    })
    farm_id = farm["farm_id"]
    plot_id = f"{farm_id}-S1"

    db.insert_reading({
        "plot_id": plot_id, "owner_name": "Juan", "lat": 14.5, "lng": 121.0,
        "timestamp": "2026-06-25T00:00:00Z", "soil_n": 10, "soil_p": 5, "soil_k": 8,
        "soil_ph": 6.5, "air_temp_c": 28.0, "humidity_pct": 70.0, "rainfall_mm": 100.0,
        "soil_moisture_pct": 40.0, "predicted_crop": "rice", "confidence": 0.9, "filtered": False,
    })

    assert len(db.get_readings_for_plot(plot_id)) == 1

    db.delete_farm(farm_id)

    assert db.get_farm(farm_id) is None
    assert db.get_readings_for_plot(plot_id) == []


def test_farmer_crud(clear_firestore):
    import db
    db.init_db()

    farmer = db.insert_farmer({
        "id": "FARMER-1",
        "name": "Maria",
        "created_at": "2026-06-25T00:00:00Z",
        "password_hash": None,
        "role": "farmer",
    })
    assert farmer["id"] == "FARMER-1"
    assert farmer["name"] == "Maria"

    fetched = db.get_farmer("FARMER-1")
    assert fetched["name"] == "Maria"

    by_name = db.get_farmer_by_name("Maria")
    assert by_name["id"] == "FARMER-1"

    db.set_farmer_password("FARMER-1", "salt$hash")
    assert db.get_farmer("FARMER-1")["password_hash"] == "salt$hash"

    farm = db.insert_farm({
        "farm_id": "FARM-2",
        "farm_name": "Maria's Farm",
        "owner_name": "Maria",
        "hectares": 2.0,
        "polygon": "[]",
        "created_at": "2026-06-25T00:00:00Z",
    })
    db.assign_farm_to_farmer(farm["farm_id"], "FARMER-1")
    assert db.get_farm("FARM-2")["farmer_id"] == "FARMER-1"

    all_farmers = db.get_all_farmers()
    assert len(all_farmers) == 1
    assert all_farmers[0]["farm_count"] == 1

    updated = db.update_farmer("FARMER-1", "Maria Updated")
    assert updated["name"] == "Maria Updated"

    db.delete_farmer("FARMER-1")
    assert db.get_farmer("FARMER-1") is None
    assert db.get_farm("FARM-2")["farmer_id"] is None


def test_readings_crud(clear_firestore):
    import db
    db.init_db()

    r1 = db.insert_reading({
        "plot_id": "FARM-3-S1", "owner_name": "Pedro", "lat": 14.5, "lng": 121.0,
        "timestamp": "2026-06-25T00:00:00Z", "soil_n": 10, "soil_p": 5, "soil_k": 8,
        "soil_ph": 6.5, "air_temp_c": 28.0, "humidity_pct": 70.0, "rainfall_mm": 100.0,
        "soil_moisture_pct": 40.0, "predicted_crop": "rice", "confidence": 0.9, "filtered": False,
    })
    assert r1["plot_id"] == "FARM-3-S1"
    assert "id" in r1

    r2 = db.insert_reading({
        "plot_id": "FARM-3-S1", "owner_name": "Pedro", "lat": 14.5, "lng": 121.0,
        "timestamp": "2026-06-25T01:00:00Z", "soil_n": 12, "soil_p": 6, "soil_k": 9,
        "soil_ph": 6.6, "air_temp_c": 29.0, "humidity_pct": 71.0, "rainfall_mm": 101.0,
        "soil_moisture_pct": 41.0, "predicted_crop": "rice", "confidence": 0.91, "filtered": False,
    })

    fetched = db.get_reading_by_id(r1["id"])
    assert fetched["soil_n"] == 10

    for_plot = db.get_readings_for_plot("FARM-3-S1")
    assert len(for_plot) == 2
    assert for_plot[0]["timestamp"] == "2026-06-25T01:00:00Z"  # newest first

    latest_per_plot = db.get_latest_per_plot()
    assert len(latest_per_plot) == 1
    assert latest_per_plot[0]["timestamp"] == "2026-06-25T01:00:00Z"

    latest_for_farm = db.get_latest_for_farm("FARM-3")
    assert len(latest_for_farm) == 1
    assert latest_for_farm[0]["plot_id"] == "FARM-3-S1"

    all_readings = db.get_all_readings()
    assert len(all_readings) == 2
