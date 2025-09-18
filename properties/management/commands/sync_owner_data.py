import mysql.connector
from django.core.management.base import BaseCommand
from properties.models import Property


class Command(BaseCommand):
    help = 'Sync owner data from MariaDB globalcrm database to Django database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # MariaDB connection settings
        mariadb_config = {
            'user': 'root',
            'password': 'zerocall',
            'host': 'localhost',
            'database': 'globalcrm'
        }

        try:
            # Connect to MariaDB
            self.stdout.write(self.style.SUCCESS('Connecting to MariaDB globalcrm database...'))
            connection = mysql.connector.connect(**mariadb_config)
            cursor = connection.cursor(dictionary=True)

            # Query to get owner data from MariaDB
            query = """
                SELECT id, propertyNumber, name, mobileNo, propertyOfferedBy
                FROM properties 
                WHERE name IS NOT NULL OR mobileNo IS NOT NULL
            """
            
            cursor.execute(query)
            mariadb_properties = cursor.fetchall()
            
            self.stdout.write(f'Found {len(mariadb_properties)} properties with owner data in MariaDB')
            
            updated_count = 0
            created_count = 0
            
            for mariadb_prop in mariadb_properties:
                property_id = mariadb_prop['id']
                owner_name = mariadb_prop['name'] if mariadb_prop['name'] and mariadb_prop['name'] != '--' else None
                owner_phone = mariadb_prop['mobileNo']
                property_offered_by = mariadb_prop['propertyOfferedBy']
                
                if dry_run:
                    self.stdout.write(
                        f'Would update Property {property_id}: '
                        f'owner_name="{owner_name}", owner_phone="{owner_phone}"'
                    )
                    continue
                
                try:
                    # Try to get existing property in Django
                    django_property = Property.objects.get(property_id=property_id)
                    
                    # Update owner fields if they have values
                    updated = False
                    if owner_name and owner_name != django_property.owner_name:
                        django_property.owner_name = owner_name
                        updated = True
                    
                    if owner_phone and owner_phone != django_property.owner_phone:
                        django_property.owner_phone = owner_phone
                        updated = True
                    
                    if updated:
                        django_property.save()
                        updated_count += 1
                        self.stdout.write(
                            f'Updated Property {property_id}: '
                            f'owner_name="{owner_name}", owner_phone="{owner_phone}"'
                        )
                    
                except Property.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Property {property_id} not found in Django database')
                    )
                    continue
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error updating Property {property_id}: {str(e)}')
                    )
                    continue
            
            if not dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully updated {updated_count} properties with owner data'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Dry run complete. Would update {len(mariadb_properties)} properties'
                    )
                )
            
        except mysql.connector.Error as err:
            self.stdout.write(self.style.ERROR(f'MariaDB Error: {err}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
                self.stdout.write('MariaDB connection closed')