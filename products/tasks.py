# products/tasks.py
from celery import shared_task
import time

@shared_task
def test_background_task(user_name):
    print(f"👉 Celery Task Started for: {user_name}")
    
    # हम जानबूझकर 10 सेकंड का ब्रेक ले रहे हैं (जैसे भारी ईमेल भेजने में टाइम लगता है)
    time.sleep(10) 
    
    print(f"✅ Success! 10 second wala kaam background me ho gaya for {user_name}!")
    return "Task Done"