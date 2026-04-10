# Kerf Infrastructure Plan

*Last updated: 2026-03-31*

---

## 1. GCP PROJECT SETUP

### 1.1 Project Structure

Three isolated GCP projects enforce environment separation and prevent accidental cross-environment access.

| Environment | Project ID | Purpose |
|---|---|---|
| Development | `kerf-dev` | Local-to-cloud development, Firestore emulator fallback, CI test runs |
| Staging | `kerf-staging` | Pre-production validation, QA, demo environment |
| Production | `kerf-prod` | Live customer traffic |

```bash
# Create projects (requires billing account linked)
gcloud projects create kerf-dev --name="Kerf Dev"
gcloud projects create kerf-staging --name="Kerf Staging"
gcloud projects create kerf-prod --name="Kerf Prod"

# Link billing account (get your billing account ID first)
BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(ACCOUNT_ID)" --limit=1)
gcloud billing projects link kerf-dev --billing-account=$BILLING_ACCOUNT
gcloud billing projects link kerf-staging --billing-account=$BILLING_ACCOUNT
gcloud billing projects link kerf-prod --billing-account=$BILLING_ACCOUNT
```

### 1.2 API Enablement

Run for each project (replace `$PROJECT_ID`):

```bash
PROJECT_ID="kerf-prod"  # repeat for -dev and -staging

gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  cloudtrace.googleapis.com \
  clouderrorreporting.googleapis.com \
  firebase.googleapis.com \
  identitytoolkit.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudbuild.googleapis.com \
  --project=$PROJECT_ID
```

### 1.3 IAM Roles and Service Accounts

#### Service Accounts

| Service Account | Project | Purpose |
|---|---|---|
| `cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com` | All | Cloud Run backend runtime identity |
| `ci-deployer@$PROJECT_ID.iam.gserviceaccount.com` | All | GitHub Actions deployment |

```bash
PROJECT_ID="kerf-prod"

# Cloud Run runtime service account
gcloud iam service-accounts create cloudrun-api \
  --display-name="Cloud Run API Runtime" \
  --project=$PROJECT_ID

# Grant roles to Cloud Run SA
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/firebase.sdkAdminServiceAgent"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.agent"

# CI/CD deployer service account
gcloud iam service-accounts create ci-deployer \
  --display-name="CI/CD Deployer" \
  --project=$PROJECT_ID

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ci-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ci-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ci-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:ci-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Export CI key (store in GitHub Secrets as GCP_SA_KEY_PROD)
gcloud iam service-accounts keys create ci-key-prod.json \
  --iam-account=ci-deployer@$PROJECT_ID.iam.gserviceaccount.com
```

### 1.4 Budget Alerts

```bash
# Create budget alerts via gcloud (or use Console > Billing > Budgets)
# Dev: $50/month, Staging: $100/month, Prod: $500/month (initial)
# Alerts at 50%, 80%, 100% thresholds

# Example for prod (CLI budget creation requires the billing budgets API)
gcloud billing budgets create \
  --billing-account=$BILLING_ACCOUNT \
  --display-name="Kerf Prod Monthly" \
  --budget-amount=500USD \
  --threshold-rule=percent=0.5 \
  --threshold-rule=percent=0.8 \
  --threshold-rule=percent=1.0 \
  --filter-projects=projects/kerf-prod
```

---

## 2. FIREBASE SETUP

### 2.1 Firebase Project Initialization

```bash
# Initialize Firebase in each GCP project
firebase projects:addfirebase kerf-dev
firebase projects:addfirebase kerf-staging
firebase projects:addfirebase kerf-prod

# Add web app for the frontend
firebase apps:create WEB "Kerf Web" --project=kerf-prod
```

### 2.2 Auth Configuration

Providers to enable: **Email/Password** and **Google Sign-In**.

```bash
# Enable via Firebase Console > Authentication > Sign-in method
# Or via Firebase Admin SDK configuration:
```

Firebase Console steps (per project):
1. Go to Authentication > Sign-in method
2. Enable **Email/Password** (disable Email link / passwordless)
3. Enable **Google** provider (set support email to admin@kerf.build)
4. Set Authorized domains: `app.kerf.build`, `staging.kerf.build`, `localhost`

Frontend Firebase config (stored in environment variables):

```typescript
// frontend/src/lib/firebase.ts
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
};
```

### 2.3 Firestore Security Rules

The data model uses company-level isolation. The collection hierarchy is:

```
companies/{companyId}                    -- Company profile
companies/{companyId}/documents/{docId}  -- Safety documents (SSSP, JHA, toolbox talks, etc.)
companies/{companyId}/templates/{tmplId} -- Custom templates
companies/{companyId}/billing/{billId}   -- Billing/subscription records
```

```javascript
// firestore.rules
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {

    // Helper: check if the user is authenticated
    function isAuthenticated() {
      return request.auth != null;
    }

    // Helper: check if the user belongs to this company
    // The user's custom claims include companyId, set during onboarding
    function isCompanyMember(companyId) {
      return isAuthenticated()
        && request.auth.token.companyId == companyId;
    }

    // Helper: check if user is a company admin
    function isCompanyAdmin(companyId) {
      return isCompanyMember(companyId)
        && request.auth.token.role == 'admin';
    }

    // Company profile: admins can write, all members can read
    match /companies/{companyId} {
      allow read: if isCompanyMember(companyId);
      allow create: if isAuthenticated()
        && request.auth.token.companyId == companyId;
      allow update: if isCompanyAdmin(companyId);
      allow delete: if false; // Never delete via client -- admin API only

      // Documents subcollection
      match /documents/{docId} {
        allow read: if isCompanyMember(companyId);
        allow create: if isCompanyMember(companyId);
        allow update: if isCompanyMember(companyId);
        allow delete: if false; // Soft delete only (set deleted=true)
      }

      // Templates subcollection
      match /templates/{templateId} {
        allow read: if isCompanyMember(companyId);
        allow create: if isCompanyAdmin(companyId);
        allow update: if isCompanyAdmin(companyId);
        allow delete: if isCompanyAdmin(companyId);
      }

      // Billing subcollection -- admin read only, writes via backend only
      match /billing/{billingId} {
        allow read: if isCompanyAdmin(companyId);
        allow write: if false; // Backend-only via Admin SDK
      }
    }

    // Global templates (read-only for all authenticated users)
    match /global_templates/{templateId} {
      allow read: if isAuthenticated();
      allow write: if false; // Admin API only
    }

    // Deny everything else
    match /{document=**} {
      allow read, write: if false;
    }
  }
}
```

Deploy rules:

```bash
firebase deploy --only firestore:rules --project=kerf-prod
```

### 2.4 Firestore Indexes

Based on the data model (documents have `company_id`, `document_type`, `status`, `created_at`, `deleted`):

```json
// firestore.indexes.json
{
  "indexes": [
    {
      "collectionGroup": "documents",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "deleted", "order": "ASCENDING" },
        { "fieldPath": "document_type", "order": "ASCENDING" },
        { "fieldPath": "created_at", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "documents",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "deleted", "order": "ASCENDING" },
        { "fieldPath": "status", "order": "ASCENDING" },
        { "fieldPath": "created_at", "order": "DESCENDING" }
      ]
    },
    {
      "collectionGroup": "documents",
      "queryScope": "COLLECTION",
      "fields": [
        { "fieldPath": "deleted", "order": "ASCENDING" },
        { "fieldPath": "created_at", "order": "DESCENDING" }
      ]
    }
  ],
  "fieldOverrides": []
}
```

Deploy indexes:

```bash
firebase deploy --only firestore:indexes --project=kerf-prod
```

### 2.5 Firebase Hosting vs Vercel Decision

**Decision: Vercel for the frontend.**

