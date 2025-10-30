from django.urls import path
from . import views

urlpatterns = [
    path('template/', views.legal_template_handler, name='legal_template_handler'),
    path('template/<int:template_id>/', views.update_delete_legal_template, name='update_delete_legal_template'),
    path('template/<int:template_id>/complete/', views.mark_obligation_completed, name='mark_obligation_completed'),
    path('template/<int:template_id>/history/', views.get_completion_history, name='get_completion_history'),
    path('completions/', views.get_all_completions, name='get_all_completions'),
]
