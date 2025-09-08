SHELL := /bin/bash
.ONESHELL:
ENV_FILE ?= .env.local

define LOAD_ENV
   set -a; source $(ENV_FILE); set +a
endef

# Services management (Docker)
.PHONY: services services-down services-logs services-restart

services:
	@docker compose up -d
	@echo "✅ Services started:"
	@echo "   - MySQL: localhost:3306"
	@echo "   - Redis: localhost:6379"
	@echo ""
	@echo "🚀 Ready for local development:"
	@echo "   source .venv/bin/activate"
	@echo "   python manage.py runserver"

services-down:
	@docker compose down

services-logs:
	@docker compose logs -f

services-restart:
	@docker compose restart

# Local Django development
.PHONY: local migrate shell test dbshell load-million

local:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py runserver 0.0.0.0:$${PORT:-8070}

migrate:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py makemigrations
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py migrate

shell:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py shell

test:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py test

dbshell:
	@docker compose exec mysql mysql -u root -p

load-million:
	@echo "Loading 1M test records..."
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py load_million_records --records=1000000

# Local Celery (optional)
.PHONY: celery flower

celery:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; celery -A core worker -l info

flower:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; celery -A core flower --port=5555

# Development workflow
.PHONY: up dev flush

up: services migrate
	@echo "🎯 Development setup complete!"
	@echo "   Run: make local (or source .venv/bin/activate && python manage.py runserver)"

dev: services
	@$(MAKE) migrate
	@$(MAKE) local

# Database operations
flush:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py flush --noinput

# Cleanup
clean:
	@docker compose down -v
	@docker system prune -f

# Health check
health:
	@echo "🏥 Services Health Check:"
	@docker compose ps
	@echo ""
	@curl -s http://localhost:3306 > /dev/null && echo "✅ MySQL" || echo "❌ MySQL"
	@redis-cli ping > /dev/null && echo "✅ Redis" || echo "❌ Redis"