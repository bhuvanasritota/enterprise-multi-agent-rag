.PHONY: up down logs test lint migrate
up:
	docker compose up --build
down:
	docker compose down
logs:
	docker compose logs -f --tail=200
test:
	cd backend && pytest -q
lint:
	cd backend && ruff check app tests
migrate:
	cd backend && alembic upgrade head
