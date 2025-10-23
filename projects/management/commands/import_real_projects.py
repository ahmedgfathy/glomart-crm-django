from django.core.management.base import BaseCommand
import mysql.connector
from projects.models import Project, ProjectStatus, ProjectType
from django.contrib.auth.models import User
from datetime import datetime

class Command(BaseCommand):
    help = 'Import real projects from MariaDB globalcrm database'

    def handle(self, *args, **options):
        try:
            # Connect to MariaDB
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='zerocall',
                database='globalcrm'
            )
            cursor = connection.cursor()
            
            # Clear existing fake projects
            self.stdout.write('Clearing existing projects...')
            Project.objects.all().delete()
            
            # Get real projects from MariaDB
            cursor.execute("""
                SELECT id, name, description, location, status, startDate, endDate, 
                       totalUnits, availableUnits, priceRange, developer, 
                       created_at, updated_at, completionYear
                FROM projects
            """)
            
            projects = cursor.fetchall()
            self.stdout.write(f'Found {len(projects)} projects in MariaDB')
            
            # Get or create default status and type
            default_status, _ = ProjectStatus.objects.get_or_create(
                name='active', 
                defaults={'display_name': 'Active', 'color': '#28a745', 'order': 1}
            )
            
            default_type, _ = ProjectType.objects.get_or_create(
                name='residential', 
                defaults={'display_name': 'Residential', 'icon': 'bi bi-building', 'order': 1}
            )
            
            # Get system user for import
            system_user, _ = User.objects.get_or_create(
                username='system_import',
                defaults={'email': 'system@import.local', 'first_name': 'System', 'last_name': 'Import'}
            )
            
            imported_count = 0
            
            for project_data in projects:
                (project_id, name, description, location, status_name, start_date, 
                 end_date, total_units, available_units, price_range, developer,
                 created_at, updated_at, completion_year) = project_data
                
                # Create meaningful name if empty
                if not name or name.strip() == '':
                    name = f'Project {project_id[:8]}'
                
                # Create project
                project = Project.objects.create(
                    project_id=project_id,
                    name=name,
                    description=description or '',
                    location=location or '',
                    developer=developer or '',
                    price_range=price_range or '',
                    start_date=start_date.date() if start_date else None,
                    end_date=end_date.date() if end_date else None,
                    completion_year=completion_year,
                    total_units=total_units or 0,
                    available_units=available_units or 0,
                    status=default_status,
                    project_type=default_type,
                    created_by=system_user,
                    notes=f'Imported from MariaDB globalcrm on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    is_active=True,
                    created_at=created_at or datetime.now(),
                    updated_at=updated_at or datetime.now()
                )
                
                imported_count += 1
                self.stdout.write(f'Imported: {project.name} (ID: {project.project_id})')
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully imported {imported_count} real projects from MariaDB!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing projects: {str(e)}')
            )
        finally:
            if 'connection' in locals():
                connection.close()