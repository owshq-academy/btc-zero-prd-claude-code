# BigQuery Writer - Cloud Run Function
# Build from functions/gcp/v1: docker build -f deploy/bigquery_writer.Dockerfile -t bigquery-writer .

FROM python:3.11-slim

WORKDIR /app

# Copy shared library
COPY src/shared /app/shared

# Copy function code
COPY src/functions/__init__.py /app/functions/__init__.py
COPY src/functions/bigquery_writer /app/functions/bigquery_writer

# Install dependencies
RUN pip install --no-cache-dir \
    functions-framework>=3.0.0 \
    google-cloud-bigquery>=3.13.0 \
    google-cloud-pubsub>=2.18.0 \
    google-cloud-storage>=2.14.0 \
    pydantic>=2.0.0 \
    cloudevents>=1.10.0

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8080

# Entry point
CMD exec functions-framework --target=handle_invoice_extracted --source=/app/functions/bigquery_writer/main.py --port=$PORT
