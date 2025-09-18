import mysql.connector
from django.core.management.base import BaseCommand
from properties.models import Property
import os


class Command(BaseCommand):
    help = 'Update property names and images from original MariaDB database'
    
    def __init__(self):
        super().__init__()
        self.maria_connection = None
        self.cursor = None
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            type=str,
            default='localhost',
            help='MariaDB host (default: localhost)'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='root',
            help='MariaDB username (default: root)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='zerocall',
            help='MariaDB password (default: zerocall)'
        )
        parser.add_argument(
            '--database',
            type=str,
            default='globalcrm',
            help='MariaDB database name (default: globalcrm)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual changes)'
        )
        
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Property Names and Images Update...'))
        
        try:
            # Connect to MariaDB
            self.connect_mariadb(options)
            
            # Update property names and images
            self.update_properties_data(options['dry_run'])
            
            self.stdout.write(self.style.SUCCESS('Update completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Update failed: {str(e)}'))
            raise
        finally:
            if self.cursor:
                self.cursor.close()
            if self.maria_connection:
                self.maria_connection.close()
    
    def connect_mariadb(self, options):
        """Connect to MariaDB database"""
        try:
            self.maria_connection = mysql.connector.connect(
                host=options['host'],
                user=options['user'],
                password=options['password'],
                database=options['database']
            )
            self.cursor = self.maria_connection.cursor(dictionary=True)
            self.stdout.write(self.style.SUCCESS('Connected to MariaDB successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to connect to MariaDB: {str(e)}'))
            raise
    
    def update_properties_data(self, dry_run):
        """Update property names and images from MariaDB"""
        
        # First, let's see what columns are available in the old database
        self.cursor.execute("DESCRIBE properties")
        columns = [col['Field'] for col in self.cursor.fetchall()]
        self.stdout.write(f'Available columns in MariaDB: {", ".join(columns)}')
        
        # Get property data from MariaDB
        query = """
        SELECT 
            id,
            propertyNumber,
            compoundName,
            propertyImage,
            name
        FROM properties 
        ORDER BY id
        """
        
        self.cursor.execute(query)
        maria_properties = self.cursor.fetchall()
        
        self.stdout.write(f'Found {len(maria_properties)} properties in MariaDB')
        
        # Counters
        updated_names = 0
        updated_images = 0
        not_found = 0
        
        for maria_prop in maria_properties:
            # Try to find the corresponding property in Django
            property_id = str(maria_prop['id'])
            property_number = maria_prop.get('propertyNumber', '')
            
            try:
                # Try to find by property_id first, then by property_number
                django_prop = None
                try:
                    django_prop = Property.objects.get(property_id=property_id)
                except Property.DoesNotExist:
                    if property_number:
                        try:
                            django_prop = Property.objects.get(property_number=property_number)
                        except Property.DoesNotExist:
                            pass
                
                if not django_prop:
                    not_found += 1
                    continue
                
                changes_made = False
                
                # Update property name from compoundName if it's currently "Unnamed Property"
                compound_name = maria_prop.get('compoundName', '').strip()
                current_name = django_prop.name or ''
                
                if compound_name and (not current_name or current_name == '' or 'unnamed' in current_name.lower()):
                    if not dry_run:
                        django_prop.name = compound_name
                        changes_made = True
                    updated_names += 1
                    if dry_run:
                        self.stdout.write(f'[DRY RUN] Would update {property_number} name to: "{compound_name}"')
                
                # Update property image from propertyImage
                property_image = maria_prop.get('propertyImage', '').strip()
                
                if property_image:
                    if not dry_run:
                        django_prop.primary_image = property_image
                        changes_made = True
                    updated_images += 1
                    if dry_run:
                        self.stdout.write(f'[DRY RUN] Would update {property_number} image to: "{property_image}"')
                
                # Save changes
                if changes_made and not dry_run:
                    django_prop.save()
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating property {property_id}: {str(e)}'))
                continue
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\nUpdate Summary:'))
        self.stdout.write(f'Properties with updated names: {updated_names}')
        self.stdout.write(f'Properties with updated images: {updated_images}')
        self.stdout.write(f'Properties not found in Django: {not_found}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN. No changes were made.'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated property data!'))