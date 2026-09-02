#!/bin/bash

# 1. डेटाबेस माइग्रेट करना (ताकि हर डिप्लॉय पर खुद अपडेट हो जाए)
python manage.py migrate

# 2. Celery वर्कर को बैकग्राउंड (&) में चालू करना
celery -A store_backend worker --loglevel=info &

# 3. Gunicorn (आपकी मुख्य वेबसाइट) को चालू करना
gunicorn store_backend.wsgi:application