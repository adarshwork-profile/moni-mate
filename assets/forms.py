from django import forms
from .models import Asset,Liabilities

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name','type','tenure','purpose','invested_value']
        widgets = {
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'type':forms.Select(attrs={'class':'form-control'}),
            'tenure':forms.Select(attrs={'class':'form-control'}),
            'purpose':forms.TextInput(attrs={'class':'form-control'}),
            'invested_value':forms.NumberInput(attrs={'class':'form-control'}),
            'current_value':forms.NumberInput(attrs={'class':'form-control'}),

        }
        
class LiabilityForm(forms.ModelForm):
    class Meta:
        model = Liabilities
        fields = ['name','type','notes','total_amount','installments']
        widgets = {
            'name':forms.TextInput(attrs={'class':'form-control'}),
            'type':forms.Select(attrs={'class':'form-control'}),
            'notes':forms.TextInput(attrs={'class':'form-control'}),
            'total_amount':forms.NumberInput(attrs={'class':'form-control'}),
            'installments':forms.NumberInput(attrs={'class':'form-control'}),
        }