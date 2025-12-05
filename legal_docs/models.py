from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building

User = get_user_model()

class LegalDocument(models.Model):
    DOCUMENT_TYPE_CHOICES = [
        ('statute', 'Building Statute'),
        ('regulation', 'Internal Regulation'),
        ('contract', 'Service Contract'),
        ('insurance', 'Insurance Policy'),
        ('license', 'Municipal License'),
        ('certificate', 'Certificate'),
        ('other', 'Other Document'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='legal_documents')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    document_number = models.CharField(max_length=100, blank=True)
    issuing_authority = models.CharField(max_length=200, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    file_document = models.FileField(upload_to='legal_documents/', null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.building.name}"
    
    @property
    def is_expired(self):
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False

class LegalObligation(models.Model):
    OBLIGATION_TYPE_CHOICES = [
        ('fire_safety', 'Fire Safety'),
        ('elevator_inspection', 'Elevator Inspection'),
        ('electrical_inspection', 'Electrical Inspection'),
        ('water_quality', 'Water Quality Test'),
        ('building_inspection', 'Building Inspection'),
        ('insurance_renewal', 'Insurance Renewal'),
        ('tax_payment', 'Tax Payment'),
        ('other', 'Other Obligation'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='legal_obligations')
    obligation_type = models.CharField(max_length=30, choices=OBLIGATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    responsible_party = models.CharField(max_length=200)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_obligations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.building.name}"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status != 'completed'


class LegalTemplate(models.Model):
    BUILDING_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('mixed', 'Mixed Use'),
        ('industrial', 'Industrial'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    building = models.ForeignKey(Building, on_delete=models.CASCADE, null=True, blank=True)
    building_type = models.CharField(max_length=20, choices=BUILDING_TYPE_CHOICES, null=True, blank=True)
    frequency = models.CharField(max_length=50, default='annual')
    conditions = models.TextField(blank=True)
    requires_quote = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    due_month = models.DateField(null=True, blank=True)
    notice_period = models.IntegerField(default=14, help_text="Notice period in days")
    responsible_emails = models.TextField(blank=True, help_text="Comma-separated email addresses")

    # Completion tracking fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    last_completion_date = models.DateField(null=True, blank=True, help_text="Date when obligation was last completed")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_overdue(self):
        if self.due_month and self.status != 'completed':
            from django.utils import timezone
            return self.due_month < timezone.now().date()
        return False

    def calculate_next_due_date(self, completion_date):
        """Calculate next due date based on completion date and frequency.
        Returns the full date (year, month, day) for the next due date.
        """
        from dateutil.relativedelta import relativedelta

        frequency_map = {
            'annual': relativedelta(years=1),
            'biannual': relativedelta(months=6),
            'semiannual': relativedelta(months=6),
            'quarterly': relativedelta(months=3),
            'monthly': relativedelta(months=1),
            'biennial': relativedelta(years=2),
            'triennial': relativedelta(years=3),
            'quinquennial': relativedelta(years=5),
            'one_time': None
        }

        delta = frequency_map.get(self.frequency)
        if delta:
            # Return the full date, preserving the day
            return completion_date + delta
        return None


class LegalObligationCompletion(models.Model):
    """Track completion history for legal obligation templates"""
    template = models.ForeignKey(LegalTemplate, on_delete=models.CASCADE, related_name='completions')
    completion_date = models.DateField()
    previous_due_date = models.DateField(null=True, blank=True)
    new_due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completion_date']

    def __str__(self):
        return f"{self.template.name} - Completed on {self.completion_date}"


class ObligationLibrary(models.Model):
    """
    Global library of legal obligations that serves as a master repository.
    When a new obligation is created for a building, it is automatically added here.
    This allows selecting obligations from the library when creating new buildings.
    """
    BUILDING_TYPE_CHOICES = [
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('mixed', 'Mixed Use'),
        ('industrial', 'Industrial'),
    ]

    name = models.CharField(max_length=200, unique=True)
    description = models.TextField()
    building_type = models.CharField(max_length=20, choices=BUILDING_TYPE_CHOICES, null=True, blank=True)
    frequency = models.CharField(max_length=50, default='annual')
    conditions = models.TextField(blank=True)
    requires_quote = models.BooleanField(default=False)
    notice_period = models.IntegerField(default=14, help_text="Notice period in days")

    # Track usage
    usage_count = models.IntegerField(default=0, help_text="Number of times this obligation has been activated for buildings")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Obligation Library Entry'
        verbose_name_plural = 'Obligation Library'

    def __str__(self):
        return self.name