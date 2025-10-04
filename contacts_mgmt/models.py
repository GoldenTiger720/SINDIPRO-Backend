from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ContactsEvent(models.Model):
    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=50)
    date_time = models.DateTimeField()
    condominium = models.CharField(max_length=255)
    people_involved = models.JSONField(default=list)
    comments = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.event_type} ({self.date_time})"
    
    class Meta:
        db_table = 'contacts_mgmt_event'
        ordering = ['-date_time']

class ContactsSupplier(models.Model):
    company_name = models.CharField(max_length=255)
    condominium = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    email_address = models.EmailField()
    notes = models.TextField(blank=True)
    phone_numbers = models.JSONField(default=list)
    service_category = models.CharField(max_length=100)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company_name} - {self.service_category} ({self.condominium})"
    
    class Meta:
        db_table = 'contacts_mgmt_supplier'
        ordering = ['-created_at']
