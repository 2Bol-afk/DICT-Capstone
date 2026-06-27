import os

import firebase_admin
import google.auth.credentials
from firebase_admin import credentials, firestore

_app = None
_db = None


class _EmulatorCredential(credentials.Base):
    """Satisfies firebase_admin's credential interface without touching
    Application Default Credentials. firebase_admin.initialize_app() always
    lazily resolves real ADC via google.auth.default() when no explicit
    credential is given — even with FIRESTORE_EMULATOR_HOST set — so a real
    GCP login (or GOOGLE_APPLICATION_CREDENTIALS) would otherwise be required
    just to talk to the local emulator."""

    def get_credential(self):
        return google.auth.credentials.AnonymousCredentials()


def get_db():
    global _app, _db
    if _db is not None:
        return _db

    if os.environ.get("FIRESTORE_EMULATOR_HOST"):
        # ponytail: emulator mode needs no real credentials — firebase_admin
        # still requires an app, so initialize with a dummy project id matching
        # GOOGLE_CLOUD_PROJECT.
        _app = firebase_admin.initialize_app(
            _EmulatorCredential(),
            options={"projectId": os.environ["GOOGLE_CLOUD_PROJECT"]},
        )
    else:
        cred_path = os.path.join(os.path.dirname(__file__), "firebase-service-account.json")
        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred)

    _db = firestore.client()
    return _db
