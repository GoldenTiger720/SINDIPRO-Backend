# Generated manually
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('building_mgmt', '0002_auto_20250805_1329'),
    ]

    operations = [
        # First remove the unique_together constraint
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together=set(),
        ),
        
        # Remove the old Unit model fields
        migrations.RemoveField(
            model_name='unit',
            name='building',
        ),
        migrations.RemoveField(
            model_name='unit',
            name='unit_type',
        ),
        migrations.RemoveField(
            model_name='unit',
            name='bedrooms',
        ),
        migrations.RemoveField(
            model_name='unit',
            name='owner_cpf',
        ),
        migrations.RemoveField(
            model_name='unit',
            name='owner_email',
        ),
        migrations.RemoveField(
            model_name='unit',
            name='common_fee_percentage',
        ),
        
        # Rename fields
        migrations.RenameField(
            model_name='unit',
            old_name='area_sqm',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='unit',
            old_name='unit_number',
            new_name='number',
        ),
        migrations.RenameField(
            model_name='unit',
            old_name='owner_name',
            new_name='owner',
        ),
        migrations.RenameField(
            model_name='unit',
            old_name='bathrooms',
            new_name='parking_spaces',
        ),
        
        # Add new fields
        migrations.AddField(
            model_name='unit',
            name='block',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='units', to='building_mgmt.tower'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='unit',
            name='ideal_fraction',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='unit',
            name='identification',
            field=models.CharField(choices=[('residential', 'Residential'), ('commercial', 'Commercial')], default='residential', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='unit',
            name='deposit_location',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='unit',
            name='has_deposit',
            field=models.CharField(default='no', max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='unit',
            name='key_delivery',
            field=models.CharField(default='no', max_length=3),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='unit',
            name='status',
            field=models.CharField(choices=[('vacant', 'Vacant'), ('occupied', 'Occupied')], default='vacant', max_length=20),
            preserve_default=False,
        ),
        
        # Update unique_together
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together={('block', 'number')},
        ),
    ]