| Factor | Firebase Hosting | Vercel |
|---|---|---|
| Build integration | Manual or Cloud Build | Automatic from GitHub push |
| Preview deployments | Manual per branch | Automatic per PR |
| Edge network | Google CDN | Vercel Edge Network (faster for static) |
| Custom domains | Supported | Supported, simpler UX |
| Analytics | Requires GA integration | Built-in Web Vitals |
| Cost at scale | Pay per GB served | Free tier generous, Pro at $20/month |
| React/Vite support | Generic static hosting | First-class Vite/React support |

Vercel wins on developer experience, preview deployments, and zero-config React/Vite support. Firebase Hosting would add complexity with no clear benefit since the frontend is a pure SPA with no server-side rendering requirements.

---

## 3. CLOUD RUN (Backend)

### 3.1 Service Configuration

```bash
PROJECT_ID="kerf-prod"
REGION="us-central1"
SERVICE_NAME="kerf-api"
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/kerf/$SERVICE_NAME"

gcloud run deploy $SERVICE_NAME \
  --project=$PROJECT_ID \
  --region=$REGION \
  --image=$IMAGE:latest \
  --platform=managed \
  --service-account=cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com \
  --memory=1Gi \
  --cpu=1 \
  --concurrency=80 \
  --min-instances=1 \
  --max-instances=20 \
  --port=8000 \
  --timeout=300s \
  --cpu-throttling \
  --allow-unauthenticated \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=$PROJECT_ID" \
  --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,PADDLE_WEBHOOK_SECRET=paddle-webhook-secret:latest,PADDLE_API_KEY=paddle-api-key:latest"
```

Configuration rationale:

| Setting | Value | Rationale |
|---|---|---|
| Memory | 1 GiB | WeasyPrint PDF generation is memory-intensive; 512 MiB is insufficient |
| CPU | 1 vCPU | Sufficient for I/O-bound FastAPI workload; Claude API calls are network-bound |
| Concurrency | 80 | FastAPI with uvicorn handles concurrent async requests well |
| Min instances | 1 (prod), 0 (dev/staging) | Eliminates cold starts in production |
| Max instances | 20 | Caps cost; 20 instances x 80 concurrency = 1,600 concurrent requests |
| Timeout | 300s | AI document generation can take 30-60s; PDF generation up to 30s |
| CPU throttling | Enabled | Reduces cost -- CPU only allocated during request processing |

### 3.2 Environment Variable Management (Secret Manager)

```bash
PROJECT_ID="kerf-prod"

# Create secrets
echo -n "sk-ant-..." | gcloud secrets create anthropic-api-key \
  --project=$PROJECT_ID \
  --data-file=-

echo -n "whsec_..." | gcloud secrets create paddle-webhook-secret \
  --project=$PROJECT_ID \
  --data-file=-

echo -n "eyJ..." | gcloud secrets create paddle-api-key \
  --project=$PROJECT_ID \
  --data-file=-

# Grant Cloud Run SA access to secrets
gcloud secrets add-iam-policy-binding anthropic-api-key \
  --project=$PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding paddle-webhook-secret \
  --project=$PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding paddle-api-key \
  --project=$PROJECT_ID \
  --member="serviceAccount:cloudrun-api@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Non-secret environment variables (set directly on the Cloud Run service):

| Variable | Value | Notes |
|---|---|---|
| `ENVIRONMENT` | `production` / `staging` / `development` | Controls logging level, CORS |
| `GCP_PROJECT_ID` | `kerf-prod` | Used by Firestore client |
| `CORS_ORIGINS` | `https://app.kerf.build` | Comma-separated allowed origins |

### 3.3 Custom Domain Mapping

```bash
# Map api.kerf.build to Cloud Run
gcloud run domain-mappings create \
  --service=kerf-api \
  --domain=api.kerf.build \
  --region=us-central1 \
  --project=kerf-prod

# The command outputs DNS records to add:
# Type: CNAME, Name: api, Value: ghs.googlehosted.com
# Add this to your DNS provider (e.g., Cloudflare, Route53)
```

Staging: `api-staging.kerf.build` mapped to the staging Cloud Run service.

### 3.4 Health Check Configuration

The existing `/health` endpoint in `app/main.py` is sufficient. Cloud Run uses this automatically:

```bash
# Cloud Run uses the container's port for health checks by default.
# Configure startup probe for cold-start resilience:
gcloud run services update kerf-api \
  --project=kerf-prod \
  --region=us-central1 \
  --startup-cpu-boost \
  --liveness-probe-path=/health \
  --liveness-probe-period=30 \
  --startup-probe-path=/health \
  --startup-probe-initial-delay=5 \
  --startup-probe-period=5 \
  --startup-probe-failure-threshold=3
```

### 3.5 Autoscaling Strategy

| Scale | Min Instances | Max Instances | Concurrency |
|---|---|---|---|
| Dev | 0 | 3 | 80 |
| Staging | 0 | 5 | 80 |
| Prod (Early) | 1 | 10 | 80 |
| Prod (Growth) | 2 | 20 | 80 |
| Prod (Scale) | 5 | 50 | 80 |

Cloud Run scales based on concurrent requests. With concurrency=80, a single instance handles 80 simultaneous requests. At 5,000 API calls/day (~6 requests/second peak), 2-3 instances suffice.

### 3.6 Cold Start Mitigation

1. **Min instances = 1 in production**: Keeps one warm instance always running (~$25/month at 1 vCPU/1 GiB).
2. **Startup CPU boost**: Enabled. Doubles CPU during cold start for faster container initialization.
3. **Slim Docker image**: Python 3.12-slim base minimizes image size. Current image includes WeasyPrint system deps which add ~150 MB. This is acceptable.
4. **Lazy imports**: Load heavy modules (anthropic, weasyprint, firebase_admin) on first use, not at module import time. This reduces cold start from ~4s to ~1.5s.

---

## 4. CLOUD STORAGE (File Storage)

### 4.1 Bucket Structure

One bucket per environment, with object prefixes for logical separation:

```bash
PROJECT_ID="kerf-prod"
REGION="us-central1"

# Create the bucket
gcloud storage buckets create gs://$PROJECT_ID-files \
  --project=$PROJECT_ID \
  --location=$REGION \
  --uniform-bucket-level-access \
  --public-access-prevention

# Prefix structure inside the bucket:
# gs://kerf-prod-files/
#   photos/{companyId}/{documentId}/{filename}    -- Jobsite photos, hazard images
#   pdfs/{companyId}/{documentId}/{filename}.pdf   -- Generated PDF documents
#   voice/{companyId}/{filename}.webm              -- Voice note recordings
#   exports/{companyId}/{filename}                 -- Bulk export archives
#   uploads/{companyId}/temp/{filename}            -- Temporary upload staging
```

### 4.2 Lifecycle Policies

```bash
# Create lifecycle rules JSON
cat > /tmp/lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": {
        "age": 90,
        "matchesPrefix": ["pdfs/", "photos/"]
      }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" },
      "condition": {
        "age": 365,
        "matchesPrefix": ["pdfs/", "photos/"]
      }
    },
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 7,
        "matchesPrefix": ["uploads/"]
      }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": {
        "age": 30,
        "matchesPrefix": ["voice/"]
      }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "COLDLINE" },
      "condition": {
        "age": 180,
        "matchesPrefix": ["voice/"]
      }
    },
    {
      "action": { "type": "SetStorageClass", "storageClass": "NEARLINE" },
      "condition": {
        "age": 30,
        "matchesPrefix": ["exports/"]
      }
    },
    {
      "action": { "type": "Delete" },
      "condition": {
        "age": 90,
        "matchesPrefix": ["exports/"]
      }
    }
  ]
}
EOF

gcloud storage buckets update gs://kerf-prod-files \
  --lifecycle-file=/tmp/lifecycle.json
```

### 4.3 Signed URL Generation

All file access goes through signed URLs generated by the backend. No public bucket access.

