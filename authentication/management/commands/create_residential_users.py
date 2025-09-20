from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from authentication.models import UserProfile, Profile, Rule, Module, Permission


class Command(BaseCommand):
    help = 'Create residential users with limited permissions'

    def handle(self, *args, **options):
        # Employee data
        employees = [
            ("Rehab Hamedo", "1050852466"),
            ("Amira Abdelghani", "1021676576"),
            ("Hadeer Foaad", "1080392095"),
            ("Farah Hassan", "1103130106"),
            ("Hala Ahmed", "1050852477"),
            ("Abdullah Mostafa", "1110486231"),
            ("Manar Mohamed", "1060103768"),
            ("Shahd Nabil", "1011676572"),
            ("Shrouk Ibrahem", "1111964587"),
            ("Hana Ahmed", "1141360001"),
            ("Asmaa khalid", "1128161554"),
            ("Asmaa Ali", "1126881189"),
            ("Nardin Kamal", "1032324953"),
            ("Asmaa Ali", "1126881189"),  # Duplicate - will handle
            ("Eslam hassan", "1092760743"),
            ("Ziad Awis", "1110251989"),
            ("Muhammad Ragheed", "1068485249"),
            ("Dina Mohamed", "1111738359"),
            ("Mohammd Atta", "1111459002"),
            ("Mohamed Fawzy", "1550621242"),
            ("Yasmin Zaki", "1091676557"),
            ("Marina Gamal thabet", "201277021327"),
            ("Ahmed Ashraf Ali", "201140600085"),
            ("Mostafa Ahmed Saad", "201148117171"),
            ("Aya Ramadan Youssief", "201103130096"),
            ("Yathreb Ibrahim", "201103130104"),
            ("Ahmed Emad", "1103130094"),
            ("Ahmed Essam", "1102176222"),
            ("Mohamed salah", "1021019789"),
            ("Omar Fathy", "1032277102"),
            ("rehab atta", "1287485928"),
            ("aseem omar", "1111738346"),
            ("Radwa ElNagar", "1146000792"),
            ("Fatma ElNagar", "1153738145"),
            ("toqa", "1156985387"),
            ("yasmin zaki", "1091676557"),  # Duplicate - will handle
            ("ramy", "1126882335"),
            ("karim saqr", "1027714548"),
            ("ahmed mostafa", "1145135532"),
            ("mahmuod abdelfatah", "1017124398"),
            ("nesma samir", "1144744613"),
            ("Youssef samy", "1147343466"),
            ("lamiaa foaad", "1066408509"),
            ("Francois khalil", "1017898973"),
        ]

        # Get or create necessary modules and permissions
        properties_module, _ = Module.objects.get_or_create(
            name='properties',
            defaults={
                'display_name': 'Properties',
                'icon': 'bi-building',
                'url_name': 'properties:dashboard',
                'order': 2
            }
        )
        
        # Get or create view permission for properties module
        view_permission, _ = Permission.objects.get_or_create(
            module=properties_module,
            code='view',
            defaults={
                'name': 'View',
                'level': 1,
                'description': 'Can view properties'
            }
        )

        created_users = 0
        updated_users = 0
        duplicate_usernames = []

        for name, mobile in employees:
            # Generate username from first name
            first_name = name.split()[0].lower()
            username = first_name
            
            # Handle duplicate usernames
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
                
            if username != original_username:
                duplicate_usernames.append(f"{name} -> {username}")

            # Create or get user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': name.split()[0],
                    'last_name': ' '.join(name.split()[1:]) if len(name.split()) > 1 else '',
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                }
            )
            
            if created:
                user.set_password('123456789')
                user.save()
                created_users += 1
                self.stdout.write(f"Created user: {username} ({name})")
            else:
                updated_users += 1
                self.stdout.write(f"User already exists: {username} ({name})")

            # Create or update user profile
            user_profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'phone': mobile}
            )
            
            if not profile_created and user_profile.phone != mobile:
                user_profile.phone = mobile
                user_profile.save()

            # Create or get profile for permissions
            if not user_profile.profile:
                profile = Profile.objects.create(
                    name=f"{name} - Residential",
                    description=f"Residential user profile for {name}"
                )
                user_profile.profile = profile
                user_profile.save()
            else:
                profile = user_profile.profile

            # Add properties module permission (view only) to the profile
            if view_permission not in profile.permissions.all():
                profile.permissions.add(view_permission)
                self.stdout.write(f"  - Added properties view permission for {username}")
            else:
                self.stdout.write(f"  - Properties view permission already exists for {username}")

        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary:\n"
                f"- Created: {created_users} new users\n"
                f"- Updated: {updated_users} existing users\n"
                f"- Total processed: {len(employees)} employees"
            )
        )
        
        if duplicate_usernames:
            self.stdout.write(
                self.style.WARNING(
                    f"\nDuplicate usernames handled:\n" + 
                    "\n".join([f"  - {dup}" for dup in duplicate_usernames])
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nAll users created with:\n"
                f"- Password: 123456789\n"
                f"- Access: Properties module only (view permission)\n"
                f"- Mobile numbers stored in profiles"
            )
        )