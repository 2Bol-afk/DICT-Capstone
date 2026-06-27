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
