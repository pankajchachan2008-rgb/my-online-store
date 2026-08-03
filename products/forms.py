from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='OTP verification ke liye sahi email daalein.')

    class Meta:
        model = User
        fields = ('username', 'email')

    # 🌟 FIX: without this, two accounts could register with the same
    # email (Django's User model doesn't enforce email uniqueness by
    # default). forgot_password's `User.objects.get(email=...)` would then
    # raise MultipleObjectsReturned and crash with a 500 error for that
    # email forever, since only User.DoesNotExist is caught there.
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ye email pehle se ek account se registered hai.")
        return email