# Generated manually to remove status field choices validation
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building_mgmt', '0008_remove_field_validations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='status',
            field=models.CharField(max_length=20),
        ),
    ]