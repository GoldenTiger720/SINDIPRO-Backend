from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Building(models.Model):
    BUILDING_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('mixed', 'Mixed Use'),
    ]
    
    name = models.CharField(max_length=200)
    address = models.TextField()
    building_type = models.CharField(max_length=20, choices=BUILDING_TYPE_CHOICES, default='residential')
    total_units = models.PositiveIntegerField()
    floors = models.PositiveIntegerField()
    year_built = models.PositiveIntegerField()
    total_area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    common_area_sqm = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Contact Information
    manager_name = models.CharField(max_length=200)
    manager_phone = models.CharField(max_length=20)
    manager_email = models.EmailField()
    
    # Legal Information
    cnpj = models.CharField(max_length=18, unique=True)
    registration_number = models.CharField(max_length=50)
    municipal_registration = models.CharField(max_length=50, blank=True)
    
    # Financial Information
    monthly_common_fee = models.DecimalField(max_digits=10, decimal_places=2)
    reserve_fund_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Unit(models.Model):
    UNIT_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('store', 'Store'),
        ('parking', 'Parking Space'),
        ('storage', 'Storage'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=20)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='apartment')
    floor = models.PositiveIntegerField()
    area_sqm = models.DecimalField(max_digits=8, decimal_places=2)
    bedrooms = models.PositiveIntegerField(default=0)
    bathrooms = models.PositiveIntegerField(default=0)
    
    # Owner Information
    owner_name = models.CharField(max_length=200)
    owner_cpf = models.CharField(max_length=14)
    owner_phone = models.CharField(max_length=20)
    owner_email = models.EmailField()
    
    # Financial Information
    common_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('building', 'unit_number')
    
    def __str__(self):
        return f"{self.building.name} - Unit {self.unit_number}"