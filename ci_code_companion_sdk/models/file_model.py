"""
File and Project Information Models

This module contains data models for representing file and project information
used throughout the CI Code Companion SDK for analysis and processing.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime
import os
import hashlib


@dataclass
class FileInfo:
    """
    Comprehensive file information model containing metadata and content analysis.
    Used for tracking file details, dependencies, and analysis context.
    """
    
    path: str
    name: str
    extension: str
    size: int
    content: str
    encoding: str = 'utf-8'
    language: Optional[str] = None
    framework: Optional[str] = None
    
    # File metadata
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    checksum: Optional[str] = None
    
    # Content analysis
    line_count: int = 0
    complexity_score: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    
    # Analysis context
    project_context: Dict[str, Any] = field(default_factory=dict)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_path(cls, file_path: str, content: str = None) -> 'FileInfo':
        """
        Create FileInfo instance from a file path and optional content.
        
        Args:
            file_path: Path to the file
            content: File content (will be read if not provided)
            
        Returns:
            FileInfo instance with populated metadata
        """
        path_obj = Path(file_path)
        
        # Read content if not provided
        if content is None and path_obj.exists():
            try:
                with open(path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
            except (UnicodeDecodeError, PermissionError):
                content = ""
        elif content is None:
            content = ""
        
        # Extract file information
        name = path_obj.name
        extension = path_obj.suffix.lower()
        size = len(content.encode('utf-8'))
        
        # Get file timestamps if file exists
        created_at = None
        modified_at = None
        if path_obj.exists():
            stat_info = path_obj.stat()
            created_at = datetime.fromtimestamp(stat_info.st_ctime)
            modified_at = datetime.fromtimestamp(stat_info.st_mtime)
        
        # Calculate checksum
        checksum = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Detect language and framework
        language = cls._detect_language(extension, content)
        framework = cls._detect_framework(content, language)
        
        # Analyze content
        line_count = len(content.splitlines())
        complexity_score = cls._calculate_complexity(content, language)
        dependencies = cls._extract_dependencies(content, language)
        imports = cls._extract_imports(content, language)
        exports = cls._extract_exports(content, language)
        functions = cls._extract_functions(content, language)
        classes = cls._extract_classes(content, language)
        
        return cls(
            path=str(path_obj),
            name=name,
            extension=extension,
            size=size,
            content=content,
            language=language,
            framework=framework,
            created_at=created_at,
            modified_at=modified_at,
            checksum=checksum,
            line_count=line_count,
            complexity_score=complexity_score,
            dependencies=dependencies,
            imports=imports,
            exports=exports,
            functions=functions,
            classes=classes
        )
    
    @staticmethod
    def _detect_language(extension: str, content: str) -> Optional[str]:
        """Detect programming language from file extension and content."""
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.swift': 'swift',
            '.dart': 'dart',
            '.sql': 'sql',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.sass': 'sass',
            '.less': 'less',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.xml': 'xml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.bat': 'batch',
            '.ps1': 'powershell'
        }
        
        # First try extension-based detection
        if extension in language_map:
            return language_map[extension]
        
        # Content-based detection for files without extension
        if 'import ' in content or 'def ' in content or 'class ' in content:
            return 'python'
        elif 'function ' in content or 'const ' in content or 'let ' in content:
            return 'javascript'
        elif 'public class' in content or 'import java' in content:
            return 'java'
        
        return None
    
    @staticmethod
    def _detect_framework(content: str, language: Optional[str]) -> Optional[str]:
        """Detect framework based on content analysis."""
        if not language:
            return None
        
        framework_patterns = {
            'python': {
                'django': ['from django', 'import django', 'Django'],
                'flask': ['from flask', 'import flask', 'Flask'],
                'fastapi': ['from fastapi', 'import fastapi', 'FastAPI'],
                'pytest': ['import pytest', 'def test_'],
                'unittest': ['import unittest', 'class Test']
            },
            'javascript': {
                'react': ['import React', 'from "react"', 'React.', 'jsx'],
                'vue': ['import Vue', 'from "vue"', 'Vue.'],
                'angular': ['import { Component }', '@Component', 'angular'],
                'express': ['const express', 'require("express")', 'app.get'],
                'jest': ['describe(', 'it(', 'test(', 'expect(']
            },
            'typescript': {
                'react': ['import React', 'from "react"', 'React.', 'tsx'],
                'angular': ['import { Component }', '@Component', 'angular'],
                'nest': ['@Injectable', '@Controller', 'nest']
            }
        }
        
        if language in framework_patterns:
            for framework, patterns in framework_patterns[language].items():
                if any(pattern in content for pattern in patterns):
                    return framework
        
        return None
    
    @staticmethod
    def _calculate_complexity(content: str, language: Optional[str]) -> float:
        """Calculate cyclomatic complexity score."""
        if not content or not language:
            return 0.0
        
        complexity_keywords = {
            'python': ['if', 'elif', 'for', 'while', 'except', 'and', 'or'],
            'javascript': ['if', 'for', 'while', 'switch', 'catch', '&&', '||'],
            'typescript': ['if', 'for', 'while', 'switch', 'catch', '&&', '||']
        }
        
        keywords = complexity_keywords.get(language, [])
        if not keywords:
            return 0.0
        
        count = sum(content.count(keyword) for keyword in keywords)
        return min(count / 10.0, 10.0)  # Normalize to 0-10 scale
    
    @staticmethod
    def _extract_dependencies(content: str, language: Optional[str]) -> List[str]:
        """Extract dependencies from file content."""
        dependencies = []
        
        if language == 'python':
            import re
            # Find import statements
            imports = re.findall(r'(?:from\s+(\S+)\s+import|import\s+(\S+))', content)
            for imp in imports:
                dep = imp[0] if imp[0] else imp[1]
                if dep and not dep.startswith('.'):
                    dependencies.append(dep.split('.')[0])
        
        elif language in ['javascript', 'typescript']:
            import re
            # Find require and import statements
            requires = re.findall(r'require\(["\']([^"\']+)["\']\)', content)
            imports = re.findall(r'from\s+["\']([^"\']+)["\']', content)
            dependencies.extend(requires + imports)
        
        return list(set(dependencies))  # Remove duplicates
    
    @staticmethod
    def _extract_imports(content: str, language: Optional[str]) -> List[str]:
        """Extract import statements."""
        imports = []
        
        if language == 'python':
            import re
            imports = re.findall(r'(?:from\s+\S+\s+import\s+(.+)|import\s+(.+))', content)
            imports = [imp[0] if imp[0] else imp[1] for imp in imports]
        
        elif language in ['javascript', 'typescript']:
            import re
            imports = re.findall(r'import\s+(.+?)\s+from', content)
        
        return [imp.strip() for imp in imports if imp]
    
    @staticmethod
    def _extract_exports(content: str, language: Optional[str]) -> List[str]:
        """Extract export statements."""
        exports = []
        
        if language in ['javascript', 'typescript']:
            import re
            exports = re.findall(r'export\s+(?:default\s+)?(?:function\s+|class\s+|const\s+|let\s+|var\s+)?(\w+)', content)
        
        return exports
    
    @staticmethod
    def _extract_functions(content: str, language: Optional[str]) -> List[str]:
        """Extract function definitions."""
        functions = []
        
        if language == 'python':
            import re
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
        
        elif language in ['javascript', 'typescript']:
            import re
            functions = re.findall(r'function\s+(\w+)\s*\(', content)
            functions.extend(re.findall(r'const\s+(\w+)\s*=\s*\(', content))
            functions.extend(re.findall(r'(\w+)\s*:\s*\([^)]*\)\s*=>', content))
        
        return functions
    
    @staticmethod
    def _extract_classes(content: str, language: Optional[str]) -> List[str]:
        """Extract class definitions."""
        classes = []
        
        if language == 'python':
            import re
            classes = re.findall(r'class\s+(\w+)[\s\(]', content)
        
        elif language in ['javascript', 'typescript']:
            import re
            classes = re.findall(r'class\s+(\w+)[\s\{]', content)
        
        return classes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert FileInfo to dictionary representation."""
        return {
            'path': self.path,
            'name': self.name,
            'extension': self.extension,
            'size': self.size,
            'encoding': self.encoding,
            'language': self.language,
            'framework': self.framework,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'checksum': self.checksum,
            'line_count': self.line_count,
            'complexity_score': self.complexity_score,
            'dependencies': self.dependencies,
            'imports': self.imports,
            'exports': self.exports,
            'functions': self.functions,
            'classes': self.classes,
            'project_context': self.project_context,
            'analysis_metadata': self.analysis_metadata
        }


