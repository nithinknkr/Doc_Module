#!/usr/bin/env bash
# Exit on error
set -e
# Install dependencies
pip install -r requirements.txt
# Collect static files (if applicable)
python manage.py collectstatic --noinput
# Apply database migrations
python manage.py migrate