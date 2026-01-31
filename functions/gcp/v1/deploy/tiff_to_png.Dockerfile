# TIFF-to-PNG Converter - Cloud Run Function
FROM python:3.14-slim

WORKDIR /app

# Copy shared library
COPY src/shared /app/shared

# Copy function code
COPY src/functions/__init__.py /app/functions/__init__.py
COPY src/functions/tiff_to_png /app/functions/tiff_to_png

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
CMD exec functions-framework --target=handle_invoice_uploaded --source=/app/functions/tiff_to_png/main.py --port=$PORT
