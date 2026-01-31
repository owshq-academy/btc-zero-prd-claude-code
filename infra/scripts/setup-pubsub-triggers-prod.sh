#!/bin/bash
# =============================================================================
# Invoice Processing Pipeline - Setup Pub/Sub Triggers (Production)
# =============================================================================
# Creates Pub/Sub subscriptions that trigger Cloud Run functions
# Run AFTER Terraform deployment
# =============================================================================

set -e

PROJECT_ID="eda-gemini-prd"
REGION="us-central1"

echo "============================================="
echo "Setting up Pub/Sub Triggers (Production)"
echo "============================================="
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo ""

# Use the dedicated pubsub invoker service account created by Terraform
SA_EMAIL="sa-pubsub-invoker-prd@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Using service account: $SA_EMAIL"
echo ""

# Create subscriptions
create_subscription() {
    local SUB_NAME=$1
    local TOPIC=$2
    local SERVICE=$3
    local ACK_DEADLINE=$4
    local MAX_RETRY=${5:-5}

    SERVICE_URL=$(gcloud run services describe "$SERVICE" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")

    if [ -z "$SERVICE_URL" ]; then
        echo "  ✗ $SERVICE not found - skipping"
        return 1
    fi

    if gcloud pubsub subscriptions describe "$SUB_NAME" --project="$PROJECT_ID" &>/dev/null; then
        echo "  ✓ $SUB_NAME (exists) -> $SERVICE"
        # Update the subscription endpoint
        gcloud pubsub subscriptions update "$SUB_NAME" \
            --push-endpoint="$SERVICE_URL" \
            --push-auth-service-account="$SA_EMAIL" \
            --project="$PROJECT_ID" \
            --quiet 2>/dev/null || true
    else
        gcloud pubsub subscriptions create "$SUB_NAME" \
            --topic="$TOPIC" \
            --push-endpoint="$SERVICE_URL" \
            --push-auth-service-account="$SA_EMAIL" \
            --ack-deadline="$ACK_DEADLINE" \
            --max-delivery-attempts="$MAX_RETRY" \
            --dead-letter-topic="${TOPIC}-dlq" \
            --min-retry-delay="10s" \
            --max-retry-delay="600s" \
            --project="$PROJECT_ID" \
            --quiet
        echo "  ✓ $SUB_NAME (created) -> $SERVICE"
    fi
}

echo "Creating Pub/Sub subscriptions..."
echo ""

# Pipeline flow:
# 1. invoice-uploaded -> tiff-to-png-converter
# 2. invoice-converted -> invoice-classifier
# 3. invoice-classified -> data-extractor
# 4. invoice-extracted -> bigquery-writer

create_subscription \
    "eda-gemini-prd-tiff-converter-sub" \
    "eda-gemini-prd-invoice-uploaded" \
    "fnc-tiff-to-png-converter-prd" \
    300 5

create_subscription \
    "eda-gemini-prd-classifier-sub" \
    "eda-gemini-prd-invoice-converted" \
    "fnc-invoice-classifier-prd" \
    300 5

create_subscription \
    "eda-gemini-prd-extractor-sub" \
    "eda-gemini-prd-invoice-classified" \
    "fnc-data-extractor-prd" \
    540 5

create_subscription \
    "eda-gemini-prd-writer-sub" \
    "eda-gemini-prd-invoice-extracted" \
    "fnc-bigquery-writer-prd" \
    120 5

echo ""
echo "============================================="
echo "✅ Production Triggers Configured!"
echo "============================================="
echo ""
echo "Pipeline is ready! Test with:"
echo "  gsutil cp your_invoice.tiff gs://eda-gemini-prd-pipeline/landing/"
echo ""
echo "Monitor logs:"
echo "  gcloud logging read 'resource.type=\"cloud_run_revision\"' --limit=50 --project=$PROJECT_ID"
echo ""