@dataclass
class ProjectInfo:
    """
    Comprehensive project information model containing metadata and structure analysis.
    Used for understanding project context and providing better analysis results.
    """
    
    name: str
    path: str
    description: Optional[str] = None
    version: Optional[str] = None
    
    # Project metadata
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    size: int = 0
    
    # Project structure
    files: List[FileInfo] = field(default_factory=list)
    directories: List[str] = field(default_factory=list)
    languages: Set[str] = field(default_factory=set)
    frameworks: Set[str] = field(default_factory=set)
    
    # Configuration files
    config_files: Dict[str, str] = field(default_factory=dict)
    dependency_files: Dict[str, str] = field(default_factory=dict)
    
    # Project statistics
    total_files: int = 0
    total_lines: int = 0
    avg_complexity: float = 0.0
    
    # Git information
    git_repository: Optional[str] = None
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None
    
    # Analysis context
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_path(cls, project_path: str, scan_depth: int = 3) -> 'ProjectInfo':
        """
        Create ProjectInfo instance by scanning a project directory.
        
        Args:
            project_path: Path to the project directory
            scan_depth: Maximum depth to scan for files
            
        Returns:
            ProjectInfo instance with populated project data
        """
        path_obj = Path(project_path)
        if not path_obj.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        name = path_obj.name
        
        # Get project timestamps
        stat_info = path_obj.stat()
        created_at = datetime.fromtimestamp(stat_info.st_ctime)
        modified_at = datetime.fromtimestamp(stat_info.st_mtime)
        
        # Initialize collections
        files = []
        directories = []
        languages = set()
        frameworks = set()
        config_files = {}
        dependency_files = {}
        
        # Scan project structure
        for root, dirs, filenames in os.walk(project_path):
            # Calculate current depth
            depth = root[len(project_path):].count(os.sep)
            if depth >= scan_depth:
                dirs[:] = []  # Don't go deeper
                continue
            
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'venv', 'env', 'build', 'dist',
                'target', '.git', '.vscode', '.idea', 'coverage'
            }]
            
            # Add directories
            for dir_name in dirs:
                directories.append(os.path.join(root, dir_name))
            
            # Process files
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, project_path)
                
                # Skip hidden files and common build artifacts
                if filename.startswith('.') or filename.endswith(('.pyc', '.class', '.o')):
                    continue
                
                try:
                    # Create FileInfo for code files
                    if cls._is_code_file(filename):
                        file_info = FileInfo.from_path(file_path)
                        files.append(file_info)
                        
                        if file_info.language:
                            languages.add(file_info.language)
                        if file_info.framework:
                            frameworks.add(file_info.framework)
                    
                    # Identify config and dependency files
                    if cls._is_config_file(filename):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            config_files[rel_path] = f.read()
                    
                    if cls._is_dependency_file(filename):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            dependency_files[rel_path] = f.read()
                            
                except (UnicodeDecodeError, PermissionError, OSError):
                    # Skip files that can't be read
                    continue
        
        # Calculate statistics
        total_files = len(files)
        total_lines = sum(f.line_count for f in files)
        avg_complexity = sum(f.complexity_score for f in files) / max(1, total_files)
        
        # Try to detect Git information
        git_repository = None
        git_branch = None
        git_commit = None
        
        git_dir = path_obj / '.git'
        if git_dir.exists():
            try:
                # Try to get Git info using Git commands
                import subprocess
                
                # Get repository URL
                try:
                    result = subprocess.run(
                        ['git', 'remote', 'get-url', 'origin'],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        git_repository = result.stdout.strip()
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    pass
                
                # Get current branch
                try:
                    result = subprocess.run(
                        ['git', 'branch', '--show-current'],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        git_branch = result.stdout.strip()
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    pass
                
                # Get current commit
                try:
                    result = subprocess.run(
                        ['git', 'rev-parse', 'HEAD'],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        git_commit = result.stdout.strip()[:8]  # Short hash
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    pass
                    
            except (ImportError, FileNotFoundError):
                # Git not available
                pass
        
        return cls(
            name=name,
            path=str(path_obj),
            created_at=created_at,
            modified_at=modified_at,
            files=files,
            directories=directories,
            languages=languages,
            frameworks=frameworks,
            config_files=config_files,
            dependency_files=dependency_files,
            total_files=total_files,
            total_lines=total_lines,
            avg_complexity=avg_complexity,
            git_repository=git_repository,
            git_branch=git_branch,
            git_commit=git_commit
        )
    
    @staticmethod
    def _is_code_file(filename: str) -> bool:
        """Check if file is a code file that should be analyzed."""
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.cs',
            '.php', '.rb', '.go', '.rs', '.kt', '.scala', '.swift', '.dart',
            '.sql', '.html', '.css', '.scss', '.sass', '.less'
        }
        return any(filename.endswith(ext) for ext in code_extensions)
    
    @staticmethod
    def _is_config_file(filename: str) -> bool:
        """Check if file is a configuration file."""
        config_files = {
            'package.json', 'tsconfig.json', 'webpack.config.js', 'babel.config.js',
            'jest.config.js', 'eslint.config.js', '.eslintrc.js', '.eslintrc.json',
            'prettier.config.js', '.prettierrc', 'setup.py', 'pyproject.toml',
            'requirements.txt', 'Pipfile', 'tox.ini', 'pytest.ini', '.gitignore',
            'Dockerfile', 'docker-compose.yml', '.env', '.env.example'
        }
        return filename in config_files or filename.endswith(('.json', '.yaml', '.yml', '.toml', '.ini'))
    
    @staticmethod
    def _is_dependency_file(filename: str) -> bool:
        """Check if file contains dependency information."""
        dependency_files = {
            'package.json', 'package-lock.json', 'yarn.lock', 'requirements.txt',
            'Pipfile', 'Pipfile.lock', 'poetry.lock', 'composer.json', 'composer.lock',
            'Gemfile', 'Gemfile.lock', 'go.mod', 'go.sum', 'Cargo.toml', 'Cargo.lock'
        }
        return filename in dependency_files
    
    def get_file_by_path(self, file_path: str) -> Optional[FileInfo]:
        """Get FileInfo by file path."""
        for file_info in self.files:
            if file_info.path == file_path or file_info.path.endswith(file_path):
                return file_info
        return None
    
    def get_files_by_language(self, language: str) -> List[FileInfo]:
        """Get all files for a specific language."""
        return [f for f in self.files if f.language == language]
    
    def get_files_by_framework(self, framework: str) -> List[FileInfo]:
        """Get all files for a specific framework."""
        return [f for f in self.files if f.framework == framework]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ProjectInfo to dictionary representation."""
        return {
            'name': self.name,
            'path': self.path,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'size': self.size,
            'files': [f.to_dict() for f in self.files],
            'directories': self.directories,
            'languages': list(self.languages),
            'frameworks': list(self.frameworks),
            'config_files': self.config_files,
            'dependency_files': self.dependency_files,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'avg_complexity': self.avg_complexity,
            'git_repository': self.git_repository,
            'git_branch': self.git_branch,
            'git_commit': self.git_commit,
            'analysis_metadata': self.analysis_metadata
        } 