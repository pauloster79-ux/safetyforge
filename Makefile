.PHONY: dev dev-local dev-backend dev-frontend neo4j-up neo4j-schema seed-all seed-regulatory seed-golden seed-golden-only clean-golden test lint format frontend-build

# --- Full Docker stack ---
dev:
	docker compose up --build

# --- Local development (Neo4j in Docker, backend+frontend local) ---
dev-local: neo4j-up neo4j-schema
	@echo "Neo4j ready. Starting backend + frontend..."
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

# --- Neo4j ---
neo4j-up:
	@docker ps --filter name=neo4j-test --format '{{.Names}}' | grep -q neo4j-test \
		|| docker run -d --name neo4j-test \
			-p 7474:7474 -p 7687:7687 \
			-e NEO4J_AUTH=neo4j/password \
			neo4j:5
	@echo "Waiting for Neo4j..."
	@for i in 1 2 3 4 5 6 7 8 9 10; do \
		curl -sf http://localhost:7474 >/dev/null 2>&1 && break || sleep 2; \
	done
	@echo "Neo4j is up"

neo4j-schema:
	cd backend && python -c "from app.services.neo4j_client import run_schema; run_schema('graph/schema.cypher'); print('Schema applied')"

# --- Seeding ---
seed-all: neo4j-schema seed-golden
	@echo "Schema + golden data ready"

seed-regulatory:
	python -m backend.scripts.seed_regulatory_graph

seed-golden:
	python -m backend.fixtures.golden.seed_all

seed-golden-only:
	python -m backend.fixtures.golden.seed_all --skip-regulatory --only $(GP)

clean-golden:
	python -m backend.fixtures.golden.seed_all --clean --skip-regulatory

# --- Testing ---
test-backend:
	cd backend && ENVIRONMENT=test pytest -v

lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff format . && ruff check --fix .

frontend-build:
	cd frontend && npm run build
