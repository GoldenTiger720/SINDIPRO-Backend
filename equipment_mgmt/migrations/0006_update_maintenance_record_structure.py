# Generated manually on 2025-08-11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('equipment_mgmt', '0005_auto_20250811_1503'),
    ]

    operations = [
        # Remove all existing fields except equipment
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='maintenance_type',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='scheduled_date',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='completion_date',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='status',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='technician_name',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='technician_company',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='parts_replaced',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='work_performed',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='recommendations',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='next_maintenance_date',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='maintenancerecord',
            name='updated_at',
        ),
        
        # Add new fields
        migrations.AlterField(
            model_name='maintenancerecord',
            name='cost',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='date',
            field=models.DateField(default='2025-01-01'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='maintenancerecord',
            name='description',
            field=models.TextField(),
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='notes',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='technician',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='maintenancerecord',
            name='type',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]