#!/bin/bash
# Setup Dead-Letter Queue policies for invoice pipeline subscriptions
#
# This script:
# 1. Creates DLQ subscriptions that push to the dlq-processor Cloud Run function
# 2. Updates main subscriptions with dead-letter policies (max 5 delivery attempts)
#
# Prerequisites:
# - dlq-processor Cloud Run service must be deployed
# - DLQ topics already exist (invoice-*-dlq)
#
# Usage:
#   ./setup-dlq.sh [PROJECT_ID] [REGION]
#
# Example:
#   ./setup-dlq.sh eda-gemini-dev us-central1

set -euo pipefail

PROJECT_ID="${1:-eda-gemini-dev}"
REGION="${2:-us-central1}"
DLQ_SERVICE="dlq-processor"
MAX_DELIVERY_ATTEMPTS=5

echo "🔧 Setting up DLQ policies for project: $PROJECT_ID"
echo ""

# Get the Cloud Run service URL
DLQ_SERVICE_URL=$(gcloud run services describe "$DLQ_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format="value(status.url)" 2>/dev/null || echo "")

if [ -z "$DLQ_SERVICE_URL" ]; then
    echo "❌ Error: dlq-processor Cloud Run service not found."
    echo "   Deploy the service first with:"
    echo "   gcloud run deploy dlq-processor --source=. --region=$REGION"
    exit 1
fi

echo "✅ Found dlq-processor service: $DLQ_SERVICE_URL"
echo ""

# Service account for push subscriptions
SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"

# Define subscription to DLQ topic mappings
declare -A SUBSCRIPTIONS=(
    ["tiff-to-png-sub"]="invoice-uploaded-dlq"
    ["classifier-sub"]="invoice-converted-dlq"
    ["extractor-sub"]="invoice-classified-dlq"
    ["writer-sub"]="invoice-extracted-dlq"
)

echo "📋 Step 1: Creating DLQ subscriptions..."
echo ""

for DLQ_TOPIC in "${!SUBSCRIPTIONS[@]}"; do
    DLQ_TOPIC_NAME="${SUBSCRIPTIONS[$DLQ_TOPIC]}"
    DLQ_SUB_NAME="${DLQ_TOPIC_NAME}-sub"

    echo "   Creating subscription: $DLQ_SUB_NAME → $DLQ_TOPIC_NAME"

    # Check if subscription exists
    if gcloud pubsub subscriptions describe "$DLQ_SUB_NAME" --project="$PROJECT_ID" &>/dev/null; then
        echo "   ⏭️  Subscription already exists, skipping..."
    else
        gcloud pubsub subscriptions create "$DLQ_SUB_NAME" \
            --project="$PROJECT_ID" \
            --topic="$DLQ_TOPIC_NAME" \
            --push-endpoint="$DLQ_SERVICE_URL" \
            --push-auth-service-account="$SA_EMAIL" \
            --ack-deadline=120 \
            --message-retention-duration=7d
        echo "   ✅ Created $DLQ_SUB_NAME"
    fi
done

echo ""
echo "📋 Step 2: Updating main subscriptions with dead-letter policies..."
echo ""

for SUB_NAME in "${!SUBSCRIPTIONS[@]}"; do
    DLQ_TOPIC="${SUBSCRIPTIONS[$SUB_NAME]}"

    echo "   Updating: $SUB_NAME → DLQ: $DLQ_TOPIC (max $MAX_DELIVERY_ATTEMPTS attempts)"

    gcloud pubsub subscriptions update "$SUB_NAME" \
        --project="$PROJECT_ID" \
        --dead-letter-topic="$DLQ_TOPIC" \
        --max-delivery-attempts="$MAX_DELIVERY_ATTEMPTS"

    echo "   ✅ Updated $SUB_NAME"
done

echo ""
echo "🎉 DLQ setup complete!"
echo ""
echo "Verification:"
echo "  gcloud pubsub subscriptions describe writer-sub --project=$PROJECT_ID --format='yaml(deadLetterPolicy)'"
echo ""
echo "Test a failure:"
echo "  1. Upload an invoice that will fail validation"
echo "  2. Wait for $MAX_DELIVERY_ATTEMPTS retry attempts"
echo "  3. Check failed bucket: gsutil ls gs://${PROJECT_ID}-invoices-failed/"
