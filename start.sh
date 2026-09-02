#!/bin/bash

# 1. डेटाबेस माइग्रेट करना
python manage.py migrate

# 2. Celery वर्कर को 1 प्रोसेस (solo) पर चालू करना ताकि RAM फुल न हो
celery -A store_backend worker --pool=solo --loglevel=info &

# 3. Gunicorn को चालू करना
gunicorn store_backend.wsgi:application --bind 0.0.0.0:$PORT