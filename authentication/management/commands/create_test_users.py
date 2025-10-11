from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import Profile, UserProfile

class Command(BaseCommand):
    help = 'Create test users with different RBAC profiles'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating test users...')
        
        # Test users data
        test_users = [
            {
                'username': 'commercial_agent',
                'email': 'commercial@example.com',
                'first_name': 'John',
                'last_name': 'Commercial',
                'profile': 'Commercial Property Specialist',
                'employee_id': 'EMP001',
                'department': 'Sales',
                'position': 'Commercial Agent'
            },
            {
                'username': 'residential_agent',
                'email': 'residential@example.com',
                'first_name': 'Jane',
                'last_name': 'Residential',
                'profile': 'Residential Property Specialist',
                'employee_id': 'EMP002',
                'department': 'Sales',
                'position': 'Residential Agent'
            },
            {
                'username': 'lead_manager',
                'email': 'leadmgr@example.com',
                'first_name': 'Mike',
                'last_name': 'Manager',
                'profile': 'Lead Manager',
                'employee_id': 'EMP003',
                'department': 'Management',
                'position': 'Lead Manager'
            },
            {
                'username': 'sales_rep',
                'email': 'salesrep@example.com',
                'first_name': 'Sarah',
                'last_name': 'Sales',
                'profile': 'Sales Representative',
                'employee_id': 'EMP004',
                'department': 'Sales',
                'position': 'Sales Representative'
            }
        ]
        
        created_count = 0
        
        for user_data in test_users:
            username = user_data['username']
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(f'  ✓ User {username} already exists')
                continue
            
            # Get the profile
            profile_name = user_data['profile']
            try:
                profile = Profile.objects.get(name=profile_name)
            except Profile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Profile "{profile_name}" not found. Run init_enhanced_rbac first.')
                )
                continue
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password='testpass123'  # Default password for testing
            )
            
            # Create or update user profile
            user_profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'profile': profile,
                    'employee_id': user_data['employee_id'],
                    'department': user_data['department'],
                    'position': user_data['position'],
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'  ✓ Created user: {username} with profile: {profile_name}')
                created_count += 1
            else:
                # Update existing profile
                user_profile.profile = profile
                user_profile.employee_id = user_data['employee_id']
                user_profile.department = user_data['department']
                user_profile.position = user_data['position']
                user_profile.is_active = True
                user_profile.save()
                self.stdout.write(f'  ✓ Updated user: {username} with profile: {profile_name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nCompleted! Created {created_count} new test users.')
        )
        
        # Show login information
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST USER LOGIN CREDENTIALS:')
        self.stdout.write('='*50)
        for user_data in test_users:
            username = user_data['username']
            profile_name = user_data['profile']
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: testpass123')
            self.stdout.write(f'Profile:  {profile_name}')
            self.stdout.write('-' * 30)
        
        self.stdout.write('\nYou can now login with these users to test the enhanced RBAC system!')