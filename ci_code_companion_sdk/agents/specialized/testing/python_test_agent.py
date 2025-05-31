"""
Python Test Agent - Specialized for Python Testing

This agent focuses exclusively on Python test generation, test analysis, and testing
best practices. It provides expert guidance for pytest, unittest, mocking, fixtures,
integration testing, and other Python testing tools and patterns.
"""

import re
import ast
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class PythonTestAgent(BaseAgent):
    """
    Specialized agent for Python testing and test generation.
    Focuses on pytest, unittest, mocking, and testing best practices.
    """
    
    def _initialize(self):
        """Initialize Python Test Agent with specialized configuration"""
        super()._initialize()
        self.name = "python_test"
        self.version = "2.0.0"
        
        # Python testing framework patterns
        self.test_patterns = {
            'pytest_function': r'def\s+test_[\w_]+\s*\(',
            'unittest_class': r'class\s+Test[\w_]+\s*\(\s*unittest\.TestCase\s*\)',
            'unittest_method': r'def\s+test_[\w_]+\s*\(\s*self\s*\)',
            'pytest_fixture': r'@pytest\.fixture',
            'pytest_parametrize': r'@pytest\.mark\.parametrize',
            'pytest_mark': r'@pytest\.mark\.\w+',
            'mock_usage': r'(?:mock\.|Mock\(|MagicMock\(|patch\()',
            'assert_statement': r'assert\s+',
            'unittest_assert': r'self\.assert\w+\s*\(',
            'pytest_raises': r'pytest\.raises\s*\(',
            'test_setup': r'def\s+(?:setUp|setup_method|setup_function)\s*\(',
            'test_teardown': r'def\s+(?:tearDown|teardown_method|teardown_function)\s*\(',
            'conftest_file': r'conftest\.py$',
            'test_discovery': r'test_.*\.py$|.*_test\.py$'
        }
        
        # Testing best practices indicators
        self.quality_indicators = {
            'has_fixtures': False,
            'has_parametrization': False,
            'uses_mocking': False,
            'has_setup_teardown': False,
            'tests_exceptions': False,
            'uses_proper_assertions': False,
            'has_integration_tests': False,
            'has_docstrings': False
        }
        
        # Framework-specific patterns
        self.framework_patterns = {
            'pytest': {
                'fixtures': r'@pytest\.fixture',
                'parametrize': r'@pytest\.mark\.parametrize',
                'markers': r'@pytest\.mark\.',
                'config': r'pytest\.ini|pyproject\.toml',
                'plugins': r'pytest_\w+',
                'conftest': r'conftest\.py'
            },
            'unittest': {
                'test_case': r'unittest\.TestCase',
                'assertions': r'self\.assert\w+',
                'setup': r'def\s+setUp\s*\(',
                'teardown': r'def\s+tearDown\s*\(',
                'mock': r'unittest\.mock',
                'skip': r'@unittest\.skip'
            },
            'django': {
                'test_case': r'django\.test\.TestCase',
                'client': r'self\.client\.',
                'fixtures': r'fixtures\s*=',
                'test_runner': r'TEST_RUNNER',
                'database': r'@override_settings'
            },
            'flask': {
                'test_client': r'app\.test_client\(\)',
                'test_config': r'TESTING\s*=\s*True',
                'fixture': r'@pytest\.fixture.*app',
                'client_fixture': r'client\s*\(\s*app\s*\)'
            }
        }
        
        # Coverage and quality patterns
        self.coverage_patterns = {
            'coverage_import': r'import\s+coverage|from\s+coverage',
            'coverage_config': r'\.coveragerc|coverage\.xml',
            'pytest_cov': r'pytest-cov',
            'coverage_report': r'coverage\s+report',
            'branch_coverage': r'--cov-branch',
            'missing_lines': r'--cov-report=missing'
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Python Test Agent capabilities"""
        return [
            AgentCapability.TEST_GENERATION,
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported test file types"""
        return ['.py']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported testing frameworks"""
        return ['pytest', 'unittest', 'nose2', 'django-test', 'flask-test', 'tox']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Python test files for best practices and completeness.
        
        Args:
            file_path: Path to test file
            content: Test file content
            context: Analysis context
            
        Returns:
            Dictionary containing test analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract test metadata
        metadata = self.extract_metadata(file_path, content)
        metadata.update(await self._extract_test_metadata(content))
        
        # Analyze test structure and quality
        issues.extend(await self._analyze_test_structure(content))
        issues.extend(await self._analyze_test_patterns(content))
        issues.extend(await self._analyze_assertions(content))
        issues.extend(await self._analyze_mocking_usage(content))
        issues.extend(await self._analyze_fixtures_and_setup(content))
        
        # Generate test improvement suggestions
        suggestions.extend(await self._suggest_test_improvements(content))
        suggestions.extend(await self._suggest_coverage_improvements(content, context))
        suggestions.extend(await self._suggest_best_practices(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_test_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_test_metadata(self, content: str) -> Dict[str, Any]:
        """Extract test-specific metadata"""
        metadata = {
            'test_framework': 'unknown',
            'test_functions': [],
            'test_classes': [],
            'fixtures': [],
            'mocked_objects': [],
            'parametrized_tests': [],
            'test_markers': [],
            'assertion_count': 0,
            'setup_methods': [],
            'teardown_methods': [],
            'coverage_usage': False,
            'test_types': []
        }
        
        # Detect testing framework
        if 'pytest' in content:
            metadata['test_framework'] = 'pytest'
        elif 'unittest' in content:
            metadata['test_framework'] = 'unittest'
        elif 'django.test' in content:
            metadata['test_framework'] = 'django'
        elif 'nose' in content:
            metadata['test_framework'] = 'nose'
        
        # Extract test functions and classes using AST
        try:
            tree = ast.parse(content)
            metadata.update(self._extract_ast_metadata(tree, content))
        except SyntaxError:
            # Fall back to regex if AST parsing fails
            metadata.update(self._extract_regex_metadata(content))
        
        # Determine test types
        metadata['test_types'] = self._categorize_tests(content)
        
        # Check for coverage usage
        metadata['coverage_usage'] = any(
            re.search(pattern, content) for pattern in self.coverage_patterns.values()
        )
        
        return metadata
    
    def _extract_ast_metadata(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """Extract metadata using AST analysis"""
        metadata = {
            'test_functions': [],
            'test_classes': [],
            'fixtures': [],
            'assertion_count': 0,
            'setup_methods': [],
            'teardown_methods': []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_'):
                    metadata['test_functions'].append(node.name)
                elif node.name in ['setUp', 'setup_method', 'setup_function']:
                    metadata['setup_methods'].append(node.name)
                elif node.name in ['tearDown', 'teardown_method', 'teardown_function']:
                    metadata['teardown_methods'].append(node.name)
                
                # Check for pytest fixtures
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Attribute) and decorator.attr == 'fixture':
                        metadata['fixtures'].append(node.name)
                    elif isinstance(decorator, ast.Name) and decorator.id == 'fixture':
                        metadata['fixtures'].append(node.name)
            
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith('Test') or any(
                    isinstance(base, ast.Attribute) and base.attr == 'TestCase'
                    for base in node.bases
                ):
                    metadata['test_classes'].append(node.name)
            
            elif isinstance(node, ast.Assert):
                metadata['assertion_count'] += 1
        
        return metadata
    
    def _extract_regex_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata using regex patterns"""
        metadata = {
            'test_functions': [],
            'test_classes': [],
            'fixtures': [],
            'assertion_count': 0
        }
        
        # Extract test functions
        test_func_matches = re.findall(self.test_patterns['pytest_function'], content)
        unittest_func_matches = re.findall(self.test_patterns['unittest_method'], content)
        metadata['test_functions'] = test_func_matches + unittest_func_matches
        
        # Extract test classes
        test_class_matches = re.findall(self.test_patterns['unittest_class'], content)
        metadata['test_classes'] = test_class_matches
        
        # Extract fixtures
        fixture_matches = re.findall(r'@pytest\.fixture[^)]*\)\s*def\s+(\w+)', content)
        metadata['fixtures'] = fixture_matches
        
        # Count assertions
        assertion_matches = re.findall(self.test_patterns['assert_statement'], content)
        unittest_assertion_matches = re.findall(self.test_patterns['unittest_assert'], content)
        metadata['assertion_count'] = len(assertion_matches) + len(unittest_assertion_matches)
        
        return metadata
    
    async def _analyze_test_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze test structure and organization"""
        issues = []
        lines = content.split('\n')
        
        # Check for test naming conventions
        test_functions = re.findall(r'def\s+(test_\w+)\s*\(', content)
        for func_name in test_functions:
            if not self._is_good_test_name(func_name):
                issues.append(self.create_issue(
                    'test_naming',
                    'low',
                    'Poor test naming convention',
                    f'Test function "{func_name}" should describe what is being tested',
                    suggestion='Use descriptive names like test_should_return_success_when_valid_input'
                ))
        
        # Check for empty test functions
        for i, line in enumerate(lines, 1):
            if re.search(r'def\s+test_\w+\s*\([^)]*\):\s*$', line):
                # Check if next few lines are empty or just pass
                next_lines = lines[i:i+3]
                if all(not line.strip() or line.strip() == 'pass' for line in next_lines):
                    issues.append(self.create_issue(
                        'test_implementation',
                        'high',
                        'Empty test function',
                        'Test function has no implementation',
                        line_number=i,
                        suggestion='Implement the test or remove it'
                    ))
        
        # Check for test file organization
        test_count = len(test_functions)
        if test_count > 25:
            issues.append(self.create_issue(
                'test_organization',
                'medium',
                'Large test file',
                f'Test file contains {test_count} tests. Consider splitting into multiple files.',
                suggestion='Group related tests into separate test files or classes'
            ))
        
        return issues
    
    async def _analyze_test_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze testing patterns and practices"""
        issues = []
        lines = content.split('\n')
        
        # Check for proper test isolation
        global_state_patterns = [
            r'global\s+\w+',
            r'^\s*\w+\s*=\s*\[',  # Global list assignments
            r'^\s*\w+\s*=\s*\{',  # Global dict assignments
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in global_state_patterns:
                if re.search(pattern, line) and not line.strip().startswith('#'):
                    issues.append(self.create_issue(
                        'test_isolation',
                        'medium',
                        'Potential shared state between tests',
                        'Global state can cause tests to interfere with each other',
                        line_number=i,
                        suggestion='Use fixtures or setup methods to create fresh state for each test'
                    ))
        
        # Check for hardcoded values
        for i, line in enumerate(lines, 1):
            if re.search(r'assert\s+\w+\s*==\s*[\'"]\w+[\'"]', line):
                issues.append(self.create_issue(
                    'test_maintenance',
                    'low',
                    'Hardcoded assertion value',
                    'Hardcoded values make tests brittle and hard to maintain',
                    line_number=i,
                    suggestion='Use constants or fixtures for test data'
                ))
        
        # Check for sleep/wait in tests
        for i, line in enumerate(lines, 1):
            if re.search(r'time\.sleep\s*\(|time\.wait\s*\(', line):
                issues.append(self.create_issue(
                    'test_reliability',
                    'high',
                    'Sleep/wait in test',
                    'Sleep statements make tests slow and unreliable',
                    line_number=i,
                    suggestion='Use proper synchronization or mocking instead of sleep'
                ))
        
        return issues
    
    async def _analyze_assertions(self, content: str) -> List[Dict[str, Any]]:
        """Analyze assertion quality and patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for tests without assertions
        test_functions = self._extract_test_functions(content)
        for func_name, func_content in test_functions.items():
            if not re.search(r'assert\s+|self\.assert\w+', func_content):
                issues.append(self.create_issue(
                    'missing_assertions',
                    'high',
                    'Test without assertions',
                    f'Test function "{func_name}" has no assertions',
                    suggestion='Add assertions to verify expected behavior'
                ))
        
        # Check for weak assertions
        weak_patterns = [
            r'assert\s+True',
            r'assert\s+\w+',  # Single variable assertion
            r'self\.assertTrue\s*\(\s*True\s*\)',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in weak_patterns:
                if re.search(pattern, line):
                    issues.append(self.create_issue(
                        'weak_assertion',
                        'medium',
                        'Weak or generic assertion',
                        'Use specific assertions that verify expected behavior',
                        line_number=i,
                        suggestion='Use specific assertions like assertEqual, assertIn, etc.'
                    ))
        
        # Check for multiple assertions in one test
        for func_name, func_content in test_functions.items():
            assertion_count = len(re.findall(r'assert\s+|self\.assert\w+', func_content))
            if assertion_count > 5:
                issues.append(self.create_issue(
                    'multiple_assertions',
                    'medium',
                    'Too many assertions in one test',
                    f'Test "{func_name}" has {assertion_count} assertions. Consider splitting.',
                    suggestion='Split into multiple focused tests, each testing one behavior'
                ))
        
        return issues
    
    async def _analyze_mocking_usage(self, content: str) -> List[Dict[str, Any]]:
        """Analyze mocking patterns and usage"""
        issues = []
        lines = content.split('\n')
        
        # Check for external dependencies without mocking
        external_patterns = [
            r'requests\.(?:get|post|put|delete)',
            r'urllib\.request',
            r'socket\.',
            r'subprocess\.',
            r'os\.system',
            r'open\s*\([\'"][^\'\"]*[\'"]',
        ]
        
        has_mocking = bool(re.search(self.test_patterns['mock_usage'], content))
        
        for i, line in enumerate(lines, 1):
            for pattern in external_patterns:
                if re.search(pattern, line) and not has_mocking:
                    issues.append(self.create_issue(
                        'missing_mocking',
                        'high',
                        'External dependency without mocking',
                        'Tests should mock external dependencies for reliability and speed',
                        line_number=i,
                        suggestion='Use unittest.mock or pytest-mock to mock external calls'
                    ))
                    break
        
        # Check for over-mocking
        if has_mocking:
            mock_count = len(re.findall(self.test_patterns['mock_usage'], content))
            total_lines = len([line for line in lines if line.strip()])
            if mock_count / total_lines > 0.3:  # More than 30% of lines involve mocking
                issues.append(self.create_issue(
                    'over_mocking',
                    'medium',
                    'Excessive mocking detected',
                    'Too much mocking can make tests complex and brittle',
                    suggestion='Consider testing at a higher level or simplifying the code under test'
                ))
        
        return issues
    
    async def _analyze_fixtures_and_setup(self, content: str) -> List[Dict[str, Any]]:
        """Analyze fixture and setup/teardown usage"""
        issues = []
        
        # Check for repeated setup code
        test_functions = self._extract_test_functions(content)
        common_setup_patterns = []
        
        for func_content in test_functions.values():
            setup_lines = func_content.split('\n')[:5]  # First 5 lines typically setup
            for line in setup_lines:
                if '=' in line and 'assert' not in line:
                    common_setup_patterns.append(line.strip())
        
        # If same setup appears in multiple tests, suggest fixture
        from collections import Counter
        setup_counts = Counter(common_setup_patterns)
        repeated_setup = [setup for setup, count in setup_counts.items() if count > 2]
        
        if repeated_setup:
            issues.append(self.create_issue(
                'repeated_setup',
                'medium',
                'Repeated setup code detected',
                'Common setup code should be extracted into fixtures or setup methods',
                suggestion='Create pytest fixtures or setUp methods for common test setup'
            ))
        
        # Check for missing cleanup
        if 'open(' in content and 'close()' not in content and 'with open' not in content:
            issues.append(self.create_issue(
                'resource_cleanup',
                'medium',
                'Missing resource cleanup',
                'Tests should properly clean up resources like files',
                suggestion='Use context managers (with statements) or tearDown methods'
            ))
        
        return issues
    
    async def _suggest_test_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest improvements for test quality"""
        suggestions = []
        
        # Suggest parametrized tests
        if 'test_' in content and '@pytest.mark.parametrize' not in content:
            # Look for similar test functions that could be parametrized
            test_functions = re.findall(r'def\s+(test_\w+)', content)
            similar_tests = self._find_similar_test_names(test_functions)
            
            if similar_tests:
                suggestions.append(self.create_suggestion(
                    'parametrization',
                    'Use parametrized tests',
                    'Similar test functions could be combined using pytest.mark.parametrize',
                    impact='medium',
                    effort='low'
                ))
        
        # Suggest property-based testing
        if 'test_' in content and 'hypothesis' not in content:
            suggestions.append(self.create_suggestion(
                'property_testing',
                'Consider property-based testing',
                'Use Hypothesis for more thorough testing with generated test data',
                impact='high',
                effort='medium'
            ))
        
        # Suggest test factories
        if len(re.findall(r'def\s+test_', content)) > 10:
            suggestions.append(self.create_suggestion(
                'test_factories',
                'Use test data factories',
                'Create factories for test data generation to reduce duplication',
                impact='medium',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_coverage_improvements(self, content: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest improvements for test coverage"""
        suggestions = []
        
        # Get source code info from context if available
        source_info = context.get('previous_results', {}).get('code_analysis', {})
        
        # Suggest integration tests
        if 'unit' in content.lower() and 'integration' not in content.lower():
            suggestions.append(self.create_suggestion(
                'test_coverage',
                'Add integration tests',
                'Complement unit tests with integration tests for end-to-end scenarios',
                impact='high',
                effort='high'
            ))
        
        # Suggest edge case testing
        if 'test_' in content and ('edge' not in content.lower() and 'boundary' not in content.lower()):
            suggestions.append(self.create_suggestion(
                'edge_cases',
                'Test edge cases and boundaries',
                'Add tests for edge cases, error conditions, and boundary values',
                impact='high',
                effort='medium'
            ))
        
        # Suggest performance testing
        if source_info and 'performance' not in content.lower():
            suggestions.append(self.create_suggestion(
                'performance_testing',
                'Add performance tests',
                'Include performance tests for critical code paths',
                impact='medium',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_best_practices(self, content: str) -> List[Dict[str, Any]]:
        """Suggest testing best practices"""
        suggestions = []
        
        # Suggest test documentation
        if 'def test_' in content and '"""' not in content:
            suggestions.append(self.create_suggestion(
                'test_documentation',
                'Add test docstrings',
                'Document test purpose and expected behavior with docstrings',
                impact='low',
                effort='low'
            ))
        
        # Suggest coverage reporting
        if 'test_' in content and 'coverage' not in content.lower():
            suggestions.append(self.create_suggestion(
                'coverage_reporting',
                'Add coverage reporting',
                'Use pytest-cov or coverage.py to track test coverage',
                impact='medium',
                effort='low'
            ))
        
        # Suggest test markers
        if 'pytest' in content and '@pytest.mark' not in content:
            suggestions.append(self.create_suggestion(
                'test_markers',
                'Use pytest markers',
                'Use markers to categorize tests (slow, integration, unit, etc.)',
                impact='low',
                effort='low'
            ))
        
        return suggestions
    
    async def generate_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive test cases for Python code.
        
        Args:
            context: Context containing source code information
            
        Returns:
            Dictionary containing generated test code and metadata
        """
        file_path = context.get('file_path', '')
        content = context.get('content', '')
        
        if not content:
            return {
                'test_code': '# No source code provided for test generation',
                'test_file_path': '',
                'coverage_areas': [],
                'explanation': 'Cannot generate tests without source code content',
                'confidence_score': 0.0
            }
        
        # Analyze source code
        functions = self._extract_source_functions(content)
        classes = self._extract_source_classes(content)
        imports = self._extract_imports(content)
        
        # Generate test code
        test_code = self._generate_comprehensive_test_code(
            functions, classes, imports, content, file_path
        )
        
        # Determine test file path
        test_file_path = self._generate_test_file_path(file_path)
        
        # Define coverage areas
        coverage_areas = self._define_coverage_areas(content, functions, classes)
        
        return {
            'test_code': test_code,
            'test_file_path': test_file_path,
            'coverage_areas': coverage_areas,
            'explanation': f'Generated comprehensive test suite for {len(functions)} functions and {len(classes)} classes',
            'confidence_score': self._calculate_generation_confidence(content),
            'metadata': {
                'functions_count': len(functions),
                'classes_count': len(classes),
                'framework': 'pytest',
                'test_types': ['unit', 'integration', 'edge_cases']
            }
        }
    
    def _extract_test_functions(self, content: str) -> Dict[str, str]:
        """Extract individual test functions for analysis"""
        test_functions = {}
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    func_lines = content.split('\n')[node.lineno-1:node.end_lineno]
                    test_functions[node.name] = '\n'.join(func_lines)
        except:
            # Fall back to regex
            lines = content.split('\n')
            current_func = None
            current_lines = []
            indent_level = 0
            
            for line in lines:
                if re.match(r'\s*def\s+test_\w+', line):
                    if current_func:
                        test_functions[current_func] = '\n'.join(current_lines)
                    current_func = re.search(r'def\s+(test_\w+)', line).group(1)
                    current_lines = [line]
                    indent_level = len(line) - len(line.lstrip())
                elif current_func:
                    line_indent = len(line) - len(line.lstrip()) if line.strip() else indent_level + 1
                    if line.strip() and line_indent <= indent_level:
                        test_functions[current_func] = '\n'.join(current_lines)
                        current_func = None
                        current_lines = []
                    else:
                        current_lines.append(line)
            
            if current_func:
                test_functions[current_func] = '\n'.join(current_lines)
        
        return test_functions
    
    def _is_good_test_name(self, test_name: str) -> bool:
        """Check if test name follows good practices"""
        good_patterns = [
            r'test_should_\w+_when_\w+',
            r'test_\w+_returns_\w+',
            r'test_\w+_raises_\w+',
            r'test_\w+_with_\w+',
        ]
        
        return any(re.match(pattern, test_name) for pattern in good_patterns) or len(test_name) > 15
    
    def _find_similar_test_names(self, test_functions: List[str]) -> List[str]:
        """Find test functions with similar names that could be parametrized"""
        similar_groups = {}
        
        for func_name in test_functions:
            # Extract base name (remove numbers, specific values)
            base_name = re.sub(r'_\d+$|_with_\w+$|_when_\w+$', '', func_name)
            if base_name not in similar_groups:
                similar_groups[base_name] = []
            similar_groups[base_name].append(func_name)
        
        return [group for group in similar_groups.values() if len(group) > 2]
    
    def _categorize_tests(self, content: str) -> List[str]:
        """Categorize tests by type"""
        test_types = []
        
        if re.search(r'def\s+test_', content):
            test_types.append('unit')
        
        if re.search(r'integration|end_to_end|e2e', content.lower()):
            test_types.append('integration')
        
        if re.search(r'mock|patch|Mock', content):
            test_types.append('mocked')
        
        if re.search(r'@pytest\.mark\.parametrize', content):
            test_types.append('parametrized')
        
        if re.search(r'performance|benchmark|timing', content.lower()):
            test_types.append('performance')
        
        return test_types or ['unknown']
    
    def _extract_source_functions(self, content: str) -> List[Dict[str, Any]]:
        """Extract function information from source code"""
        functions = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    func_info = {
                        'name': node.name,
                        'args': [arg.arg for arg in node.args.args],
                        'returns': node.returns is not None,
                        'docstring': ast.get_docstring(node),
                        'line_number': node.lineno
                    }
                    functions.append(func_info)
        except:
            # Fall back to regex
            func_matches = re.findall(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)', content)
            functions = [{'name': name, 'args': [], 'returns': False, 'docstring': None} for name in func_matches]
        
        return functions
    
    def _extract_source_classes(self, content: str) -> List[Dict[str, Any]]:
        """Extract class information from source code"""
        classes = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    class_info = {
                        'name': node.name,
                        'methods': methods,
                        'docstring': ast.get_docstring(node),
                        'line_number': node.lineno
                    }
                    classes.append(class_info)
        except:
            # Fall back to regex
            class_matches = re.findall(r'class\s+([A-Z][a-zA-Z0-9_]*)', content)
            classes = [{'name': name, 'methods': [], 'docstring': None} for name in class_matches]
        
        return classes
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extract import statements from source code"""
        imports = []
        import_patterns = [
            r'import\s+([\w.]+)',
            r'from\s+([\w.]+)\s+import',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content)
            imports.extend(matches)
        
        return list(set(imports))
    
    def _generate_comprehensive_test_code(
        self, 
        functions: List[Dict[str, Any]], 
        classes: List[Dict[str, Any]], 
        imports: List[str],
        content: str,
        file_path: str
    ) -> str:
        """Generate comprehensive test code"""
        
        module_name = file_path.replace('.py', '').replace('/', '.')
        
        test_imports = f'''"""
Tests for {module_name}

Generated comprehensive test suite covering:
- Unit tests for all public functions and methods
- Edge cases and error conditions
- Integration scenarios
- Mocking external dependencies
"""

import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock
import sys
import os

# Import the module under test
{f"from {module_name} import *" if module_name else "# Import statements here"}

'''
        
        # Generate fixtures
        fixtures = '''
@pytest.fixture
def sample_data():
    """Fixture providing sample test data"""
    return {
        'test_string': 'hello world',
        'test_number': 42,
        'test_list': [1, 2, 3],
        'test_dict': {'key': 'value'}
    }

@pytest.fixture
def mock_external_service():
    """Fixture for mocking external services"""
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'success': True}
        yield mock_get

'''
        
        # Generate function tests
        function_tests = ''
        for func in functions:
            function_tests += self._generate_function_tests(func)
        
        # Generate class tests
        class_tests = ''
        for cls in classes:
            class_tests += self._generate_class_tests(cls)
        
        # Generate integration tests
        integration_tests = '''
class TestIntegration:
    """Integration tests for end-to-end scenarios"""
    
    def test_complete_workflow(self, sample_data):
        """Test complete workflow integration"""
        # TODO: Implement end-to-end workflow test
        pass
    
    def test_error_handling_integration(self):
        """Test error handling across components"""
        # TODO: Implement error handling integration test
        pass

'''
        
        return test_imports + fixtures + function_tests + class_tests + integration_tests
    
    def _generate_function_tests(self, func: Dict[str, Any]) -> str:
        """Generate tests for a function"""
        func_name = func['name']
        
        return f'''
class Test{func_name.title()}:
    """Tests for {func_name} function"""
    
    def test_{func_name}_with_valid_input(self, sample_data):
        """Test {func_name} with valid input"""
        # Arrange
        # TODO: Set up test data
        
        # Act
        result = {func_name}(sample_data['test_string'])
        
        # Assert
        assert result is not None
        # TODO: Add specific assertions
    
    def test_{func_name}_with_invalid_input(self):
        """Test {func_name} with invalid input"""
        # Arrange
        invalid_input = None
        
        # Act & Assert
        with pytest.raises(ValueError):
            {func_name}(invalid_input)
    
    def test_{func_name}_edge_cases(self):
        """Test {func_name} with edge cases"""
        # Test empty input
        result = {func_name}("")
        assert result is not None
        
        # Test boundary values
        # TODO: Add boundary value tests
    
    @pytest.mark.parametrize("input_value,expected", [
        ("test1", "expected1"),
        ("test2", "expected2"),
        ("test3", "expected3"),
    ])
    def test_{func_name}_parametrized(self, input_value, expected):
        """Parametrized test for {func_name}"""
        result = {func_name}(input_value)
        assert result == expected

'''
    
    def _generate_class_tests(self, cls: Dict[str, Any]) -> str:
        """Generate tests for a class"""
        class_name = cls['name']
        
        tests = f'''
class Test{class_name}:
    """Tests for {class_name} class"""
    
    @pytest.fixture
    def {class_name.lower()}_instance(self):
        """Fixture providing {class_name} instance"""
        return {class_name}()
    
    def test_{class_name.lower()}_initialization(self):
        """Test {class_name} initialization"""
        instance = {class_name}()
        assert instance is not None
        # TODO: Add initialization assertions
    
'''
        
        # Generate tests for each method
        for method in cls['methods']:
            if not method.startswith('_'):  # Skip private methods
                tests += f'''
    def test_{method}(self, {class_name.lower()}_instance):
        """Test {method} method"""
        # Arrange
        # TODO: Set up test data
        
        # Act
        result = {class_name.lower()}_instance.{method}()
        
        # Assert
        assert result is not None
        # TODO: Add specific assertions
    
'''
        
        return tests
    
    def _generate_test_file_path(self, source_file_path: str) -> str:
        """Generate appropriate test file path"""
        if not source_file_path:
            return 'test_module.py'
        
        if source_file_path.endswith('.py'):
            return f"test_{source_file_path}"
        return f"test_{source_file_path}.py"
    
    def _define_coverage_areas(self, content: str, functions: List, classes: List) -> List[str]:
        """Define what areas the tests should cover"""
        coverage_areas = ['function_testing', 'class_testing']
        
        if functions:
            coverage_areas.append('unit_testing')
        
        if classes:
            coverage_areas.append('object_testing')
        
        if 'import' in content:
            coverage_areas.append('integration_testing')
        
        if any(keyword in content for keyword in ['def __init__', 'class']):
            coverage_areas.append('initialization_testing')
        
        coverage_areas.extend(['edge_cases', 'error_handling', 'parametrized_testing'])
        
        return coverage_areas
    
    def _calculate_test_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for test analysis"""
        base_confidence = 0.7
        
        # Boost confidence for good test practices
        if 'pytest' in content or 'unittest' in content:
            base_confidence += 0.1
        if '@pytest.fixture' in content:
            base_confidence += 0.1
        if 'mock' in content.lower():
            base_confidence += 0.1
        
        # Reduce confidence for issues
        if len(issues) > 5:
            base_confidence -= 0.2
        
        return max(0.3, min(1.0, base_confidence))
    
    def _calculate_generation_confidence(self, content: str) -> float:
        """Calculate confidence for test generation"""
        confidence = 0.6
        
        # Increase confidence based on source code complexity
        if 'def ' in content:
            confidence += 0.1
        if 'class ' in content:
            confidence += 0.1
        if len(content.split('\n')) > 20:
            confidence += 0.1
        if 'import' in content:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle chat interactions for Python testing assistance"""
        message = context.get('message', '').lower()
        
        if 'pytest' in message:
            return "I'm a pytest expert! I can help you write pytest tests, use fixtures, parametrize tests, create conftest.py files, use markers, and follow pytest best practices. What pytest question do you have?"
        elif 'unittest' in message:
            return "I can help with unittest! I specialize in TestCase classes, setUp/tearDown methods, assertion methods, test discovery, and migrating from unittest to pytest. What unittest challenge are you facing?"
        elif 'mock' in message:
            return "Mocking in Python tests is my specialty! I can help with unittest.mock, patch decorators, MagicMock, side_effects, and mocking best practices. What do you need to mock?"
        elif 'coverage' in message:
            return "Test coverage is crucial! I can help with pytest-cov, coverage.py, branch coverage, identifying untested code, and improving test coverage strategies. What coverage question do you have?"
        elif 'fixture' in message:
            return "Pytest fixtures are powerful! I can help with fixture scopes, dependency injection, parametrized fixtures, autouse fixtures, and fixture best practices. What fixture challenge are you working on?"
        elif 'django' in message and 'test' in message:
            return "Django testing has special considerations! I can help with TestCase vs TransactionTestCase, test databases, fixtures, factories, client testing, and Django-specific testing patterns. What Django testing issue do you have?"
        else:
            return "I'm your Python testing specialist! I can help with pytest, unittest, mocking, fixtures, test organization, coverage analysis, and testing best practices. I generate comprehensive test suites and improve existing tests. What testing challenge can I help you solve?" 