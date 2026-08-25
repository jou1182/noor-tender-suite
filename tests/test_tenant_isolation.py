import unittest
from app.core.tenant_manager import TenantManager

class TestTenantIsolation(unittest.TestCase):
    def setUp(self):
        self.manager = TenantManager()

    def test_vector_collection_routing_isolation(self):
        tenant_id = "acme_corp"
        collection = "rfp_knowledge"
        
        # Verify strict Qdrant vector space prefixing
        routed_collection = self.manager.get_vector_collection(tenant_id, collection)
        self.assertEqual(routed_collection, "org_acme_corp_rfp_knowledge")

    def test_db_isolation_filter(self):
        raw_query = "SELECT * FROM commercial_audits"
        tenant_id = "stark_industries"
        
        # Verify simulated SQLAlchemy tenant isolation lock
        isolated_query = self.manager.enforce_db_isolation(raw_query, tenant_id)
        self.assertEqual(isolated_query["tenant_filter"], "stark_industries")
        
    def test_missing_tenant_id_rejection(self):
        # Verify system strictly blocks queries without an injected tenant context
        with self.assertRaises(PermissionError):
            self.manager.enforce_db_isolation("SELECT *", None)

    def test_rate_limiting_enforcement_and_cross_tenant_leakage(self):
        heavy_tenant = "heavy_user_org"
        
        # Simulate firing allowable requests up to the exact threshold
        for _ in range(50):
            self.assertTrue(self.manager.check_rate_limit(heavy_tenant, max_requests_per_minute=50))
            
        # The 51st request must trigger a strict Rate Limit exception block
        self.assertFalse(self.manager.check_rate_limit(heavy_tenant, max_requests_per_minute=50))
        
        # A completely different tenant querying concurrently MUST remain unaffected (Zero Leakage)
        new_tenant = "clean_user_org"
        self.assertTrue(self.manager.check_rate_limit(new_tenant, max_requests_per_minute=50))

if __name__ == "__main__":
    unittest.main()
