from django.db import models
from db_connection import db

# Create your models here.
class UserModel(models.Model):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)

