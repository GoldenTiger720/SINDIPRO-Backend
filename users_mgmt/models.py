from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='user_avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Preferences
    language_preference = models.CharField(max_length=10, choices=[('en', 'English'), ('pt', 'Portuguese')], default='en')
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.full_name}"

class BuildingAccess(models.Model):
    ACCESS_LEVEL_CHOICES = [
        ('read_only', 'Read Only'),
        ('limited', 'Limited Access'),
        ('full', 'Full Access'),
        ('admin', 'Admin Access'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='building_access')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='user_access')
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default='read_only')
    
    # Module-specific permissions
    can_view_financial = models.BooleanField(default=False)
    can_edit_financial = models.BooleanField(default=False)
    can_view_equipment = models.BooleanField(default=False)
    can_edit_equipment = models.BooleanField(default=False)
    can_view_legal = models.BooleanField(default=False)
    can_edit_legal = models.BooleanField(default=False)
    can_view_field_requests = models.BooleanField(default=True)
    can_edit_field_requests = models.BooleanField(default=False)
    can_view_reports = models.BooleanField(default=False)
    can_generate_reports = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    
    # Date restrictions
    access_start_date = models.DateField(null=True, blank=True)
    access_end_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='granted_access')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'building')
    
    def __str__(self):
        return f"{self.user.full_name} - {self.building.name} - {self.access_level}"
    
    @property
    def is_access_valid(self):
        from django.utils import timezone
        now = timezone.now().date()
        
        if not self.is_active:
            return False
        
        if self.access_start_date and now < self.access_start_date:
            return False
        
        if self.access_end_date and now > self.access_end_date:
            return False
        
        return True

class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create Record'),
        ('update', 'Update Record'),
        ('delete', 'Delete Record'),
        ('view', 'View Record'),
        ('download', 'Download File'),
        ('upload', 'Upload File'),
        ('generate_report', 'Generate Report'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    building = models.ForeignKey(Building, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50, blank=True)  # Which app/module
    object_type = models.CharField(max_length=50, blank=True)  # Model name
    object_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.full_name} - {self.action} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']

class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.full_name} - {self.login_time}"
    
    class Meta:
        ordering = ['-login_time']