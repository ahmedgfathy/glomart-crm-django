import os
import mimetypes
from pathlib import Path
from typing import List
import glob
import logging

logger = logging.getLogger(__name__)

class FileSystemService:
    """Service for handling file system operations with security restrictions."""
    
    def __init__(self):
        # Get the base path from environment or default to the CRM project
        self.base_path = Path(os.getenv('CRM_PROJECT_PATH', '/Users/ahmedgomaa/Downloads/crm')).resolve()
        logger.info(f"FileSystemService initialized with base path: {self.base_path}")
    
    def _validate_path(self, path: str) -> Path:
        """Validate and resolve a path, ensuring it's within the allowed directory."""
        # Convert to Path object and resolve
        full_path = (self.base_path / path).resolve()
        
        # Check if the resolved path is within the base directory
        if not str(full_path).startswith(str(self.base_path)):
            raise PermissionError(f"Access denied: Path '{path}' is outside the allowed directory")
        
        return full_path
    
    def read_file(self, path: str) -> str:
        """Read the contents of a file."""
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not full_path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        
        try:
            # Detect encoding
            with open(full_path, 'rb') as f:
                raw_data = f.read()
            
            # Try to decode as UTF-8 first
            try:
                content = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                # If UTF-8 fails, try other common encodings
                for encoding in ['latin-1', 'cp1252']:
                    try:
                        content = raw_data.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, return base64 encoded content
                    import base64
                    content = f"[Binary file - Base64 encoded]\n{base64.b64encode(raw_data).decode('ascii')}"
            
            # Get file info
            stat = full_path.stat()
            mime_type = mimetypes.guess_type(str(full_path))[0] or 'application/octet-stream'
            
            result = f"""File: {path}
MIME Type: {mime_type}
Size: {stat.st_size} bytes
Last Modified: {stat.st_mtime}

Content:
{content}"""
            
            return result
            
        except Exception as e:
            raise IOError(f"Error reading file {path}: {str(e)}")
    
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file."""
        full_path = self._validate_path(path)
        
        try:
            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"Successfully wrote {len(content)} characters to {path}"
            
        except Exception as e:
            raise IOError(f"Error writing file {path}: {str(e)}")
    
    def list_directory(self, path: str = ".") -> str:
        """List the contents of a directory."""
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not full_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")
        
        try:
            items = []
            for item in sorted(full_path.iterdir()):
                relative_path = item.relative_to(self.base_path)
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    items.append(f"📄 {item.name} ({size} bytes)")
            
            if not items:
                items = ["(empty directory)"]
            
            return f"Directory listing for {path}:\n\n" + "\n".join(items)
            
        except Exception as e:
            raise IOError(f"Error listing directory {path}: {str(e)}")
    
    def create_directory(self, path: str) -> str:
        """Create a new directory."""
        full_path = self._validate_path(path)
        
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            return f"Successfully created directory: {path}"
            
        except Exception as e:
            raise IOError(f"Error creating directory {path}: {str(e)}")
    
    def delete_file(self, path: str) -> str:
        """Delete a file or directory."""
        full_path = self._validate_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        try:
            if full_path.is_dir():
                # Remove directory and all contents
                import shutil
                shutil.rmtree(full_path)
                return f"Successfully deleted directory: {path}"
            else:
                # Remove file
                full_path.unlink()
                return f"Successfully deleted file: {path}"
                
        except Exception as e:
            raise IOError(f"Error deleting {path}: {str(e)}")
    
    def search_files(self, pattern: str, directory: str = ".") -> str:
        """Search for files matching a pattern."""
        search_dir = self._validate_path(directory)
        
        if not search_dir.exists():
            raise FileNotFoundError(f"Search directory not found: {directory}")
        
        if not search_dir.is_dir():
            raise NotADirectoryError(f"Search path is not a directory: {directory}")
        
        try:
            # Use glob to search for files
            search_pattern = str(search_dir / pattern)
            matches = glob.glob(search_pattern, recursive=True)
            
            # Filter out files outside our base directory and convert to relative paths
            relative_matches = []
            for match in matches:
                match_path = Path(match).resolve()
                if str(match_path).startswith(str(self.base_path)):
                    relative_path = match_path.relative_to(self.base_path)
                    relative_matches.append(str(relative_path))
            
            if not relative_matches:
                return f"No files found matching pattern '{pattern}' in {directory}"
            
            return f"Files matching pattern '{pattern}' in {directory}:\n\n" + "\n".join(sorted(relative_matches))
            
        except Exception as e:
            raise IOError(f"Error searching for files: {str(e)}")