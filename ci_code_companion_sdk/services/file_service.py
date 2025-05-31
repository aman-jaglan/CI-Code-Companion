"""
File Service for CI Code Companion SDK

This service handles all file operations including reading, writing, validation,
and metadata extraction. It provides a centralized interface for file handling
with proper error management and security checks.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging
from ..core.config import SDKConfig
from ..core.exceptions import FileOperationError
from ..core.utils import validate_file_path, is_text_file, format_file_size


class FileService:
    """
    Service for handling file operations throughout the SDK.
    """
    
    def __init__(self, config: SDKConfig, logger: logging.Logger):
        """
        Initialize the file service.
        
        Args:
            config: SDK configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.allowed_extensions = set(config.allowed_file_types)
        self.blocked_patterns = config.blocked_patterns
        self.max_file_size = config.file_size_limit
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Read file content with validation and error handling.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            File content as string
            
        Raises:
            FileOperationError: If file cannot be read
        """
        try:
            if not self.validate_file_access(file_path):
                raise FileOperationError(f"File access denied: {file_path}")
            
            path = Path(file_path)
            if not path.exists():
                raise FileOperationError(f"File not found: {file_path}")
            
            if not path.is_file():
                raise FileOperationError(f"Path is not a file: {file_path}")
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                raise FileOperationError(
                    f"File too large: {format_file_size(file_size)} > {format_file_size(self.max_file_size)}"
                )
            
            # Read file content
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.debug(f"Successfully read file: {file_path} ({format_file_size(file_size)})")
            return content
            
        except UnicodeDecodeError as e:
            raise FileOperationError(f"File encoding error: {str(e)}", file_path=file_path)
        except PermissionError as e:
            raise FileOperationError(f"Permission denied: {str(e)}", file_path=file_path)
        except Exception as e:
            raise FileOperationError(f"Failed to read file: {str(e)}", file_path=file_path)
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Write content to file with validation.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding
            
        Returns:
            True if successful
            
        Raises:
            FileOperationError: If file cannot be written
        """
        try:
            if not self.validate_file_access(file_path, for_writing=True):
                raise FileOperationError(f"File write access denied: {file_path}")
            
            path = Path(file_path)
            
            # Create directory if it doesn't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            file_size = len(content.encode(encoding))
            self.logger.debug(f"Successfully wrote file: {file_path} ({format_file_size(file_size)})")
            return True
            
        except PermissionError as e:
            raise FileOperationError(f"Permission denied: {str(e)}", file_path=file_path)
        except Exception as e:
            raise FileOperationError(f"Failed to write file: {str(e)}", file_path=file_path)
    
    def validate_file_access(self, file_path: str, for_writing: bool = False) -> bool:
        """
        Validate if file access is allowed based on configuration.
        
        Args:
            file_path: Path to validate
            for_writing: Whether validation is for write access
            
        Returns:
            True if access is allowed
        """
        # Basic path validation
        if not validate_file_path(file_path, self.allowed_extensions):
            return False
        
        # Check against blocked patterns
        for pattern in self.blocked_patterns:
            if pattern in file_path:
                self.logger.warning(f"File blocked by pattern '{pattern}': {file_path}")
                return False
        
        # Additional security checks for writing
        if for_writing:
            path = Path(file_path)
            # Don't allow writing to system directories
            forbidden_dirs = ['/etc', '/usr', '/bin', '/sbin', '/boot']
            if any(str(path).startswith(forbidden) for forbidden in forbidden_dirs):
                return False
        
        return True
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive file information.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file metadata
        """
        try:
            path = Path(file_path)
            
            if not path.exists():
                return {'error': 'File not found'}
            
            stat = path.stat()
            
            # Basic file info
            info = {
                'name': path.name,
                'path': str(path),
                'size': stat.st_size,
                'size_formatted': format_file_size(stat.st_size),
                'extension': path.suffix.lower(),
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
            }
            
            # MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            info['mime_type'] = mime_type
            
            # Check if it's a text file
            if path.is_file():
                with open(path, 'rb') as f:
                    sample = f.read(1024)  # Read first 1KB
                info['is_text'] = is_text_file(file_path, sample)
                
                # Calculate file hash for text files
                if info['is_text'] and stat.st_size < self.max_file_size:
                    content = self.read_file(file_path)
                    info['hash'] = hashlib.sha256(content.encode()).hexdigest()
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get file info for {file_path}: {str(e)}")
            return {'error': str(e)}
    
    def list_files(self, directory: str, recursive: bool = False, 
                   file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List files in a directory with filtering.
        
        Args:
            directory: Directory path
            recursive: Whether to search recursively
            file_types: List of file extensions to include
            
        Returns:
            List of file information dictionaries
        """
        try:
            path = Path(directory)
            
            if not path.exists() or not path.is_dir():
                raise FileOperationError(f"Directory not found: {directory}")
            
            files = []
            pattern = "**/*" if recursive else "*"
            
            for file_path in path.glob(pattern):
                if file_path.is_file():
                    # Apply file type filter
                    if file_types and file_path.suffix.lower() not in file_types:
                        continue
                    
                    # Check if file access is allowed
                    if not self.validate_file_access(str(file_path)):
                        continue
                    
                    # Get file info
                    file_info = self.get_file_info(str(file_path))
                    if 'error' not in file_info:
                        files.append(file_info)
            
            self.logger.debug(f"Listed {len(files)} files in {directory}")
            return files
            
        except Exception as e:
            raise FileOperationError(f"Failed to list files in {directory}: {str(e)}")
    
    def copy_file(self, source: str, destination: str) -> bool:
        """
        Copy file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful
        """
        try:
            content = self.read_file(source)
            return self.write_file(destination, content)
        except Exception as e:
            raise FileOperationError(f"Failed to copy file from {source} to {destination}: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file safely.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if successful
        """
        try:
            if not self.validate_file_access(file_path, for_writing=True):
                raise FileOperationError(f"File delete access denied: {file_path}")
            
            path = Path(file_path)
            
            if not path.exists():
                self.logger.warning(f"File already doesn't exist: {file_path}")
                return True
            
            if not path.is_file():
                raise FileOperationError(f"Path is not a file: {file_path}")
            
            path.unlink()
            self.logger.debug(f"Successfully deleted file: {file_path}")
            return True
            
        except Exception as e:
            raise FileOperationError(f"Failed to delete file: {str(e)}", file_path=file_path)
    
    def ensure_directory(self, directory: str) -> bool:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            directory: Directory path
            
        Returns:
            True if successful
        """
        try:
            path = Path(directory)
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            raise FileOperationError(f"Failed to create directory {directory}: {str(e)}")
    
    def get_temp_file_path(self, prefix: str = "temp", suffix: str = ".tmp") -> str:
        """
        Generate a temporary file path.
        
        Args:
            prefix: File prefix
            suffix: File suffix
            
        Returns:
            Temporary file path
        """
        import tempfile
        import uuid
        
        temp_dir = tempfile.gettempdir()
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{prefix}_{unique_id}{suffix}"
        
        return os.path.join(temp_dir, filename) 