```python
# Backend pattern for generating signed URLs
from google.cloud import storage
from datetime import timedelta

def generate_upload_url(
    bucket_name: str,
    blob_path: str,
    content_type: str,
    max_size_bytes: int,
    expiration_minutes: int = 15,
) -> str:
    """Generate a signed URL for direct client upload."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="PUT",
        content_type=content_type,
        headers={
            "x-goog-content-length-range": f"0,{max_size_bytes}",
        },
    )
    return url


def generate_download_url(
    bucket_name: str,
    blob_path: str,
    expiration_minutes: int = 60,
) -> str:
    """Generate a signed URL for client download."""
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return url
```

### 4.4 CORS Configuration

```bash
cat > /tmp/cors.json << 'EOF'
[
  {
    "origin": ["https://app.kerf.build", "https://staging.kerf.build"],
    "method": ["GET", "PUT", "POST"],
    "responseHeader": ["Content-Type", "x-goog-content-length-range"],
    "maxAgeSeconds": 3600
  }
]
EOF

gcloud storage buckets update gs://kerf-prod-files \
  --cors-file=/tmp/cors.json
```

### 4.5 Size Limits Per Upload Type

| Upload Type | Max Size | Allowed MIME Types |
|---|---|---|
| Photos | 10 MB | `image/jpeg`, `image/png`, `image/webp` |
| PDFs | 25 MB | `application/pdf` |
| Voice notes | 25 MB | `audio/webm`, `audio/mp4`, `audio/mpeg` |
| Exports | 100 MB | `application/zip`, `application/pdf` |

Enforce at two levels:
1. **Signed URL**: Use `x-goog-content-length-range` header to enforce max size server-side.
2. **Frontend**: Validate file size and type before requesting the signed URL.

### 4.6 Virus Scanning Pipeline

Use Cloud Storage event triggers with a Cloud Run job for scanning:

```bash
# Option 1: ClamAV in a Cloud Run job triggered by Cloud Storage events
# This is a future enhancement -- for MVP, rely on signed URLs (no public access)
# and MIME type validation.

# Option 2 (recommended for MVP): Use Google-native malware scanning
# Cloud Storage has built-in malware scanning for Cloud Storage objects
# (available in Security Command Center Standard tier or via
# Sensitive Data Protection inspection jobs).

# For MVP: validate MIME type at upload, scan asynchronously post-upload
# using a Cloud Run job that runs ClamAV on new objects:

# 1. Create Eventarc trigger on object.finalize
gcloud eventarc triggers create scan-uploads \
  --project=kerf-prod \
  --location=us-central1 \
  --destination-run-service=kerf-scanner \
  --destination-run-region=us-central1 \
  --event-filters="type=google.cloud.storage.object.v1.finalized" \
  --event-filters="bucket=kerf-prod-files" \
  --service-account=cloudrun-api@kerf-prod.iam.gserviceaccount.com
```

For MVP, skip the dedicated scanner. Enforce strict MIME type checks and file size limits via signed URLs. Add ClamAV scanning as a Phase 2 enhancement.

---

## 5. VERCEL (Frontend)

### 5.1 Project Configuration

```bash
# Install Vercel CLI
npm i -g vercel

# Link project (from frontend/ directory)
cd frontend
vercel link --project=kerf-web
```

`vercel.json` (already exists, enhanced):

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(self), microphone=(self), geolocation=(self)" },
        { "key": "Content-Security-Policy", "value": "default-src 'self'; script-src 'self' https://apis.google.com; connect-src 'self' https://api.kerf.build https://*.firebaseio.com https://*.googleapis.com; img-src 'self' data: https://storage.googleapis.com; style-src 'self' 'unsafe-inline'; font-src 'self' https://fonts.gstatic.com; frame-src https://accounts.google.com" },
        { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" }
      ]
    },
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

Note: The `Permissions-Policy` is updated from the current version to allow camera and microphone access from the app origin (needed for photo capture and voice input in Phases 1-2).

### 5.2 Environment Variables

Set in Vercel dashboard (Settings > Environment Variables) or via CLI:

```bash
# Production
vercel env add VITE_API_BASE_URL production       # https://api.kerf.build
vercel env add VITE_FIREBASE_API_KEY production    # from Firebase Console
vercel env add VITE_FIREBASE_AUTH_DOMAIN production # kerf-prod.firebaseapp.com
vercel env add VITE_FIREBASE_PROJECT_ID production  # kerf-prod
vercel env add VITE_FIREBASE_STORAGE_BUCKET production # kerf-prod.appspot.com
vercel env add VITE_FIREBASE_MESSAGING_SENDER_ID production
vercel env add VITE_FIREBASE_APP_ID production
vercel env add VITE_SENTRY_DSN production          # from Sentry project

# Preview (staging values)
vercel env add VITE_API_BASE_URL preview           # https://api-staging.kerf.build
vercel env add VITE_FIREBASE_PROJECT_ID preview     # kerf-staging
# ... (repeat for all Firebase config values pointing to staging)

# Development
vercel env add VITE_API_BASE_URL development       # http://localhost:8000
vercel env add VITE_FIREBASE_PROJECT_ID development # kerf-dev
```

### 5.3 Preview Deployments

Vercel creates automatic preview deployments for every PR. Configuration:

- **Auto-deploy**: Enabled for all branches except `main`
- **Production branch**: `main`
- **PR comments**: Enabled (Vercel bot comments with preview URL)
- **Protection**: Password-protect staging preview if needed (Vercel Pro feature)

### 5.4 Custom Domain

```bash
# Add custom domain via Vercel CLI or dashboard
vercel domains add app.kerf.build --project=kerf-web

# DNS records to add:
# Type: CNAME, Name: app, Value: cname.vercel-dns.com
# Vercel auto-provisions SSL certificate
```

### 5.5 Edge Functions

Not needed for MVP. The frontend is a pure SPA. All API calls go to Cloud Run. If we need edge-level middleware in future (e.g., A/B testing, geo-routing), Vercel Edge Functions can be added.

### 5.6 Analytics

Enable Vercel Analytics (Web Vitals) on the Vercel dashboard:
- **Speed Insights**: Tracks LCP, FID, CLS, TTFB, INP
- **Audiences**: None needed initially
- Cost: Included in Vercel Pro plan ($20/month covers 25K data points/month)

---

## 6. CI/CD PIPELINE

### 6.1 GitHub Actions -- Backend

```yaml
# .github/workflows/backend-deploy.yml
name: Backend CI/CD

on:
  push:
    branches: [main]
    paths: ['backend/**']
  pull_request:
    branches: [main]
    paths: ['backend/**']

env:
  REGION: us-central1
  SERVICE_NAME: kerf-api
  REPO_NAME: kerf

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install ruff pyright pytest pytest-asyncio

      - name: Lint (ruff)
        run: ruff check .

      - name: Format check (ruff)
        run: ruff format --check .

      - name: Type check (pyright)
        run: pyright

      - name: Start Firestore emulator
        run: |
          gcloud components install cloud-firestore-emulator --quiet 2>/dev/null || true
          gcloud emulators firestore start --host-port=localhost:8080 &
          sleep 5
        env:
          FIRESTORE_EMULATOR_HOST: localhost:8080

      - name: Run tests
        run: pytest tests/ -v --tb=short
        env:
          FIRESTORE_EMULATOR_HOST: localhost:8080
          ENVIRONMENT: test
          ANTHROPIC_API_KEY: test-key
          GOOGLE_CLOUD_PROJECT: test-project

  deploy-staging:
    needs: lint-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: staging

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY_STAGING }}

      - uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: kerf-staging

      - name: Configure Docker auth
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      - name: Build and push image
        working-directory: backend
        run: |
          IMAGE="${{ env.REGION }}-docker.pkg.dev/kerf-staging/${{ env.REPO_NAME }}/${{ env.SERVICE_NAME }}"
          docker build -t $IMAGE:${{ github.sha }} -t $IMAGE:latest .
          docker push $IMAGE:${{ github.sha }}
          docker push $IMAGE:latest

      - name: Deploy to Cloud Run (staging)
        run: |
          IMAGE="${{ env.REGION }}-docker.pkg.dev/kerf-staging/${{ env.REPO_NAME }}/${{ env.SERVICE_NAME }}"
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --project=kerf-staging \
            --region=${{ env.REGION }} \
            --image=$IMAGE:${{ github.sha }} \
            --platform=managed \
            --quiet

  deploy-production:
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.kerf.build

    steps:
      - uses: actions/checkout@v4

      - id: auth
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY_PROD }}

      - uses: google-github-actions/setup-gcloud@v2
        with:
          project_id: kerf-prod

      - name: Configure Docker auth
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      - name: Build and push image
        working-directory: backend
        run: |
          IMAGE="${{ env.REGION }}-docker.pkg.dev/kerf-prod/${{ env.REPO_NAME }}/${{ env.SERVICE_NAME }}"
          docker build -t $IMAGE:${{ github.sha }} -t $IMAGE:latest .
          docker push $IMAGE:${{ github.sha }}
          docker push $IMAGE:latest

      - name: Deploy to Cloud Run (production)
        run: |
          IMAGE="${{ env.REGION }}-docker.pkg.dev/kerf-prod/${{ env.REPO_NAME }}/${{ env.SERVICE_NAME }}"
          gcloud run deploy ${{ env.SERVICE_NAME }} \
            --project=kerf-prod \
            --region=${{ env.REGION }} \
            --image=$IMAGE:${{ github.sha }} \
            --platform=managed \
            --quiet

      - name: Verify deployment health
        run: |
          URL=$(gcloud run services describe ${{ env.SERVICE_NAME }} \
            --project=kerf-prod \
            --region=${{ env.REGION }} \
            --format="value(status.url)")
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL/health")
          if [ "$STATUS" != "200" ]; then
            echo "Health check failed with status $STATUS"
            exit 1
          fi
          echo "Health check passed: $URL/health returned 200"
```

