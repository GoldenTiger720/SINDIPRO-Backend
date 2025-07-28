from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building, Unit

User = get_user_model()

class FieldRequest(models.Model):
    REQUEST_TYPE_CHOICES = [
        ('maintenance', 'Maintenance Request'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('information', 'Information Request'),
        ('emergency', 'Emergency'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('in_review', 'In Review'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='field_requests')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, null=True, blank=True)
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    
    # Request Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    
    # Requester Information
    requester_name = models.CharField(max_length=200)
    requester_phone = models.CharField(max_length=20)
    requester_email = models.EmailField(blank=True)
    
    # Dates
    requested_date = models.DateField(auto_now_add=True)
    preferred_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_requests')
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.building.name} - {self.status}"
    
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
        return f"Comment by {self.created_by.full_name} on {self.field_request.title}"
    
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