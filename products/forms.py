from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class CustomRegisterForm(UserCreationForm):
    # Email field mandatory hai kyunki OTP verification zaroori hai
    email = forms.EmailField(
        required=True, 
        help_text='OTP verification ke liye apna chaloo email daalein.'
    )

    class Meta:
        model = User
        fields = ('username', 'email')

    # 🌟 Yahan hum email uniqueness check kar rahe hain
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Yeh email pehle se registered hai. Kripya doosri email use karein ya login karein.")
        return email