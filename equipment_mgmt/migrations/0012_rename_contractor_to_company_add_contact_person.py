# Generated migration to rename contractor fields to company fields and add contact person
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment_mgmt', '0011_maintenancerecord_technician_phone'),
    ]

    operations = [
        # Rename contractor_name to company_name
        migrations.RenameField(
            model_name='equipment',
            old_name='contractor_name',
            new_name='company_name',
        ),
        # Rename contractor_phone to company_phone
        migrations.RenameField(
            model_name='equipment',
            old_name='contractor_phone',
            new_name='company_phone',
        ),
        # Add contact_person_name field
        migrations.AddField(
            model_name='equipment',
            name='contact_person_name',
            field=models.CharField(max_length=200, blank=True, null=True),
        ),
    ]
