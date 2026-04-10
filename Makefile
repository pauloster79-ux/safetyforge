.PHONY: dev test lint format

dev:
	docker compose up --build

test-backend:
	cd backend && ENVIRONMENT=test pytest -v

lint:
	cd backend && ruff check . && ruff format --check .

format:
	cd backend && ruff format . && ruff check --fix .

frontend-build:
	cd frontend && npm run build

frontend-dev:
	cd frontend && npm run dev
