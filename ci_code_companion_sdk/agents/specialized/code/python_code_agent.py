"""
Python Code Agent - Specialized for Python Development

This agent focuses exclusively on Python code development, analysis, and optimization.
It provides expert guidance for Python best practices, modern patterns, performance
optimization, and framework-specific recommendations.
"""

import re
import ast
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class PythonCodeAgent(BaseAgent):
    """
    Specialized agent for Python code development and analysis.
    Focuses on Python syntax, patterns, performance, and framework best practices.
    """
    
    def __init__(self, config: Dict[str, Any], logger, prompt_loader=None):
        """Initialize PythonCodeAgent with optional PromptLoader"""
        super().__init__(config, logger)
        self.prompt_loader = prompt_loader
    
    def _initialize(self):
        """Initialize Python Code Agent with specialized configuration"""
        super()._initialize()
        self.name = "python_code"
        self.version = "2.0.0"
        
        # Python-specific patterns and rules
        self.python_patterns = {
            'function_def': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'class_def': r'class\s+([A-Z][a-zA-Z0-9_]*)(?:\([^)]*\))?:',
            'import_statement': r'(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+',
            'async_def': r'async\s+def\s+([a-zA-Z_][a-zA-Z0-9_]*)',
            'list_comprehension': r'\[.*for.*in.*\]',
            'dict_comprehension': r'\{.*for.*in.*\}',
            'generator_expression': r'\(.*for.*in.*\)',
            'lambda_function': r'lambda\s+[^:]*:',
            'decorator': r'@\w+(?:\([^)]*\))?',
            'type_hint': r':\s*[A-Z][a-zA-Z0-9_\[\],\s]*(?:\s*=|\s*->)'
        }
        
        self.performance_checks = {
            'list_append_in_loop': r'for\s+\w+\s+in\s+.*:\s*\n\s*\w+\.append\(',
            'string_concatenation': r'\+\s*[\'"].*[\'"]|\w+\s*\+=\s*[\'"]',
            'inefficient_membership': r'in\s+\[.*\]',
            'global_variable': r'global\s+\w+',
            'nested_loops': r'for\s+.*:\s*\n\s*for\s+.*:',
            'regex_compilation': r're\.(?:match|search|findall)\s*\(',
            'file_operations': r'open\s*\([^)]*\)(?!\s*as|\s*with)',
            'exception_bare': r'except\s*:'
        }
        
        # Framework-specific patterns
        self.framework_patterns = {
            'django': {
                'model_class': r'class\s+\w+\s*\(\s*models\.Model\s*\)',
                'view_function': r'def\s+\w+\s*\([^)]*request[^)]*\)',
                'url_pattern': r'path\s*\([^)]*\)',
                'template_tag': r'{%\s*\w+.*%}',
                'orm_query': r'\.objects\.(?:filter|get|all|create)'
            },
            'flask': {
                'route_decorator': r'@app\.route\s*\(',
                'view_function': r'def\s+\w+\s*\([^)]*\):',
                'template_render': r'render_template\s*\(',
                'request_usage': r'request\.\w+',
                'session_usage': r'session\[\w+\]'
            },
            'fastapi': {
                'path_decorator': r'@app\.(?:get|post|put|delete)\s*\(',
                'dependency_injection': r'Depends\s*\(',
                'pydantic_model': r'class\s+\w+\s*\(\s*BaseModel\s*\)',
                'async_endpoint': r'async\s+def\s+\w+\s*\(',
                'response_model': r'response_model\s*=\s*\w+'
            }
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Python Code Agent capabilities"""
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CODE_OPTIMIZATION,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.REFACTORING,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported file types for Python code analysis"""
        return ['.py', '.pyw', '.pyi']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported Python frameworks"""
        return ['django', 'flask', 'fastapi', 'pyramid', 'tornado', 'asyncio']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Python code for development best practices and optimization opportunities.
        
        Args:
            file_path: Path to Python file
            content: File content to analyze
            context: Analysis context including project info
            
        Returns:
            Dictionary containing comprehensive code analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract file metadata
        metadata = self.extract_metadata(file_path, content)
        metadata.update(await self._extract_python_metadata(content))
        
        # Perform Python-specific code analysis
        issues.extend(await self._analyze_code_structure(content))
        issues.extend(await self._analyze_python_patterns(content))
        issues.extend(await self._analyze_performance_issues(content))
        issues.extend(await self._analyze_error_handling(content))
        issues.extend(await self._analyze_framework_usage(content))
        
        # Generate optimization suggestions
        suggestions.extend(await self._suggest_performance_optimizations(content))
        suggestions.extend(await self._suggest_code_improvements(content))
        suggestions.extend(await self._suggest_modern_patterns(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_python_metadata(self, content: str) -> Dict[str, Any]:
        """Extract Python-specific metadata from file content"""
        metadata = {
            'python_version': 'unknown',
            'functions': [],
            'classes': [],
            'imports': [],
            'decorators': [],
            'async_functions': [],
            'complexity_score': 0,
            'framework': None,
            'type_hints_usage': False,
            'docstring_coverage': 0.0
        }
        
        # Parse with AST for more accurate analysis
        try:
            tree = ast.parse(content)
            metadata.update(self._analyze_ast(tree))
        except SyntaxError:
            # Fall back to regex if AST parsing fails
            metadata.update(self._analyze_with_regex(content))
        
        # Detect framework
        metadata['framework'] = self._detect_framework(content)
        
        # Check for type hints
        metadata['type_hints_usage'] = bool(re.search(self.python_patterns['type_hint'], content))
        
        # Calculate docstring coverage
        metadata['docstring_coverage'] = self._calculate_docstring_coverage(content)
        
        return metadata
    
    def _analyze_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python code using AST"""
        metadata = {
            'functions': [],
            'classes': [],
            'imports': [],
            'decorators': [],
            'async_functions': [],
            'complexity_score': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metadata['functions'].append(node.name)
                if node.decorator_list:
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name):
                            metadata['decorators'].append(decorator.id)
            
            elif isinstance(node, ast.AsyncFunctionDef):
                metadata['async_functions'].append(node.name)
            
            elif isinstance(node, ast.ClassDef):
                metadata['classes'].append(node.name)
            
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        metadata['imports'].append(alias.name)
                else:  # ImportFrom
                    module = node.module or ''
                    for alias in node.names:
                        metadata['imports'].append(f"{module}.{alias.name}")
        
        # Calculate cyclomatic complexity
        metadata['complexity_score'] = self._calculate_cyclomatic_complexity(tree)
        
        return metadata
    
    def _analyze_with_regex(self, content: str) -> Dict[str, Any]:
        """Fallback analysis using regex patterns"""
        metadata = {
            'functions': [],
            'classes': [],
            'imports': [],
            'async_functions': []
        }
        
        # Extract functions
        func_matches = re.findall(self.python_patterns['function_def'], content)
        metadata['functions'] = func_matches
        
        # Extract classes
        class_matches = re.findall(self.python_patterns['class_def'], content)
        metadata['classes'] = class_matches
        
        # Extract async functions
        async_matches = re.findall(self.python_patterns['async_def'], content)
        metadata['async_functions'] = async_matches
        
        # Extract imports
        import_matches = re.findall(self.python_patterns['import_statement'], content)
        metadata['imports'] = import_matches
        
        return metadata
    
    async def _analyze_code_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Python code structure and organization"""
        issues = []
        lines = content.split('\n')
        
        # Check for PEP 8 violations
        issues.extend(self._check_pep8_violations(lines))
        
        # Check for long functions
        issues.extend(self._check_function_length(content))
        
        # Check for complex classes
        issues.extend(self._check_class_complexity(content))
        
        # Check for missing docstrings
        issues.extend(self._check_missing_docstrings(content))
        
        return issues
    
    def _check_pep8_violations(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Check for common PEP 8 violations"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # Line too long
            if len(line) > 88:  # Black's default line length
                issues.append(self.create_issue(
                    'pep8_violation',
                    'low',
                    'Line too long',
                    f'Line {i} exceeds 88 characters ({len(line)} chars)',
                    line_number=i,
                    suggestion='Break long lines using parentheses or backslashes'
                ))
            
            # Multiple statements on one line
            if ';' in line and not line.strip().startswith('#'):
                issues.append(self.create_issue(
                    'pep8_violation',
                    'medium',
                    'Multiple statements on one line',
                    'Multiple statements should be on separate lines',
                    line_number=i,
                    suggestion='Put each statement on its own line'
                ))
            
            # Trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                issues.append(self.create_issue(
                    'pep8_violation',
                    'low',
                    'Trailing whitespace',
                    'Line has trailing whitespace',
                    line_number=i,
                    suggestion='Remove trailing whitespace'
                ))
        
        return issues
    
    def _check_function_length(self, content: str) -> List[Dict[str, Any]]:
        """Check for overly long functions"""
        issues = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func_lines = node.end_lineno - node.lineno + 1
                    if func_lines > 50:
                        issues.append(self.create_issue(
                            'function_complexity',
                            'medium',
                            'Long function detected',
                            f'Function "{node.name}" has {func_lines} lines. Consider breaking it into smaller functions.',
                            line_number=node.lineno,
                            suggestion='Extract common logic into separate functions'
                        ))
        except:
            pass  # Skip if AST parsing fails
        
        return issues
    
    def _check_class_complexity(self, content: str) -> List[Dict[str, Any]]:
        """Check for overly complex classes"""
        issues = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    if len(methods) > 20:
                        issues.append(self.create_issue(
                            'class_complexity',
                            'medium',
                            'Complex class detected',
                            f'Class "{node.name}" has {len(methods)} methods. Consider breaking it into smaller classes.',
                            line_number=node.lineno,
                            suggestion='Apply Single Responsibility Principle and extract related methods'
                        ))
        except:
            pass
        
        return issues
    
    def _check_missing_docstrings(self, content: str) -> List[Dict[str, Any]]:
        """Check for missing docstrings"""
        issues = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if not ast.get_docstring(node):
                        node_type = 'function' if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 'class'
                        issues.append(self.create_issue(
                            'documentation',
                            'low',
                            f'Missing docstring for {node_type}',
                            f'{node_type.title()} "{node.name}" lacks documentation',
                            line_number=node.lineno,
                            suggestion=f'Add docstring explaining {node_type} purpose and parameters'
                        ))
        except:
            pass
        
        return issues
    
    async def _analyze_python_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Python-specific patterns and idioms"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for range(len()) anti-pattern
            if re.search(r'range\s*\(\s*len\s*\(', line):
                issues.append(self.create_issue(
                    'python_antipattern',
                    'medium',
                    'range(len()) anti-pattern',
                    'Use enumerate() instead of range(len()) for iteration',
                    line_number=i,
                    suggestion='Replace with: for i, item in enumerate(sequence)'
                ))
            
            # Check for mutable default arguments
            if re.search(r'def\s+\w+\s*\([^)]*=\s*(?:\[\]|\{\})', line):
                issues.append(self.create_issue(
                    'python_antipattern',
                    'high',
                    'Mutable default argument',
                    'Mutable default arguments can cause unexpected behavior',
                    line_number=i,
                    suggestion='Use None as default and initialize inside function'
                ))
            
            # Check for bare except clauses
            if re.search(r'except\s*:', line):
                issues.append(self.create_issue(
                    'error_handling',
                    'high',
                    'Bare except clause',
                    'Catching all exceptions can hide bugs and make debugging difficult',
                    line_number=i,
                    suggestion='Catch specific exception types'
                ))
        
        return issues
    
    async def _analyze_performance_issues(self, content: str) -> List[Dict[str, Any]]:
        """Analyze performance-related issues"""
        issues = []
        lines = content.split('\n')
        
        for pattern_name, pattern in self.performance_checks.items():
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    severity, title, description, suggestion = self._get_performance_issue_info(pattern_name)
                    issues.append(self.create_issue(
                        'performance',
                        severity,
                        title,
                        description,
                        line_number=i,
                        suggestion=suggestion
                    ))
        
        return issues
    
    def _get_performance_issue_info(self, pattern_name: str) -> tuple:
        """Get performance issue information"""
        info = {
            'list_append_in_loop': (
                'medium',
                'List append in loop',
                'Appending to list in loop can be inefficient',
                'Consider list comprehension or pre-allocating list size'
            ),
            'string_concatenation': (
                'medium',
                'String concatenation in loop',
                'String concatenation can be inefficient for large strings',
                'Use join() for multiple strings or f-strings for formatting'
            ),
            'inefficient_membership': (
                'low',
                'Inefficient membership test',
                'Membership test on list is O(n), consider using set',
                'Convert list to set for frequent membership tests'
            ),
            'global_variable': (
                'low',
                'Global variable usage',
                'Global variables can make code harder to test and maintain',
                'Consider passing variables as parameters or using classes'
            ),
            'nested_loops': (
                'medium',
                'Nested loops detected',
                'Nested loops can have poor performance with large datasets',
                'Consider algorithmic improvements or vectorization'
            )
        }
        return info.get(pattern_name, ('low', 'Performance issue', 'Potential performance concern', 'Review for optimization'))
    
    async def _analyze_error_handling(self, content: str) -> List[Dict[str, Any]]:
        """Analyze error handling patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for try blocks without finally or proper cleanup
        in_try_block = False
        has_finally = False
        try_line = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith('try:'):
                in_try_block = True
                has_finally = False
                try_line = i
            elif stripped.startswith('finally:') and in_try_block:
                has_finally = True
            elif stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ')) and in_try_block:
                if not has_finally and 'open(' in content[content.find('try:'):content.find('\n', content.find('try:') + 100)]:
                    issues.append(self.create_issue(
                        'error_handling',
                        'medium',
                        'Missing finally block for resource cleanup',
                        'Try block with file operations should have finally block or use context manager',
                        line_number=try_line,
                        suggestion='Use "with" statement for automatic resource management'
                    ))
                in_try_block = False
        
        return issues
    
    async def _analyze_framework_usage(self, content: str) -> List[Dict[str, Any]]:
        """Analyze framework-specific usage patterns"""
        issues = []
        framework = self._detect_framework(content)
        
        if framework and framework in self.framework_patterns:
            framework_issues = self._analyze_framework_specific(content, framework)
            issues.extend(framework_issues)
        
        return issues
    
    def _analyze_framework_specific(self, content: str, framework: str) -> List[Dict[str, Any]]:
        """Analyze framework-specific patterns"""
        issues = []
        
        if framework == 'django':
            issues.extend(self._analyze_django_patterns(content))
        elif framework == 'flask':
            issues.extend(self._analyze_flask_patterns(content))
        elif framework == 'fastapi':
            issues.extend(self._analyze_fastapi_patterns(content))
        
        return issues
    
    def _analyze_django_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Django-specific patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for N+1 queries
        for i, line in enumerate(lines, 1):
            if re.search(r'\.objects\.filter\([^)]*\)\.(?!prefetch_related|select_related)', line):
                if any('for' in lines[j] for j in range(max(0, i-3), min(len(lines), i+3))):
                    issues.append(self.create_issue(
                        'django_performance',
                        'high',
                        'Potential N+1 query',
                        'Database query inside loop can cause performance issues',
                        line_number=i,
                        suggestion='Use select_related() or prefetch_related() for optimization'
                    ))
        
        return issues
    
    def _analyze_flask_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Flask-specific patterns"""
        issues = []
        
        # Check for debug mode in production
        if 'app.run(debug=True)' in content:
            issues.append(self.create_issue(
                'flask_security',
                'high',
                'Debug mode enabled',
                'Debug mode should never be enabled in production',
                suggestion='Set debug=False or use environment variables'
            ))
        
        return issues
    
    def _analyze_fastapi_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze FastAPI-specific patterns"""
        issues = []
        
        # Check for missing response models
        if '@app.' in content and 'response_model' not in content:
            issues.append(self.create_issue(
                'fastapi_best_practice',
                'low',
                'Missing response model',
                'Consider adding response_model for better API documentation',
                suggestion='Add response_model parameter to endpoints'
            ))
        
        return issues
    
    async def _suggest_performance_optimizations(self, content: str) -> List[Dict[str, Any]]:
        """Suggest performance optimizations"""
        suggestions = []
        
        # Suggest list comprehensions
        if 'for' in content and 'append(' in content:
            suggestions.append(self.create_suggestion(
                'performance',
                'Use list comprehensions',
                'Replace loops with list comprehensions for better performance and readability',
                impact='medium',
                effort='low'
            ))
        
        # Suggest generator expressions for large datasets
        if re.search(r'\[.*for.*in.*\]', content) and 'len(' in content:
            suggestions.append(self.create_suggestion(
                'memory_optimization',
                'Consider generator expressions',
                'Use generator expressions for memory-efficient iteration over large datasets',
                impact='high',
                effort='low'
            ))
        
        return suggestions
    
    async def _suggest_code_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest general code improvements"""
        suggestions = []
        
        # Suggest type hints
        if not re.search(self.python_patterns['type_hint'], content):
            suggestions.append(self.create_suggestion(
                'code_quality',
                'Add type hints',
                'Type hints improve code readability and enable better IDE support',
                impact='medium',
                effort='medium'
            ))
        
        # Suggest dataclasses for simple classes
        if 'class' in content and '__init__' in content:
            suggestions.append(self.create_suggestion(
                'modernization',
                'Consider using dataclasses',
                'Dataclasses can reduce boilerplate code for data-holding classes',
                impact='medium',
                effort='low'
            ))
        
        return suggestions
    
    async def _suggest_modern_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Suggest modern Python patterns"""
        suggestions = []
        
        # Suggest pathlib over os.path
        if 'os.path' in content:
            suggestions.append(self.create_suggestion(
                'modernization',
                'Use pathlib instead of os.path',
                'pathlib provides a more object-oriented approach to path handling',
                impact='low',
                effort='medium'
            ))
        
        # Suggest f-strings over format()
        if '.format(' in content or '%' in content:
            suggestions.append(self.create_suggestion(
                'modernization',
                'Use f-strings for string formatting',
                'f-strings are more readable and performant than older formatting methods',
                impact='low',
                effort='low'
            ))
        
        return suggestions
    
    def _detect_framework(self, content: str) -> Optional[str]:
        """Detect Python framework being used"""
        if 'django' in content.lower() or 'from django' in content:
            return 'django'
        elif 'flask' in content.lower() or 'from flask' in content:
            return 'flask'
        elif 'fastapi' in content.lower() or 'from fastapi' in content:
            return 'fastapi'
        elif 'tornado' in content.lower():
            return 'tornado'
        elif 'pyramid' in content.lower():
            return 'pyramid'
        
        return None
    
    def _calculate_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity of the code"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _calculate_docstring_coverage(self, content: str) -> float:
        """Calculate percentage of functions/classes with docstrings"""
        try:
            tree = ast.parse(content)
            total_definitions = 0
            documented_definitions = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total_definitions += 1
                    if ast.get_docstring(node):
                        documented_definitions += 1
            
            return (documented_definitions / total_definitions * 100) if total_definitions > 0 else 100.0
        except:
            return 0.0
    
    def _calculate_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score based on analysis completeness"""
        base_confidence = 0.8
        
        # Boost confidence for successful AST parsing
        try:
            ast.parse(content)
            base_confidence += 0.1
        except:
            base_confidence -= 0.2
        
        # Adjust based on code size
        lines = len(content.split('\n'))
        if lines < 50:
            base_confidence += 0.1
        elif lines > 500:
            base_confidence -= 0.1
        
        # Adjust based on issues found
        if len(issues) == 0:
            base_confidence += 0.1
        elif len(issues) > 15:
            base_confidence -= 0.1
        
        return max(0.5, min(1.0, base_confidence))
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """
        Python agent chat implementation using PromptLoader.
        
        Args:
            context: Chat context including message, file info, and conversation history
            
        Returns:
            Helpful Python-specific response from PromptLoader
        """
        user_message = context.get('user_message', context.get('message', ''))
        file_path = context.get('file_path', '')
        file_content = context.get('file_content', context.get('content', ''))
        conversation_history = context.get('conversation_history', [])
        
        self.logger.info(f"🐍 PYTHON CHAT: Processing message: '{user_message[:100]}{'...' if len(user_message) > 100 else ''}'")
        
        # Use PromptLoader if available (should be injected via constructor)
        if hasattr(self, 'prompt_loader') and self.prompt_loader:
            self.logger.info(f"📚 PYTHON CHAT: Using PromptLoader for enhanced response")
            
            # Build enhanced context for PromptLoader
            enhanced_context = {
                'user_message': user_message,
                'selected_file': {
                    'path': file_path,
                    'content': file_content,
                    'language': 'python'
                } if file_content else None,
                'conversation_history': conversation_history,
                'chat_mode': True,
                'agent_type': 'python_code'
            }
            
            # Get enhanced prompt with context
            enhanced_prompt = self.prompt_loader.get_enhanced_prompt('python_code', enhanced_context)
            
            # Use the enhanced prompt to provide contextual guidance
            response = await self._generate_response_with_prompt_loader(
                user_message, enhanced_context, enhanced_prompt
            )
            
            self.logger.info(f"✅ PYTHON CHAT: Generated enhanced response ({len(response)} characters)")
            return response
        else:
            # Fallback to basic response if no PromptLoader
            self.logger.warning(f"⚠️ PYTHON CHAT: No PromptLoader available, using basic response")
            return await self._generate_basic_chat_response(user_message, file_path, file_content)
    
    async def _generate_response_with_prompt_loader(
        self, 
        user_message: str, 
        context: Dict[str, Any], 
        enhanced_prompt: str
    ) -> str:
        """Generate response using PromptLoader and enhanced context via Vertex AI."""
        
        try:
            # Import here to avoid circular imports
            from ....integrations.vertex_ai_client import VertexAIClient
            
            # Initialize Vertex AI client (reuse from service if available)
            # Use config.get() method to properly read from environment variables
            project_id = self.config.get('project_id') if hasattr(self.config, 'get') else os.getenv('GCP_PROJECT_ID')
            region = self.config.get('region', 'us-central1') if hasattr(self.config, 'get') else 'us-central1'
            
            vertex_client = VertexAIClient(
                project_id=project_id,
                location=region,
                model_name=None,  # Will read from GEMINI_MODEL env var
            )
            
            self.logger.info(f"🤖 PYTHON CHAT: Using Vertex AI with model: {vertex_client.model_name}")
            self.logger.info(f"📏 PYTHON CHAT: Enhanced prompt length: {len(enhanced_prompt)} characters")
            
            # Use the enhanced prompt with Vertex AI
            response = await vertex_client.chat_with_context(
                message=user_message,
                enhanced_prompt=enhanced_prompt,
                conversation_history=context.get('conversation_history', [])
            )
            
            self.logger.info(f"✅ PYTHON CHAT: Vertex AI response received")
            
            # Extract text from response
            if isinstance(response, dict):
                text_response = response.get('text') or response.get('response') or response.get('content')
                if text_response:
                    self.logger.info(f"📝 PYTHON CHAT: Returning AI-generated response ({len(text_response)} characters)")
                    return text_response
                else:
                    error_msg = response.get('error', 'Unknown error')
                    self.logger.error(f"❌ PYTHON CHAT: No text in AI response - Error: {error_msg}")
                    return await self._generate_basic_chat_response(user_message, context.get('selected_file', {}).get('path', ''), context.get('selected_file', {}).get('content', ''))
            else:
                self.logger.error(f"❌ PYTHON CHAT: Unexpected response format: {type(response)}")
                return await self._generate_basic_chat_response(user_message, context.get('selected_file', {}).get('path', ''), context.get('selected_file', {}).get('content', ''))
                
        except Exception as e:
            self.logger.error(f"❌ PYTHON CHAT: Error using PromptLoader with Vertex AI: {e}")
            # Fall back to basic response
            return await self._generate_basic_chat_response(
                user_message, 
                context.get('selected_file', {}).get('path', ''), 
                context.get('selected_file', {}).get('content', '')
            )
    
    async def _generate_basic_chat_response(
        self, 
        user_message: str, 
        file_path: str, 
        file_content: str
    ) -> str:
        """Basic fallback response when PromptLoader is not available."""
        
        return f"""## Python Development Assistant

I'm your Python specialist. I can help with:

- Code analysis and best practices
- Web frameworks (Django, Flask, FastAPI)
- Performance optimization
- Security improvements
- Modern Python patterns

{f"Currently analyzing: `{file_path}`" if file_path else ""}

What Python challenge can I help you solve?""" 