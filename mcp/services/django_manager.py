import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DjangoService:
    """Service for handling Django management commands."""
    
    def __init__(self):
        self.project_path = Path(os.getenv('CRM_PROJECT_PATH', '/Users/ahmedgomaa/Downloads/crm')).resolve()
        self.manage_py = self.project_path / 'manage.py'
        
        # Verify manage.py exists
        if not self.manage_py.exists():
            logger.warning(f"manage.py not found at {self.manage_py}")
        
        logger.info(f"DjangoService initialized with project path: {self.project_path}")
    
    def _run_command(self, command: list, description: str) -> str:
        """Run a Django management command."""
        if not self.manage_py.exists():
            raise FileNotFoundError(f"Django manage.py not found at {self.manage_py}")
        
        try:
            # Build the full command
            full_command = ['python', str(self.manage_py)] + command
            
            logger.info(f"Running Django command: {' '.join(command)}")
            
            # Execute the command
            result = subprocess.run(
                full_command,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Format the output
            output = f"{description} completed.\n\n"
            
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            
            if result.stderr:
                output += f"Warnings/Errors:\n{result.stderr}\n"
            
            output += f"Exit code: {result.returncode}"
            
            if result.returncode != 0:
                raise RuntimeError(f"{description} failed with exit code {result.returncode}:\n{result.stderr}")
            
            return output
            
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"{description} timed out after 5 minutes")
        except Exception as e:
            logger.error(f"Error running Django command {command}: {e}")
            raise RuntimeError(f"Failed to run {description}: {str(e)}")
    
    def run_migrations(self) -> str:
        """Run Django database migrations."""
        return self._run_command(['migrate'], 'Database migrations')
    
    def make_migrations(self, app: Optional[str] = None) -> str:
        """Create new Django migrations."""
        command = ['makemigrations']
        if app:
            command.append(app)
        
        description = f"Make migrations{f' for {app}' if app else ''}"
        return self._run_command(command, description)
    
    def collect_static(self) -> str:
        """Collect static files for Django."""
        return self._run_command(['collectstatic', '--noinput'], 'Static files collection')
    
    def run_shell_command(self, python_command: str) -> str:
        """Execute a command in Django shell."""
        try:
            if not self.manage_py.exists():
                raise FileNotFoundError(f"Django manage.py not found at {self.manage_py}")
            
            # Create a temporary script to run in the shell
            script = f"""
import sys
sys.path.insert(0, '{self.project_path}')
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'real_estate_crm.settings')
import django
django.setup()

# Execute the user's command
try:
    {python_command}
except Exception as e:
    print(f"Error: {{e}}")
"""
            
            # Run the command
            result = subprocess.run(
                ['python', '-c', script],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout for shell commands
            )
            
            output = f"Django shell command executed:\nCommand: {python_command}\n\n"
            
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            
            if result.stderr:
                output += f"Errors:\n{result.stderr}\n"
            
            output += f"Exit code: {result.returncode}"
            
            return output
            
        except subprocess.TimeoutExpired:
            raise RuntimeError("Shell command timed out after 1 minute")
        except Exception as e:
            logger.error(f"Error running Django shell command: {e}")
            raise RuntimeError(f"Failed to run shell command: {str(e)}")
    
    def run_tests(self, app: Optional[str] = None) -> str:
        """Run Django tests."""
        command = ['test']
        if app:
            command.append(app)
        
        description = f"Tests{f' for {app}' if app else ''}"
        return self._run_command(command, description)
    
    def check_system(self) -> str:
        """Run Django system checks."""
        return self._run_command(['check'], 'System check')
    
    def show_migrations(self, app: Optional[str] = None) -> str:
        """Show migration status."""
        command = ['showmigrations']
        if app:
            command.append(app)
        
        description = f"Migration status{f' for {app}' if app else ''}"
        return self._run_command(command, description)
    
    def create_superuser(self, username: str, email: str) -> str:
        """Create a Django superuser (interactive)."""
        try:
            # This is more complex as it requires interactive input
            # We'll use environment variables to provide the credentials
            env = os.environ.copy()
            env['DJANGO_SUPERUSER_USERNAME'] = username
            env['DJANGO_SUPERUSER_EMAIL'] = email
            env['DJANGO_SUPERUSER_PASSWORD'] = 'changeme123'  # Default password
            
            result = subprocess.run(
                ['python', str(self.manage_py), 'createsuperuser', '--noinput'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            output = f"Superuser creation attempted.\n\n"
            
            if result.stdout:
                output += f"Output:\n{result.stdout}\n"
            
            if result.stderr:
                output += f"Warnings/Errors:\n{result.stderr}\n"
            
            output += f"Exit code: {result.returncode}\n"
            output += "\nNote: Default password is 'changeme123' - please change it after first login."
            
            return output
            
        except Exception as e:
            logger.error(f"Error creating superuser: {e}")
            raise RuntimeError(f"Failed to create superuser: {str(e)}")
    
    def get_project_info(self) -> str:
        """Get Django project information."""
        try:
            output = f"Django Project Information:\n\n"
            output += f"Project Path: {self.project_path}\n"
            output += f"Manage.py: {'✓ Found' if self.manage_py.exists() else '✗ Not Found'}\n\n"
            
            # Try to get Django version and settings
            if self.manage_py.exists():
                try:
                    result = subprocess.run(
                        ['python', str(self.manage_py), 'version'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        output += f"Django Version: {result.stdout.strip()}\n"
                except:
                    output += "Django Version: Unable to determine\n"
                
                # List installed apps
                try:
                    check_result = subprocess.run(
                        ['python', str(self.manage_py), 'check', '--deploy'],
                        cwd=self.project_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    output += f"\nSystem Check:\n{check_result.stdout[:500]}\n"
                except:
                    output += "\nSystem Check: Unable to run\n"
            
            # List Python files in the project
            python_files = list(self.project_path.glob('**/*.py'))
            app_dirs = [d for d in self.project_path.iterdir() 
                       if d.is_dir() and (d / 'models.py').exists()]
            
            output += f"\nApps detected: {len(app_dirs)}\n"
            for app_dir in app_dirs:
                output += f"  📁 {app_dir.name}\n"
            
            output += f"\nTotal Python files: {len(python_files)}\n"
            
            return output
            
        except Exception as e:
            logger.error(f"Error getting project info: {e}")
            return f"Error getting project information: {str(e)}"