from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from .models import *
import re


User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Form for user registration with phone number."""
    
    phone_number = forms.CharField(
        max_length=17,
        validators=[
            RegexValidator(
                regex=r'^\+[1-9]\d{1,14}$',
                message="Le numéro de téléphone doit être au format international (ex: +33612345678)."
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+33612345678'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@exemple.com'})
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Prénom'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nom'})
    )
    
    referral_code = forms.CharField(
        max_length=10,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Code de parrainage (optionnel)'})
    )
    
    class Meta:
        model = User
        fields = ('email', 'phone_number', 'first_name', 'last_name', 'password1', 'password2')
    
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Mot de passe'})
        self.fields['password2'].widget.attrs.update({'class': 'form-input', 'placeholder': 'Confirmer le mot de passe'})
        
    def clean_phone_number(self):
        """Validate and format phone number."""
        phone_number = self.cleaned_data.get('phone_number', '')
        
        # Ensure phone number starts with +
        if phone_number and not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            
        # Remove any spaces or non-essential characters
        phone_number = ''.join(c for c in phone_number if c in '+0123456789')
        
        # Validate the phone number format
        if not re.match(r'^\+[1-9]\d{1,14}$', phone_number):
            raise forms.ValidationError(
                "Le numéro de téléphone doit être au format international (ex: +33612345678)."
            )
            
        return phone_number
    
    def clean(self):
        """Validation supplémentaire pour les mots de passe."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            self.add_error('password2', "Les deux mots de passe ne correspondent pas.")
        
        return cleaned_data
    
    
class CustomAuthenticationForm(AuthenticationForm):
    """Custom login form."""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Email ou numéro de téléphone'})
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Mot de passe'})
    )



class PhoneVerificationForm(forms.Form):
    """Form for phone verification with OTP."""
    
    verification_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-input text-center tracking-widest',
            'placeholder': '123456',
            'autocomplete': 'one-time-code'
        })
    )


class PinCodeForm(forms.Form):
    """Form for setting up or verifying PIN code."""
    
    pin_code = forms.CharField(
        max_length=4,
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input text-center tracking-widest',
            'placeholder': '****',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )
    
    confirm_pin_code = forms.CharField(
        max_length=4,
        min_length=4,
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-input text-center tracking-widest',
            'placeholder': '****',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        pin_code = cleaned_data.get('pin_code')
        confirm_pin_code = cleaned_data.get('confirm_pin_code')
        
        # Vérifier que le PIN contient uniquement des chiffres
        if pin_code and not pin_code.isdigit():
            self.add_error('pin_code', "Le code PIN doit contenir uniquement des chiffres.")
        
        # Vérifier que les deux PIN correspondent
        if confirm_pin_code and pin_code != confirm_pin_code:
            self.add_error('confirm_pin_code', "Les codes PIN ne correspondent pas.")
        
        return cleaned_data
import re
from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()  # Ceci récupère votre modèle User personnalisé

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile."""
    
    class Meta:
        model = User  # Utilise votre modèle User personnalisé
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture',
                 'date_of_birth', 'language', 'dark_mode', 'enable_notifications')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'hidden' # Gardé caché car il est stylisé différemment
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
                'type': 'date'
            }),
            'language': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500'
            }),
            'dark_mode': forms.CheckboxInput(attrs={
                'class': 'sr-only peer' # Style spécial pour les toggles
            }),
            'enable_notifications': forms.CheckboxInput(attrs={
                'class': 'sr-only peer' # Style spécial pour les toggles
            }),
        }
    
    def clean_phone_number(self):
        """Validate and format phone number."""
        phone_number = self.cleaned_data.get('phone_number', '')
        
        # Ensure phone number starts with +
        if phone_number and not phone_number.startswith('+'):
            phone_number = '+' + phone_number
            
        # Remove any spaces or non-essential characters
        phone_number = ''.join(c for c in phone_number if c in '+0123456789')
        
        # Validate the phone number format
        if not re.match(r'^\+[1-9]\d{1,14}$', phone_number):
            raise forms.ValidationError("Le numéro de téléphone doit être au format international (ex: +33612345678).")
            
        return phone_number



class SecurityQuestionForm(forms.ModelForm):
    """Form for security questions."""
    
    class Meta:
        model = UserSecurityQuestion
        fields = ('question', 'answer')
        widgets = {
            'question': forms.TextInput(attrs={'class': 'form-input'}),
            'answer': forms.TextInput(attrs={'class': 'form-input'}),
        }
