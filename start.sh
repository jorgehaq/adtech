#!/bin/bash
set -e

echo "Starting Django application..."
echo "Environment variables:"
echo "  PORT=$PORT"
echo "  DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE"

# Check if .venv exists, if not use poetry run
PYTHON_CMD="python"

# Run Django checks
echo "Running Django system checks..."
$PYTHON_CMD manage.py check --deploy

# Collect static files (skip for now, will configure later)
echo "Skipping static files collection for now..."

# Run database migrations
echo "Running database migrations..."
$PYTHON_CMD manage.py migrate --noinput || echo "Migration failed, continuing..."

echo "Starting Django development server on 0.0.0.0:$PORT"
exec $PYTHON_CMD manage.py runserver 0.0.0.0:$PORT