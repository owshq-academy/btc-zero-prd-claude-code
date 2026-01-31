# DLQ Processor - Cloud Run Function
# Build from functions/gcp/v1: docker build -f deploy/dlq_processor.Dockerfile -t dlq-processor .

FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY src/shared /app/shared

# Copy function code
COPY src/functions/__init__.py /app/functions/__init__.py
COPY src/functions/dlq_processor /app/functions/dlq_processor

# Install dependencies
RUN pip install --no-cache-dir \
    functions-framework>=3.0.0 \
    google-cloud-storage>=2.13.0 \
    pydantic>=2.0.0 \
    cloudevents>=1.10.0

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8080

# Entry point
CMD exec functions-framework --target=handle_dlq_message --source=/app/functions/dlq_processor/main.py --port=$PORT
