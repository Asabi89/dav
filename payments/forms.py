from django import forms
from django.core.validators import RegexValidator
from .models import BillPayment, MobileRecharge, BillProvider, MobileOperator, DataPlan

class BillPaymentForm(forms.ModelForm):
    """Form for bill payments."""
    
    provider = forms.ModelChoiceField(
        queryset=BillProvider.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    account_number = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Numéro de compte'})
    )
    
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'})
    )
    
    class Meta:
        model = BillPayment
        fields = ('provider', 'account_number', 'amount')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If provider is selected, update account_number label
        if 'provider' in self.data:
            try:
                provider_id = int(self.data.get('provider'))
                provider = BillProvider.objects.get(id=provider_id)
                self.fields['account_number'].label = provider.account_number_label
                
                # Add regex validator if specified
                if provider.account_number_regex:
                    self.fields['account_number'].validators.append(
                        RegexValidator(
                            regex=provider.account_number_regex,
                            message=f"Format invalide pour {provider.account_number_label}"
                        )
                    )
            except (ValueError, BillProvider.DoesNotExist):
                pass

class MobileRechargeForm(forms.ModelForm):
    """Form for mobile recharges."""
    operator = forms.ModelChoiceField(
        queryset=MobileOperator.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    phone_number = forms.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="Le numéro de téléphone doit être au format: '+999999999'. 15 chiffres maximum."
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+33612345678'})
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00'})
    )
    data_plan = forms.ModelChoiceField(
        queryset=DataPlan.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = MobileRecharge
        fields = ('operator', 'phone_number', 'amount', 'data_plan')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make data_plan field optional
        self.fields['data_plan'].required = False
        
        # If operator is selected in form data, filter data plans
        if 'operator' in self.data:
            try:
                operator_id = int(self.data.get('operator'))
                self.fields['data_plan'].queryset = DataPlan.objects.filter(
                    operator_id=operator_id, is_active=True
                )
            except (ValueError, TypeError):
                pass
        # Check if instance exists, has a primary key, and has an operator attribute with a value
        elif self.instance and self.instance.pk and hasattr(self.instance, 'operator_id') and self.instance.operator_id:
            self.fields['data_plan'].queryset = DataPlan.objects.filter(
                operator=self.instance.operator, is_active=True
            )
