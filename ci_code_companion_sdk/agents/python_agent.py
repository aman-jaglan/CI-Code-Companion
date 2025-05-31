"""
Python Agent for Backend Code Analysis

This agent specializes in analyzing Python code including Django, Flask, FastAPI applications.
It provides comprehensive analysis including syntax checking, PEP8 validation, security scanning,
performance optimization, and Python best practices.
"""

import re
import ast
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentCapability


class PythonAgent(BaseAgent):
    """
    Specialized agent for Python backend analysis.
    """
    
    def _initialize(self):
        """Initialize Python-specific configurations"""
        super()._initialize()
        self.name = "python"
        
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Python agent capabilities"""
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.CODE_OPTIMIZATION,
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.STYLE_CHECK,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported file types for Python analysis"""
        return ['.py', '.pyx', '.pyi']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported Python frameworks"""
        return ['django', 'flask', 'fastapi', 'pytest', 'sqlalchemy']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Python file for issues and suggestions.
        
        Args:
            file_path: Path to Python file
            content: File content to analyze
            context: Analysis context
            
        Returns:
            Dictionary containing analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract metadata
        metadata = self.extract_metadata(file_path, content)
        
        # Perform Python-specific analysis
        issues.extend(await self._analyze_syntax(content))
        issues.extend(await self._analyze_style(content))
        issues.extend(await self._analyze_security(content))
        issues.extend(await self._analyze_performance(content))
        issues.extend(await self._analyze_framework_specific(content))
        
        # Generate suggestions
        suggestions.extend(await self._suggest_optimizations(content))
        suggestions.extend(await self._suggest_best_practices(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _analyze_syntax(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Python syntax and basic issues"""
        issues = []
        
        try:
            # Parse AST to check for syntax errors
            tree = ast.parse(content)
            
            # Check for common syntax issues
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for missing docstrings
                    if not ast.get_docstring(node):
                        issues.append(self.create_issue(
                            'documentation',
                            'low',
                            f'Missing docstring for function {node.name}',
                            'Functions should have docstrings explaining their purpose',
                            line_number=node.lineno,
                            suggestion='Add a docstring describing the function purpose, parameters, and return value'
                        ))
                    
                    # Check for too many arguments
                    if len(node.args.args) > 5:
                        issues.append(self.create_issue(
                            'complexity',
                            'medium',
                            f'Function {node.name} has too many parameters',
                            f'Function has {len(node.args.args)} parameters. Consider reducing complexity.',
                            line_number=node.lineno,
                            suggestion='Consider using dataclasses or configuration objects'
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    # Check for missing class docstrings
                    if not ast.get_docstring(node):
                        issues.append(self.create_issue(
                            'documentation',
                            'medium',
                            f'Missing docstring for class {node.name}',
                            'Classes should have docstrings explaining their purpose',
                            line_number=node.lineno,
                            suggestion='Add a class docstring describing its purpose and usage'
                        ))
        
        except SyntaxError as e:
            issues.append(self.create_issue(
                'syntax',
                'critical',
                'Syntax error',
                f'Python syntax error: {str(e)}',
                line_number=e.lineno,
                suggestion='Fix the syntax error before proceeding'
            ))
        
        return issues
    
    async def _analyze_style(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Python code style (PEP 8)"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 79:
                issues.append(self.create_issue(
                    'style',
                    'low',
                    'Line too long',
                    f'Line {i} exceeds 79 characters ({len(line)} chars)',
                    line_number=i,
                    suggestion='Break long lines or use parentheses for continuation'
                ))
            
            # Check for improper indentation (not multiple of 4)
            if line.strip() and not line.startswith('#'):
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces % 4 != 0:
                    issues.append(self.create_issue(
                        'style',
                        'medium',
                        'Improper indentation',
                        'Python code should be indented with 4 spaces per level',
                        line_number=i,
                        suggestion='Use 4 spaces for each indentation level'
                    ))
            
            # Check for multiple imports on one line
            if re.match(r'import\s+\w+,', line):
                issues.append(self.create_issue(
                    'style',
                    'low',
                    'Multiple imports on one line',
                    'Imports should be on separate lines',
                    line_number=i,
                    suggestion='Put each import on a separate line'
                ))
            
            # Check for wildcard imports
            if re.match(r'from\s+.+\s+import\s+\*', line):
                issues.append(self.create_issue(
                    'style',
                    'medium',
                    'Wildcard import',
                    'Wildcard imports are discouraged as they pollute namespace',
                    line_number=i,
                    suggestion='Import specific names instead of using *'
                ))
        
        return issues
    
    async def _analyze_security(self, content: str) -> List[Dict[str, Any]]:
        """Analyze security vulnerabilities"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for eval() usage
            if re.search(r'\beval\s*\(', line):
                issues.append(self.create_issue(
                    'security',
                    'critical',
                    'Use of eval() function',
                    'eval() can execute arbitrary code and is a security risk',
                    line_number=i,
                    suggestion='Use safer alternatives like ast.literal_eval() for literals'
                ))
            
            # Check for exec() usage
            if re.search(r'\bexec\s*\(', line):
                issues.append(self.create_issue(
                    'security',
                    'critical',
                    'Use of exec() function',
                    'exec() can execute arbitrary code and is a security risk',
                    line_number=i,
                    suggestion='Avoid dynamic code execution or use safer alternatives'
                ))
            
            # Check for subprocess with shell=True
            if re.search(r'subprocess.*shell\s*=\s*True', line):
                issues.append(self.create_issue(
                    'security',
                    'high',
                    'Subprocess with shell=True',
                    'Using shell=True can lead to shell injection vulnerabilities',
                    line_number=i,
                    suggestion='Use shell=False and pass command as a list'
                ))
            
            # Check for hardcoded passwords/secrets
            if re.search(r'(password|secret|token|key)\s*=\s*[\'"][^\'"]+[\'"]', line, re.IGNORECASE):
                issues.append(self.create_issue(
                    'security',
                    'high',
                    'Hardcoded secret detected',
                    'Secrets should not be hardcoded in source code',
                    line_number=i,
                    suggestion='Use environment variables or secure configuration files'
                ))
            
            # Check for SQL concatenation
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*\+.*[\'"]', line, re.IGNORECASE):
                issues.append(self.create_issue(
                    'security',
                    'high',
                    'Potential SQL injection',
                    'SQL queries should use parameterized statements',
                    line_number=i,
                    suggestion='Use parameterized queries or ORM methods'
                ))
        
        return issues
    
    async def _analyze_performance(self, content: str) -> List[Dict[str, Any]]:
        """Analyze performance-related issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for string concatenation in loops
            if re.search(r'for\s+.*in.*:', line) and i < len(lines):
                next_lines = lines[i:i+5]  # Check next 5 lines
                for j, next_line in enumerate(next_lines):
                    if re.search(r'\w+\s*\+=\s*[\'"].*[\'"]', next_line):
                        issues.append(self.create_issue(
                            'performance',
                            'medium',
                            'String concatenation in loop',
                            'String concatenation in loops is inefficient',
                            line_number=i+j+1,
                            suggestion='Use list comprehension and join() or f-strings'
                        ))
                        break
            
            # Check for inefficient list operations
            if re.search(r'\.append\s*\([^)]*\)\s*$', line) and 'for ' in ''.join(lines[max(0, i-3):i]):
                issues.append(self.create_issue(
                    'performance',
                    'low',
                    'Consider list comprehension',
                    'List comprehensions are often more efficient than append in loops',
                    line_number=i,
                    suggestion='Consider using list comprehension instead'
                ))
            
            # Check for global variable usage
            if re.search(r'\bglobal\s+\w+', line):
                issues.append(self.create_issue(
                    'performance',
                    'low',
                    'Global variable usage',
                    'Global variables can impact performance and maintainability',
                    line_number=i,
                    suggestion='Consider passing variables as parameters'
                ))
        
        return issues
    
    async def _analyze_framework_specific(self, content: str) -> List[Dict[str, Any]]:
        """Analyze framework-specific issues"""
        issues = []
        
        # Django-specific checks
        if 'django' in content.lower():
            issues.extend(await self._analyze_django(content))
        
        # Flask-specific checks
        if 'flask' in content.lower():
            issues.extend(await self._analyze_flask(content))
        
        # FastAPI-specific checks
        if 'fastapi' in content.lower():
            issues.extend(await self._analyze_fastapi(content))
        
        return issues
    
    async def _analyze_django(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Django-specific issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for raw SQL queries
            if re.search(r'\.raw\s*\(', line):
                issues.append(self.create_issue(
                    'django',
                    'medium',
                    'Raw SQL query detected',
                    'Consider using Django ORM methods for better security and maintainability',
                    line_number=i,
                    suggestion='Use Django ORM queryset methods when possible'
                ))
            
            # Check for missing CSRF protection
            if re.search(r'@csrf_exempt', line):
                issues.append(self.create_issue(
                    'security',
                    'high',
                    'CSRF protection disabled',
                    'Disabling CSRF protection can lead to security vulnerabilities',
                    line_number=i,
                    suggestion='Only disable CSRF for API endpoints, consider using proper authentication'
                ))
        
        return issues
    
    async def _analyze_flask(self, content: str) -> List[Dict[str, Any]]:
        """Analyze Flask-specific issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for debug mode in production
            if re.search(r'app\.run.*debug\s*=\s*True', line):
                issues.append(self.create_issue(
                    'security',
                    'critical',
                    'Debug mode enabled',
                    'Debug mode should never be enabled in production',
                    line_number=i,
                    suggestion='Set debug=False for production deployment'
                ))
            
            # Check for missing error handling
            if re.search(r'@app\.route', line) and i < len(lines):
                route_lines = lines[i:i+20]  # Check next 20 lines for try/except
                has_error_handling = any('try:' in route_line or 'except' in route_line 
                                       for route_line in route_lines)
                if not has_error_handling:
                    issues.append(self.create_issue(
                        'reliability',
                        'medium',
                        'Missing error handling in route',
                        'Flask routes should have proper error handling',
                        line_number=i,
                        suggestion='Add try/except blocks to handle potential errors'
                    ))
        
        return issues
    
    async def _analyze_fastapi(self, content: str) -> List[Dict[str, Any]]:
        """Analyze FastAPI-specific issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for missing type hints
            if re.search(r'@app\.(get|post|put|delete)', line) and i < len(lines):
                func_line = lines[i] if i < len(lines) else ""
                if 'def ' in func_line and '->' not in func_line:
                    issues.append(self.create_issue(
                        'fastapi',
                        'medium',
                        'Missing return type annotation',
                        'FastAPI endpoints should have return type annotations',
                        line_number=i+1,
                        suggestion='Add return type annotation to the function'
                    ))
        
        return issues
    
    async def _suggest_optimizations(self, content: str) -> List[Dict[str, Any]]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Suggest type hints if missing
        if 'typing import' not in content and 'def ' in content:
            suggestions.append(self.create_suggestion(
                'maintainability',
                'Add type hints',
                'Type hints improve code readability and IDE support',
                impact='medium',
                effort='low'
            ))
        
        # Suggest dataclasses for simple classes
        if re.search(r'class\s+\w+.*:\s*\n\s*def\s+__init__', content):
            suggestions.append(self.create_suggestion(
                'maintainability',
                'Consider using dataclasses',
                'Dataclasses can reduce boilerplate code for simple data containers',
                impact='medium',
                effort='low'
            ))
        
        return suggestions
    
    async def _suggest_best_practices(self, content: str) -> List[Dict[str, Any]]:
        """Generate best practice suggestions"""
        suggestions = []
        
        # Suggest logging instead of print statements
        if 'print(' in content:
            suggestions.append(self.create_suggestion(
                'best_practice',
                'Use logging instead of print',
                'Logging provides better control over output and log levels',
                impact='medium',
                effort='low'
            ))
        
        # Suggest context managers for file operations
        if re.search(r'open\s*\(', content) and 'with ' not in content:
            suggestions.append(self.create_suggestion(
                'best_practice',
                'Use context managers for file operations',
                'Context managers ensure proper resource cleanup',
                impact='high',
                effort='low'
            ))
        
        return suggestions
    
    async def _generate_tests_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Python unit tests"""
        file_path = context.get('file_path', '')
        content = context.get('content', '')
        
        # Extract function and class information
        functions = self._extract_functions(content)
        classes = self._extract_classes(content)
        
        # Generate test code
        test_code = self._generate_python_test_code(functions, classes)
        test_file_path = file_path.replace('.py', '_test.py')
        
        coverage_areas = ['function_testing']
        if classes:
            coverage_areas.append('class_testing')
        
        return {
            'test_code': test_code,
            'test_file_path': test_file_path,
            'coverage_areas': coverage_areas,
            'test_cases': self._generate_test_cases(functions, classes),
            'explanation': f'Generated unit tests for {len(functions)} functions and {len(classes)} classes',
            'confidence_score': 0.8,
            'framework': 'pytest',
            'dependencies': ['pytest', 'pytest-mock'],
            'metadata': {
                'functions_count': len(functions),
                'classes_count': len(classes)
            }
        }
    
    async def _optimize_code_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Python-specific optimizations"""
        content = context.get('content', '')
        optimizations = []
        
        # List comprehension optimization
        if re.search(r'for\s+\w+\s+in.*:\s*\n\s*\w+\.append\(', content):
            optimizations.append({
                'type': 'performance',
                'title': 'Use list comprehension',
                'description': 'Replace loop with list comprehension for better performance',
                'before': 'for item in items:\n    result.append(transform(item))',
                'after': 'result = [transform(item) for item in items]',
                'impact': 'medium',
                'effort': 'low',
                'auto_applicable': True
            })
        
        return {
            'optimizations': optimizations,
            'metrics': {'potential_performance_gain': '10-25%'},
            'confidence_score': 0.75,
            'metadata': {'optimization_type': 'python_performance'}
        }
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle Python-specific chat requests"""
        message = context.get('message', '').lower()
        content = context.get('content', '')
        
        if 'performance' in message:
            return self._generate_performance_advice(content)
        elif 'security' in message:
            return self._generate_security_advice(content)
        elif 'testing' in message:
            return self._generate_testing_advice(content)
        else:
            return "As a Python expert, I can help with performance optimization, security best practices, testing strategies, and framework-specific guidance for Django, Flask, and FastAPI. What would you like to know?"
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extract function names from Python code"""
        functions = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            functions = re.findall(r'def\s+(\w+)\s*\(', content)
        
        return functions
    
    def _extract_classes(self, content: str) -> List[str]:
        """Extract class names from Python code"""
        classes = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
        except SyntaxError:
            # Fallback to regex if AST parsing fails
            classes = re.findall(r'class\s+(\w+)', content)
        
        return classes
    
    def _generate_python_test_code(self, functions: List[str], classes: List[str]) -> str:
        """Generate Python test code"""
        test_code = "import pytest\nfrom unittest.mock import Mock, patch\n\n"
        
        # Import the module being tested
        test_code += "# Import your module here\n# from your_module import function_name, ClassName\n\n"
        
        # Generate function tests
        for func in functions[:5]:  # Limit to first 5 functions
            test_code += f"""def test_{func}():
    \"\"\"Test {func} function.\"\"\"
    # Arrange
    # Act
    result = {func}()
    # Assert
    assert result is not None
    # Add more specific assertions

"""
        
        # Generate class tests
        for cls in classes[:3]:  # Limit to first 3 classes
            test_code += f"""class Test{cls}:
    \"\"\"Test {cls} class.\"\"\"
    
    def test_init(self):
        \"\"\"Test {cls} initialization.\"\"\"
        instance = {cls}()
        assert instance is not None
    
    def test_methods(self):
        \"\"\"Test {cls} methods.\"\"\"
        instance = {cls}()
        # Add method tests here

"""
        
        return test_code
    
    def _generate_test_cases(self, functions: List[str], classes: List[str]) -> List[Dict[str, Any]]:
        """Generate test case descriptions"""
        test_cases = []
        
        for func in functions:
            test_cases.append({
                'name': f'test_{func}',
                'description': f'Test {func} function behavior'
            })
        
        for cls in classes:
            test_cases.append({
                'name': f'test_{cls}_init',
                'description': f'Test {cls} class initialization'
            })
        
        return test_cases
    
    def _generate_performance_advice(self, content: str) -> str:
        """Generate performance advice"""
        advice = "Python Performance Tips:\n"
        advice += "• Use list comprehensions instead of loops where possible\n"
        advice += "• Avoid string concatenation in loops; use join() instead\n"
        advice += "• Use generators for memory-efficient iteration\n"
        advice += "• Profile your code with cProfile to identify bottlenecks"
        return advice
    
    def _generate_security_advice(self, content: str) -> str:
        """Generate security advice"""
        advice = "Python Security Best Practices:\n"
        advice += "• Never use eval() or exec() with user input\n"
        advice += "• Use parameterized queries to prevent SQL injection\n"
        advice += "• Store secrets in environment variables, not in code\n"
        advice += "• Validate and sanitize all user inputs"
        return advice
    
    def _generate_testing_advice(self, content: str) -> str:
        """Generate testing advice"""
        advice = "Python Testing Strategy:\n"
        advice += "• Write unit tests for individual functions and methods\n"
        advice += "• Use pytest for a modern testing framework\n"
        advice += "• Mock external dependencies and API calls\n"
        advice += "• Aim for high test coverage but focus on critical paths"
        return advice
    
    def _calculate_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for analysis"""
        base_score = 0.8
        
        # Higher confidence for valid Python syntax
        try:
            ast.parse(content)
            base_score += 0.1
        except SyntaxError:
            base_score -= 0.2
        
        # Adjust based on file size and complexity
        lines = len(content.split('\n'))
        if lines > 50:
            base_score += 0.1
        
        return max(0.0, min(base_score, 1.0)) 