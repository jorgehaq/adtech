from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    tenant_id = models.IntegerField(db_index=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, default='user')
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class UserPermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.CharField(max_length=100)
    action = models.CharField(max_length=50)
    tenant_id = models.IntegerField(db_index=True)