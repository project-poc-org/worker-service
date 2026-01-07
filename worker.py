import time
import os
import logging
from pathlib import Path
from rq import Worker, Queue
import redis

# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

VERSION = os.getenv("WORKER_VERSION", "dev")

# Basic application logging to both stdout and a file for central collection.
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "worker-service.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [worker-service] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger("worker-service")

# Instrumentation
resource = Resource(attributes={"service.name": "worker-service", "service.version": VERSION})
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces"),
)
span_processor = SimpleSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Also log spans to console for debugging
console_exporter = ConsoleSpanExporter()
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(console_exporter))
tracer = trace.get_tracer(__name__)

def example_task(data):
    with tracer.start_as_current_span("example_task"):
        logger.info(f"Processing: {data}")
        time.sleep(5)
        logger.info(f"Done: {data}")

if __name__ == "__main__":
    redis_url = "redis://localhost:6379/0"
    conn = redis.from_url(redis_url)
    queue = Queue('default', connection=conn)
    logger.info(f"Worker version: {VERSION}")
    worker = Worker([queue], connection=conn)
    worker.work()
