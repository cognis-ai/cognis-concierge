"""Cognis Concierge auth dependency.

Verifies a Clerk-issued JWT presented via ``Authorization: Bearer <jwt>``,
maps the JWT's ``org_id`` claim to a Letta ``organization_id`` via the
``organizations.cognis_org_id`` column added by the c0951a13aa55 migration,
and stashes the resolved ids on ``request.state`` for downstream routes.

This module is a FastAPI dependency only — it does NOT mutate any
upstream router. Mount via ``Depends(cognis_auth_dependency)`` from
``app.py`` on routes that need org scope.

Configuration (env):
    JWT_PUBLIC_KEY_URL   Clerk JWKS URL, e.g.
                         ``https://<your-clerk-frontend-api>/.well-known/jwks.json``
    JWT_ISSUER           (optional) expected ``iss`` claim
                         (e.g. ``https://<your-clerk-frontend-api>``)
    JWT_AUDIENCE         (optional) expected ``aud`` claim

If ``JWT_PUBLIC_KEY_URL`` is not set, the dependency is a no-op pass-through
(useful for local upstream-parity dev). Production deployments MUST set it.

Implementation note: deliberately built on stdlib + ``cryptography`` (already
a transitive dep) + ``httpx`` (already a Letta dep) to avoid adding a
JWT library. Supports RS256/RS384/RS512 keys — the algorithms Clerk uses.
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from typing import Any, Optional

import httpx
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives.hashes import SHA256, SHA384, SHA512
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from letta.log import get_logger
from letta.server.db import db_registry

logger = get_logger(__name__)

_JWKS_CACHE: dict[str, Any] = {"keys": None, "fetched_at": 0.0}
_JWKS_CACHE_TTL_SECONDS = 600  # 10 minutes
_JWKS_LOCK = threading.Lock()

_HASH_ALGORITHMS = {"RS256": SHA256(), "RS384": SHA384(), "RS512": SHA512()}

security = HTTPBearer(auto_error=False)


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + padding)


def _fetch_jwks(jwks_url: str) -> dict[str, Any]:
    now = time.time()
    with _JWKS_LOCK:
        if _JWKS_CACHE["keys"] is not None and now - _JWKS_CACHE["fetched_at"] < _JWKS_CACHE_TTL_SECONDS:
            return _JWKS_CACHE["keys"]
        try:
            response = httpx.get(jwks_url, timeout=5.0)
            response.raise_for_status()
            jwks = response.json()
        except Exception as exc:  # noqa: BLE001 — re-raise as HTTPException
            logger.error("Failed to fetch Clerk JWKS from %s: %s", jwks_url, exc)
            raise HTTPException(status_code=503, detail="Auth service unavailable") from exc
        _JWKS_CACHE["keys"] = jwks
        _JWKS_CACHE["fetched_at"] = now
        return jwks


def _public_key_from_jwk(jwk: dict[str, Any]):
    n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
    e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
    return RSAPublicNumbers(e=e, n=n).public_key()


def _verify_jwt(token: str, jwks_url: str, issuer: Optional[str], audience: Optional[str]) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Malformed bearer token") from exc

    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        signature = _b64url_decode(signature_b64)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Malformed bearer token") from exc

    alg = header.get("alg")
    if alg not in _HASH_ALGORITHMS:
        raise HTTPException(status_code=401, detail=f"Unsupported JWT alg: {alg!r}")

    kid = header.get("kid")
    jwks = _fetch_jwks(jwks_url)
    jwk_match = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if jwk_match is None:
        # Force-refresh once in case the signing key was rotated.
        with _JWKS_LOCK:
            _JWKS_CACHE["fetched_at"] = 0.0
        jwks = _fetch_jwks(jwks_url)
        jwk_match = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if jwk_match is None:
        raise HTTPException(status_code=401, detail="Unknown JWT signing key")

    public_key = _public_key_from_jwk(jwk_match)
    signed_input = f"{header_b64}.{payload_b64}".encode("ascii")
    try:
        public_key.verify(signature, signed_input, PKCS1v15(), _HASH_ALGORITHMS[alg])
    except Exception as exc:  # noqa: BLE001 — InvalidSignature
        raise HTTPException(status_code=401, detail="Invalid JWT signature") from exc

    now = int(time.time())
    if "exp" in payload and now >= int(payload["exp"]):
        raise HTTPException(status_code=401, detail="JWT expired")
    if "nbf" in payload and now < int(payload["nbf"]):
        raise HTTPException(status_code=401, detail="JWT not yet valid")
    if issuer and payload.get("iss") != issuer:
        raise HTTPException(status_code=401, detail="JWT issuer mismatch")
    if audience and payload.get("aud") not in (audience, [audience]):
        raise HTTPException(status_code=401, detail="JWT audience mismatch")

    return payload


async def _resolve_letta_org_id(cognis_org_id: str) -> Optional[str]:
    """Look up the Letta organization row whose ``cognis_org_id`` matches."""
    from sqlalchemy import select

    from letta.orm.organization import Organization

    async with db_registry.async_session() as session:
        result = await session.execute(select(Organization.id).where(Organization.cognis_org_id == cognis_org_id))
        return result.scalar_one_or_none()


async def cognis_auth_dependency(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> None:
    """FastAPI dependency: verify Clerk JWT, set request.state.{actor_id,organization_id}.

    No-op if ``JWT_PUBLIC_KEY_URL`` is unset (preserves upstream parity for
    local dev). In production this env MUST be set.
    """
    jwks_url = os.environ.get("JWT_PUBLIC_KEY_URL")
    if not jwks_url:
        return  # auth disabled — upstream-parity mode

    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    issuer = os.environ.get("JWT_ISSUER")
    audience = os.environ.get("JWT_AUDIENCE")
    payload = _verify_jwt(credentials.credentials, jwks_url, issuer, audience)

    cognis_org_id = payload.get("org_id")
    if not cognis_org_id:
        raise HTTPException(status_code=401, detail="JWT missing org_id claim")

    letta_org_id = await _resolve_letta_org_id(cognis_org_id)
    if letta_org_id is None:
        raise HTTPException(status_code=401, detail="No Letta organization mapped to this Cognis org")

    # actor_id falls back to the JWT subject ("sub") when no user-level
    # mapping is configured. Downstream routes that need a real Letta user
    # id can still call into the existing api_key_to_user flow.
    request.state.actor_id = payload.get("sub") or letta_org_id
    request.state.organization_id = letta_org_id
    request.state.cognis_org_id = cognis_org_id
