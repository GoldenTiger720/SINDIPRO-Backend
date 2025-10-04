# Generated manually on 2025-09-27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment_mgmt', '0007_alter_equipment_maintenance_frequency_and_more'),
    ]

    operations = [
        # Step 1: Rename condominium field to building_id (keeping as CharField for now)
        migrations.RenameField(
            model_name='equipment',
            old_name='condominium',
            new_name='building_id',
        ),
    ]