from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building

User = get_user_model()

class ReportTemplate(models.Model):
    REPORT_TYPE_CHOICES = [
        ('financial', 'Financial Report'),
        ('maintenance', 'Maintenance Report'),
        ('consumption', 'Consumption Report'),
        ('field_requests', 'Field Requests Report'),
        ('legal_compliance', 'Legal Compliance Report'),
        ('custom', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    template_config = models.JSONField()  # Store template configuration
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"

class GeneratedReport(models.Model):
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='reports')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    report_name = models.CharField(max_length=200)
    report_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    
    # Date range for report data
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Generated file
    report_file = models.FileField(upload_to='generated_reports/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)  # Size in bytes
    
    # Metadata
    generation_time = models.FloatField(null=True, blank=True)  # Time in seconds
    error_message = models.TextField(blank=True)
    
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.report_name} - {self.building.name} - {self.created_at.date()}"
    
    class Meta:
        ordering = ['-created_at']

class ReportSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='report_schedules')
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    is_active = models.BooleanField(default=True)
    
    # Email settings
    email_recipients = models.JSONField()  # List of email addresses
    email_subject = models.CharField(max_length=200)
    email_body = models.TextField(blank=True)
    
    # Schedule settings
    next_run_date = models.DateTimeField()
    last_run_date = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.frequency} - {self.building.name}"

class ReportAccess(models.Model):
    ACCESS_LEVEL_CHOICES = [
        ('view', 'View Only'),
        ('download', 'View and Download'),
        ('generate', 'Generate Reports'),
        ('manage', 'Full Management'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    report_template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, null=True, blank=True)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_report_access')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'building', 'report_template')
    
    def __str__(self):
        template_name = self.report_template.name if self.report_template else 'All Reports'
        return f"{self.user.full_name} - {template_name} - {self.access_level}"