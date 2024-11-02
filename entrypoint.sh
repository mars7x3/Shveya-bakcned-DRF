python manage.py collectstatic --noinput
gunicorn main.wsgi:application --bind 0.0.0.0:8000
