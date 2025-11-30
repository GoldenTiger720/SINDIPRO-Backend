from django.urls import path
from . import views

urlpatterns = [
    path('generate/', views.generate_report, name='generate_report'),
    # Report Justifications - Get all justifications for a building
    path('justifications/<int:building_id>/', views.get_report_justifications, name='get_report_justifications'),
    # Page-specific update endpoints
    path('justifications/<int:building_id>/page/<int:page_number>/', views.update_page_justification, name='update_page_justification'),
]
