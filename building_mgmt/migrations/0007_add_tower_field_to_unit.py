# Generated manually to add tower field to Unit model
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('building_mgmt', '0006_replace_block_with_building'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='tower',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='units', to='building_mgmt.tower'),
        ),
    ]