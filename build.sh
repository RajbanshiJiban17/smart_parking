#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files into staticfiles/
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Seed initial test data (Admin, Staff, Driver, Parking Areas & Slots)
python manage.py seed_data
