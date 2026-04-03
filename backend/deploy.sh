#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID environment variable}"
REGION="${GCP_REGION:-europe-west2}"
SERVICE_NAME="safetyforge-api"
REPO_NAME="safetyforge"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME"

# ── Ensure Artifact Registry repo exists ─────────────────────────
echo "==> Ensuring Artifact Registry repository exists..."
gcloud artifacts repositories describe "$REPO_NAME" \
  --project="$PROJECT_ID" \
  --location="$REGION" > /dev/null 2>&1 || \
gcloud artifacts repositories create "$REPO_NAME" \
  --project="$PROJECT_ID" \
  --location="$REGION" \
  --repository-format=docker \
  --description="SafetyForge Docker images"

# ── Build and push ───────────────────────────────────────────────
echo "==> Building Docker image..."
docker build -t "$IMAGE:latest" .

echo "==> Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

echo "==> Pushing image..."
docker push "$IMAGE:latest"

# ── Deploy to Cloud Run ──────────────────────────────────────────
echo "==> Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --image="$IMAGE:latest" \
  --platform=managed \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --port=8000 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID"

# ── Output service URL ───────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="value(status.url)")

echo ""
echo "==> Deployed successfully!"
echo "    Service URL: $SERVICE_URL"