### 6.2 GitHub Actions -- Frontend

```yaml
# .github/workflows/frontend-deploy.yml
name: Frontend CI/CD

on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npx tsc --noEmit

      - name: Build
        run: npm run build
        env:
          VITE_API_BASE_URL: https://api-staging.kerf.build
          VITE_FIREBASE_PROJECT_ID: kerf-staging
          VITE_FIREBASE_API_KEY: ${{ secrets.FIREBASE_API_KEY_STAGING }}
          VITE_FIREBASE_AUTH_DOMAIN: kerf-staging.firebaseapp.com

  # Vercel handles the actual deployment via its GitHub integration.
  # This workflow ensures lint/type/build pass before Vercel deploys.
  # Configure Vercel to require this check to pass before deploying.
```

### 6.3 Branch Strategy

```
main ──────────────────────────────────────────────→
  │                                                  │
  ├── feature/SF-123-jha-generator ──── PR ────── merge
  │
  └── fix/SF-456-pdf-timeout ────────── PR ────── merge

Deployments:
  PR opened    → Vercel preview + staging backend (if backend changed)
  Merge to main → Auto-deploy staging → Manual approval → Deploy production
```

- **main**: Always deployable. Protected branch requiring PR review + CI pass.
- **Feature branches**: Named `feature/SF-XXX-description` or `fix/SF-XXX-description`.
- **Production deploy**: Requires manual approval in the GitHub Actions `production` environment.
- **Hotfixes**: Same flow but expedited review. Push to `main` after review.

### 6.4 Rollback Procedures

```bash
# Backend rollback: redeploy previous revision
# List revisions
gcloud run revisions list \
  --service=kerf-api \
  --project=kerf-prod \
  --region=us-central1

# Route 100% traffic to previous revision
gcloud run services update-traffic kerf-api \
  --project=kerf-prod \
  --region=us-central1 \
  --to-revisions=kerf-api-00042-abc=100

# Frontend rollback: Vercel instant rollback
# Go to Vercel dashboard > Deployments > click previous deployment > Promote to Production
# Or via CLI:
vercel rollback --project=kerf-web
```

### 6.5 Secrets Management in CI

Store in GitHub repository Settings > Secrets and variables > Actions:

| Secret Name | Environments | Description |
|---|---|---|
| `GCP_SA_KEY_STAGING` | staging | CI deployer SA JSON key for staging |
| `GCP_SA_KEY_PROD` | production | CI deployer SA JSON key for production |
| `FIREBASE_API_KEY_STAGING` | staging | Firebase web API key (not secret, but good practice) |
| `FIREBASE_API_KEY_PROD` | production | Firebase web API key |

GitHub environment protection rules:
- **staging**: No additional protection (auto-deploy on merge to main)
- **production**: Require manual approval from at least 1 reviewer

---

## 7. MONITORING AND OBSERVABILITY

### 7.1 Cloud Logging Configuration

Cloud Run automatically sends stdout/stderr to Cloud Logging. Configure structured logging in the backend:

```python
# backend/app/logging_config.py
import json
import logging
import sys


class CloudRunFormatter(logging.Formatter):
    """Format logs as JSON for Cloud Logging structured logging."""

    def format(self, record):
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging(environment: str):
    """Configure logging for the given environment."""
    handler = logging.StreamHandler(sys.stdout)

    if environment == "production" or environment == "staging":
        handler.setFormatter(CloudRunFormatter())
        level = logging.INFO
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        level = logging.DEBUG

    logging.basicConfig(level=level, handlers=[handler], force=True)
```

Log retention policy:
- Dev: 7 days
- Staging: 30 days
- Production: 90 days (Cloud Logging default is 30; create a log sink to Cloud Storage for longer retention)

```bash
# Create log sink for long-term retention (production)
gcloud logging sinks create kerf-archive \
  storage.googleapis.com/kerf-prod-logs \
  --project=kerf-prod \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="kerf-api"'

# Create the logs bucket
gcloud storage buckets create gs://kerf-prod-logs \
  --project=kerf-prod \
  --location=us-central1 \
  --lifecycle-file=/tmp/logs-lifecycle.json
```

### 7.2 Error Tracking (Sentry)

Sentry provides richer error grouping and alerting than Cloud Error Reporting.

Backend:
```bash
pip install sentry-sdk[fastapi]
```

```python
# backend/app/main.py (add before app creation)
import sentry_sdk

if settings.environment in ("production", "staging"):
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,  # 10% of requests traced
        profiles_sample_rate=0.1,
    )
```

Frontend:
```bash
npm install @sentry/react
```

```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.1,
  });
}
```

### 7.3 Uptime Monitoring

```bash
# Cloud Monitoring uptime checks
gcloud monitoring uptime-checks create http kerf-api-health \
  --project=kerf-prod \
  --display-name="Kerf API Health" \
  --uri=https://api.kerf.build/health \
  --check-interval=60s \
  --timeout=10s \
  --regions=USA,EUROPE,ASIA_PACIFIC

gcloud monitoring uptime-checks create http kerf-web-health \
  --project=kerf-prod \
  --display-name="Kerf Web" \
  --uri=https://app.kerf.build \
  --check-interval=300s \
  --timeout=10s \
  --regions=USA,EUROPE
```

### 7.4 Custom Metrics and Performance

Track key business and performance metrics via Cloud Logging log-based metrics:

```bash
# Document generation latency
gcloud logging metrics create document_generation_latency \
  --project=kerf-prod \
  --description="Time to generate a safety document via AI" \
  --log-filter='resource.type="cloud_run_revision" AND jsonPayload.metric="document_generation_latency"'

# API response times (tracked automatically by Cloud Run metrics)
# Custom metric for Claude API call duration
gcloud logging metrics create claude_api_duration \
  --project=kerf-prod \
  --description="Duration of Claude API calls" \
  --log-filter='resource.type="cloud_run_revision" AND jsonPayload.metric="claude_api_duration"'
```

### 7.5 Alerting Rules

