#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
sleep 10

python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput

gunicorn --bind 0.0.0.0:8000 dearday_project.wsgi:application
