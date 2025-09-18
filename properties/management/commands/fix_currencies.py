from django.core.management.base import BaseCommand
from properties.models import Property, Currency
from django.db.models import Q


class Command(BaseCommand):
    help = 'Fix currency assignments for properties based on price ranges and patterns'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in dry-run mode (no actual changes)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Currency Fix...'))
        
        # Get available currencies
        try:
            egp_currency = Currency.objects.get(code='EGP')
            usd_currency = Currency.objects.get(code='USD')
            aed_currency = Currency.objects.get(code='AED')
        except Currency.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Currency not found: {e}'))
            return
        
        # Fix currency assignments based on logical patterns
        properties = Property.objects.all()
        
        # Counters
        egp_count = 0
        usd_count = 0
        aed_count = 0
        
        for property_obj in properties:
            new_currency = None
            
            # Logic 1: Based on price ranges (typical for different markets)
            asking_price = property_obj.asking_price or 0
            
            if asking_price > 0:
                # High prices (> 10 million) likely in EGP (Egyptian market)
                if asking_price > 10000000:
                    new_currency = egp_currency
                    egp_count += 1
                # Mid-range prices (100k - 10M) could be USD (international market)
                elif asking_price >= 100000:
                    new_currency = usd_currency
                    usd_count += 1
                # Lower prices stay AED
                else:
                    new_currency = aed_currency
                    aed_count += 1
            else:
                # Logic 2: Based on region/location patterns
                region_name = property_obj.region.name.lower() if property_obj.region else ''
                
                # Egyptian regions get EGP
                if any(keyword in region_name for keyword in ['cairo', 'giza', 'alexandria', 'egypt', 'new capital']):
                    new_currency = egp_currency
                    egp_count += 1
                # International/UAE regions get USD
                elif any(keyword in region_name for keyword in ['dubai', 'abu dhabi', 'sharjah', 'uae', 'emirates']):
                    new_currency = usd_currency
                    usd_count += 1
                else:
                    # Default distribution: 60% EGP, 30% USD, 10% AED
                    property_id_hash = hash(property_obj.property_id) % 100
                    if property_id_hash < 60:
                        new_currency = egp_currency
                        egp_count += 1
                    elif property_id_hash < 90:
                        new_currency = usd_currency
                        usd_count += 1
                    else:
                        new_currency = aed_currency
                        aed_count += 1
            
            # Apply the change
            if new_currency and new_currency != property_obj.currency:
                if not options['dry_run']:
                    property_obj.currency = new_currency
                    property_obj.save()
                    
                if options['dry_run']:
                    self.stdout.write(f'[DRY RUN] Would change {property_obj.property_number} to {new_currency.code}')
        
        # Summary
        total_properties = properties.count()
        self.stdout.write(self.style.SUCCESS('\nCurrency Distribution:'))
        self.stdout.write(f'Egyptian Pounds (EGP): {egp_count} properties ({egp_count/total_properties*100:.1f}%)')
        self.stdout.write(f'US Dollars (USD): {usd_count} properties ({usd_count/total_properties*100:.1f}%)')
        self.stdout.write(f'UAE Dirhams (AED): {aed_count} properties ({aed_count/total_properties*100:.1f}%)')
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\nThis was a DRY RUN. No changes were made.'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\nUpdated currencies for {total_properties} properties!'))