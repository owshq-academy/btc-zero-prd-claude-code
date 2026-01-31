#!/bin/bash
# Setup Workload Identity Federation for GitHub Actions
#
# This script configures GCP to allow GitHub Actions to authenticate
# without storing long-lived service account keys.
#
# Usage:
#   ./setup-workload-identity.sh <PROJECT_ID> <GITHUB_ORG> <GITHUB_REPO>
#
# Example:
#   ./setup-workload-identity.sh eda-gemini-dev owshq-academy btc-zero-prd-claude-code

set -e

# ============================================
# Configuration
# ============================================
PROJECT_ID="${1:?Error: PROJECT_ID required}"
GITHUB_ORG="${2:?Error: GITHUB_ORG required}"
GITHUB_REPO="${3:?Error: GITHUB_REPO required}"

POOL_NAME="github-actions"
PROVIDER_NAME="github"
SERVICE_ACCOUNT_NAME="github-actions-sa"

echo "============================================"
echo "Workload Identity Federation Setup"
echo "============================================"
echo "Project:     $PROJECT_ID"
echo "GitHub Org:  $GITHUB_ORG"
echo "GitHub Repo: $GITHUB_REPO"
echo "============================================"
echo ""

# ============================================
# Step 1: Enable required APIs
# ============================================
echo "📦 Enabling required APIs..."
gcloud services enable iamcredentials.googleapis.com --project="$PROJECT_ID"
gcloud services enable iam.googleapis.com --project="$PROJECT_ID"
gcloud services enable cloudbuild.googleapis.com --project="$PROJECT_ID"
gcloud services enable run.googleapis.com --project="$PROJECT_ID"
gcloud services enable artifactregistry.googleapis.com --project="$PROJECT_ID"

# ============================================
# Step 2: Create Workload Identity Pool
# ============================================
echo ""
echo "🔐 Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create "$POOL_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool" \
  --description="Workload Identity Pool for GitHub Actions" \
  2>/dev/null || echo "Pool already exists, continuing..."

# ============================================
# Step 3: Create OIDC Provider
# ============================================
echo ""
echo "🔑 Creating OIDC Provider..."
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_NAME" \
  --display-name="GitHub OIDC Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  2>/dev/null || echo "Provider already exists, continuing..."

# ============================================
# Step 4: Create Service Account
# ============================================
echo ""
echo "👤 Creating Service Account..."
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions Service Account" \
  --description="Service account for GitHub Actions CI/CD" \
  2>/dev/null || echo "Service account already exists, continuing..."

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Service Account: $SERVICE_ACCOUNT_EMAIL"

# ============================================
# Step 5: Grant IAM roles to Service Account
# ============================================
echo ""
echo "🔓 Granting IAM roles to Service Account..."

# Cloud Build
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/cloudbuild.builds.editor" \
  --condition=None \
  --quiet

# Cloud Run Admin
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/run.admin" \
  --condition=None \
  --quiet

# Storage Admin (for GCS buckets)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/storage.admin" \
  --condition=None \
  --quiet

# Service Account User (to deploy Cloud Run)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/iam.serviceAccountUser" \
  --condition=None \
  --quiet

# Artifact Registry Writer (for container images)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
  --role="roles/artifactregistry.writer" \
  --condition=None \
  --quiet

echo "✅ IAM roles granted"

# ============================================
# Step 6: Allow GitHub to impersonate Service Account
# ============================================
echo ""
echo "🔗 Configuring Workload Identity binding..."

# Get project number
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

gcloud iam service-accounts add-iam-policy-binding "$SERVICE_ACCOUNT_EMAIL" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"

echo "✅ Workload Identity binding configured"

# ============================================
# Output: GitHub Secrets
# ============================================
echo ""
echo "============================================"
echo "🎉 Setup Complete!"
echo "============================================"
echo ""
echo "Add these secrets to GitHub:"
echo ""
echo "GCP_WORKLOAD_IDENTITY_PROVIDER:"
echo "  projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
echo ""
echo "GCP_SERVICE_ACCOUNT:"
echo "  ${SERVICE_ACCOUNT_EMAIL}"
echo ""
echo "============================================"
