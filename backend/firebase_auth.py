"""Verifies Firebase Auth ID tokens without pulling in the full firebase-admin SDK.

A Firebase ID token is a standard RS256 JWT signed by Google. We fetch
Google's public certs for the Firebase token signer, cache them for their
stated lifetime, and let PyJWT check the signature, issuer, audience, and
expiry. No service account key needed - only the (public) project ID.
"""
import time
from typing import Dict

import httpx
import jwt
from cryptography.x509 import load_pem_x509_certificate

from backend import config

CERTS_URL = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"

_certs_cache: Dict[str, str] = {}
_certs_expire_at = 0.0


async def _fetch_certs(force: bool = False) -> Dict[str, str]:
    global _certs_cache, _certs_expire_at
    if not force and _certs_cache and time.time() < _certs_expire_at:
        return _certs_cache
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(CERTS_URL)
        response.raise_for_status()
    _certs_cache = response.json()
    max_age = 3600
    for part in response.headers.get("cache-control", "").split(","):
        part = part.strip()
        if part.startswith("max-age="):
            max_age = int(part.split("=", 1)[1])
    _certs_expire_at = time.time() + max_age
    return _certs_cache


async def verify_firebase_id_token(id_token: str) -> Dict:
    """Verifies a Firebase Auth ID token and returns its decoded claims.

    Raises jwt.InvalidTokenError (or a subclass) on any verification failure.
    """
    if not config.FIREBASE_PROJECT_ID:
        raise RuntimeError("FIREBASE_PROJECT_ID is not configured on this server.")

    kid = jwt.get_unverified_header(id_token).get("kid")
    certs = await _fetch_certs()
    if kid not in certs:
        certs = await _fetch_certs(force=True)  # key rotated since our last fetch
    if kid not in certs:
        raise jwt.InvalidTokenError("Unknown signing key.")

    public_key = load_pem_x509_certificate(certs[kid].encode()).public_key()
    return jwt.decode(
        id_token,
        key=public_key,
        algorithms=["RS256"],
        audience=config.FIREBASE_PROJECT_ID,
        issuer=f"https://securetoken.google.com/{config.FIREBASE_PROJECT_ID}",
    )
