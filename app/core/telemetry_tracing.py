import time
from prometheus_client import Counter, Histogram, Gauge

# Prometheus Metrics Definitions
ACTIVE_WORKFLOWS = Counter('noor_active_workflows_total', 'Total number of LangGraph agent workflows executed')
ERROR_RATES = Counter('noor_error_rates_total', 'Total number of fatal system or agent execution errors')
LLM_LATENCY = Histogram('noor_llm_call_latency_seconds', 'Latency of multi-provider LLM API calls in seconds')
SYSTEM_HEALTH = Gauge('noor_system_health', 'System health availability status (1=Online, 0=Offline)')

class TelemetryEngine:
    @staticmethod
    def init_telemetry():
        """
        Initializes OpenTelemetry traces and Prometheus metric states.
        (Hooks for OTEL Collector OTLP exporter would be attached here)
        """
        SYSTEM_HEALTH.set(1.0)
        
    @staticmethod
    def record_workflow_start():
        ACTIVE_WORKFLOWS.inc()

    @staticmethod
    def record_error():
        ERROR_RATES.inc()
        
    @staticmethod
    def observe_llm_latency(duration_seconds: float):
        LLM_LATENCY.observe(duration_seconds)
        
    @staticmethod
    def trace_agent_execution(agent_name: str):
        """
        OpenTelemetry span tracing decorator for LangGraph node execution.
        Automates latency tracking and error boundary encapsulation.
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # In production: with tracer.start_as_current_span(agent_name):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    # For agent-level duration observability
                    duration = time.time() - start_time
                    # If this was specifically an LLM invocation, observe it:
                    if "llm" in agent_name.lower():
                        TelemetryEngine.observe_llm_latency(duration)
                    return result
                except Exception as e:
                    TelemetryEngine.record_error()
                    raise e
            return wrapper
        return decorator
