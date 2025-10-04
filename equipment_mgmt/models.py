from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building

User = get_user_model()

class Equipment(models.Model):
    EQUIPMENT_TYPE_CHOICES = [
        ('elevator', 'Elevator'),
        ('generator', 'Generator'),
        ('pump', 'Water Pump'),
        ('hvac', 'HVAC System'),
        ('fire_system', 'Fire Safety System'),
        ('security_system', 'Security System'),
        ('garage_door', 'Garage Door'),
        ('intercom', 'Intercom System'),
        ('lighting', 'Lighting System'),
        ('other', 'Other Equipment'),
    ]
    
    STATUS_CHOICES = [
        ('operational', 'Operational'),
        ('maintenance', 'Under Maintenance'),
        ('repair', 'Under Repair'),
        ('broken', 'Broken'),
        ('retired', 'Retired'),
    ]
    
    MAINTENANCE_FREQUENCY_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannual', 'Semi-Annual'),
        ('semi_annual', 'Semi-Annual'),
        ('annual', 'Annual'),
    ]
    
    # Required fields based on new structure
    # Temporarily using CharField until migrations are applied
    building_id = models.CharField(max_length=200, db_column='building_id')
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=100)  # Equipment type (e.g., "Social")
    location = models.CharField(max_length=200)
    purchase_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    maintenance_frequency = models.CharField(max_length=20, choices=MAINTENANCE_FREQUENCY_CHOICES, default='monthly')
    contractor_name = models.CharField(max_length=200)
    contractor_phone = models.CharField(max_length=20)
    
    # Keep some useful existing fields
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - Building {self.building_id}"
    
    @property
    def maintenance_overdue(self):
        return False

class MaintenanceRecord(models.Model):
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField()
    notes = models.TextField()
    technician = models.CharField(max_length=200)
    type = models.CharField(max_length=200)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.type} - {self.date}"

class EquipmentDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('manual', 'User Manual'),
        ('warranty', 'Warranty Document'),
        ('certificate', 'Certificate'),
        ('invoice', 'Purchase Invoice'),
        ('maintenance_report', 'Maintenance Report'),
        ('other', 'Other Document'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file_document = models.FileField(upload_to='equipment_documents/')
    upload_date = models.DateField(auto_now_add=True)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.equipment.name}"