from flask import Blueprint, request, jsonify
import gitlab
import base64
import ast
import re
import os
import json
from datetime import datetime
from typing import Dict, List, Set, Tuple, Any

# Create Blueprint
gitlab_bp = Blueprint('gitlab', __name__)

# Initialize GitLab connection
gl = None

def init_gitlab(gitlab_url, gitlab_token):
    global gl
    try:
        gl = gitlab.Gitlab(gitlab_url, private_token=gitlab_token)
        gl.auth()
        return True
    except Exception as e:
        print(f"Failed to initialize GitLab connection: {e}")
        return False

@gitlab_bp.route('/projects')
def get_projects():
    try:
        projects = gl.projects.list(membership=True, per_page=50)
        
        projects_data = []
        for project in projects:
            projects_data.append({
                'id': project.id,
                'name': project.name,
                'path': project.path,
                'path_with_namespace': project.path_with_namespace,
                'description': project.description,
                'web_url': project.web_url,
                'last_activity_at': project.last_activity_at,
                'default_branch': project.default_branch,
                'topics': getattr(project, 'topics', [])
            })
        
        return jsonify({
            'success': True,
            'projects': projects_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gitlab_bp.route('/repository/<int:project_id>/branches')
def get_repository_branches(project_id):
    try:
        project = gl.projects.get(project_id)
        branches = project.branches.list(all=True)
        
        branches_data = []
        for branch in branches:
            branches_data.append({
                'name': branch.name,
                'protected': branch.protected,
                'default': branch.name == project.default_branch,
                'commit': {
                    'id': branch.commit['id'],
                    'short_id': branch.commit['short_id'],
                    'message': branch.commit['message'],
                    'author_name': branch.commit['author_name'],
                    'authored_date': branch.commit['authored_date']
                }
            })
        
        return jsonify({
            'success': True,
            'branches': branches_data,
            'default_branch': project.default_branch
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gitlab_bp.route('/repository/<int:project_id>/tree')
def get_repository_tree(project_id):
    try:
        branch = request.args.get('branch', 'main')
        path = request.args.get('path', '')
        
        project = gl.projects.get(project_id)
        tree = project.repository_tree(path=path, ref=branch, recursive=False, all=True)
        
        tree_data = []
        for item in tree:
            tree_data.append({
                'id': item['id'],
                'name': item['name'],
                'type': item['type'],
                'path': item['path'],
                'mode': item['mode']
            })
        
        return jsonify({
            'success': True,
            'items': tree_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gitlab_bp.route('/repository/<int:project_id>/file')
def get_repository_file(project_id):
    try:
        file_path = request.args.get('path')
        branch = request.args.get('branch', 'main')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'File path is required'
            }), 400
        
        project = gl.projects.get(project_id)
        file_data = project.files.get(file_path=file_path, ref=branch)
        
        # Decode content
        content = base64.b64decode(file_data.content).decode('utf-8')
        
        return jsonify({
            'success': True,
            'content': content,
            'size': file_data.size,
            'encoding': file_data.encoding,
            'file_name': file_data.file_name,
            'file_path': file_data.file_path,
            'last_commit_id': file_data.last_commit_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gitlab_bp.route('/repository/<int:project_id>/commit', methods=['POST'])
def commit_file(project_id):
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        branch = data.get('branch', 'main')
        content = data.get('content')
        commit_message = data.get('commit_message')
        
        if not all([file_path, content, commit_message]):
            return jsonify({
                'success': False,
                'error': 'file_path, content, and commit_message are required'
            }), 400
        
        project = gl.projects.get(project_id)
        
        # Update file
        try:
            file_data = project.files.get(file_path=file_path, ref=branch)
            file_data.content = content
            file_data.save(branch=branch, commit_message=commit_message)
        except:
            # File doesn't exist, create it
            project.files.create({
                'file_path': file_path,
                'branch': branch,
                'content': content,
                'commit_message': commit_message
            })
        
        return jsonify({
            'success': True,
            'message': 'File committed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@gitlab_bp.route('/repository/<int:project_id>/commits')
def get_repository_commits(project_id):
    try:
        branch = request.args.get('branch', 'main')
        per_page = int(request.args.get('per_page', 20))
        
        commits = gl.projects.get(project_id).commits.list(
            ref_name=branch,
            per_page=per_page,
            all=False
        )
        
        commits_data = []
        for commit in commits:
            commits_data.append({
                'id': commit.id,
                'short_id': commit.short_id,
                'title': commit.title,
                'message': commit.message,
                'author_name': commit.author_name,
                'author_email': commit.author_email,
                'authored_date': commit.authored_date,
                'committer_name': commit.committer_name,
                'committer_email': commit.committer_email,
                'committed_date': commit.committed_date,
                'web_url': commit.web_url
            })
        
        return jsonify({
            'success': True,
            'commits': commits_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@gitlab_bp.route('/repository/<int:project_id>/dependencies')
def get_repository_dependencies(project_id):
    """Analyze repository dependencies and return graph data"""
    try:
        branch = request.args.get('branch', 'main')
        
        # Get project and file tree
        project = gl.projects.get(project_id)
        tree = project.repository_tree(ref=branch, recursive=True, all=True)
        
        # Initialize dependency analyzer
        analyzer = DependencyAnalyzer(project, branch)
        
        # Analyze all files
        analysis_result = analyzer.analyze_project(tree)
        
        return jsonify({
            'success': True,
            'files': analysis_result['files'],
            'metadata': analysis_result['metadata']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


class DependencyAnalyzer:
    """Analyzes file dependencies for multiple programming languages"""
    
    def __init__(self, project, branch: str):
        self.project = project
        self.branch = branch
        self.file_cache = {}
        
    def analyze_project(self, tree) -> Dict[str, Any]:
        """Analyze the entire project for dependencies"""
        files_data = []
        total_files = len(tree)
        analyzed_files = 0
        
        # Filter only code files
        code_files = [f for f in tree if self._is_code_file(f['name'])]
        
        for file_item in code_files:
            try:
                file_analysis = self._analyze_file(file_item)
                if file_analysis:
                    files_data.append(file_analysis)
                    analyzed_files += 1
            except Exception as e:
                print(f"Error analyzing {file_item['path']}: {e}")
                continue
        
        # Build import resolution map
        import_map = self._build_import_resolution_map(files_data)
        
        # Resolve imports to actual file paths
        for file_data in files_data:
            file_data['imports'] = self._resolve_imports(file_data['imports'], file_data['path'], import_map)
        
        return {
            'files': files_data,
            'metadata': {
                'total_files': total_files,
                'analyzed_files': analyzed_files,
                'code_files': len(code_files),
                'analysis_date': datetime.now().isoformat()
            }
        }
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file worth analyzing"""
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.vue', '.java', '.php', 
            '.rb', '.go', '.rs', '.swift', '.kt', '.cs', '.cpp', '.c', 
            '.h', '.hpp', '.scala', '.r', '.m', '.dart', '.json'
        }
        
        # Skip common non-code files
        skip_patterns = {
            '__pycache__', '.git', 'node_modules', '.vscode', '.idea',
            'dist', 'build', 'target', '.DS_Store'
        }
        
        if any(pattern in filename.lower() for pattern in skip_patterns):
            return False
            
        return any(filename.lower().endswith(ext) for ext in code_extensions)
    
    def _analyze_file(self, file_item) -> Dict[str, Any]:
        """Analyze a single file for dependencies"""
        file_path = file_item['path']
        
        try:
            # Get file content
            file_content = self._get_file_content(file_path)
            if not file_content:
                return None
            
            # Determine file type and analyze accordingly
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.py':
                return self._analyze_python_file(file_path, file_content)
            elif file_extension in ['.js', '.jsx', '.ts', '.tsx']:
                return self._analyze_javascript_file(file_path, file_content)
            elif file_extension == '.java':
                return self._analyze_java_file(file_path, file_content)
            elif file_extension == '.json':
                return self._analyze_json_file(file_path, file_content)
            else:
                return self._analyze_generic_file(file_path, file_content)
                
        except Exception as e:
            print(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _get_file_content(self, file_path: str) -> str:
        """Get file content with caching"""
        if file_path in self.file_cache:
            return self.file_cache[file_path]
        
        try:
            file_data = self.project.files.get(file_path=file_path, ref=self.branch)
            content = base64.b64decode(file_data.content).decode('utf-8')
            self.file_cache[file_path] = content
            return content
        except Exception as e:
            print(f"Could not read file {file_path}: {e}")
            return ""
    
    def _analyze_python_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Python file for dependencies"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return self._analyze_generic_file(file_path, content)
        
        imports = []
        functions = []
        classes = []
        function_calls = []
        
        for node in ast.walk(tree):
            # Imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            
            # Function definitions
            elif isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args]
                })
            
            # Class definitions
            elif isinstance(node, ast.ClassDef):
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'bases': [self._get_name(base) for base in node.bases]
                })
            
            # Function calls
            elif isinstance(node, ast.Call):
                func_name = self._get_name(node.func)
                if func_name:
                    function_calls.append({
                        'function': func_name,
                        'line': node.lineno
                    })
        
        return {
            'path': file_path,
            'type': 'python',
            'size': len(content),
            'imports': imports,
            'functions': functions,
            'classes': classes,
            'function_calls': function_calls,
            'exports': [f['name'] for f in functions] + [c['name'] for c in classes]
        }
    
    def _analyze_javascript_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript file for dependencies"""
        imports = []
        functions = []
        classes = []
        exports = []
        
        # Simple regex-based analysis for JavaScript
        # Import statements
        import_patterns = [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'import\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            r'import\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
        
        # Function definitions
        func_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[\w,\s]+)\s*=>\s*{',
            r'(\w+)\s*:\s*(?:async\s+)?function\s*\(',
            r'(\w+)\s*\([^)]*\)\s*{'
        ]
        
        for pattern in func_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            functions.extend([{'name': match, 'line': 0} for match in matches])
        
        # Class definitions
        class_matches = re.findall(r'class\s+(\w+)', content, re.MULTILINE)
        classes = [{'name': match, 'line': 0} for match in class_matches]
        
        # Export statements
        export_patterns = [
            r'export\s+(?:default\s+)?(?:function\s+)?(\w+)',
            r'export\s*{\s*([^}]+)\s*}',
            r'module\.exports\s*=\s*(\w+)',
            r'exports\.(\w+)'
        ]
        
        for pattern in export_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            exports.extend(matches)
        
        return {
            'path': file_path,
            'type': 'javascript',
            'size': len(content),
            'imports': imports,
            'functions': functions,
            'classes': classes,
            'exports': exports,
            'function_calls': []
        }
    
    def _analyze_java_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Java file for dependencies"""
        imports = []
        classes = []
        functions = []
        
        # Import statements
        import_matches = re.findall(r'import\s+([^;]+);', content, re.MULTILINE)
        imports = [imp.strip() for imp in import_matches]
        
        # Class definitions
        class_matches = re.findall(r'(?:public\s+|private\s+|protected\s+)?class\s+(\w+)', content, re.MULTILINE)
        classes = [{'name': match, 'line': 0} for match in class_matches]
        
        # Method definitions
        method_matches = re.findall(r'(?:public\s+|private\s+|protected\s+|static\s+)*\w+\s+(\w+)\s*\([^)]*\)\s*{', content, re.MULTILINE)
        functions = [{'name': match, 'line': 0} for match in method_matches if match not in ['if', 'for', 'while', 'switch']]
        
        return {
            'path': file_path,
            'type': 'java',
            'size': len(content),
            'imports': imports,
            'functions': functions,
            'classes': classes,
            'exports': [c['name'] for c in classes],
            'function_calls': []
        }
    
    def _analyze_json_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze JSON file for dependencies (package.json, etc.)"""
        try:
            data = json.loads(content)
            dependencies = []
            
            if isinstance(data, dict):
                # Package.json dependencies
                for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                    if dep_type in data:
                        dependencies.extend(data[dep_type].keys())
            
            return {
                'path': file_path,
                'type': 'json',
                'size': len(content),
                'imports': dependencies,
                'functions': [],
                'classes': [],
                'exports': [],
                'function_calls': []
            }
        except json.JSONDecodeError:
            return self._analyze_generic_file(file_path, content)
    
    def _analyze_generic_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Generic analysis for unsupported file types"""
        return {
            'path': file_path,
            'type': 'generic',
            'size': len(content),
            'imports': [],
            'functions': [],
            'classes': [],
            'exports': [],
            'function_calls': []
        }
    
    def _get_name(self, node) -> str:
        """Extract name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        return ""
    
    def _build_import_resolution_map(self, files_data: List[Dict]) -> Dict[str, str]:
        """Build map from import names to actual file paths"""
        resolution_map = {}
        
        for file_data in files_data:
            file_path = file_data['path']
            
            # Add file itself
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            resolution_map[name_without_ext] = file_path
            
            # Add exports
            for export in file_data.get('exports', []):
                if isinstance(export, str):
                    resolution_map[export] = file_path
        
        return resolution_map
    
    def _resolve_imports(self, imports: List[str], current_file: str, resolution_map: Dict[str, str]) -> List[str]:
        """Resolve import names to actual file paths"""
        resolved = []
        current_dir = os.path.dirname(current_file)
        
        for imp in imports:
            # Skip standard library imports
            if self._is_standard_library(imp):
                continue
            
            # Try direct resolution
            if imp in resolution_map:
                resolved.append(resolution_map[imp])
                continue
        
        return resolved
    
    def _is_standard_library(self, import_name: str) -> bool:
        """Check if import is from standard library"""
        python_stdlib = {
            'os', 'sys', 'json', 'datetime', 'time', 'random', 'math', 're',
            'collections', 'itertools', 'functools', 'typing', 'pathlib',
            'subprocess', 'threading', 'multiprocessing', 'asyncio', 'urllib',
            'http', 'html', 'xml', 'csv', 'sqlite3', 'logging', 'unittest'
        }
        
        js_builtins = {
            'react', 'vue', 'angular', 'lodash', 'jquery', 'express',
            'axios', 'moment', 'fs', 'path', 'url', 'http', 'https'
        }
        
        return (import_name in python_stdlib or 
                import_name in js_builtins or
                import_name.startswith('@') or  # npm scoped packages
                '/' in import_name)  # relative imports 