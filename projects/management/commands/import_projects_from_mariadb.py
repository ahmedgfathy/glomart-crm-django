from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
import mysql.connector
from projects.models import Project, ProjectStatus, ProjectType


class Command(BaseCommand):
    help = 'Import projects from MariaDB globalcrm database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='MariaDB host (default: localhost)',
        )
        parser.add_argument(
            '--user',
            type=str,
            default='root',
            help='MariaDB username (default: root)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='zerocall',
            help='MariaDB password (default: zerocall)',
        )
        parser.add_argument(
            '--database',
            type=str,
            default='globalcrm',
            help='MariaDB database name (default: globalcrm)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting project import from MariaDB...'))
        
        try:
            # Get or create a default user for imported projects
            default_user, created = User.objects.get_or_create(
                username='system_import',
                defaults={
                    'first_name': 'System',
                    'last_name': 'Import',
                    'email': 'system@import.local',
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write('Created default import user: system_import')
            
            # Connect to MariaDB
            connection = mysql.connector.connect(
                host=options['host'],
                user=options['user'],
                password=options['password'],
                database=options['database']
            )
            cursor = connection.cursor(dictionary=True)
            
            # Fetch projects from MariaDB
            cursor.execute("SELECT * FROM projects")
            mariadb_projects = cursor.fetchall()
            
            self.stdout.write(f'Found {len(mariadb_projects)} projects in MariaDB')
            
            # Get default status and type for import
            active_status = ProjectStatus.objects.filter(name='active').first()
            residential_type = ProjectType.objects.filter(name='residential').first()
            
            if not active_status:
                self.stdout.write(self.style.ERROR('No active status found. Run setup_project_lookup_data first.'))
                return
            
            if not residential_type:
                self.stdout.write(self.style.ERROR('No residential type found. Run setup_project_lookup_data first.'))
                return
            
            imported_count = 0
            updated_count = 0
            
            with transaction.atomic():
                for maria_project in mariadb_projects:
                    project_id = maria_project['id']
                    
                    # Check if project already exists
                    existing_project = Project.objects.filter(project_id=project_id).first()
                    
                    # Prepare project data
                    project_data = {
                        'name': maria_project.get('name', f'Project {project_id}'),
                        'description': maria_project.get('description', ''),
                        'location': maria_project.get('location', ''),
                        'developer': maria_project.get('developer', ''),
                        'status': active_status,
                        'project_type': residential_type,
                        'start_date': maria_project.get('startDate'),
                        'end_date': maria_project.get('endDate'),
                        'completion_year': maria_project.get('completionYear'),
                        'total_units': maria_project.get('totalUnits'),
                        'available_units': maria_project.get('availableUnits'),
                        'price_range': maria_project.get('priceRange', ''),
                        'notes': f"Imported from MariaDB globalcrm on {maria_project.get('created_at', '')}",
                        'is_active': True,
                        'created_by': default_user,
                    }
                    
                    if existing_project:
                        # Update existing project
                        for field, value in project_data.items():
                            if value is not None:
                                setattr(existing_project, field, value)
                        existing_project.save()
                        updated_count += 1
                        self.stdout.write(f'Updated project: {existing_project.name}')
                    else:
                        # Create new project with custom project_id
                        project = Project(**project_data)
                        project.project_id = project_id  # Set custom ID
                        project.save()
                        imported_count += 1
                        self.stdout.write(f'Imported project: {project.name}')
            
            cursor.close()
            connection.close()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Import completed! Imported {imported_count} new projects, '
                    f'updated {updated_count} existing projects.'
                )
            )
            
        except mysql.connector.Error as e:
            self.stdout.write(
                self.style.ERROR(f'MariaDB connection error: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Import error: {e}')
            )