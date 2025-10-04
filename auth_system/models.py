from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core import validators
from django.db import models


class CustomUsernameValidator(UnicodeUsernameValidator):
    regex = r'^[\w.@+\- ]+$'
    message = 'Enter a valid username. This value may contain only letters, numbers, spaces, and @/./+/-/_ characters.'


class User(AbstractUser):
    ROLE_CHOICES = [
        ('master', 'Master - Full Access'),
        ('manager', 'Manager - Admin Access'),
        ('field', 'Field - Limited Access'),
        ('readonly', 'Read-Only Access'),
    ]
    
    username_validator = CustomUsernameValidator()
    
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits, spaces and @/./+/-/_ only.',
        validators=[username_validator],
        error_messages={
            'unique': 'A user with that username already exists.',
        },
    )
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='readonly')
    is_active_user = models.BooleanField(default=True)
    building = models.ForeignKey('building_mgmt.Building', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        return f"{self.username} ({self.email})"