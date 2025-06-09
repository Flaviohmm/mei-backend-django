from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    cnpj = models.CharField(max_length=18, unique=True) # Formato XXX.XXX.XXX/XXXX-XX
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.name
