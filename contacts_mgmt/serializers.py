from rest_framework import serializers
from .models import ContactsEvent, ContactsSupplier

class ContactsEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactsEvent
        fields = [
            'id', 'title', 'event_type', 'date_time', 'condominium', 
            'people_involved', 'comments', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ContactsSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactsSupplier
        fields = [
            'id', 'company_name', 'condominium', 'contact_person', 'email_address',
            'notes', 'phone_numbers', 'service_category', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']