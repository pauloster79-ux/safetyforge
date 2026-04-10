# Kerf

AI-powered safety document generation platform. Upload workplace context and Kerf produces compliant safety policies, risk assessments, and method statements as professionally formatted PDFs.

## Tech Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS 4, shadcn/ui, React Router, TanStack Query
- **Backend:** Python 3.12, FastAPI, Pydantic, WeasyPrint (PDF generation)
- **AI:** Anthropic Claude API
- **Database:** Neo4j (knowledge graph)
- **Auth:** Clerk
- **Hosting:** Cloud Run (backend), Vercel (frontend)

## Prerequisites

- Node.js 20+
- Python 3.12+
- Docker and Docker Compose
- Neo4j 5+ (local or Aura)

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
- **Neo4j** at http://localhost:7474 (browser) / bolt://localhost:7687

The backend volume mount enables hot reload -- changes to `backend/app/` are reflected immediately.

### Manual setup (without Docker)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude | Yes |
| `NEO4J_URI` | Neo4j connection URI | Yes |
| `NEO4J_USER` | Neo4j username | Yes |
| `NEO4J_PASSWORD` | Neo4j password | Yes |
| `CLERK_SECRET_KEY` | Clerk secret key | Yes |
| `CORS_ORIGINS` | CORS allowed origins (comma-separated) | Yes |

### Frontend

Frontend environment variables are baked into the build via Vite. Create a `.env` file in `frontend/`:

| Variable | Description | Required |
|----------|-------------|----------|
| `VITE_API_URL` | Backend API base URL | Yes |
| `VITE_CLERK_PUBLISHABLE_KEY` | Clerk publishable key | Yes |

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
kerf/
  backend/
    app/
      main.py            # FastAPI application entry point
      models/            # Pydantic models
      services/          # Business logic services
      routers/           # API route handlers
    graph/
      schema.cypher      # Neo4j constraints and indexes
    tests/               # pytest test suite
    Dockerfile           # Backend container image
    deploy.sh            # Cloud Run deployment script
    requirements.txt     # Python dependencies
  frontend/
    src/
      components/        # React components
      pages/             # Route pages
      hooks/             # Custom React hooks
      lib/               # Utilities, API client
    Dockerfile           # Multi-stage build (Node + nginx)
    nginx.conf           # nginx SPA routing and API proxy config
    vercel.json          # Vercel deployment config
    package.json         # Node dependencies
  docker-compose.yml     # Local development orchestration
```
