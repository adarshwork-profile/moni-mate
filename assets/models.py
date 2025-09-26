from django.db import models
from django.contrib.auth.models import User

class Asset(models.Model):
    TYPE_CHOICES = [
        ('gold', 'Gold'),
        ('silver', 'Silver'),
        ('stocks', 'Stocks'),
        ('debt_mf', 'Debt MF'),
        ('equity_mf', 'Equity MF'),
        ('hybrid_mf', 'Hybrid MF'),
        ('other_mf', 'Other MF'),
        ('real_estate', 'Real Estate'),
        ('fixed_deposit', 'Fixed Deposit'),
        ('others', 'Others'),
    ]
    TENURE_CHOICES = [
        ('short_term', 'Short Term'),
        ('long_term', 'Long Term'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    tenure = models.CharField(max_length=50,choices=TENURE_CHOICES)
    purpose = models.CharField(max_length=255)
    invested_value = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12,decimal_places=2)
    growth_rate = models.FloatField(default=0)
    added_on = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.name

class GrowthHistory(models.Model):
    asset = models.ForeignKey(Asset,on_delete=models.CASCADE)
    invested_value = models.DecimalField(max_digits=12, decimal_places=2)
    current_value = models.DecimalField(max_digits=12,decimal_places=2)
    growth_rate = models.FloatField(default=0)
    added_on = models.DateTimeField(auto_now_add=True) 

class Liabilities(models.Model):
    TYPE_CHOICE = [
        ('home_loans','Home Loans'),
        ('education_loans','Education Loans'),
        ('car_loans','Car Loans'),
        ('other_personal_loans','Other Personal Loans'),
        ('business_loan','Business Loans'),
        ('product_purchase_loans','Product Purchase Loans (EMIs)'),
        ('payable_to_friends_family','Payable to Family or Friends'),
        ('others','Other Loans'),
    ]

    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=100,choices=TYPE_CHOICE)
    notes = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=12,decimal_places=2)
    installments = models.DecimalField(max_digits=12,decimal_places=2)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