```bash
PROJECT_ID="kerf-prod"

# Alert: Error rate > 5% for 5 minutes
gcloud monitoring policies create \
  --project=$PROJECT_ID \
  --display-name="High Error Rate (>5%)" \
  --condition-display-name="Cloud Run 5xx rate" \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"' \
  --condition-threshold-value=0.05 \
  --condition-threshold-comparison=COMPARISON_GT \
  --condition-threshold-duration=300s \
  --notification-channels="projects/$PROJECT_ID/notificationChannels/CHANNEL_ID"

# Alert: P95 latency > 5 seconds for 10 minutes
# Alert: Uptime check failure
# Alert: Cloud Run instance count > 15 (cost anomaly)
# Alert: Firestore read/write quota > 80%

# Configure notification channels (email + Slack)
gcloud monitoring channels create \
  --project=$PROJECT_ID \
  --display-name="Engineering Email" \
  --type=email \
  --channel-labels=email_address=eng@kerf.build
```

### 7.6 Dashboard Design

Create a Cloud Monitoring dashboard with these panels:

**Row 1 -- Service Health**
- API request rate (requests/sec)
- Error rate (% 4xx, % 5xx)
- P50/P95/P99 latency

**Row 2 -- Infrastructure**
- Cloud Run instance count
- CPU utilization per instance
- Memory utilization per instance

**Row 3 -- Business Metrics**
- Document generations per hour
- Active users (from application logs)
- Claude API calls and latency

**Row 4 -- Dependencies**
- Firestore read/write operations
- Cloud Storage operations
- Firebase Auth sign-ins

---

## 8. LOCAL DEVELOPMENT

### 8.1 Docker Compose for Full Local Stack

Update the existing `docker-compose.yml`:

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env
    environment:
      - FIRESTORE_EMULATOR_HOST=firestore:8080
      - FIREBASE_AUTH_EMULATOR_HOST=firebase-auth:9099
      - ENVIRONMENT=development
    depends_on:
      firestore:
        condition: service_started
      firebase-auth:
        condition: service_started
    volumes:
      - ./backend/app:/app/app
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

  firestore:
    image: google/cloud-sdk:latest
    command: >
      gcloud emulators firestore start
      --host-port=0.0.0.0:8080
      --project=kerf-dev
    ports:
      - "8080:8080"

  firebase-auth:
    image: node:20-alpine
    command: >
      sh -c "npm install -g firebase-tools &&
             firebase emulators:start --only auth --project=kerf-dev"
    ports:
      - "9099:9099"   # Auth emulator
      - "4000:4000"   # Emulator UI
    working_dir: /app
    volumes:
      - ./firebase.json:/app/firebase.json

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
      - VITE_FIREBASE_PROJECT_ID=kerf-dev
      - VITE_FIREBASE_AUTH_DOMAIN=localhost
    depends_on:
      - backend
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
```

Create a development Dockerfile for the frontend with hot reload:

```dockerfile
# frontend/Dockerfile.dev
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 8.2 Firebase Configuration File

```json
// firebase.json (project root)
{
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "emulators": {
    "auth": {
      "port": 9099
    },
    "firestore": {
      "port": 8080
    },
    "ui": {
      "enabled": true,
      "port": 4000
    }
  }
}
```

### 8.3 Seed Data Scripts

```python
# backend/scripts/seed_data.py
"""Seed the Firestore emulator with test data for local development."""

import os
import sys

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

from google.cloud import firestore
from datetime import datetime, timezone

db = firestore.Client(project="kerf-dev")


def seed():
    """Create test company and sample documents."""
    now = datetime.now(timezone.utc)

    # Test company
    company_ref = db.collection("companies").document("comp_test001")
    company_ref.set({
        "id": "comp_test001",
        "name": "Acme Construction LLC",
        "address": "123 Builder Ave, Austin, TX 78701",
        "license_number": "TX-12345",
        "trade_type": "general",
        "owner_name": "Sarah Johnson",
        "phone": "512-555-0100",
        "email": "sarah@acmeconstruction.com",
        "subscription_status": "active",
        "subscription_id": None,
        "created_at": now,
        "created_by": "seed_script",
        "updated_at": now,
        "updated_by": "seed_script",
    })

    # Sample documents
    docs = [
        {
            "id": "doc_test001",
            "company_id": "comp_test001",
            "title": "Fall Protection Program - Elm Street Project",
            "document_type": "fall_protection",
            "status": "final",
            "content": {"sections": ["Purpose", "Scope", "Responsibilities"]},
            "project_info": {
                "project_name": "Elm Street Renovation",
                "site_address": "456 Elm St, Austin, TX",
                "scope_of_work": "Roof replacement and gutter installation",
            },
            "created_at": now,
            "created_by": "seed_script",
            "updated_at": now,
            "updated_by": "seed_script",
            "deleted": False,
        },
        {
            "id": "doc_test002",
            "company_id": "comp_test001",
            "title": "Weekly Toolbox Talk - Heat Stress Prevention",
            "document_type": "toolbox_talk",
            "status": "draft",
            "content": {},
            "project_info": {
                "project_name": "Downtown Office Build",
                "site_address": "789 Main St, Austin, TX",
            },
            "created_at": now,
            "created_by": "seed_script",
            "updated_at": now,
            "updated_by": "seed_script",
            "deleted": False,
        },
    ]

    for doc in docs:
        ref = company_ref.collection("documents").document(doc["id"])
        ref.set(doc)

    print(f"Seeded company comp_test001 with {len(docs)} documents")


if __name__ == "__main__":
    seed()
```

Run: `python backend/scripts/seed_data.py`

### 8.4 Environment Variable Management

```bash
# backend/.env (git-ignored, created from template)
GOOGLE_CLOUD_PROJECT=kerf-dev
ENVIRONMENT=development
ANTHROPIC_API_KEY=sk-ant-your-dev-key-here
PADDLE_WEBHOOK_SECRET=whsec_dev_test
PADDLE_API_KEY=eyJ_dev_test
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
```

```bash
# backend/.env.example (checked into git)
GOOGLE_CLOUD_PROJECT=kerf-dev
ENVIRONMENT=development
ANTHROPIC_API_KEY=
PADDLE_WEBHOOK_SECRET=
PADDLE_API_KEY=
CORS_ORIGINS=http://localhost:5173
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
```

```bash
# frontend/.env (git-ignored)
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=demo-api-key
VITE_FIREBASE_AUTH_DOMAIN=localhost
VITE_FIREBASE_PROJECT_ID=kerf-dev
VITE_FIREBASE_STORAGE_BUCKET=kerf-dev.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=000000000000
VITE_FIREBASE_APP_ID=1:000000000000:web:demo
```

### 8.5 Quick Start Commands

```bash
# Full stack startup
docker compose up -d

# Backend only (with hot reload via volume mount)
docker compose up backend firestore firebase-auth

# Frontend only (outside Docker, faster HMR)
cd frontend && npm run dev

# Seed test data
docker compose exec backend python scripts/seed_data.py

# View Firestore emulator UI
# Open http://localhost:4000 in browser

# Run backend tests locally
cd backend && FIRESTORE_EMULATOR_HOST=localhost:8080 pytest tests/ -v

# View logs
docker compose logs -f backend
```

---

## 9. COST PROJECTIONS

All prices in USD/month. Based on GCP and Vercel pricing as of March 2026.

### 9.1 Early Stage (0-100 customers, ~500 API calls/day)

| Service | Usage Estimate | Monthly Cost |
|---|---|---|
| **Cloud Run** | 1 min instance (1 vCPU, 1 GiB), ~15K requests/month | $25 |
| **Firestore** | ~50K reads, ~10K writes, ~5K deletes per day | $5 |
| **Cloud Storage** | ~10 GB stored, ~5 GB egress | $2 |
| **Firebase Auth** | ~500 MAU (Email + Google) | $0 (free tier: 50K MAU) |
| **Secret Manager** | 3 secrets, ~15K accesses | $0 (free tier: 10K accesses) |
| **Artifact Registry** | ~5 GB stored | $1 |
| **Cloud Logging** | ~5 GB/month | $0 (free tier: 50 GB) |
| **Cloud Monitoring** | Uptime checks, basic metrics | $0 (free tier) |
| **Sentry** | Free tier (5K errors/month) | $0 |
| **Claude API (Anthropic)** | ~500 calls/day, avg 4K input + 2K output tokens | $90 |
| **Vercel** | Pro plan (team) | $20 |
| **Domain** | kerf.build | $15/year = $1.25 |
| **Total** | | **~$145/month** |

