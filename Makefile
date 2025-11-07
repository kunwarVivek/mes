.PHONY: help build up down restart logs clean migrate migrate-create install-backend install-frontend test

help:
	@echo "Available commands:"
	@echo "  make build           - Build all Docker containers"
	@echo "  make up              - Start all services"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View logs from all services"
	@echo "  make clean           - Remove containers, volumes, and images"
	@echo "  make migrate         - Run database migrations"
	@echo "  make migrate-create  - Create a new migration"
	@echo "  make install-backend - Install backend dependencies"
	@echo "  make install-frontend- Install frontend dependencies"
	@echo "  make test            - Run all tests"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi all

migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

test:
	docker-compose exec backend pytest
	cd frontend && npm test
