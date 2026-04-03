# SafetyForge

AI-powered safety document generation platform. Upload workplace context and SafetyForge produces compliant safety policies, risk assessments, and method statements as professionally formatted PDFs.

## Tech Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui, React Router, TanStack Query
- **Backend:** Python 3.12, FastAPI, Pydantic, WeasyPrint (PDF generation)
- **AI:** Anthropic Claude API
- **Database:** Google Cloud Firestore
- **Auth:** Firebase Authentication
- **Hosting:** Cloud Run (backend), Vercel (frontend)

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker and Docker Compose
- Google Cloud SDK (for deployment)
- A Firebase project with Firestore enabled

## Local Development

### Quick start with Docker Compose

```bash
# Create backend env file
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Start all services
docker compose up --build
```

This starts:
- **Frontend** at http://localhost:5173
- **Backend API** at http://localhost:8000 (Swagger docs at /docs)
- **Firestore emulator** at http://localhost:8080

The backend volume mount enables hot reload -- changes to `backend/app/` are reflected immediately.

### Manual setup (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FIRESTORE_EMULATOR_HOST=localhost:8080
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Firestore emulator:**

```bash
gcloud emulators firestore start --host-port=localhost:8080
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Yes |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | Yes |
| `FIRESTORE_EMULATOR_HOST` | Firestore emulator address (local dev only) | No |
| `FIREBASE_AUTH_EMULATOR_HOST` | Firebase Auth emulator address (local dev only) | No |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | Yes |

### Frontend

Frontend environment variables are baked into the build via Vite. Create a `.env` file in `frontend/`:

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API base URL | Yes |
| `VITE_FIREBASE_API_KEY` | Firebase client API key | Yes |
| `VITE_FIREBASE_AUTH_DOMAIN` | Firebase auth domain | Yes |
| `VITE_FIREBASE_PROJECT_ID` | Firebase project ID | Yes |

## Deployment

### Backend (Cloud Run)

```bash
cd backend
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=europe-west2  # optional, defaults to europe-west2
bash deploy.sh
```

The deploy script builds the Docker image, pushes it to Artifact Registry, and deploys to Cloud Run with 1Gi memory (required for WeasyPrint PDF generation), up to 10 instances, scaling to zero when idle.

### Frontend (Vercel)

Connect the repository to Vercel and configure:
- **Framework:** Vite
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Root directory:** `frontend`

Or deploy manually:

```bash
cd frontend
npx vercel --prod
```

The `vercel.json` handles SPA routing rewrites and security headers.

## Project Structure

```
safetyforge/
  backend/
    app/
      main.py            # FastAPI application entry point
      models/            # Pydantic models
      services/          # Business logic services
      routers/           # API route handlers
    tests/               # pytest test suite
    Dockerfile           # Backend container image
    deploy.sh            # Cloud Run deployment script
    requirements.txt     # Python dependencies
  frontend/
    src/
      components/        # React components
      pages/             # Route pages
      hooks/             # Custom React hooks
      lib/               # Utilities, API client, Firebase config
    Dockerfile           # Multi-stage build (Node + nginx)
    nginx.conf           # nginx SPA routing and API proxy config
    vercel.json          # Vercel deployment config
    package.json         # Node dependencies
  docker-compose.yml     # Local development orchestration
```
