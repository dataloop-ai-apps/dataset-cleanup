"""
Per-user Dataloop SDK instances.

The app is served as a trusted DPK, so piper proxies it on the gateway's own origin.
The browser attaches the user's JWT cookie and the gateway's auth chain turns it into
`Authorization: Bearer <user jwt>` before the request reaches this pod. This module is
the single place that turns that header into an SDK acting as the calling user.

Every call that carries identity must go through the SDK returned here. The global
`dtlpy` singleton is only used for identity-free helpers (Filters, enums, exceptions).

Instances are cached per token because `login_token()` costs a `GET /users/me` round
trip; the cache entry expires with the token. The token is removed from disk right after
login so a user's JWT is not left at rest in the pod's filesystem.
"""
import asyncio
import hashlib
import logging
import os
import shutil
import tempfile
import threading
import time
from typing import Dict, Optional, Tuple

import jwt as pyjwt
from fastapi import HTTPException, Request

logger = logging.getLogger('[CLEANUP AUTH]')

_MAX_SESSIONS = 128
_EXPIRY_SKEW = 30  # refuse tokens this close to (or past) expiry, in seconds

_sessions: Dict[str, Tuple[object, float, str]] = {}  # token_hash -> (sdk, exp, cookie_dir)
_lock = threading.Lock()

# Successful access checks, keyed by (token_hash, dataset_id) -> expiry timestamp.
# The panel polls the status endpoints every second; this avoids a platform round trip each time.
_access_cache: Dict[Tuple[str, str], float] = {}
_access_lock = threading.Lock()
_ACCESS_TTL = 60  # seconds; short enough to respect revocations promptly
_ACCESS_CACHE_MAX = 2048


def _token_expiry(token: str) -> float:
    """Expiry of the JWT as a unix timestamp. Only the claim is read to size the cache;
    the platform verifies the signature on every call made with this token."""
    try:
        # oxsec-disable jwt-signature-disabled - only reading 'exp' for cache TTL; the
        # platform validates the signature on every API call made with this token.
        claims = pyjwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        return float(claims.get("exp", 0))
    except Exception:
        return 0.0


def _evict_locked(token_hash: str):
    entry = _sessions.pop(token_hash, None)
    if entry is not None:
        shutil.rmtree(entry[2], ignore_errors=True)


def _purge_expired_locked():
    now = time.time()
    for token_hash in [h for h, (_, exp, _) in _sessions.items() if exp <= now]:
        _evict_locked(token_hash)


def _build_sdk(token: str):
    """Create an isolated SDK instance authenticated as the token's user."""
    import dtlpy as dl
    from dtlpy.new_instance import Dtlpy

    # Own cookie file, otherwise instances share (and overwrite) the default ~/.dataloop cookie.
    cookie_dir = tempfile.mkdtemp(prefix="dl-user-sdk-")
    cookie_path = os.path.join(cookie_dir, "cookie.json")
    try:
        sdk = Dtlpy(cookie_filepath=cookie_path)
        sdk.setenv(dl.environment())
        sdk.login_token(token)
        # The client keeps the token in memory; don't leave it on disk for the session's life.
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
        return sdk, cookie_dir
    except Exception:
        shutil.rmtree(cookie_dir, ignore_errors=True)
        raise


def get_sdk_for_token(token: str):
    """Return a cached per-user SDK for the given JWT, creating one if needed."""
    exp = _token_expiry(token)
    if exp and exp - _EXPIRY_SKEW <= time.time():
        raise HTTPException(status_code=401, detail="Token expired")

    token_hash = hashlib.sha256(token.encode()).hexdigest()

    with _lock:
        _purge_expired_locked()
        entry = _sessions.get(token_hash)
        if entry is not None:
            return entry[0]

    # Build outside the lock: login_token() does a network round trip.
    try:
        sdk, cookie_dir = _build_sdk(token)
        sdk._cache_key = token_hash
    except Exception as e:
        logger.warning(f"Failed to authenticate user token: {e}")
        raise HTTPException(status_code=401, detail="Invalid or unauthorized token")

    with _lock:
        existing = _sessions.get(token_hash)
        if existing is not None:
            shutil.rmtree(cookie_dir, ignore_errors=True)
            return existing[0]
        if len(_sessions) >= _MAX_SESSIONS:
            _evict_locked(min(_sessions, key=lambda h: _sessions[h][1]))
        _sessions[token_hash] = (sdk, exp or (time.time() + 3600), cookie_dir)

    return sdk


def extract_token(request: Request) -> Optional[str]:
    """The user's JWT from `Authorization: Bearer <jwt>`, falling back to the raw `JWT` cookie."""
    auth_header = request.headers.get("authorization") or ""
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()
    return request.cookies.get("JWT")


def get_user_sdk(request: Request):
    """FastAPI dependency: an SDK instance acting as the calling user."""
    token = extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing user credentials")
    return get_sdk_for_token(token)


def verify_dataset_access(sdk, dataset_id: str):
    """Raise 403 unless the calling user can read the dataset.

    Exported data is cached per dataset and shared between users, so permission has to be
    established before a caller reaches that cache. The check is a read performed as the
    user: if the platform refuses, so do we.
    """
    token_hash = getattr(sdk, '_cache_key', None)
    cache_key = (token_hash, dataset_id)
    if token_hash:
        with _access_lock:
            if _access_cache.get(cache_key, 0) > time.time():
                return
    try:
        sdk.datasets.get(dataset_id=dataset_id)
    except Exception as e:
        logger.info(f"Denying access to dataset {dataset_id}: {e}")
        raise HTTPException(status_code=403, detail=f"No access to dataset {dataset_id}")
    if token_hash:
        with _access_lock:
            if len(_access_cache) >= _ACCESS_CACHE_MAX:
                del _access_cache[min(_access_cache, key=_access_cache.__getitem__)]
            _access_cache[cache_key] = time.time() + _ACCESS_TTL


async def async_verify_dataset_access(sdk, dataset_id: str):
    """`verify_dataset_access` off the event loop (the SDK calls are blocking HTTP)."""
    await asyncio.get_running_loop().run_in_executor(None, verify_dataset_access, sdk, dataset_id)
