from django.db import models
from django.contrib.auth import get_user_model
from building_mgmt.models import Building

User = get_user_model()

class ConsumptionType(models.Model):
    CONSUMPTION_CHOICES = [
        ('water', 'Water'),
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
    ]
    
    name = models.CharField(max_length=20, choices=CONSUMPTION_CHOICES, unique=True)
    unit = models.CharField(max_length=10)  # m³, kWh, etc.
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.get_name_display()} ({self.unit})"

class ConsumptionReading(models.Model):
    PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('monthly', 'Monthly'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='consumption_readings')
    consumption_type = models.ForeignKey(ConsumptionType, on_delete=models.CASCADE)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    reading_date = models.DateField()
    consumption_value = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # Auto-calculated fields
    previous_month_consumption = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    percentage_change = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('building', 'consumption_type', 'period', 'reading_date')
        ordering = ['-reading_date']
    
    def __str__(self):
        return f"{self.building.name} - {self.consumption_type.name} - {self.reading_date}"
    
    def save(self, *args, **kwargs):
        # Calculate percentage change from previous month
        if self.period == 'monthly':
            from datetime import timedelta
            from dateutil.relativedelta import relativedelta
            
            previous_month = self.reading_date - relativedelta(months=1)
            previous_reading = ConsumptionReading.objects.filter(
                building=self.building,
                consumption_type=self.consumption_type,
                period='monthly',
                reading_date__year=previous_month.year,
                reading_date__month=previous_month.month
            ).first()
            
            if previous_reading:
                self.previous_month_consumption = previous_reading.consumption_value
                if previous_reading.consumption_value > 0:
                    change = ((self.consumption_value - previous_reading.consumption_value) / previous_reading.consumption_value) * 100
                    self.percentage_change = round(change, 2)
        
        super().save(*args, **kwargs)


class ConsumptionRegister(models.Model):
    UTILITY_TYPE_CHOICES = [
        ('water', 'Water'),
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
    ]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='consumption_registers', null=True, blank=True)
    date = models.DateField()
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    sub_account = models.ForeignKey('SubAccount', on_delete=models.SET_NULL, null=True, blank=True, related_name='consumption_registers')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consumption_registers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consumptions_consumption_register'
        ordering = ['-date']

    def __str__(self):
        return f"{self.utility_type} - {self.value} - {self.date}"


class ConsumptionAccount(models.Model):
    UTILITY_TYPE_CHOICES = [
        ('water', 'Water'),
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
    ]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='consumption_accounts', null=True, blank=True)
    month = models.CharField(max_length=7)  # Format: YYYY-MM
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(null=True, blank=True)  # Made optional
    is_paid = models.BooleanField(default=False)  # Track payment status
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='consumption_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consumptions_consumption_account'
        ordering = ['-month']

    def __str__(self):
        return f"{self.utility_type} - {self.amount} - {self.month}"


class SubAccount(models.Model):
    UTILITY_TYPE_CHOICES = [
        ('water', 'Water'),
        ('electricity', 'Electricity'),
        ('gas', 'Gas'),
    ]

    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='sub_accounts', null=True, blank=True)
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_accounts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'consumptions_sub_account'
        ordering = ['utility_type', 'name']
        unique_together = ('building', 'utility_type', 'name')

    def __str__(self):
        return f"{self.utility_type} - {self.name}"