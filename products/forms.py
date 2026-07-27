from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='OTP verification ke liye sahi email daalein.')

    class Meta:
        model = User
        fields = ('username', 'email')