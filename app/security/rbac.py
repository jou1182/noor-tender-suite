"""
Role-Based Access Control (RBAC) — NCA ECC-aligned.

Defines the enterprise role model, permission matrix, the
``@require_permissions`` decorator, and automated payload data-masking for
unauthorized roles.

Masking policy: unit rates and profit markups are masked (replaced with a
``***`` placeholder / sanitized value) for roles without ``pricing:view``.
"""

import functools
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from fastapi import HTTPException, Request, status


class UserRole(str, Enum):
    """Enterprise user roles (NCA ECC principle of least privilege)."""

    TENDER_ENGINEER = "TENDER_ENGINEER"
    SBC_AUDITOR = "SBC_AUDITOR"
    COST_ESTIMATOR = "COST_ESTIMATOR"
    TENDER_DIRECTOR = "TENDER_DIRECTOR"
    COMPLIANCE_AUDITOR = "COMPLIANCE_AUDITOR"


# Role -> permission set matrix.
ROLE_PERMISSIONS: Dict[UserRole, Set[str]] = {
    UserRole.TENDER_ENGINEER: {
        "tender:view", "tender:edit", "document:upload", "schedule:view",
    },
    UserRole.SBC_AUDITOR: {
        "tender:view", "compliance:view", "compliance:edit", "sbc:audit",
    },
    UserRole.COST_ESTIMATOR: {
        "tender:view", "pricing:view", "pricing:edit", "cost:breakdown",
    },
    UserRole.TENDER_DIRECTOR: {
        "tender:view", "tender:edit", "pricing:view", "compliance:view",
        "sbc:audit", "proposal:approve", "audit:read",
    },
    UserRole.COMPLIANCE_AUDITOR: {
        "tender:view", "compliance:view", "audit:read", "pricing:view",
    },
}

# Permissions that unlock pricing data (unit rates, markups).
PRICING_PERMISSIONS = {"pricing:view", "pricing:edit"}

# Sensitive field names that get masked without pricing permission.
SENSITIVE_FIELDS = {
    "unit_rate", "unit_rate_sar", "profit_markup", "markup_pct", "gross_margin",
    "internal_cost", "bid_price",
}

MASK_VALUE = "***"


def role_permissions(role: str) -> Set[str]:
    """Resolve the permission set for a role string (unknown roles get none)."""
    try:
        return ROLE_PERMISSIONS[UserRole(role)]
    except (KeyError, ValueError):
        return set()


def require_permissions(required: List[str]):
    """
    Decorator enforcing a permission set on a FastAPI endpoint.

    Reads ``request.state.user_role`` (populated by auth middleware). Raises
    403 Forbidden when the caller's role lacks any required permission.
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or _find_request(args)
            role = getattr(getattr(request, "state", None), "user_role", None) if request else None
            if role is None:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing role context")
            perms = role_permissions(role)
            missing = [p for p in required if p not in perms]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: missing permissions {missing}",
                )
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def has_pricing_access(role: str) -> bool:
    """True when the role may view unmasked pricing data."""
    return bool(role_permissions(role) & PRICING_PERMISSIONS)


def mask_pricing_payload(payload: Any, role: str) -> Any:
    """
    Recursively mask sensitive pricing fields for roles without pricing access.

    Lists are mapped element-wise; dicts are copied with sensitive keys
    replaced by ``***``.
    """
    if has_pricing_access(role):
        return payload

    if isinstance(payload, list):
        return [mask_pricing_payload(item, role) for item in payload]

    if isinstance(payload, dict):
        masked: Dict[str, Any] = {}
        for key, value in payload.items():
            if key in SENSITIVE_FIELDS and isinstance(value, (int, float, str)):
                masked[key] = MASK_VALUE
            else:
                masked[key] = mask_pricing_payload(value, role)
        return masked

    return payload


def _find_request(args: tuple) -> Optional[Request]:
    """Locate the FastAPI Request instance among positional args."""
    for arg in args:
        if isinstance(arg, Request):
            return arg
    return None
