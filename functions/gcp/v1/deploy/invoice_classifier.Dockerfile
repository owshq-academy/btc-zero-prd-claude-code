# Invoice Classifier - Cloud Run Function
FROM python:3.14-slim

WORKDIR /app

# Copy shared library
COPY src/shared /app/shared

# Copy function code
COPY src/functions/__init__.py /app/functions/__init__.py
COPY src/functions/invoice_classifier /app/functions/invoice_classifier

# Install dependencies (Pillow wheels include bundled image libraries)
RUN pip install --no-cache-dir \
    functions-framework>=3.0.0 \
    "Pillow>=10.0.0" \
    google-cloud-storage>=2.10.0 \
    google-cloud-pubsub>=2.18.0 \
    pydantic>=2.0.0 \
    cloudevents>=1.10.0

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8080

# Entry point
CMD exec functions-framework --target=handle_invoice_converted --source=/app/functions/invoice_classifier/main.py --port=$PORT
