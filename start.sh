#!/bin/bash

# 1. डेटाबेस माइग्रेट करना
python manage.py migrate

# 2. Celery वर्कर को बैकग्राउंड (&) में चालू करना
celery -A store_backend worker --loglevel=info &

# 3. Gunicorn को चालू करना (Render के पब्लिक पोर्ट के साथ)
gunicorn store_backend.wsgi:application --bind 0.0.0.0:$PORT