import unittest
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from app.api.v1.endpoints.executive_dashboard import router, verify_executive_access
from app.services.executive_analytics_service import ExecutiveAnalyticsService

app = FastAPI()
app.include_router(router, prefix="/api/v1/executive")

class TestExecutiveAnalytics(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_analytics_service_strict_tenant_isolation(self):
        tenant_id = "org_enterprise_1"
        metrics = ExecutiveAnalyticsService.get_portfolio_metrics(tenant_id)
        
        # Verify response structure and isolation wrapper
        self.assertEqual(metrics["tenant_id"], tenant_id)
        self.assertEqual(metrics["total_pipeline_value_sar"], 12500000000)
        
    def test_analytics_service_rejects_missing_tenant(self):
        with self.assertRaises(PermissionError):
            ExecutiveAnalyticsService.get_portfolio_metrics(None)

    def test_executive_api_success_with_valid_role(self):
        # The default dependency mock returns 'super_admin' and 'org_master_123'
        response = self.client.get("/api/v1/executive/portfolio")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["tenant_id"], "org_master_123")

    def test_rbac_dependency_rejection(self):
        # Directly test the RBAC verification dependency logic with an unauthorized role
        unauthorized_token = {"role": "junior_estimator", "sub": "org_123"}
        
        with self.assertRaises(HTTPException) as exc:
            verify_executive_access(unauthorized_token)
            
        self.assertEqual(exc.exception.status_code, 403)
        self.assertIn("Forbidden", exc.exception.detail)

if __name__ == "__main__":
    unittest.main()
