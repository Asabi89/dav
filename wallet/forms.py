from django import forms
from .models import Card, BankAccount
from django.core.validators import RegexValidator
class CardForm(forms.ModelForm):
    """Form for adding a virtual card."""
    
    card_number = forms.CharField(
        max_length=16,
        validators=[
            RegexValidator(
                regex=r'^\d{16}$',
                message="Le numéro de carte doit contenir 16 chiffres."
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '1234567890123456',
            'inputmode': 'numeric'
        })
    )
    
    card_holder = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'NOM PRÉNOM'
        })
    )
    
    expiry_month = forms.IntegerField(
        min_value=1,
        max_value=12,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'MM',
            'inputmode': 'numeric'
        })
    )
    
    expiry_year = forms.IntegerField(
        min_value=2023,
        max_value=2050,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'YYYY',
            'inputmode': 'numeric'
        })
    )
    
    cvv = forms.CharField(
        max_length=3,
        validators=[
            RegexValidator(
                regex=r'^\d{3}$',
                message="Le CVV doit contenir 3 chiffres."
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '123',
            'inputmode': 'numeric'
        })
    )
    
    class Meta:
        model = Card
        fields = ('card_number', 'card_holder', 'expiry_month', 'expiry_year', 'cvv', 'card_type')
        widgets = {
            'card_type': forms.Select(attrs={'class': 'form-select'})
        }
    
    def clean_card_number(self):
        """
        Nettoie le numéro de carte en supprimant tous les caractères non numériques
        et vérifie qu'il contient exactement 16 chiffres.
        """
        card_number = self.cleaned_data.get('card_number')
        # Supprimer tous les caractères non numériques (espaces, tirets, etc.)
        card_number = ''.join(filter(str.isdigit, card_number))
        
        if len(card_number) != 16:
            raise forms.ValidationError("Le numéro de carte doit contenir 16 chiffres.")
        
        return card_number




class BankAccountForm(forms.ModelForm):
    """Form for adding a bank account."""
    
    bank_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Nom de la banque'
        })
    )
    
    account_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Numéro de compte'
        })
    )
    
    account_holder = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Titulaire du compte'
        })
    )
    
    is_primary = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox'
        })
    )
    
    class Meta:
        model = BankAccount
        fields = ('bank_name', 'account_number', 'account_holder', 'account_type', 'is_primary')
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select'})
        }


class DepositForm(forms.Form):
    """Form for depositing money into wallet."""
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0.00',
            'inputmode': 'decimal'
        })
    )
    
    bank_account = forms.ModelChoiceField(
        queryset=BankAccount.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, wallet, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_account'].queryset = BankAccount.objects.filter(wallet=wallet, is_verified=True)


class WithdrawForm(forms.Form):
    """Form for withdrawing money from wallet."""
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': '0.00',
            'inputmode': 'decimal'
        })
    )
    
    bank_account = forms.ModelChoiceField(
        queryset=BankAccount.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    def __init__(self, wallet, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_account'].queryset = BankAccount.objects.filter(wallet=wallet, is_verified=True)
        self.wallet = wallet
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if not self.wallet.can_withdraw(amount):
            raise forms.ValidationError("Solde insuffisant pour effectuer ce retrait.")
        return amount
