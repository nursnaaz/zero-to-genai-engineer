.PHONY: dev dev-backend dev-frontend install install-backend install-frontend test lint pull-model setup

dev:
	make -j2 dev-backend dev-frontend

dev-backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

install: install-backend install-frontend

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

test:
	cd backend && pytest tests/ -v --tb=short

lint:
	cd backend && ruff check . && black --check .
	cd frontend && npm run lint

pull-model:
	ollama pull $(MODEL)

setup:
	cp -n .env.example .env || true
	@echo "Edit .env with your API keys, then run: make install"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete"
