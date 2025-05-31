"""
Core Utilities for CI Code Companion SDK

This module provides utility functions used throughout the SDK including
file type detection, language identification, framework detection, and
various helper functions for file processing and validation.
"""

import hashlib
import mimetypes
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import logging


# File extension to language mapping
LANGUAGE_MAPPINGS = {
    # Frontend/Web
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.vue': 'vue',
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    
    # Backend
    '.py': 'python',
    '.pyx': 'python',
    '.pyi': 'python',
    '.java': 'java',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.go': 'go',
    '.rs': 'rust',
    '.rb': 'ruby',
    '.php': 'php',
    '.cs': 'csharp',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.c': 'c',
    '.h': 'c',
    '.hpp': 'cpp',
    
    # Mobile
    '.swift': 'swift',
    '.m': 'objective-c',
    '.dart': 'dart',
    
    # Data/Config
    '.json': 'json',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.xml': 'xml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    '.conf': 'config',
    
    # Database
    '.sql': 'sql',
    
    # DevOps
    '.dockerfile': 'dockerfile',
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'zsh',
    '.fish': 'fish',
    '.ps1': 'powershell',
    '.tf': 'terraform',
    
    # Documentation
    '.md': 'markdown',
    '.rst': 'restructuredtext',
    '.tex': 'latex',
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    'react': [
        r'import\s+.*\s+from\s+[\'"]react[\'"]',
        r'from\s+[\'"]react[\'"]',
        r'React\.',
        r'useState|useEffect|useContext|useMemo|useCallback',
        r'React\.Component|React\.FC|React\.FunctionComponent',
    ],
    'vue': [
        r'import\s+.*\s+from\s+[\'"]vue[\'"]',
        r'<template>|<script>|<style>',
        r'Vue\.',
        r'@Component|@Prop|@Watch',
    ],
    'angular': [
        r'import\s+.*\s+from\s+[\'"]@angular',
        r'@Component|@Injectable|@NgModule',
        r'NgModule|Component|Injectable',
    ],
    'next.js': [
        r'import\s+.*\s+from\s+[\'"]next',
        r'getServerSideProps|getStaticProps|getStaticPaths',
        r'next/router|next/head|next/image',
    ],
    'gatsby': [
        r'import\s+.*\s+from\s+[\'"]gatsby[\'"]',
        r'gatsby-.*',
        r'graphql`',
    ],
    'express': [
        r'require\([\'"]express[\'"]',
        r'import\s+.*\s+from\s+[\'"]express[\'"]',
        r'app\.use|app\.get|app\.post|app\.put|app\.delete',
        r'express\(\)',
    ],
    'nestjs': [
        r'import\s+.*\s+from\s+[\'"]@nestjs',
        r'@Controller|@Injectable|@Module',
        r'NestFactory\.create',
    ],
    'django': [
        r'from\s+django',
        r'import\s+django',
        r'models\.Model|forms\.Form|views\.View',
        r'django\.contrib|django\.conf',
    ],
    'flask': [
        r'from\s+flask',
        r'import\s+flask',
        r'Flask\(__name__\)',
        r'@app\.route',
    ],
    'fastapi': [
        r'from\s+fastapi',
        r'import\s+fastapi',
        r'FastAPI\(\)',
        r'@app\.(get|post|put|delete)',
    ],
    'spring': [
        r'@SpringBootApplication|@RestController|@Service',
        r'import\s+org\.springframework',
        r'@Autowired|@Component',
    ],
    'rails': [
        r'class\s+\w+Controller\s+<\s+ApplicationController',
        r'ActiveRecord::Base',
        r'Rails\.application',
    ],
}


