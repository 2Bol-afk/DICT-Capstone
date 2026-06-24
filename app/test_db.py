import os

import requests


def test_emulator_starts():
    assert os.environ["FIRESTORE_EMULATOR_HOST"] == "localhost:8080"

    # Independently verify the emulator is actually listening, rather than
    # just trusting that the fixture set the env var. A silent emulator
    # startup failure after the env var was set should fail this test.
    response = requests.get(f"http://{os.environ['FIRESTORE_EMULATOR_HOST']}/")
    assert response.status_code == 200
