import os
import shutil
import subprocess
import time

import pytest
import requests

EMULATOR_HOST = "localhost:8080"
EMULATOR_PROJECT = "bukid-ac67d"

# On Windows, the Firebase CLI is installed as a `.cmd`/`.ps1` shim, and
# subprocess.Popen's CreateProcess-based lookup does not resolve PATHEXT
# shims the way a shell would. shutil.which() applies PATHEXT resolution
# on Windows (and is a no-op passthrough elsewhere), so this keeps the
# fixture portable across platforms.
FIREBASE_BIN = shutil.which("firebase") or "firebase"


@pytest.fixture(scope="session", autouse=True)
def firestore_emulator():
    os.environ["FIRESTORE_EMULATOR_HOST"] = EMULATOR_HOST
    os.environ["GOOGLE_CLOUD_PROJECT"] = EMULATOR_PROJECT

    proc = subprocess.Popen(
        [FIREBASE_BIN, "emulators:start", "--only", "firestore", "--project", EMULATOR_PROJECT],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            requests.get(f"http://{EMULATOR_HOST}/")
            break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("Firestore emulator did not start within 30s")

    yield

    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture
def clear_firestore():
    yield
    requests.delete(
        f"http://{EMULATOR_HOST}/emulator/v1/projects/{EMULATOR_PROJECT}/databases/(default)/documents"
    )
