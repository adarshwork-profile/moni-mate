from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import User


class PaymentMethod(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=[
        ('bank','Bank'),
        ('credit_card', 'Credit Card'),
        ('digital_wallet', 'Digital Wallet'),
        ('cash','Cash'),
    ])
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True)
    spent_limit = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True) # credit card spent limit in amounts.
    original_credit_limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # used to reset credit limit value to normal upon billing cycle completion.
    credit_limit = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True) #for credit cards -enter total amount limit.
    billing_date = models.IntegerField(default=1) # billing date for the credit card ( credit cards only )
    minimum_balance = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True,help_text="  Enter 0 for Zero Balance Accounts.") #for banks - default = 10%
    account_type = models.CharField(max_length=50,null=True,blank=True) #banks


    def __str__(self):
        return f'{self.name} ({self.get_type_display()})'

class Expense(models.Model):
    TRANSACTION_MODE = [
        ('debit_card','Debit Card'),
        ('mobile_wallets','Mobile Wallets'),
        ('upi','UPI'),
        ('net_banking','Net Banking'),
        ('neft','NEFT'),
        ('imps','IMPS'),
        ('other','Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=now)
    payment_method = models.ForeignKey(PaymentMethod,null=True,blank=True, on_delete=models.SET_NULL)
    transaction_mode = models.CharField(max_length=100,choices=TRANSACTION_MODE,default='other')
    category = models.CharField(max_length=10,choices=[
        ('needs','Needs'),
        ('wants','Wants'),
        ('savings','Savings'),
        ('income','Income'),
    ], default='needs')

    def save(self,*args, **kwargs):
        #update the balance or limit based on the payment method & category type

        if self.payment_method:
            if self.payment_method.type == 'credit_card':
                if self.category != 'income': #cannot add income to credit cards.
                    self.payment_method.credit_limit -= self.amount
                else:
                    return None
            else:
                if self.category == 'income':
                    self.payment_method.balance += self.amount
                else:
                    self.payment_method.balance -= self.amount
            self.payment_method.save()
        super().save(*args, **kwargs)


    def __str__(self):
        return f'{self.name} = {self.amount}'
