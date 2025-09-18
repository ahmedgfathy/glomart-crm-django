# Generated migration to remove opportunities module

from django.db import migrations


def remove_opportunities_module(apps, schema_editor):
    """Remove opportunities module and all related permissions from database"""
    Module = apps.get_model('authentication', 'Module')
    Permission = apps.get_model('authentication', 'Permission')
    
    try:
        # Get opportunities module
        opportunities_module = Module.objects.get(name='opportunity')
        
        # Delete all permissions related to opportunities module
        Permission.objects.filter(module=opportunities_module).delete()
        
        # Delete the opportunities module itself
        opportunities_module.delete()
        
        print("Successfully removed opportunities module and related permissions")
        
    except Module.DoesNotExist:
        print("Opportunities module not found in database - may have been already removed")


def reverse_remove_opportunities_module(apps, schema_editor):
    """Reverse migration - recreate opportunities module (if needed)"""
    Module = apps.get_model('authentication', 'Module')
    Permission = apps.get_model('authentication', 'Permission')
    
    # Recreate opportunities module
    opportunities_module, created = Module.objects.get_or_create(
        name='opportunity',
        defaults={
            'display_name': 'Opportunities',
            'icon': 'bi-target',
            'url_name': 'opportunity:index',
            'order': 4,
            'is_active': True
        }
    )
    
    if created:
        print("Recreated opportunities module")


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_auto_20250917_1243'),
    ]

    operations = [
        migrations.RunPython(
            remove_opportunities_module,
            reverse_remove_opportunities_module
        ),
    ]