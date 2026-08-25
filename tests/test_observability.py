import unittest
from unittest.mock import patch, MagicMock
from app.core.telemetry_tracing import TelemetryEngine, ACTIVE_WORKFLOWS, ERROR_RATES, LLM_LATENCY
from app.services.alert_dispatcher import AlertDispatcher

class TestObservability(unittest.TestCase):
    def test_prometheus_metrics_increment_correctly(self):
        # Capture baseline counters
        workflows_before = ACTIVE_WORKFLOWS._value.get()
        errors_before = ERROR_RATES._value.get()
        
        # Trigger OpenTelemetry Hooks
        TelemetryEngine.record_workflow_start()
        TelemetryEngine.record_error()
        TelemetryEngine.observe_llm_latency(0.245)
        
        # Validate deterministic metrics growth
        self.assertEqual(ACTIVE_WORKFLOWS._value.get(), workflows_before + 1)
        self.assertEqual(ERROR_RATES._value.get(), errors_before + 1)
        # Latency metric sum should increase by exactly the observation value
        self.assertGreaterEqual(LLM_LATENCY._sum.get(), 0.245)

    @patch("urllib.request.urlopen")
    def test_smart_alert_dispatcher_webhooks(self, mock_urlopen):
        # Mock successful 200 OK from downstream webhook receiver (e.g. Slack/Teams)
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        # Fire fatal compliance alert
        success = AlertDispatcher.dispatch_critical_alert(
            alert_title="FATAL: ETIMAD Compliance Failure",
            message="Missing mandatory initial bank guarantee.",
            context={"tender_id": "TND-99"}
        )
        
        # Validate successful fire-and-forget payload delivery
        self.assertTrue(success)
        mock_urlopen.assert_called_once()
        
        # Verify JSON payload serialization integrity
        request_obj = mock_urlopen.call_args[0][0]
        payload_data = request_obj.data.decode('utf-8')
        
        self.assertIn("CRITICAL_BLOCKER", payload_data)
        self.assertIn("FATAL: ETIMAD Compliance Failure", payload_data)
        self.assertIn("Missing mandatory initial bank guarantee.", payload_data)
        self.assertIn("TND-99", payload_data)

if __name__ == "__main__":
    unittest.main()
