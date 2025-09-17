from django.core.management.base import BaseCommand
from authentication.models import Module, Permission


class Command(BaseCommand):
    help = 'Create initial modules and permissions for Glomart CRM'

    def handle(self, *args, **options):
        # Define modules
        modules_data = [
            {'name': 'leads', 'display_name': 'Leads', 'icon': 'bi-person-lines-fill', 'url_name': 'leads:index', 'order': 1},
            {'name': 'property', 'display_name': 'Property', 'icon': 'bi-building', 'url_name': 'property:index', 'order': 2},
            {'name': 'project', 'display_name': 'Projects', 'icon': 'bi-diagram-3', 'url_name': 'project:index', 'order': 3},
            {'name': 'opportunity', 'display_name': 'Opportunities', 'icon': 'bi-target', 'url_name': 'opportunity:index', 'order': 4},
            {'name': 'report', 'display_name': 'Reports', 'icon': 'bi-graph-up', 'url_name': 'report:index', 'order': 5},
            {'name': 'calendar', 'display_name': 'Calendar', 'icon': 'bi-calendar3', 'url_name': 'calendar:index', 'order': 6},
            {'name': 'document', 'display_name': 'Documents', 'icon': 'bi-file-earmark-text', 'url_name': 'document:index', 'order': 7},
            {'name': 'authentication', 'display_name': 'User Management', 'icon': 'bi-people', 'url_name': 'authentication:users', 'order': 8},
        ]

        # Create modules
        created_modules = []
        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=module_data['name'],
                defaults=module_data
            )
            if created:
                created_modules.append(module)
                self.stdout.write(f"Created module: {module.display_name}")

        # Define permissions for each module
        permissions_data = [
            {'code': 'view', 'name': 'View', 'level': 1, 'description': 'Can view records'},
            {'code': 'edit', 'name': 'Edit', 'level': 2, 'description': 'Can edit existing records'},
            {'code': 'create', 'name': 'Create', 'level': 3, 'description': 'Can create new records'},
            {'code': 'delete', 'name': 'Delete', 'level': 4, 'description': 'Can delete records'},
        ]

        # Create permissions for each module
        created_permissions = 0
        for module in Module.objects.all():
            for perm_data in permissions_data:
                permission, created = Permission.objects.get_or_create(
                    module=module,
                    code=perm_data['code'],
                    defaults={
                        'name': f"{perm_data['name']} {module.display_name}",
                        'level': perm_data['level'],
                        'description': f"{perm_data['description']} in {module.display_name}"
                    }
                )
                if created:
                    created_permissions += 1

        self.stdout.write(f"Created {created_permissions} permissions")
        self.stdout.write(self.style.SUCCESS('Successfully initialized modules and permissions'))