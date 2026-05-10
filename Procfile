release: flask db upgrade && flask bootstrap-admin
web: gunicorn main_app:app --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
worker: python services/social_scheduler.py
