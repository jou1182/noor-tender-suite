from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.executive_analytics_service import ExecutiveAnalyticsService

router = APIRouter()

def verify_executive_access(token_data: dict = Depends(lambda: {"role": "super_admin", "sub": "org_master_123"})):
    """
    Mock Dependency simulating JWT RBAC validation.
    Strictly restricts access to C-Suite and System Administrators.
    """
    role = token_data.get("role")
    if role not in ["super_admin", "executive_viewer"]:
        raise HTTPException(status_code=403, detail="Forbidden: Executive or Admin clearance strictly required.")
    return token_data

@router.get("/portfolio", response_model=Dict[str, Any])
def get_executive_portfolio(user: dict = Depends(verify_executive_access)):
    """
    Streams macro-level portfolio performance metrics for the authorized tenant.
    """
    tenant_id = user.get("sub")
    data = ExecutiveAnalyticsService.get_portfolio_metrics(tenant_id=tenant_id)
    return {"status": "success", "data": data}
