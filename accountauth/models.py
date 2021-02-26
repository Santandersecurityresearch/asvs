from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):

    is_two_factor_enabled = models.BooleanField()
    secret= models.CharField(max_length=400)
