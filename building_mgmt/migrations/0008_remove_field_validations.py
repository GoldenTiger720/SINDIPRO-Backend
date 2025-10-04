# Generated manually to remove validation constraints
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building_mgmt', '0007_add_tower_field_to_unit'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='ideal_fraction',
            field=models.DecimalField(decimal_places=6, max_digits=10),
        ),
        migrations.AlterField(
            model_name='unit',
            name='identification',
            field=models.CharField(max_length=20),
        ),
    ]