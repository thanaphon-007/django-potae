#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing requirements..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running database migrations..."
python manage.py migrate

echo "Creating superuser..."
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admintae').exists() or User.objects.create_superuser('admintae', '', 'admin1234')"
