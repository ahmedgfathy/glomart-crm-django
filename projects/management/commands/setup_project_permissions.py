from django.core.management.base import BaseCommand
from django.db import transaction
from authentication.models import Module, Permission


class Command(BaseCommand):
    help = 'Set up project module permissions and lookup data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up project module permissions...'))
        
        with transaction.atomic():
            # Create Projects Module
            project_module, created = Module.objects.get_or_create(
                name='projects',
                defaults={
                    'display_name': 'Projects',
                    'icon': 'bi-building',
                    'url_name': 'projects:project_list',
                    'order': 3,  # After properties (assuming properties is order 2)
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created module: {project_module.display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Module already exists: {project_module.display_name}')
                )
            
            # Create Permissions for Projects Module
            permissions_data = [
                {
                    'name': 'View Projects',
                    'code': 'view',
                    'level': 1,
                    'description': 'Can view project list and details'
                },
                {
                    'name': 'Edit Projects',
                    'code': 'edit',
                    'level': 2,
                    'description': 'Can edit existing projects'
                },
                {
                    'name': 'Create Projects',
                    'code': 'create',
                    'level': 3,
                    'description': 'Can create new projects'
                },
                {
                    'name': 'Delete Projects',
                    'code': 'delete',
                    'level': 4,
                    'description': 'Can delete projects'
                },
                {
                    'name': 'Import Projects',
                    'code': 'import',
                    'level': 3,
                    'description': 'Can import projects from files'
                },
                {
                    'name': 'Export Projects',
                    'code': 'export',
                    'level': 2,
                    'description': 'Can export projects to files'
                },
                {
                    'name': 'Assign Projects',
                    'code': 'assign',
                    'level': 3,
                    'description': 'Can assign projects to users'
                },
                {
                    'name': 'Manage Project History',
                    'code': 'history',
                    'level': 1,
                    'description': 'Can view project history and changes'
                }
            ]
            
            created_permissions = 0
            for perm_data in permissions_data:
                permission, created = Permission.objects.get_or_create(
                    module=project_module,
                    code=perm_data['code'],
                    defaults={
                        'name': perm_data['name'],
                        'level': perm_data['level'],
                        'description': perm_data['description'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_permissions += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Created permission: {permission.name}')
                    )
            
            if created_permissions == 0:
                self.stdout.write(
                    self.style.WARNING('All permissions already exist')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Created {created_permissions} new permissions')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Project module permissions setup completed!')
        )