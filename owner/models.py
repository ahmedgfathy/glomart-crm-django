from django.db import models
from django.contrib.auth.models import User
from django.core.cache import cache
import pymysql
import json
import re
from typing import List, Dict, Any


class OwnerDatabase(models.Model):
    """Model to track available owner databases"""
    name = models.CharField(max_length=100, unique=True, help_text="Database name")
    display_name = models.CharField(max_length=200, help_text="Human readable name")
    description = models.TextField(blank=True, help_text="Database description")
    table_name = models.CharField(max_length=100, default='data', help_text="Main data table name")
    is_active = models.BooleanField(default=True)
    category = models.CharField(max_length=100, blank=True, help_text="Database category (e.g., Real Estate, Automotive)")
    total_records = models.IntegerField(default=0, help_text="Cached record count")
    last_updated = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'display_name']
        permissions = [
            ("can_view_owner_data", "Can view owner database data"),
            ("can_export_owner_data", "Can export owner database data"),
            ("can_manage_owner_databases", "Can manage owner databases"),
        ]

    def __str__(self):
        return self.display_name or self.name

    def generate_display_name(self):
        """Generate a human-friendly display name from database name"""
        name = self.name
        
        # Remove 'rs_' prefix if present
        if name.startswith('rs_'):
            name = name[3:]
        
        # Define specific mappings for known databases
        name_mappings = {
            'rehab': 'Rehab City Properties',
            'marassi': 'Marassi North Coast',
            'mivida': 'Mivida New Cairo',
            'palm': 'Palm Parks October',
            'uptown': 'Uptown Cairo',
            'amwaj': 'Amwaj North Coast',
            'gouna': 'El Gouna Properties',
            'mangroovy': 'Mangroovy Bay Sahel',
            'sahel': 'North Coast Sahel',
            'katameya': 'Katameya Heights',
            'sabour': 'Sabour New Cairo',
            'tagamoa': 'Tagamoa Fifth Settlement',
            'zayed': 'Sheikh Zayed City',
            'october': '6th October City',
            'villas': 'Premium Villas Collection',
            'sodic': 'SODIC Developments',
            'jedar': 'Jedar 6th October',
            'hadaeq': 'Hadaeq Al Ahram',
            'newgiza': 'New Giza Compound',
            'newcairo': 'New Cairo Properties',
            'compounds': 'Compound Properties',
            'apartments': 'Apartment Listings',
            'studios': 'Studio Apartments',
            'duplexes': 'Duplex Properties',
            'penthouses': 'Penthouse Collection',
            'commercial': 'Commercial Properties',
            'retail': 'Retail Spaces',
            'offices': 'Office Spaces',
            'warehouses': 'Warehouse Properties',
            'lands': 'Land Plots',
            'farms': 'Farm Properties',
            'chalets': 'Chalet Properties',
            'hotels': 'Hotel Properties',
            'resorts': 'Resort Properties',
        }
        
        # Check for exact match first
        if name.lower() in name_mappings:
            return name_mappings[name.lower()]
        
        # Check for partial matches
        for key, display_name in name_mappings.items():
            if key in name.lower():
                return display_name
        
        # Generic name improvement
        # Replace underscores with spaces and title case
        display_name = name.replace('_', ' ').title()
        
        # Handle common patterns
        if 'compound' in name.lower():
            display_name += ' Compound'
        elif 'villa' in name.lower():
            display_name += ' Villas'
        elif 'apartment' in name.lower():
            display_name += ' Apartments'
        elif 'office' in name.lower():
            display_name += ' Offices'
        elif 'commercial' in name.lower():
            display_name += ' Commercial'
        elif 'land' in name.lower():
            display_name += ' Lands'
        
        return display_name

    def analyze_column_content(self, column_name, sample_size=100):
        """Analyze column content to suggest a better display name"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                # Get sample data from the column
                cursor.execute(f"SELECT {column_name} FROM {self.table_name} WHERE {column_name} IS NOT NULL AND {column_name} != '' LIMIT %s", [sample_size])
                sample_data = [row[column_name] for row in cursor.fetchall()]
                
                if not sample_data:
                    return None
                
                # Analyze patterns in the data
                return self._analyze_data_patterns(sample_data, column_name)
                
        except Exception as e:
            print(f"Error analyzing column {column_name}: {e}")
            return None
        finally:
            connection.close()

    def _analyze_data_patterns(self, data_samples, original_column):
        """Analyze data patterns to suggest column names"""
        # Convert all samples to strings for analysis
        str_samples = [str(item).strip() for item in data_samples if item is not None]
        
        if not str_samples:
            return original_column
        
        # Pattern definitions with their suggested names
        patterns = {
            # Contact Information
            r'^(\+?\d{1,4}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}$': 'Phone Number',
            r'^(\+?\d{10,15})$': 'Mobile Number',
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$': 'Email Address',
            
            # Names
            r'^[A-Z][a-z]+ [A-Z][a-z]+$': 'Full Name',
            r'^[A-Z][a-z]+$': 'First Name',
            
            # Addresses and Location
            r'.*street.*|.*st\.|.*avenue.*|.*ave\.|.*road.*|.*rd\.': 'Street Address',
            r'.*cairo.*|.*giza.*|.*alexandria.*|.*new capital.*': 'City',
            r'^\d{5}(-\d{4})?$': 'Postal Code',
            
            # Real Estate Specific
            r'.*apartment.*|.*apt.*|.*flat.*|.*unit.*': 'Unit Type',
            r'.*villa.*|.*house.*|.*duplex.*|.*penthouse.*': 'Property Type',
            r'.*bedroom.*|.*bed.*|.*br.*': 'Bedrooms',
            r'.*bathroom.*|.*bath.*|.*br.*': 'Bathrooms',
            r'.*sqm.*|.*square.*|.*meter.*|.*m2.*': 'Area (SQM)',
            r'.*price.*|.*egp.*|.*pound.*|.*le.*': 'Price (EGP)',
            r'.*budget.*|.*cost.*|.*amount.*': 'Budget',
            
            # Dates
            r'^\d{4}-\d{2}-\d{2}$': 'Date',
            r'^\d{2}/\d{2}/\d{4}$': 'Date',
            r'^\d{1,2}-\d{1,2}-\d{4}$': 'Date',
            
            # IDs and Numbers
            r'^[A-Z]{2,4}\d{6,}$': 'ID Number',
            r'^\d{10,}$': 'Reference Number',
            
            # Status fields
            r'^(active|inactive|pending|completed|cancelled)$': 'Status',
            r'^(yes|no|true|false|1|0)$': 'Yes/No',
            
            # Gender
            r'^(male|female|m|f)$': 'Gender',
            
            # Ages
            r'^\d{1,3}$': 'Age',
        }
        
        # Keyword-based suggestions for column names
        keyword_suggestions = {
            'name': 'Name',
            'fname': 'First Name',
            'lname': 'Last Name',
            'first': 'First Name',
            'last': 'Last Name',
            'email': 'Email',
            'mail': 'Email Address',
            'phone': 'Phone Number',
            'mobile': 'Mobile Number',
            'tel': 'Telephone',
            'address': 'Address',
            'city': 'City',
            'area': 'Area',
            'region': 'Region',
            'country': 'Country',
            'age': 'Age',
            'gender': 'Gender',
            'date': 'Date',
            'time': 'Time',
            'price': 'Price',
            'cost': 'Cost',
            'budget': 'Budget',
            'amount': 'Amount',
            'status': 'Status',
            'type': 'Type',
            'category': 'Category',
            'description': 'Description',
            'notes': 'Notes',
            'comments': 'Comments',
            'id': 'ID',
            'ref': 'Reference',
            'code': 'Code',
            'number': 'Number',
            'property': 'Property',
            'unit': 'Unit',
            'apartment': 'Apartment',
            'villa': 'Villa',
            'bedroom': 'Bedrooms',
            'bathroom': 'Bathrooms',
            'floor': 'Floor',
            'building': 'Building',
            'compound': 'Compound',
            'project': 'Project',
        }
        
        # First, check if column name contains keywords
        lower_column = original_column.lower()
        for keyword, suggestion in keyword_suggestions.items():
            if keyword in lower_column:
                return suggestion
        
        # Count pattern matches
        pattern_scores = {}
        for pattern, suggested_name in patterns.items():
            matches = sum(1 for sample in str_samples if re.match(pattern, sample, re.IGNORECASE))
            if matches > 0:
                # Calculate match percentage
                match_percentage = (matches / len(str_samples)) * 100
                pattern_scores[suggested_name] = match_percentage
        
        # If we have strong pattern matches (>60%), use the best one
        if pattern_scores:
            best_match = max(pattern_scores.items(), key=lambda x: x[1])
            if best_match[1] >= 60:  # 60% or more matches
                return best_match[0]
        
        # Fallback: Clean up the original column name
        cleaned_name = original_column.replace('_', ' ').replace('-', ' ').title()
        
        # Remove common prefixes/suffixes that don't add value
        cleaned_name = re.sub(r'^(Column|Field|Data|Info|Var)\s*\d*\s*', '', cleaned_name, flags=re.IGNORECASE)
        cleaned_name = re.sub(r'\s*(Column|Field|Data|Info|Var)\s*\d*$', '', cleaned_name, flags=re.IGNORECASE)
        
        return cleaned_name or original_column

    def get_smart_column_mapping(self):
        """Get intelligent column name mappings for better display"""
        cache_key = f"smart_columns_{self.name}"
        cached_mapping = cache.get(cache_key)
        
        if cached_mapping:
            return cached_mapping
        
        mapping = {}
        table_info = self.get_table_info()
        
        if not table_info or not table_info.get('columns'):
            return mapping
        
        for column in table_info['columns']:
            column_name = column['Field']
            
            # Skip source_file columns completely
            if 'source_file' in column_name.lower():
                continue
                
            smart_name = self.analyze_column_content(column_name)
            if smart_name and smart_name != column_name:
                mapping[column_name] = smart_name
            else:
                # Fallback to basic name improvement
                mapping[column_name] = column_name.replace('_', ' ').title()
        
        # Cache for 1 hour
        cache.set(cache_key, mapping, 3600)
        return mapping

    @classmethod
    def get_total_records_across_all_dbs(cls):
        """Get total count of records across all active Owner databases"""
        from django.core.cache import cache
        
        cache_key = "owner_total_records_count"
        cached_count = cache.get(cache_key)
        
        if cached_count is not None:
            return cached_count
        
        total_count = 0
        active_databases = cls.objects.filter(is_active=True)
        
        for db in active_databases:
            try:
                connection = db.get_connection()
                if connection:
                    with connection.cursor() as cursor:
                        cursor.execute(f"SELECT COUNT(*) FROM {db.table_name}")
                        count = cursor.fetchone()[0]
                        total_count += count
                        
                        # Update the database's cached record count
                        db.total_records = count
                        db.save(update_fields=['total_records'])
                    connection.close()
            except Exception as e:
                print(f"Error counting records for {db.name}: {e}")
                continue
        
        # Cache for 5 minutes
        cache.set(cache_key, total_count, 300)
        return total_count

    def get_connection(self):
        """Get database connection for this specific database"""
        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='zerocall',
                database=self.name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(f"Error connecting to database {self.name}: {e}")
            return None

    def get_table_info(self):
        """Get table structure information"""
        cache_key = f"owner_db_info_{self.name}"
        cached_info = cache.get(cache_key)
        
        if cached_info:
            return cached_info
        
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                # Get table columns
                cursor.execute(f"DESCRIBE {self.table_name}")
                columns = cursor.fetchall()
                
                # Get record count
                cursor.execute(f"SELECT COUNT(*) as count FROM {self.table_name}")
                count_result = cursor.fetchone()
                record_count = count_result['count'] if count_result else 0
                
                # Update cached record count
                self.total_records = record_count
                self.save(update_fields=['total_records'])
                
                table_info = {
                    'columns': columns,
                    'record_count': record_count,
                    'table_name': self.table_name
                }
                
                # Cache for 1 hour
                cache.set(cache_key, table_info, 3600)
                return table_info
                
        except Exception as e:
            print(f"Error getting table info for {self.name}: {e}")
            return None
        finally:
            connection.close()

    def get_data(self, limit=100, offset=0, search=None, filters=None):
        """Get data from the database table"""
        connection = self.get_connection()
        if not connection:
            return {'data': [], 'total': 0}
        
        try:
            with connection.cursor() as cursor:
                # Build WHERE clause
                where_conditions = []
                params = []
                
                if search:
                    # Get column names for search
                    table_info = self.get_table_info()
                    if table_info and table_info['columns']:
                        search_conditions = []
                        for column in table_info['columns']:
                            col_name = column['Field']
                            # Only search in text-based columns
                            if column['Type'].startswith(('varchar', 'text', 'char')):
                                search_conditions.append(f"{col_name} LIKE %s")
                                params.append(f"%{search}%")
                        
                        if search_conditions:
                            where_conditions.append(f"({' OR '.join(search_conditions)})")
                
                if filters:
                    for field, value in filters.items():
                        if value:
                            where_conditions.append(f"{field} = %s")
                            params.append(value)
                
                where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
                
                # Get total count
                count_query = f"SELECT COUNT(*) as total FROM {self.table_name} {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()['total']
                
                # Get data with pagination
                data_query = f"SELECT * FROM {self.table_name} {where_clause} LIMIT %s OFFSET %s"
                cursor.execute(data_query, params + [limit, offset])
                data = cursor.fetchall()
                
                return {
                    'data': data,
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
                
        except Exception as e:
            print(f"Error getting data from {self.name}: {e}")
            return {'data': [], 'total': 0}
        finally:
            connection.close()

    def get_record_by_id(self, record_id):
        """Get a specific record by ID"""
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [record_id])
                return cursor.fetchone()
        except Exception as e:
            print(f"Error getting record {record_id} from {self.name}: {e}")
            return None
        finally:
            connection.close()

    @classmethod
    def get_available_databases(cls):
        """Get list of available MariaDB databases"""
        try:
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='zerocall',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES")
                databases = cursor.fetchall()
                
                # Filter to only include databases that start with 'rs_'
                rs_databases = [
                    db['Database'] for db in databases 
                    if db['Database'].startswith('rs_')
                ]
                
                return rs_databases
                
        except Exception as e:
            print(f"Error getting available databases: {e}")
            return []
        finally:
            if 'connection' in locals():
                connection.close()


class OwnerDatabaseAccess(models.Model):
    """Track user access to specific owner databases"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    database = models.ForeignKey(OwnerDatabase, on_delete=models.CASCADE)
    last_accessed = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'database']
        
    def __str__(self):
        return f"{self.user.username} - {self.database.name}"
