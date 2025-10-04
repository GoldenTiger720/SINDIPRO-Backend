# Generated manually on 2025-09-27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('equipment_mgmt', '0008_change_condominium_to_building_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipment',
            name='status',
            field=models.CharField(
                choices=[
                    ('operational', 'Operational'),
                    ('maintenance', 'Under Maintenance'),
                    ('repair', 'Under Repair'),
                    ('broken', 'Broken'),
                    ('retired', 'Retired')
                ],
                default='operational',
                max_length=20
            ),
        ),
    ]