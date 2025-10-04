from django.urls import path
from . import views

urlpatterns = [
    path('', views.equipment_list_create, name='equipment_list_create'),
    path('<int:equipment_id>/maintenance/', views.create_maintenance_record, name='create_maintenance_record'),
]
