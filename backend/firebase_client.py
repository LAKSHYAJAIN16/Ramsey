"""Lazy, single Firebase Admin app instance, shared by anything that needs
service-account-authenticated access to Firebase (currently: Firestore).
"""
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore

from backend import config

_app: Optional[firebase_admin.App] = None


def _ensure_app() -> firebase_admin.App:
    global _app
    if _app is not None:
        return _app
    key_path = Path(config.FIREBASE_SERVICE_ACCOUNT_PATH)
    if not key_path.is_file():
        raise RuntimeError(
            f"Firebase service account key not found at {key_path}. Download one from "
            "Firebase Console -> Project settings (gear icon) -> Service accounts -> "
            "Generate new private key, and save it there (or point FIREBASE_SERVICE_ACCOUNT_PATH at it)."
        )
    _app = firebase_admin.initialize_app(credentials.Certificate(str(key_path)))
    return _app


def get_firestore_client():
    _ensure_app()
    return firestore.client()
