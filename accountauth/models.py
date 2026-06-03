from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    is_superuser = models.BooleanField(default=False)
    is_two_factor_enabled = models.BooleanField(default=False)
    secret= models.CharField(max_length=400, blank=True, default="")
