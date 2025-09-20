from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import UserProfile, Module, Permission


class Command(BaseCommand):
    help = 'Test residential user permissions'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to test')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f"Testing user: {user.username} ({user.first_name} {user.last_name})")
            
            # Check if user has profile
            if hasattr(user, 'user_profile'):
                user_profile = user.user_profile
                self.stdout.write(f"User Profile: {user_profile}")
                self.stdout.write(f"Phone: {user_profile.phone}")
                
                if user_profile.profile:
                    profile = user_profile.profile
                    self.stdout.write(f"Assigned Profile: {profile.name}")
                    self.stdout.write(f"Profile Description: {profile.description}")
                    
                    # Show accessible modules
                    accessible_modules = profile.get_accessible_modules()
                    self.stdout.write(f"\nAccessible Modules ({accessible_modules.count()}):")
                    for module in accessible_modules:
                        self.stdout.write(f"  • {module.display_name} ({module.name})")
                    
                    # Show permissions
                    permissions = profile.permissions.all()
                    self.stdout.write(f"\nPermissions ({permissions.count()}):")
                    for perm in permissions:
                        self.stdout.write(f"  • {perm.module.display_name}: {perm.name} (Level {perm.level})")
                    
                    # Test specific permission checks
                    self.stdout.write(f"\nPermission Checks:")
                    properties_perm = user_profile.has_permission('properties', 'view')
                    leads_perm = user_profile.has_permission('leads', 'view')
                    owner_perm = user_profile.has_permission('owner', 'view')
                    
                    self.stdout.write(f"  • Properties View: {'✓' if properties_perm else '✗'}")
                    self.stdout.write(f"  • Leads View: {'✓' if leads_perm else '✗'}")
                    self.stdout.write(f"  • Owner View: {'✓' if owner_perm else '✗'}")
                else:
                    self.stdout.write("No profile assigned to this user!")
            else:
                self.stdout.write("No user profile found for this user!")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User '{username}' not found!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))