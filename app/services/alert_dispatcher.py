import json
import logging
import urllib.request
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AlertDispatcher:
    # Webhook endpoint (Configurable in production via environment variables)
    WEBHOOK_URL = "http://localhost:8080/internal/alerts" 

    @staticmethod
    def dispatch_critical_alert(alert_title: str, message: str, context: Dict[str, Any] = None) -> bool:
        """
        Dispatches high-priority JSON payloads to Webhook targets 
        (e.g., Slack, Microsoft Teams, PagerDuty, Internal NOC) 
        when a fatal compliance blocker or systemic anomaly is detected.
        """
        payload = {
            "alert_type": "CRITICAL_BLOCKER",
            "title": alert_title,
            "message": message,
            "context": context or {}
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            AlertDispatcher.WEBHOOK_URL, 
            data=data, 
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            # Fire and forget paradigm to prevent blocking the LangGraph Execution Thread
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status in (200, 201, 202, 204):
                    logger.info(f"Smart Alert Dispatched Successfully: {alert_title}")
                    return True
        except Exception as e:
            logger.error(f"Failed to dispatch smart alert webhook: {str(e)}")
            # Fail silently in production to maintain core flow integrity
            pass
            
        return False
