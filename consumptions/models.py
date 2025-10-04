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
    
    CATEGORY_CHOICES = [
        ('units', 'Units'),
        ('liters', 'Liters'),
        ('kwh', 'kWh'),
        ('m3', 'Cubic Meters'),
    ]
    
    date = models.DateField()
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPE_CHOICES)
    gas_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
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
    
    month = models.CharField(max_length=7)  # Format: YYYY-MM
    utility_type = models.CharField(max_length=20, choices=UTILITY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'consumptions_consumption_account'
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.utility_type} - {self.amount} - {self.month}"