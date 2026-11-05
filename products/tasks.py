# products/tasks.py
import os
import time
import requests
from celery import shared_task


@shared_task
def test_background_task(user_name):
    print(f"👉 Celery Task Started for: {user_name}")
    
    # हम जानबूझकर 10 सेकंड का ब्रेक ले रहे हैं (जैसे भारी ईमेल भेजने में टाइम लगता है)
    time.sleep(10)
    
    print(f"✅ Success! 10 second wala kaam background me ho gaya for {user_name}!")
    return "Task Done"


@shared_task
def send_brevo_email_task(subject, message, to_email):
    """Background Celery task to send transactional emails via Brevo API."""
    # Fallback added: pehle BREVO_API_KEY check karega, na mile toh BREVO_PASSWORD dekhega
    raw_key = os.environ.get('BREVO_API_KEY') or os.environ.get('BREVO_PASSWORD')
    if not raw_key or not to_email:
        print("❌ Brevo Error: BREVO_API_KEY environment variable missing or to_email is empty.")
        return None

    api_key = raw_key.strip()

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {
        "sender": {"email": "support@cgsmart.in", "name": "CGSmart Store"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": message
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code not in (200, 201, 202):
            print(f"⚠️ Brevo Email API Failed ({response.status_code}): {response.text}")
        else:
            print(f"✅ Brevo Email Sent Successfully to {to_email}!")
        return response.status_code
    except Exception as e:
        print(f"❌ Email API error: {e}")
        return None


@shared_task
def send_brevo_whatsapp_task(mobile_number, message_text):
    """Background Celery task to send WhatsApp notifications via Brevo API."""
    raw_key = os.environ.get('BREVO_API_KEY') or os.environ.get('BREVO_PASSWORD')
    if not raw_key or not mobile_number:
        print("❌ Brevo WhatsApp Error: BREVO_API_KEY missing or mobile_number is empty.")
        return None

    api_key = raw_key.strip()

    clean_mobile = str(mobile_number).strip().replace("+", "")
    if len(clean_mobile) == 10:
        clean_mobile = "91" + clean_mobile

    url = "https://api.brevo.com/v3/whatsapp/sendMessage"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    payload = {"contactNumber": clean_mobile, "text": message_text}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code not in (200, 201, 202):
            print(f"⚠️ Brevo WhatsApp API Failed ({response.status_code}): {response.text}")
        return response.status_code
    except Exception as e:
        print(f"❌ WhatsApp API error: {e}")
        return None