def get_file_language(file_path: str) -> Optional[str]:
    """
    Detect the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language identifier or None if not detected
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    # Handle special cases
    if path.name.lower() == 'dockerfile':
        return 'dockerfile'
    elif path.name.lower() in ['makefile', 'makefile.mk']:
        return 'makefile'
    elif path.name.lower().startswith('.env'):
        return 'env'
    
    return LANGUAGE_MAPPINGS.get(extension)


def detect_framework(file_path: str, content: str) -> List[str]:
    """
    Detect frameworks used in a file based on content analysis.
    
    Args:
        file_path: Path to the file
        content: File content to analyze
        
    Returns:
        List of detected frameworks
    """
    detected_frameworks = []
    
    if not content:
        return detected_frameworks
    
    # Check each framework pattern
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                detected_frameworks.append(framework)
                break  # Found this framework, move to next
    
    return detected_frameworks


def calculate_file_hash(content: str, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of file content.
    
    Args:
        content: File content to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)
        
    Returns:
        Hexadecimal hash string
    """
    if algorithm not in ['md5', 'sha1', 'sha256', 'sha512']:
        algorithm = 'sha256'
    
    hash_obj = getattr(hashlib, algorithm)()
    hash_obj.update(content.encode('utf-8'))
    return hash_obj.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    
    while size_bytes >= 1024 and i < len(sizes) - 1:
        size_bytes /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size_bytes)} {sizes[i]}"
    else:
        return f"{size_bytes:.1f} {sizes[i]}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for filesystem
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = 'untitled'
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = Path(sanitized).stem, Path(sanitized).suffix
        max_name_length = 255 - len(ext)
        sanitized = name[:max_name_length] + ext
    
    return sanitized


def validate_file_path(file_path: str, allowed_extensions: Optional[Set[str]] = None) -> bool:
    """
    Validate if a file path is safe and allowed.
    
    Args:
        file_path: File path to validate
        allowed_extensions: Set of allowed file extensions
        
    Returns:
        True if path is valid and safe
    """
    path = Path(file_path)
    
    # Check for path traversal attempts
    if '..' in str(path) or str(path).startswith('/'):
        return False
    
    # Check file extension if restrictions provided
    if allowed_extensions:
        extension = path.suffix.lower()
        if extension not in allowed_extensions:
            return False
    
    # Check for hidden files (optional - might want to allow)
    if path.name.startswith('.') and path.name not in ['.env', '.gitignore', '.dockerignore']:
        return False
    
    return True