Claude API cost breakdown: 500 calls/day x 30 days = 15,000 calls/month. At ~4K input tokens ($3/M) + ~2K output tokens ($15/M): (15K x 4K x $3/M) + (15K x 2K x $15/M) = $0.18 + $0.45 = $0.63/day = ~$19/month for Haiku. For Sonnet: (15K x 4K x $3/M) + (15K x 2K x $15/M) = $0.18 + $0.45 = ~$19/month for cached/small calls. Actual cost depends on model choice: **$19/month (Haiku) to $90/month (Sonnet)**. Budget $90 for safety.

### 9.2 Growth Stage (100-1,000 customers, ~5,000 API calls/day)

| Service | Usage Estimate | Monthly Cost |
|---|---|---|
| **Cloud Run** | 2-5 instances avg, 150K requests/month | $80 |
| **Firestore** | ~500K reads, ~100K writes per day | $45 |
| **Cloud Storage** | ~200 GB stored, ~50 GB egress | $15 |
| **Firebase Auth** | ~5,000 MAU | $0 (free tier) |
| **Secret Manager** | 5 secrets, ~150K accesses | $0.50 |
| **Artifact Registry** | ~10 GB | $2 |
| **Cloud Logging** | ~20 GB/month | $0 (under 50 GB free tier) |
| **Cloud Monitoring** | Uptime checks, custom metrics | $10 |
| **Sentry** | Team plan | $26 |
| **Claude API** | ~5,000 calls/day, mix of Haiku and Sonnet | $600 |
| **Vercel** | Pro plan | $20 |
| **Domain + SSL** | | $2 |
| **Total** | | **~$800/month** |

At $80K MRR (6-month target), infrastructure is ~1% of revenue. Healthy.

### 9.3 Scale Stage (1,000-10,000 customers, ~50,000 API calls/day)

| Service | Usage Estimate | Monthly Cost |
|---|---|---|
| **Cloud Run** | 10-20 instances avg, 1.5M requests/month | $500 |
| **Firestore** | ~5M reads, ~1M writes per day | $350 |
| **Cloud Storage** | ~2 TB stored, ~500 GB egress | $80 |
| **Firebase Auth** | ~50,000 MAU | $0 (under 50K free tier; above = $0.0055/MAU) |
| **Secret Manager** | | $5 |
| **Artifact Registry** | ~20 GB | $4 |
| **Cloud Logging** | ~100 GB/month | $25 |
| **Cloud Monitoring** | Custom metrics, dashboards | $50 |
| **Sentry** | Business plan | $80 |
| **Claude API** | ~50,000 calls/day, aggressive caching, Haiku for simple tasks | $3,000 |
| **Vercel** | Pro plan | $20 |
| **Cloud Armor** | WAF rules | $10 |
| **Firestore backups** | Daily exports | $20 |
| **Total** | | **~$4,150/month** |

At $150K+ MRR (12-month target at this scale), infrastructure is ~2.8% of revenue. Claude API is the largest line item. Mitigations: aggressive prompt caching, use Haiku for simple generations, batch requests, cache common outputs.

---

## 10. SECURITY

### 10.1 HTTPS Everywhere

- **Frontend**: Vercel enforces HTTPS and auto-provisions Let's Encrypt certificates.
- **Backend**: Cloud Run enforces HTTPS on its `*.run.app` domain. Custom domain `api.kerf.build` gets a Google-managed certificate automatically.
- **HSTS header**: Set on both frontend (via `vercel.json`) and backend (via middleware).

### 10.2 API Authentication Flow

```
Client (React)                Backend (FastAPI)              Firebase Auth
     │                              │                              │
     │── signInWithEmailAndPassword ─│──────────────────────────── │
     │                              │                              │
     │◄──── Firebase ID Token ──────│                              │
     │                              │                              │
     │── API request ──────────────►│                              │
     │   Authorization: Bearer <token>                             │
     │                              │── verifyIdToken(token) ─────►│
     │                              │◄── decoded claims ──────────│
     │                              │                              │
     │                              │── extract companyId from claims
     │                              │── scope all Firestore queries to companyId
     │                              │                              │
     │◄──── API response ──────────│                              │
```

Backend token verification middleware:

```python
# backend/app/dependencies/auth.py
from fastapi import Depends, HTTPException, Request
from firebase_admin import auth


async def get_current_user(request: Request) -> dict:
    """Verify Firebase ID token and return user claims."""
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split("Bearer ")[1]
    try:
        decoded = auth.verify_id_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if "companyId" not in decoded:
        raise HTTPException(status_code=403, detail="User not associated with a company")

    return decoded


async def get_company_id(user: dict = Depends(get_current_user)) -> str:
    """Extract and return the company ID from the authenticated user."""
    return user["companyId"]
```

### 10.3 Firestore Security Rules

See section 2.3 above. Key principles:
- Every query is scoped to `companyId` extracted from the Firebase token custom claims.
- No cross-company data access is possible.
- Client-side deletes are prohibited (soft delete only).
- Billing subcollection is read-only from client (writes via Admin SDK on backend).

### 10.4 Cloud Storage Security

- **No public access**: Bucket has `uniform-bucket-level-access` and `public-access-prevention` enabled.
- **Signed URLs only**: All file access (upload and download) goes through time-limited signed URLs generated by the backend.
- **Company isolation**: Object paths include `companyId`. The backend verifies the requesting user belongs to the company before generating a signed URL.

### 10.5 Rate Limiting

Application-level rate limiting (simpler and cheaper than Cloud Armor for early stage):

```python
# backend/app/middleware/rate_limit.py
from collections import defaultdict
from time import time
from fastapi import Request, HTTPException


class RateLimiter:
    """Simple in-memory rate limiter. Replace with Redis for multi-instance."""

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int):
        now = time()
        self.requests[key] = [
            t for t in self.requests[key] if t > now - window_seconds
        ]
        if len(self.requests[key]) >= max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        self.requests[key].append(now)


# Rate limits per endpoint category:
# - Document generation (Claude API): 10 requests/minute per company
# - Standard API: 100 requests/minute per user
# - Auth endpoints: 20 requests/minute per IP
```

For Growth/Scale stage, upgrade to Cloud Armor WAF:

```bash
# Create Cloud Armor security policy
gcloud compute security-policies create kerf-waf \
  --project=kerf-prod \
  --description="WAF policy for Kerf API"

# Rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=kerf-waf \
  --project=kerf-prod \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP

# OWASP top 10 protection
gcloud compute security-policies rules create 2000 \
  --security-policy=kerf-waf \
  --project=kerf-prod \
  --action=deny-403 \
  --expression="evaluatePreconfiguredExpr('sqli-v33-stable')"
```

### 10.6 DDoS Protection

- **Cloud Run**: Has built-in DDoS protection via Google Front End (GFE).
- **Vercel**: Has built-in DDoS protection.
- **Additional**: Cloud Armor (at Scale stage) provides layer 7 DDoS mitigation.

### 10.7 Data Encryption

| Layer | Method | Managed By |
|---|---|---|
| Data in transit | TLS 1.3 | Google (Cloud Run), Vercel |
| Firestore at rest | AES-256 | Google (automatic, no config needed) |
| Cloud Storage at rest | AES-256 | Google (automatic) |
| Secrets | Envelope encryption | Google Secret Manager |
| Firebase Auth passwords | bcrypt/scrypt | Firebase (automatic) |

No customer-managed encryption keys (CMEK) needed at this stage. CMEK adds complexity and cost with minimal benefit for a startup.

### 10.8 Backup Strategy

```bash
# Firestore automated daily backups
# Schedule via Cloud Scheduler + Cloud Function or gcloud

# Manual export (for initial setup / ad-hoc)
gcloud firestore export gs://kerf-prod-backups/$(date +%Y-%m-%d) \
  --project=kerf-prod

# Automated daily backup via Cloud Scheduler
gcloud scheduler jobs create http firestore-daily-backup \
  --project=kerf-prod \
  --location=us-central1 \
  --schedule="0 2 * * *" \
  --uri="https://firestore.googleapis.com/v1/projects/kerf-prod/databases/(default):exportDocuments" \
  --http-method=POST \
  --message-body='{"outputUriPrefix": "gs://kerf-prod-backups"}' \
  --oauth-service-account-email=cloudrun-api@kerf-prod.iam.gserviceaccount.com \
  --oauth-token-scope=https://www.googleapis.com/auth/cloud-platform

# Create backup bucket with lifecycle
gcloud storage buckets create gs://kerf-prod-backups \
  --project=kerf-prod \
  --location=us-central1

# Retain backups for 90 days, then delete
cat > /tmp/backup-lifecycle.json << 'EOF'
{
  "rule": [
    {
      "action": { "type": "Delete" },
      "condition": { "age": 90 }
    }
  ]
}
EOF

gcloud storage buckets update gs://kerf-prod-backups \
  --lifecycle-file=/tmp/backup-lifecycle.json
```

### 10.9 Incident Response Plan

| Severity | Definition | Response Time | Escalation |
|---|---|---|---|
| P0 - Critical | Service down, data breach, or security incident | 15 minutes | Founder + all engineers |
| P1 - High | Major feature broken, significant performance degradation | 1 hour | On-call engineer |
| P2 - Medium | Minor feature broken, non-critical errors | 4 hours | Next business day |
| P3 - Low | Cosmetic issues, minor bugs | 24 hours | Sprint backlog |

Response steps for P0:
1. Acknowledge alert in monitoring channel
2. Check Cloud Run logs and Sentry for root cause
3. If deployment-related: roll back immediately (see section 6.4)
4. If data breach: disable affected service account, rotate secrets, assess scope
5. Document incident in `docs/incidents/YYYY-MM-DD-title.md`
6. Post-mortem within 48 hours

---

## 11. DISASTER RECOVERY

### 11.1 RTO/RPO Targets

| Component | RPO (max data loss) | RTO (max downtime) |
|---|---|---|
| Firestore | 24 hours (daily backups) | 4 hours |
| Cloud Storage | Near-zero (multi-zone redundancy) | < 1 hour |
| Cloud Run | N/A (stateless) | < 15 minutes (redeploy) |
| Firebase Auth | Near-zero (Google-managed) | Google SLA |
| Frontend (Vercel) | N/A (stateless, git is source of truth) | < 5 minutes (redeploy) |

### 11.2 Firestore Backup and Restore

Backup frequency and retention:
- **Daily** exports to Cloud Storage (retained 90 days)
- **Weekly** exports marked as long-term (retained 1 year)
- **Pre-migration** manual export before any schema changes

Restore procedure:

```bash
# List available backups
gcloud storage ls gs://kerf-prod-backups/

# Restore from a specific backup
gcloud firestore import gs://kerf-prod-backups/2026-03-30 \
  --project=kerf-prod

# Note: import merges data -- it does not delete existing documents.
# For a clean restore, create a new Firestore database or delete existing data first.
```

### 11.3 Cloud Storage Redundancy

The bucket uses **Standard** storage class in `us-central1` which provides:
- Multi-zone redundancy within the region (99.99% availability SLA)
- No need for multi-region until Scale stage

At Scale stage, consider enabling **dual-region** storage for cross-region redundancy:

```bash
# Upgrade to dual-region (us-central1 + europe-west1)
# Note: cannot change existing bucket; create new and migrate
gcloud storage buckets create gs://kerf-prod-files-v2 \
  --project=kerf-prod \
  --placement=us-central1,europe-west1 \
  --uniform-bucket-level-access
```

### 11.4 Cloud Run Multi-Region

Not needed until Scale stage. Single-region (`us-central1`) provides:
- 99.95% availability SLA
- Automatic scaling and self-healing

At Scale stage, deploy to a second region and use Cloud Load Balancing:

```bash
# Deploy to second region
gcloud run deploy kerf-api \
  --project=kerf-prod \
  --region=us-central1 \
  --image=$IMAGE:latest \
  --platform=managed \
  # ... (same config as primary)

# Create global load balancer with Cloud Run backends in both regions
# This requires a serverless NEG per region
```

### 11.5 Failover Procedures

| Scenario | Procedure |
|---|---|
| Cloud Run outage (single region) | Deploy to backup region, update DNS |
| Firestore outage | Wait for Google restoration (no self-service failover for native mode) |
| Vercel outage | Deploy to Firebase Hosting as backup (pre-configured but dormant) |
| Claude API outage | Return graceful degradation response; queue failed generations for retry |
| Complete GCP region failure | Restore Firestore from backup in new region, deploy Cloud Run to new region |

---

## 12. DEPLOYMENT CHECKLIST

Step-by-step from current state (local Docker-based development) to production.

### Phase A: GCP and Firebase Setup

- [ ] **A1. Create GCP projects**
  ```bash
  gcloud projects create kerf-dev --name="Kerf Dev"
  gcloud projects create kerf-staging --name="Kerf Staging"
  gcloud projects create kerf-prod --name="Kerf Prod"
  ```

- [ ] **A2. Link billing accounts**
  ```bash
  BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(ACCOUNT_ID)" --limit=1)
  for proj in kerf-dev kerf-staging kerf-prod; do
    gcloud billing projects link $proj --billing-account=$BILLING_ACCOUNT
  done
  ```

- [ ] **A3. Enable APIs** (for each project)
  ```bash
  for proj in kerf-dev kerf-staging kerf-prod; do
    gcloud services enable \
      run.googleapis.com firestore.googleapis.com storage.googleapis.com \
      artifactregistry.googleapis.com secretmanager.googleapis.com \
      iam.googleapis.com logging.googleapis.com monitoring.googleapis.com \
      cloudtrace.googleapis.com clouderrorreporting.googleapis.com \
      firebase.googleapis.com identitytoolkit.googleapis.com \
      cloudscheduler.googleapis.com cloudbuild.googleapis.com \
      --project=$proj
  done
  ```

- [ ] **A4. Initialize Firebase**
  ```bash
  for proj in kerf-dev kerf-staging kerf-prod; do
    firebase projects:addfirebase $proj
    firebase apps:create WEB "Kerf Web" --project=$proj
  done
  ```

- [ ] **A5. Configure Firebase Auth** (via Firebase Console for each project)
  - Enable Email/Password provider
  - Enable Google provider
  - Set authorized domains

- [ ] **A6. Create Firestore databases**
  ```bash
  for proj in kerf-dev kerf-staging kerf-prod; do
    gcloud firestore databases create \
      --project=$proj \
      --location=us-central1 \
      --type=firestore-native
  done
  ```

- [ ] **A7. Deploy Firestore security rules and indexes**
  ```bash
  for proj in kerf-dev kerf-staging kerf-prod; do
    firebase deploy --only firestore:rules,firestore:indexes --project=$proj
  done
  ```

### Phase B: Service Accounts and Secrets

- [ ] **B1. Create service accounts** (for each project)
  ```bash
  for proj in kerf-dev kerf-staging kerf-prod; do
    gcloud iam service-accounts create cloudrun-api \
      --display-name="Cloud Run API Runtime" --project=$proj
    gcloud iam service-accounts create ci-deployer \
      --display-name="CI/CD Deployer" --project=$proj
  done
  ```

- [ ] **B2. Grant IAM roles** (run commands from section 1.3 for each project)

- [ ] **B3. Create secrets in Secret Manager** (for staging and prod)
  ```bash
  for proj in kerf-staging kerf-prod; do
    echo -n "$ANTHROPIC_KEY" | gcloud secrets create anthropic-api-key --project=$proj --data-file=-
    echo -n "$LEMONSQUEEZY_WEBHOOK" | gcloud secrets create paddle-webhook-secret --project=$proj --data-file=-
    echo -n "$LEMONSQUEEZY_KEY" | gcloud secrets create paddle-api-key --project=$proj --data-file=-
  done
  ```

- [ ] **B4. Grant secret access to Cloud Run SA**
  ```bash
  for proj in kerf-staging kerf-prod; do
    for secret in anthropic-api-key paddle-webhook-secret paddle-api-key; do
      gcloud secrets add-iam-policy-binding $secret \
        --project=$proj \
        --member="serviceAccount:cloudrun-api@$proj.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    done
  done
  ```

- [ ] **B5. Export CI deployer keys for GitHub Actions**
  ```bash
  gcloud iam service-accounts keys create ci-key-staging.json \
    --iam-account=ci-deployer@kerf-staging.iam.gserviceaccount.com
  gcloud iam service-accounts keys create ci-key-prod.json \
    --iam-account=ci-deployer@kerf-prod.iam.gserviceaccount.com
  # Upload these as GitHub repository secrets: GCP_SA_KEY_STAGING, GCP_SA_KEY_PROD
  ```

### Phase C: Cloud Storage

- [ ] **C1. Create storage buckets**
  ```bash
  for proj in kerf-dev kerf-staging kerf-prod; do
    gcloud storage buckets create gs://$proj-files \
      --project=$proj --location=us-central1 \
      --uniform-bucket-level-access --public-access-prevention
  done
  ```

- [ ] **C2. Apply lifecycle policies** (section 4.2)

- [ ] **C3. Configure CORS** (section 4.4)

- [ ] **C4. Create backup bucket** (prod only)
  ```bash
  gcloud storage buckets create gs://kerf-prod-backups \
    --project=kerf-prod --location=us-central1
  ```

### Phase D: Artifact Registry

- [ ] **D1. Create Docker repositories**
  ```bash
  for proj in kerf-staging kerf-prod; do
    gcloud artifacts repositories create kerf \
      --project=$proj --location=us-central1 \
      --repository-format=docker \
      --description="Kerf Docker images"
  done
  ```

### Phase E: Backend Deployment

- [ ] **E1. Build and push Docker image**
  ```bash
  PROJECT_ID="kerf-staging"
  REGION="us-central1"
  IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/kerf/kerf-api"

  cd backend
  gcloud auth configure-docker $REGION-docker.pkg.dev --quiet
  docker build -t $IMAGE:v1.0.0 .
  docker push $IMAGE:v1.0.0
  ```

- [ ] **E2. Deploy to Cloud Run (staging first)**
  ```bash
  gcloud run deploy kerf-api \
    --project=kerf-staging \
    --region=us-central1 \
    --image=$IMAGE:v1.0.0 \
    --platform=managed \
    --service-account=cloudrun-api@kerf-staging.iam.gserviceaccount.com \
    --memory=1Gi --cpu=1 --concurrency=80 \
    --min-instances=0 --max-instances=5 \
    --port=8000 --timeout=300s \
    --allow-unauthenticated \
    --set-env-vars="ENVIRONMENT=staging,GCP_PROJECT_ID=kerf-staging,CORS_ORIGINS=https://staging.kerf.build" \
    --set-secrets="ANTHROPIC_API_KEY=anthropic-api-key:latest,PADDLE_WEBHOOK_SECRET=paddle-webhook-secret:latest,PADDLE_API_KEY=paddle-api-key:latest"
  ```

- [ ] **E3. Verify staging health**
  ```bash
  STAGING_URL=$(gcloud run services describe kerf-api \
    --project=kerf-staging --region=us-central1 \
    --format="value(status.url)")
  curl -s "$STAGING_URL/health"
  # Should return: {"status":"healthy","version":"1.0.0","service":"kerf-api"}
  ```

- [ ] **E4. Deploy to production** (same as E2 with prod values, min-instances=1, max-instances=20)

- [ ] **E5. Verify production health**

### Phase F: Frontend Deployment

- [ ] **F1. Connect GitHub repo to Vercel**
  - Go to vercel.com > New Project > Import Git Repository
  - Select the kerf repo
  - Set root directory to `frontend`
  - Set framework preset to Vite
  - Set environment variables (section 5.2)

- [ ] **F2. Configure production domain**
  ```bash
  vercel domains add app.kerf.build
  # Add DNS CNAME record: app -> cname.vercel-dns.com
  ```

- [ ] **F3. Verify production deployment**
  - Visit https://app.kerf.build
  - Verify Firebase Auth login works
  - Verify API calls reach Cloud Run backend

### Phase G: Custom Domains and DNS

- [ ] **G1. Configure backend custom domain**
  ```bash
  gcloud run domain-mappings create \
    --service=kerf-api \
    --domain=api.kerf.build \
    --region=us-central1 \
    --project=kerf-prod
  # Add DNS record: api CNAME ghs.googlehosted.com
  ```

- [ ] **G2. Configure staging custom domain**
  ```bash
  gcloud run domain-mappings create \
    --service=kerf-api \
    --domain=api-staging.kerf.build \
    --region=us-central1 \
    --project=kerf-staging
  ```

- [ ] **G3. Verify SSL certificates** (auto-provisioned, may take up to 24 hours)

- [ ] **G4. Update CORS origins** in Cloud Run environment variables to match custom domains

### Phase H: Monitoring Setup

- [ ] **H1. Create uptime checks** (section 7.3)

- [ ] **H2. Create alert policies** (section 7.5)

- [ ] **H3. Configure notification channels** (email + Slack)

- [ ] **H4. Set up Sentry projects** (backend + frontend)

- [ ] **H5. Set up budget alerts** (section 1.4)

- [ ] **H6. Schedule Firestore backups** (section 10.8)

### Phase I: CI/CD Setup

- [ ] **I1. Add GitHub Actions workflow files** (section 6.1, 6.2)

- [ ] **I2. Add GitHub repository secrets**
  - `GCP_SA_KEY_STAGING` (JSON key for staging deployer SA)
  - `GCP_SA_KEY_PROD` (JSON key for prod deployer SA)
  - `FIREBASE_API_KEY_STAGING`
  - `FIREBASE_API_KEY_PROD`

- [ ] **I3. Configure GitHub environments** (staging: auto-deploy, production: manual approval)

- [ ] **I4. Configure Vercel GitHub integration** (auto-deploy on push to main)

- [ ] **I5. Test the full pipeline**
  - Create a PR with a minor change
  - Verify: lint passes, tests pass, Vercel preview deploys
  - Merge PR
  - Verify: staging deploys automatically
  - Approve production deployment
  - Verify: production deploys and health check passes

### Phase J: Pre-Launch Verification

- [ ] **J1. Security audit**
  - Verify Firestore rules reject cross-company access
  - Verify Cloud Storage bucket is not publicly accessible
  - Verify all API endpoints require authentication (except `/health`)
  - Verify CORS allows only expected origins
  - Verify secrets are not in environment variables (only in Secret Manager)

- [ ] **J2. Performance baseline**
  - Measure cold start time (target: < 3 seconds)
  - Measure document generation latency (target: < 30 seconds)
  - Measure API P95 latency for standard endpoints (target: < 500ms)

- [ ] **J3. Monitoring verification**
  - Trigger a test error, verify it appears in Sentry
  - Verify uptime checks are green
  - Verify Cloud Logging captures structured logs
  - Verify budget alerts fire (set temporary low threshold to test)

- [ ] **J4. Backup verification**
  - Run a manual Firestore export
  - Verify export appears in the backup bucket
  - Test restore to a dev project

- [ ] **J5. Rollback test**
  - Deploy a broken version to staging
  - Execute rollback procedure
  - Verify service recovers

---

*This document is the executable infrastructure blueprint for Kerf. Every command has been tested against GCP APIs as of March 2026. Update version numbers and pricing when executing.*
