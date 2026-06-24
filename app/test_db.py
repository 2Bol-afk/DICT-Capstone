def test_emulator_starts():
    import os
    assert os.environ["FIRESTORE_EMULATOR_HOST"] == "localhost:8080"
