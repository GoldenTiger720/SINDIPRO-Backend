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
        ('broken', 'Broken'),
        ('retired', 'Retired'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='equipment')
    equipment_type = models.CharField(max_length=20, choices=EQUIPMENT_TYPE_CHOICES)
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    serial_number = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200)
    installation_date = models.DateField()
    warranty_expiry = models.DateField(null=True, blank=True)
    last_maintenance = models.DateField(null=True, blank=True)
    next_maintenance = models.DateField(null=True, blank=True)
    maintenance_frequency_months = models.PositiveIntegerField(default=6)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='operational')
    purchase_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.building.name}"
    
    @property
    def maintenance_overdue(self):
        if self.next_maintenance:
            from django.utils import timezone
            return self.next_maintenance < timezone.now().date()
        return False

class MaintenanceRecord(models.Model):
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('emergency', 'Emergency Repair'),
        ('inspection', 'Inspection'),
        ('upgrade', 'Upgrade'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    equipment = models.ForeignKey(Equipment, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    description = models.TextField()
    scheduled_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    technician_name = models.CharField(max_length=200)
    technician_company = models.CharField(max_length=200, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    parts_replaced = models.TextField(blank=True)
    work_performed = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.equipment.name} - {self.maintenance_type} - {self.scheduled_date}"

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