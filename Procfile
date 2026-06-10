release: FLASK_APP=main_app:app flask db upgrade && FLASK_APP=main_app:app flask bootstrap-admin
web: gunicorn main_app:app --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
worker: FLASK_APP=main_app:app python services/social_scheduler.py
