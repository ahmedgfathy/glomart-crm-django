# Django migration to fix primary_image field length
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0005_property_compound'),  # Adjust this to the latest migration
    ]

    operations = [
        migrations.AlterField(
            model_name='property',
            name='primary_image',
            field=models.TextField(blank=True, null=True),
        ),
    ]