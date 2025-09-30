from django import forms
from .models import Expense,PaymentMethod

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name','amount','date','payment_method', 'transaction_mode','category']
        widgets = {
            'payment_method':forms.Select(attrs={'class': 'form-control'}),
            'category':forms.Select(attrs={'class': 'form-control'}),
            'transaction_mode':forms.Select(attrs={'class': 'form-control'}),
            'date':forms.DateInput(attrs={'type':'date'}),
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'amount':forms.NumberInput(attrs={'class':'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user',None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)

class PaymentEditForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['balance','credit_limit','minimum_balance','account_type','billing_date']
        widgets = {
            'balance':forms.NumberInput(attrs={'class':'form-control'}),
            'minimum_balance':forms.NumberInput(attrs={'class':'form-control'}),
            'credit_limit':forms.NumberInput(attrs={'class':'form-control'}),
            'account_type':forms.TextInput(attrs={'class':'form-control'}),
            'billing_date':forms.NumberInput(attrs={'class':'form-control'}),
        }
class PaymentMethodForm(forms.ModelForm):
    spent_percent = forms.DecimalField(max_digits=10,decimal_places=2,required=False,help_text="Percentage of credit limit you want to set as the spent limit (e.g., 30 for 30%).")

    class Meta:
        model = PaymentMethod
        fields = ['name','type','balance','credit_limit','minimum_balance','account_type','billing_date']
        widgets = {
            'type': forms.Select(attrs={'class':'form-control'}),
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'balance':forms.NumberInput(attrs={'class':'form-control'}),
            'minimum_balance':forms.NumberInput(attrs={'class':'form-control'}),
            'credit_limit':forms.NumberInput(attrs={'class':'form-control'}),
            'account_type':forms.TextInput(attrs={'class':'form-control'}),
            'billing_date':forms.NumberInput(attrs={'class':'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        credit_limit = cleaned_data.get('credit_limit')
        spent_percent = cleaned_data.get('spent_percent')
        type_ = cleaned_data.get('type')

        if type_ == 'credit_card':
            if credit_limit is None:
                raise forms.ValidationError('Credit limit is required for credit card.')
            if spent_percent is None or spent_percent < 0 or spent_percent > 100:
                # print(spent_percent)
                raise forms.ValidationError("Spent percent must be a number between 0 and 100.")
        else:
            cleaned_data['spent_percent'] = None
            cleaned_data['credit_limit'] = None

        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        spent_percent = self.cleaned_data.get('spent_percent')

        # calculate spent limit for credit cards.
        if instance.type == 'credit_card' and spent_percent is not None:
            instance.spent_limit = (spent_percent / 100) * instance.credit_limit
            instance.original_credit_limit = instance.credit_limit

        if commit:
            instance.save()
        return instance
    

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['name','amount','date','payment_method','transaction_mode']
        widgets = {
            'date':forms.DateInput(attrs={'type': 'date'}),
            'payment_method':forms.Select(attrs={'class': 'form-control'}),
            'transaction_mode':forms.Select(attrs={'class': 'form-control'}),
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'amount':forms.NumberInput(attrs={'class':'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user',None)  # Retrieve the user passed during form initialization
        super().__init__(*args, **kwargs)
        self.fields['transaction_mode'].label = 'Income Source'
        if user:
            print(user)
            self.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=user)


    def save(self, commit = True):
        instance = super().save(commit=False)
        instance.category = 'income' # Auto set to income 
        if commit:
            instance.save()
        return instance