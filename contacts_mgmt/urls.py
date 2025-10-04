from django.urls import path
from . import views

urlpatterns = [
    path('event/', views.event_handler, name='event_handler'),
    path('<int:id>/event/', views.event_detail_handler, name='event_detail_handler'),
    path('supplier/', views.supplier_handler, name='supplier_handler'),
]