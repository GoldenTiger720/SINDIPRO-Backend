#!/usr/bin/env python
"""
Test script to verify Django setup without database connection
"""
import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sindipro_backend.settings')

try:
    django.setup()
    print("✅ Django setup successful!")
    
    # Test imports
    from auth_system.models import User
    from building_mgmt.models import Building, Unit
    from legal_docs.models import LegalDocument, LegalObligation
    from equipment_mgmt.models import Equipment, MaintenanceRecord
    from financials.models import BudgetCategory, Expense, Revenue
    from consumptions.models import ConsumptionType, ConsumptionReading
    from field_mgmt.models import FieldRequest, Survey
    from reporting.models import ReportTemplate, GeneratedReport
    from users_mgmt.models import UserProfile, BuildingAccess
    
    print("✅ All models imported successfully!")
    
    # Test serializers
    from auth_system.serializers import UserSerializer, UserRegistrationSerializer
    print("✅ Serializers imported successfully!")
    
    # Test views
    from auth_system.views import RegisterView, UserProfileView
    print("✅ Views imported successfully!")
    
    print("\n🎉 SINDIPRO Backend setup is complete and ready!")
    print("\nNext steps:")
    print("1. Set up PostgreSQL database")
    print("2. Configure .env file with database credentials")
    print("3. Run: python manage.py migrate")
    print("4. Run: python manage.py populate_initial_data")
    print("5. Run: python manage.py createsuperuser")
    print("6. Run: python manage.py runserver")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)