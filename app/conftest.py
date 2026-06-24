import os
import shutil
import socket
import subprocess
import time

import psutil
import pytest
import requests

EMULATOR_HOST = "localhost:8080"
EMULATOR_PROJECT = "bukid-ac67d"
EMULATOR_PORT = 8080

# On Windows, the Firebase CLI is installed as a `.cmd`/`.ps1` shim, and
# subprocess.Popen's CreateProcess-based lookup does not resolve PATHEXT
# shims the way a shell would. shutil.which() applies PATHEXT resolution
# on Windows (and is a no-op passthrough elsewhere), so this keeps the
# fixture portable across platforms.
#
# If firebase isn't found on PATH at all, fail loudly here rather than
# silently falling back to the literal string "firebase" — that fallback
# would just defer the same WinError 2 failure into the fixture's
# subprocess.Popen call, with a less informative stack trace.
FIREBASE_BIN = shutil.which("firebase")
if FIREBASE_BIN is None:
    raise RuntimeError(
        "firebase CLI not found on PATH — install via `npm install -g firebase-tools`"
    )


def _port_is_bound(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


def _kill_process_tree(pid):
    """Kill pid and all its descendants (Windows: firebase CLI spawns a
    java.exe emulator child that proc.terminate() alone never reaches)."""
    try:
        parent = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return
    procs = parent.children(recursive=True) + [parent]
    for p in procs:
        try:
            p.terminate()
        except psutil.NoSuchProcess:
            pass
    gone, alive = psutil.wait_procs(procs, timeout=10)
    for p in alive:
        try:
            p.kill()
        except psutil.NoSuchProcess:
            pass


def _kill_whatever_is_on_port(port):
    """Self-heal: if a prior crashed run left an orphaned emulator listening
    on our port, find and kill it before starting a fresh instance."""
    for conn in psutil.net_connections(kind="tcp"):
        if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
            if conn.pid:
                _kill_process_tree(conn.pid)


@pytest.fixture(scope="session", autouse=True)
def firestore_emulator():
    if _port_is_bound(EMULATOR_PORT):
        _kill_whatever_is_on_port(EMULATOR_PORT)

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
        _kill_process_tree(proc.pid)
        raise RuntimeError("Firestore emulator did not start within 30s")

    yield

    _kill_process_tree(proc.pid)


@pytest.fixture
def clear_firestore():
    yield
    requests.delete(
        f"http://{EMULATOR_HOST}/emulator/v1/projects/{EMULATOR_PROJECT}/databases/(default)/documents"
    )
