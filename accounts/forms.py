from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from .models import StaffProfile


class LoginForm(AuthenticationForm):
    """Custom login form with email support."""
    username = forms.CharField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-bg-elevated-2 border border-border-hairline text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
            'placeholder': 'admin@studio.com',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 rounded-lg bg-bg-elevated-2 border border-border-hairline text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['autofocus'] = True


class StaffProfileForm(forms.ModelForm):
    """Form for editing staff profile."""
    class Meta:
        model = StaffProfile
        fields = ['role', 'phone', 'avatar']
        widgets = {
            'role': forms.Select(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-bg-elevated-2 border border-border-hairline text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 rounded-lg bg-bg-elevated-2 border border-border-hairline text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-gold focus:border-transparent transition-all',
                'placeholder': '+977 98XXXXXXXX',
            }),
        }