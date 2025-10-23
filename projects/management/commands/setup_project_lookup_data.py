from django.core.management.base import BaseCommand
from django.db import transaction
from projects.models import (
    ProjectStatus, ProjectType, ProjectCategory, 
    ProjectPriority, Currency
)


class Command(BaseCommand):
    help = 'Set up project lookup data (statuses, types, categories, etc.)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up project lookup data...'))
        
        with transaction.atomic():
            # Project Statuses
            statuses_data = [
                {'name': 'planning', 'display_name': 'Planning', 'color': '#ffc107', 'order': 1},
                {'name': 'active', 'display_name': 'Active', 'color': '#28a745', 'order': 2},
                {'name': 'on_hold', 'display_name': 'On Hold', 'color': '#fd7e14', 'order': 3},
                {'name': 'completed', 'display_name': 'Completed', 'color': '#6f42c1', 'order': 4},
                {'name': 'cancelled', 'display_name': 'Cancelled', 'color': '#dc3545', 'order': 5}
            ]
            
            created_statuses = 0
            for status_data in statuses_data:
                status, created = ProjectStatus.objects.get_or_create(
                    name=status_data['name'],
                    defaults=status_data
                )
                if created:
                    created_statuses += 1
                    self.stdout.write(f'Created status: {status.display_name}')
            
            # Project Types
            types_data = [
                {'name': 'residential', 'display_name': 'Residential', 'icon': 'bi-house', 'order': 1},
                {'name': 'commercial', 'display_name': 'Commercial', 'icon': 'bi-building', 'order': 2},
                {'name': 'mixed_use', 'display_name': 'Mixed Use', 'icon': 'bi-buildings', 'order': 3},
                {'name': 'industrial', 'display_name': 'Industrial', 'icon': 'bi-gear', 'order': 4},
                {'name': 'retail', 'display_name': 'Retail', 'icon': 'bi-shop', 'order': 5},
                {'name': 'hospitality', 'display_name': 'Hospitality', 'icon': 'bi-bed', 'order': 6}
            ]
            
            created_types = 0
            for type_data in types_data:
                project_type, created = ProjectType.objects.get_or_create(
                    name=type_data['name'],
                    defaults=type_data
                )
                if created:
                    created_types += 1
                    self.stdout.write(f'Created type: {project_type.display_name}')
            
            # Project Categories
            categories_data = [
                {'name': 'luxury', 'display_name': 'Luxury', 'order': 1},
                {'name': 'affordable', 'display_name': 'Affordable Housing', 'order': 2},
                {'name': 'mid_market', 'display_name': 'Mid-Market', 'order': 3},
                {'name': 'government', 'display_name': 'Government', 'order': 4},
                {'name': 'private', 'display_name': 'Private Development', 'order': 5}
            ]
            
            created_categories = 0
            for category_data in categories_data:
                category, created = ProjectCategory.objects.get_or_create(
                    name=category_data['name'],
                    defaults=category_data
                )
                if created:
                    created_categories += 1
                    self.stdout.write(f'Created category: {category.display_name}')
            
            # Project Priorities
            priorities_data = [
                {'name': 'low', 'display_name': 'Low', 'level': 1, 'color': '#6c757d', 'order': 1},
                {'name': 'normal', 'display_name': 'Normal', 'level': 2, 'color': '#17a2b8', 'order': 2},
                {'name': 'high', 'display_name': 'High', 'level': 3, 'color': '#ffc107', 'order': 3},
                {'name': 'urgent', 'display_name': 'Urgent', 'level': 4, 'color': '#dc3545', 'order': 4}
            ]
            
            created_priorities = 0
            for priority_data in priorities_data:
                priority, created = ProjectPriority.objects.get_or_create(
                    name=priority_data['name'],
                    defaults=priority_data
                )
                if created:
                    created_priorities += 1
                    self.stdout.write(f'Created priority: {priority.display_name}')
            
            # Currencies
            currencies_data = [
                {'code': 'EGP', 'name': 'Egyptian Pound', 'symbol': 'LE', 'order': 1},
                {'code': 'USD', 'name': 'US Dollar', 'symbol': '$', 'order': 2},
                {'code': 'EUR', 'name': 'Euro', 'symbol': '€', 'order': 3},
                {'code': 'GBP', 'name': 'British Pound', 'symbol': '£', 'order': 4},
                {'code': 'SAR', 'name': 'Saudi Riyal', 'symbol': 'SR', 'order': 5},
                {'code': 'AED', 'name': 'UAE Dirham', 'symbol': 'AED', 'order': 6}
            ]
            
            created_currencies = 0
            for currency_data in currencies_data:
                currency, created = Currency.objects.get_or_create(
                    code=currency_data['code'],
                    defaults=currency_data
                )
                if created:
                    created_currencies += 1
                    self.stdout.write(f'Created currency: {currency.name}')
            
            # Summary
            total_created = created_statuses + created_types + created_categories + created_priorities + created_currencies
            if total_created > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Setup completed! Created {created_statuses} statuses, '
                        f'{created_types} types, {created_categories} categories, '
                        f'{created_priorities} priorities, and {created_currencies} currencies.'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('All lookup data already exists')
                )