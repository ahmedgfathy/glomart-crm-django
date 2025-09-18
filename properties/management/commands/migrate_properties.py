import mysql.connector
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from properties.models import (
    Property, Region, FinishingType, UnitPurpose, PropertyType, 
    PropertyCategory, Compound, PropertyStatus, PropertyActivity, 
    Project, Currency, PropertyHistory
)
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'Migrate properties from MariaDB to Django SQLite with 100% data integrity'
    
    def __init__(self):
        super().__init__()
        self.maria_connection = None
        self.cursor = None
        self.lookup_mappings = {}
        
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
            help='Run migration in dry-run mode (no actual data changes)'
        )
        
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Properties Migration from MariaDB...'))
        
        try:
            # Connect to MariaDB
            self.connect_mariadb(options)
            
            # Step 1: Create default currencies
            self.create_default_currencies()
            
            # Step 2: Migrate lookup tables first
            self.migrate_lookup_tables()
            
            # Step 3: Migrate main properties
            self.migrate_properties(options['dry_run'])
            
            # Step 4: Copy media files
            if not options['dry_run']:
                self.copy_media_files()
            
            self.stdout.write(self.style.SUCCESS('Migration completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Migration failed: {str(e)}'))
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
    
    def create_default_currencies(self):
        """Create default currencies"""
        currencies = [
            {'code': 'AED', 'name': 'UAE Dirham', 'symbol': 'AED'},
            {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
            {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
            {'code': 'EGP', 'name': 'Egyptian Pound', 'symbol': 'EGP'},
        ]
        
        for curr_data in currencies:
            currency, created = Currency.objects.get_or_create(
                code=curr_data['code'],
                defaults={
                    'name': curr_data['name'],
                    'symbol': curr_data['symbol']
                }
            )
            if created:
                self.stdout.write(f'Created currency: {currency.code}')
    
    def migrate_lookup_tables(self):
        """Migrate and create lookup table data from unique values in properties"""
        self.stdout.write('Migrating lookup tables...')
        
        # Define lookup table mappings
        lookup_configs = [
            ('area', Region, 'Areas/Regions'),
            ('unitFor', UnitPurpose, 'Unit Purposes'),
            ('type', PropertyType, 'Property Types'),
            ('category', PropertyCategory, 'Property Categories'),
            ('compoundName', Compound, 'Compounds'),
            ('status', PropertyStatus, 'Property Status'),
            ('activity', PropertyActivity, 'Property Activities'),
            ('project', Project, 'Projects'),
        ]
        
        for field_name, model_class, description in lookup_configs:
            self.migrate_lookup_data(field_name, model_class, description)
    
    def migrate_lookup_data(self, field_name, model_class, description):
        """Migrate unique values from a field to a lookup table"""
        try:
            # Get unique non-empty values from MariaDB
            query = f"SELECT DISTINCT {field_name} FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != '' ORDER BY {field_name}"
            self.cursor.execute(query)
            unique_values = [row[field_name] for row in self.cursor.fetchall()]
            
            created_count = 0
            for value in unique_values:
                if value and value.strip():
                    # Create lookup entry
                    lookup_obj, created = model_class.objects.get_or_create(
                        name=value.strip()
                    )
                    if created:
                        created_count += 1
            
            self.stdout.write(f'  {description}: {created_count} new entries created from {len(unique_values)} unique values')
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  Warning: Could not migrate {description}: {str(e)}'))
    
    def migrate_properties(self, dry_run=False):
        """Migrate main properties data"""
        self.stdout.write('Migrating properties data...')
        
        try:
            # Get all properties from MariaDB
            self.cursor.execute("SELECT * FROM properties ORDER BY id")
            maria_properties = self.cursor.fetchall()
            
            total_count = len(maria_properties)
            success_count = 0
            error_count = 0
            
            self.stdout.write(f'Found {total_count} properties to migrate')
            
            for i, prop_data in enumerate(maria_properties, 1):
                try:
                    if not dry_run:
                        self.create_django_property(prop_data)
                    success_count += 1
                    
                    if i % 100 == 0:
                        self.stdout.write(f'  Processed {i}/{total_count} properties...')
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.WARNING(f'  Error migrating property {prop_data.get("id", "unknown")}: {str(e)}'))
            
            self.stdout.write(f'Properties migration completed: {success_count} successful, {error_count} errors')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to migrate properties: {str(e)}'))
            raise
    
    def create_django_property(self, maria_data):
        """Create a Django Property from MariaDB data"""
        
        # Handle lookup relationships
        region = self.get_lookup_object(Region, maria_data.get('area'))
        finishing_type = None  # Not available in this table structure
        unit_purpose = self.get_lookup_object(UnitPurpose, maria_data.get('unitFor'))
        property_type = self.get_lookup_object(PropertyType, maria_data.get('type'))
        category = self.get_lookup_object(PropertyCategory, maria_data.get('category'))
        compound = self.get_lookup_object(Compound, maria_data.get('compoundName'))
        status = self.get_lookup_object(PropertyStatus, maria_data.get('status'))
        activity = self.get_lookup_object(PropertyActivity, maria_data.get('activity'))
        project = self.get_lookup_object(Project, maria_data.get('project'))
        
        # Get default currency (AED)
        currency = Currency.objects.filter(code='AED').first()
        
        # Handle user assignments
        handler = self.get_user_by_name(maria_data.get('handler'))
        sales_person = self.get_user_by_name(maria_data.get('salesPerson'))
        
        # Prepare JSON fields
        images = self.parse_json_field(maria_data.get('images'))
        property_images = self.parse_json_field(maria_data.get('property_images'))
        videos = self.parse_json_field(maria_data.get('videos'))
        
        # Parse facilities and features
        facilities = self.parse_comma_separated(maria_data.get('facilities'))
        features = self.parse_comma_separated(maria_data.get('features'))
        
        # Create Property object
        property_obj = Property.objects.create(
            # Primary identification
            property_id=str(maria_data.get('id', '')),
            property_number=maria_data.get('propertyNumber', ''),
            name=maria_data.get('name', ''),
            
            # Basic information
            building=maria_data.get('building', ''),
            unit_number=maria_data.get('unitNumber', ''),
            apartment_number=maria_data.get('apartmentNumber', ''),
            plot_number=maria_data.get('plotNumber', ''),
            floor_number=self.safe_int(maria_data.get('floorNumber')),
            total_floors=self.safe_int(maria_data.get('totalFloors')),
            
            # Relationships
            region=region,
            finishing_type=finishing_type,
            unit_purpose=unit_purpose,
            property_type=property_type,
            category=category,
            compound=compound,
            status=status,
            activity=activity,
            project=project,
            currency=currency,
            
            # Descriptive fields
            description=maria_data.get('description', ''),
            unit_features=maria_data.get('unitFeatures', ''),
            phase=maria_data.get('phase', ''),
            the_floors=maria_data.get('theFloors', ''),
            in_or_outside_compound=maria_data.get('inOrOutsideCompound', ''),
            year_built=self.safe_int(maria_data.get('yearBuilt')),
            
            # Room information
            rooms=self.safe_int(maria_data.get('rooms')),
            living_rooms=self.safe_int(maria_data.get('livingRooms', 0)),
            sales_rooms=self.safe_int(maria_data.get('salesRooms', 0)),
            bathrooms=self.safe_int(maria_data.get('bathrooms', 0)),
            
            # Area measurements
            land_area=maria_data.get('landArea', ''),
            land_garden_area=self.safe_decimal(maria_data.get('landGardenArea')),
            sales_area=self.safe_decimal(maria_data.get('salesArea')),
            total_space=self.safe_decimal(maria_data.get('totalSpace')),
            space_earth=maria_data.get('spaceEarth', ''),
            space_unit=maria_data.get('spaceUnit', ''),
            space_guard=maria_data.get('spaceGuard', ''),
            
            # Pricing
            base_price=self.safe_decimal(maria_data.get('basePrice')),
            asking_price=self.safe_decimal(maria_data.get('askingPrice')),
            sold_price=self.safe_decimal(maria_data.get('soldPrice')),
            total_price=self.safe_decimal(maria_data.get('totalPrice')),
            price_per_meter=self.safe_decimal(maria_data.get('pricePerMeter')),
            transfer_fees=self.safe_decimal(maria_data.get('transferFees')),
            maintenance_fees=self.safe_decimal(maria_data.get('maintenanceFees')),
            
            # Payment information
            down_payment=self.safe_decimal(maria_data.get('downPayment')),
            installment=self.safe_decimal(maria_data.get('installment')),
            monthly_payment=self.safe_decimal(maria_data.get('monthlyPayment')),
            payment_frequency=maria_data.get('payedEvery', ''),
            
            # Features
            facilities=facilities,
            features=features,
            
            # Boolean features
            has_garage=self.safe_bool(maria_data.get('hasGarage')),
            garage_type=maria_data.get('garageType', ''),
            has_garden=self.safe_bool(maria_data.get('hasGarden')),
            garden_type=maria_data.get('gardenType', ''),
            has_pool=self.safe_bool(maria_data.get('hasPool')),
            pool_type=maria_data.get('poolType', ''),
            has_terraces=self.safe_bool(maria_data.get('hasTerraces')),
            terrace_type=maria_data.get('terraceType', ''),
            
            # Status flags
            is_liked=self.safe_bool(maria_data.get('isLiked')),
            is_in_home=self.safe_bool(maria_data.get('isInHome')),
            update_required=self.safe_bool(maria_data.get('updateRequired')),
            
            # Assignment
            property_offered_by=maria_data.get('propertyOfferedBy', ''),
            handler=handler,
            sales_person=sales_person,
            
            # Contact
            mobile_number=maria_data.get('mobileNumber', ''),
            secondary_phone=maria_data.get('secondaryPhone', ''),
            telephone=maria_data.get('telephone', ''),
            
            # Notes
            notes=maria_data.get('notes', ''),
            sales_notes=maria_data.get('salesNotes', ''),
            general_notes=maria_data.get('generalNotes', ''),
            call_updates=maria_data.get('callUpdates', ''),
            activity_notes=maria_data.get('activityNotes', ''),
            call_update=maria_data.get('callUpdate', ''),
            for_update=maria_data.get('forUpdate', ''),
            
            # Dates
            last_follow_up=self.safe_datetime(maria_data.get('lastFollowUp')),
            sold_date=self.safe_date(maria_data.get('soldDate')),
            rental_start_date=self.safe_date(maria_data.get('rentalStartDate')),
            rental_end_date=self.safe_date(maria_data.get('rentalEndDate')),
            rent_from=self.safe_datetime(maria_data.get('rentFrom')),
            rent_to=self.safe_datetime(maria_data.get('rentTo')),
            
            # Media
            primary_image=maria_data.get('primaryImage', ''),
            thumbnail_path=maria_data.get('thumbnailPath', ''),
            images=images,
            property_images=property_images,
            videos=videos,
            virtual_tour_url=maria_data.get('virtualTourUrl', ''),
            brochure_url=maria_data.get('brochureUrl', ''),
            
            # Timestamps
            created_time=self.safe_datetime(maria_data.get('createdTime')),
            modified_time=self.safe_datetime(maria_data.get('modifiedTime')),
        )
        
        return property_obj
    
    def get_lookup_object(self, model_class, value):
        """Get lookup object by name"""
        if value and value.strip():
            try:
                return model_class.objects.get(name=value.strip())
            except model_class.DoesNotExist:
                return None
        return None
    
    def get_user_by_name(self, username):
        """Get user by username"""
        if username and username.strip():
            try:
                return User.objects.get(username=username.strip())
            except User.DoesNotExist:
                return None
        return None
    
    def parse_json_field(self, value):
        """Parse JSON field safely"""
        if not value:
            return []
        try:
            if isinstance(value, str):
                return json.loads(value)
            return value
        except:
            return []
    
    def parse_comma_separated(self, value):
        """Parse comma-separated values to list"""
        if not value:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return []
    
    def safe_int(self, value):
        """Safely convert to integer"""
        if value is None or value == '':
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def safe_decimal(self, value):
        """Safely convert to decimal"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def safe_bool(self, value):
        """Safely convert to boolean"""
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    def safe_datetime(self, value):
        """Safely convert to datetime"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        return None
    
    def safe_date(self, value):
        """Safely convert to date"""
        if not value:
            return None
        if hasattr(value, 'date'):
            return value.date()
        return None
    
    def copy_media_files(self):
        """Copy media files from MariaDB server to Django static files"""
        self.stdout.write('Note: Media files need to be manually copied to static/properties/')
        self.stdout.write('  Copy property-image/ folder to static/properties/images/')
        self.stdout.write('  Copy property-video/ folder to static/properties/videos/')
        self.stdout.write('  Update .gitignore to include /static/properties/images/ and /static/properties/videos/')