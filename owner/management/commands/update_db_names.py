from django.core.management.base import BaseCommand
from owner.models import OwnerDatabase


class Command(BaseCommand):
    help = 'Update display names for all Owner databases'

    def handle(self, *args, **options):
        databases = OwnerDatabase.objects.all()
        updated_count = 0
        
        for db in databases:
            old_display_name = db.display_name
            new_display_name = db.generate_display_name()
            
            if old_display_name != new_display_name:
                db.display_name = new_display_name
                db.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated "{db.name}": "{old_display_name}" -> "{new_display_name}"'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} database display names'
            )
        )