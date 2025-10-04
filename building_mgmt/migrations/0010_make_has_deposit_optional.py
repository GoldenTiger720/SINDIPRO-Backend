# Generated manually to make has_deposit field optional
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building_mgmt', '0009_remove_status_field_validation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='has_deposit',
            field=models.CharField(blank=True, max_length=3, null=True),
        ),
    ]