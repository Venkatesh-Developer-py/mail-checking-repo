#!/usr/bin/env bash

set -o errexit

echo "PORT is: $PORT"

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
gunicorn project.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --timeout 120