def get_file_mime_type(file_path: str) -> Optional[str]:
    """
    Get MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string or None
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type


def is_text_file(file_path: str, content: Optional[bytes] = None) -> bool:
    """
    Check if a file is likely a text file.
    
    Args:
        file_path: Path to the file
        content: Optional file content as bytes
        
    Returns:
        True if file is likely text
    """
    # Check by MIME type first
    mime_type = get_file_mime_type(file_path)
    if mime_type:
        if mime_type.startswith('text/') or mime_type in [
            'application/json',
            'application/xml',
            'application/javascript',
            'application/x-yaml'
        ]:
            return True
    
    # Check by extension
    extension = Path(file_path).suffix.lower()
    text_extensions = {
        '.txt', '.md', '.rst', '.log', '.cfg', '.conf', '.ini',
        '.json', '.xml', '.yaml', '.yml', '.toml',
        '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.c', '.cpp',
        '.h', '.hpp', '.cs', '.rb', '.php', '.go', '.rs', '.swift',
        '.kt', '.scala', '.sql', '.html', '.css', '.scss', '.sass',
        '.less', '.vue', '.dockerfile', '.sh', '.bash', '.ps1',
        '.tf', '.hcl', '.gitignore', '.dockerignore'
    }
    
    if extension in text_extensions:
        return True
    
    # Check content if provided
    if content:
        try:
            # Try to decode as UTF-8
            content.decode('utf-8')
            return True
        except UnicodeDecodeError:
            # Check for null bytes (binary indicator)
            if b'\x00' in content[:1024]:  # Check first 1KB
                return False
            
            # If no null bytes and reasonable ASCII ratio, likely text
            ascii_chars = sum(1 for b in content[:1024] if b < 128)
            ascii_ratio = ascii_chars / min(len(content), 1024)
            return ascii_ratio > 0.95
    
    return False


def extract_imports(content: str, language: str) -> List[str]:
    """
    Extract import statements from code content.
    
    Args:
        content: File content
        language: Programming language
        
    Returns:
        List of imported modules/packages
    """
    imports = []
    
    if language in ['python']:
        # Python imports
        import_patterns = [
            r'import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        ]
        
    elif language in ['javascript', 'typescript']:
        # JavaScript/TypeScript imports
        import_patterns = [
            r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ]
        
    elif language in ['java']:
        # Java imports
        import_patterns = [
            r'import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        ]
        
    else:
        return imports
    
    for pattern in import_patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        imports.extend(matches)
    
    return list(set(imports))  # Remove duplicates


def count_lines_of_code(content: str, language: str) -> Dict[str, int]:
    """
    Count different types of lines in code.
    
    Args:
        content: File content
        language: Programming language
        
    Returns:
        Dictionary with line counts (total, code, comments, blank)
    """
    lines = content.split('\n')
    
    counts = {
        'total': len(lines),
        'code': 0,
        'comments': 0,
        'blank': 0
    }
    
    # Define comment patterns by language
    comment_patterns = {
        'python': [r'#.*'],
        'javascript': [r'//.*', r'/\*.*?\*/'],
        'typescript': [r'//.*', r'/\*.*?\*/'],
        'java': [r'//.*', r'/\*.*?\*/'],
        'cpp': [r'//.*', r'/\*.*?\*/'],
        'c': [r'//.*', r'/\*.*?\*/'],
        'css': [r'/\*.*?\*/'],
        'html': [r'<!--.*?-->'],
        'sql': [r'--.*'],
        'bash': [r'#.*'],
        'yaml': [r'#.*'],
        'dockerfile': [r'#.*'],
    }
    
    patterns = comment_patterns.get(language, [])
    
    for line in lines:
        line = line.strip()
        
        if not line:
            counts['blank'] += 1
        elif any(re.match(pattern, line) for pattern in patterns):
            counts['comments'] += 1
        else:
            counts['code'] += 1
    
    return counts


def calculate_complexity_score(content: str, language: str) -> float:
    """
    Calculate a basic complexity score for code.
    
    Args:
        content: File content
        language: Programming language
        
    Returns:
        Complexity score (higher = more complex)
    """
    if not content.strip():
        return 0.0
    
    # Basic complexity indicators
    complexity_patterns = {
        'python': [
            r'\bif\b', r'\belif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b',
            r'\btry\b', r'\bexcept\b',
            r'\bdef\b', r'\bclass\b',
            r'\band\b', r'\bor\b',
        ],
        'javascript': [
            r'\bif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b', r'\bdo\b',
            r'\btry\b', r'\bcatch\b',
            r'\bfunction\b', r'\bclass\b',
            r'&&', r'\|\|',
        ],
        'typescript': [
            r'\bif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b', r'\bdo\b',
            r'\btry\b', r'\bcatch\b',
            r'\bfunction\b', r'\bclass\b',
            r'&&', r'\|\|',
        ],
    }
    
    patterns = complexity_patterns.get(language, [])
    if not patterns:
        return 1.0  # Default complexity for unknown languages
    
    total_matches = 0
    for pattern in patterns:
        matches = len(re.findall(pattern, content, re.IGNORECASE))
        total_matches += matches
    
    # Calculate complexity relative to file size
    lines_count = len(content.split('\n'))
    if lines_count == 0:
        return 0.0
    
    # Normalize complexity score
    complexity = total_matches / lines_count * 10
    return min(complexity, 10.0)  # Cap at 10.0


def setup_logging(name: str, level: str = 'INFO') -> logging.Logger:
    """
    Setup logger with consistent formatting.
    
    Args:
        name: Logger name
        level: Log level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger 