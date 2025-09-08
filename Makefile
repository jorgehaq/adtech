SHELL := /bin/bash
.ONESHELL:
ENV_FILE ?= .env.local

define LOAD_ENV
   set -a; source $(ENV_FILE); set +a
endef

.PHONY: up local migrate kill-port celery flower down load-million test restart-celery restart-flower

up: migrate
	@$(call LOAD_ENV); PORT=$${PORT:-8070} $(MAKE) kill-port
	@PORT=5555 $(MAKE) kill-port
	@$(MAKE) celery &
	@$(MAKE) flower &
	@$(MAKE) local

local:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py runserver 0.0.0.0:$${PORT:-8070}

migrate:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py migrate

kill-port:
	@if [ -z "$$PORT" ]; then echo "PORT no definido"; exit 1; fi
	@echo "Killing processes on port $$PORT..."
	@pids=$$(lsof -ti tcp:$$PORT || true); if [ -n "$$pids" ]; then kill -9 $$pids; fi
	@echo "Port $$PORT cleared"

celery:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; celery -A core worker -l info

flower:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; celery -A core flower --port=5555

load-million:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py load_million_records --records=1000000

test:
	@$(call LOAD_ENV); export DJANGO_SETTINGS_MODULE=core.settings.local; python manage.py test

restart-celery:
	@pkill -f "celery -A core worker" || true
	@$(MAKE) celery

restart-flower:
	@pkill -f "celery -A core flower" || true
	@$(MAKE) flower

down:
	@pkill -f "celery -A core worker" || true
	@pkill -f "celery -A core flower" || true
	@pkill -f "python manage.py runserver" || true
	@echo "All services stopped"