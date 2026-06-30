#!/usr/bin/env bash
# Deploy the MinuteLead render service to Google Cloud Run.
# No local Docker needed: Cloud Build builds the image from ./Dockerfile.
# One-time setup + full walkthrough: see CLOUDRUN.md
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID first, e.g.  export PROJECT_ID=minutelead-prod}"
REGION="${REGION:-us-central1}"
SERVICE="${SERVICE:-minutelead-render}"

echo "Project : $PROJECT_ID"
echo "Region  : $REGION"
echo "Service : $SERVICE"
echo

gcloud config set project "$PROJECT_ID" >/dev/null

# APIs this deploy needs (idempotent, safe to re-run)
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# Build from the Dockerfile via Cloud Build, then deploy to Cloud Run.
# Scales to zero (min-instances 0) so you only spend credits when a batch renders.
gcloud run deploy "$SERVICE" \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --concurrency 40 \
  --timeout 120 \
  --min-instances 0 \
  --max-instances 3

echo
URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo "Deployed: $URL"
echo "Health  : $URL/health"
echo "Test    : $URL/featured?title=Pest%20Control%20Missed%20Call&seed=3"
