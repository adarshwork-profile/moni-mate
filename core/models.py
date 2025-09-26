from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False) # approve status
    notify_email = models.EmailField(blank=True, null=True) # notification email
    inflation = models.FloatField(default=10) #inflation %
