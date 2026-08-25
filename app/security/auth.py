"""
Authentication & masking middleware.

Verifies JWTs issued by ``app.core.security``, resolves the caller's
``UserRole`` onto ``request.state``, and masks pricing payloads for
unauthorized roles (NCA ECC data-minimization).
"""

import os
from typing import Optional

import jwt
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.security import ALGORITHM, SECRET_KEY
from app.security.rbac import UserRole, mask_pricing_payload, role_permissions


def decode_user_role(token: str) -> Optional[str]:
    """Decode a JWT and return the user's role, or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("role")
    except jwt.PyJWTError:
        return None


def get_current_role(request: Request) -> str:
    """Resolve the caller role from the Authorization header."""
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    role = decode_user_role(authorization.split("Bearer ")[1])
    if role is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return role


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Starlette middleware:

      - Resolves the JWT role and attaches it to request.state.
      - When the caller lacks pricing access and the response body is JSON,
        masks sensitive pricing fields before returning.
    """

    def __init__(self, app, exempt_paths=None):
        super().__init__(app)
        self.exempt_paths = exempt_paths or {"/api/v1/health", "/api/v1/readiness"}

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in self.exempt_paths:
            return await call_next(request)

        role: Optional[str] = None
        try:
            role = get_current_role(request)
        except HTTPException:
            # Let the route's own auth guard produce the 401.
            pass

        request.state.user_role = role

        response = await call_next(request)

        if role is None or role_permissions(role) & {"pricing:view", "pricing:edit"}:
            return response

        # Mask JSON pricing payloads for unauthorized roles.
        if "application/json" in response.headers.get("content-type", ""):
            try:
                import json

                body = json.loads(response.body)
                masked = mask_pricing_payload(body, role)
                return JSONResponse(
                    status_code=response.status_code,
                    content=masked,
                    headers={k: v for k, v in response.headers.items() if k.lower() not in ("content-length",)},
                )
            except (ValueError, TypeError):
                return response
        return response
