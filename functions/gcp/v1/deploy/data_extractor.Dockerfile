# Data Extractor - Cloud Run Function
# Build from functions/gcp/v1: docker build -f deploy/data_extractor.Dockerfile -t data-extractor .

FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY src/shared /app/shared

# Copy function code
COPY src/functions/__init__.py /app/functions/__init__.py
COPY src/functions/data_extractor /app/functions/data_extractor

# Install dependencies
RUN pip install --no-cache-dir \
    functions-framework>=3.0.0 \
    google-cloud-storage>=2.10.0 \
    google-cloud-pubsub>=2.18.0 \
    google-cloud-aiplatform>=1.38.0 \
    pydantic>=2.0.0 \
    cloudevents>=1.10.0 \
    httpx>=0.25.0 \
    tenacity>=8.2.0 \
    openai>=1.0.0 \
    langfuse>=2.0.0

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8080

# Entry point
CMD exec functions-framework --target=handle_invoice_classified --source=/app/functions/data_extractor/main.py --port=$PORT
