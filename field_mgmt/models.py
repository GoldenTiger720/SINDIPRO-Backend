from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building, Unit
import base64
from django.core.files.base import ContentFile
import uuid
import string
import random

User = get_user_model()

class FieldRequest(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='field_requests')
    caretaker = models.CharField(max_length=200, default='')
    title = models.CharField(max_length=200)
    items = models.JSONField(default=list)  # Store array of items with observations, productType, quantity
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.building.name}"
    
    class Meta:
        ordering = ['-created_at']

class FieldRequestPhoto(models.Model):
    field_request = models.ForeignKey(FieldRequest, on_delete=models.CASCADE, related_name='photos')
    photo = models.ImageField(upload_to='field_request_photos/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Photo for {self.field_request.title}"

class FieldRequestComment(models.Model):
    field_request = models.ForeignKey(FieldRequest, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.created_by.username} on {self.field_request.title}"
    
    class Meta:
        ordering = ['created_at']

class Survey(models.Model):
    SURVEY_TYPE_CHOICES = [
        ('satisfaction', 'Satisfaction Survey'),
        ('feedback', 'General Feedback'),
        ('maintenance', 'Maintenance Survey'),
        ('amenities', 'Amenities Survey'),
        ('custom', 'Custom Survey'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='surveys')
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    start_date = models.DateField()
    end_date = models.DateField()
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.building.name}"

class SurveyQuestion(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text'),
        ('rating', 'Rating (1-5)'),
        ('multiple_choice', 'Multiple Choice'),
        ('yes_no', 'Yes/No'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    choices = models.JSONField(null=True, blank=True)  # For multiple choice questions
    required = models.BooleanField(default=True)
    order = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.survey.title} - Q{self.order}"

class SurveyResponse(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    respondent_name = models.CharField(max_length=200, blank=True)
    respondent_email = models.EmailField(blank=True)
    responses = models.JSONField()  # Store all responses as JSON
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Response to {self.survey.title} - {self.submitted_at}"
    
    class Meta:
        ordering = ['-submitted_at']


def generate_unique_code():
    """Generate a unique 8-character code combining letters and numbers"""
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(characters, k=8))
        # Check if this code already exists
        if not FieldMgmtTechnical.objects.filter(code=code).exists():
            return code

class FieldMgmtTechnical(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    code = models.CharField(max_length=8, unique=True, default=generate_unique_code)
    company_email = models.EmailField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.company_email}"
    
    class Meta:
        ordering = ['-created_at']
        db_table = 'field_mgmt_technical'


class FieldMgmtTechnicalImage(models.Model):
    technical_request = models.ForeignKey(FieldMgmtTechnical, on_delete=models.CASCADE, related_name='images')
    image_data = models.BinaryField()  # Stores raw image bytes (BYTEA in PostgreSQL)
    mime_type = models.CharField(max_length=50, default='image/png')  # e.g., 'image/png', 'image/jpeg'
    filename = models.CharField(max_length=255, blank=True)  # Optional original filename
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.technical_request.title}"
    
    class Meta:
        db_table = 'field_mgmt_fieldmgmttechnicalimage'