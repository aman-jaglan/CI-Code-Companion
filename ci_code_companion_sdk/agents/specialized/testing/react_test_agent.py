"""
React Test Agent - Specialized for React Testing

This agent focuses exclusively on React test generation, test analysis, and testing
best practices. It provides expert guidance for Jest, React Testing Library, Cypress,
and other React testing tools and patterns.
"""

import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class ReactTestAgent(BaseAgent):
    """
    Specialized agent for React testing and test generation.
    Focuses on unit tests, integration tests, and testing best practices.
    """
    
    def _initialize(self):
        """Initialize React Test Agent with specialized configuration"""
        super()._initialize()
        self.name = "react_test"
        self.version = "2.0.0"
        
        # Testing framework patterns
        self.test_patterns = {
            'describe_block': r'describe\s*\(\s*[\'"]([^\'"]+)[\'"]',
            'test_case': r'(?:test|it)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            'expect_assertion': r'expect\s*\([^)]+\)',
            'rtl_render': r'render\s*\(<.*>',
            'rtl_queries': r'(?:getBy|findBy|queryBy)(?:TestId|Text|Role|LabelText|PlaceholderText|AltText|Title)',
            'user_events': r'(?:userEvent|fireEvent)\.',
            'async_test': r'async\s+\(\s*\)\s*=>\s*{',
            'mock_function': r'jest\.(?:fn|mock|spyOn)',
            'cleanup': r'cleanup\s*\(\s*\)'
        }
        
        # Test quality indicators
        self.quality_indicators = {
            'has_describe': False,
            'has_assertions': False,
            'has_cleanup': False,
            'tests_behavior': False,
            'tests_edge_cases': False,
            'uses_proper_queries': False,
            'has_mocks': False
        }
        
        # React Testing Library best practices
        self.rtl_best_practices = {
            'preferred_queries': ['getByRole', 'getByLabelText', 'getByText', 'getByTestId'],
            'discouraged_queries': ['getByClassName', 'container.querySelector'],
            'good_patterns': ['user-event', 'waitFor', 'screen'],
            'bad_patterns': ['Simulate', 'wrapper.find', 'enzyme']
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get React Test Agent capabilities"""
        return [
            AgentCapability.TEST_GENERATION,
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported test file types"""
        return ['.test.js', '.test.ts', '.test.jsx', '.test.tsx', '.spec.js', '.spec.ts', '.spec.jsx', '.spec.tsx']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported testing frameworks"""
        return ['jest', 'react-testing-library', 'cypress', 'testing-library', 'enzyme']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze React test files for best practices and completeness.
        
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
        issues.extend(await self._analyze_rtl_usage(content))
        
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
            'testing_library': 'unknown',
            'describe_blocks': [],
            'test_cases': [],
            'assertions_count': 0,
            'async_tests': 0,
            'mocked_functions': [],
            'coverage_areas': [],
            'test_types': []
        }
        
        # Detect testing framework
        if 'jest' in content.lower() or 'describe(' in content or 'test(' in content or 'it(' in content:
            metadata['test_framework'] = 'jest'
        
        # Detect testing library
        if '@testing-library/react' in content or 'render(' in content:
            metadata['testing_library'] = 'react-testing-library'
        elif 'enzyme' in content.lower():
            metadata['testing_library'] = 'enzyme'
        elif 'cypress' in content.lower():
            metadata['testing_library'] = 'cypress'
        
        # Extract describe blocks
        describe_matches = re.findall(self.test_patterns['describe_block'], content)
        metadata['describe_blocks'] = describe_matches
        
        # Extract test cases
        test_matches = re.findall(self.test_patterns['test_case'], content)
        metadata['test_cases'] = test_matches
        
        # Count assertions
        assertion_matches = re.findall(self.test_patterns['expect_assertion'], content)
        metadata['assertions_count'] = len(assertion_matches)
        
        # Count async tests
        async_matches = re.findall(self.test_patterns['async_test'], content)
        metadata['async_tests'] = len(async_matches)
        
        # Extract mocked functions
        mock_matches = re.findall(self.test_patterns['mock_function'], content)
        metadata['mocked_functions'] = list(set(mock_matches))
        
        # Determine test types
        metadata['test_types'] = self._categorize_tests(content)
        
        return metadata
    
    async def _analyze_test_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze test structure and organization"""
        issues = []
        lines = content.split('\n')
        
        # Check for describe blocks
        if not re.search(self.test_patterns['describe_block'], content):
            issues.append(self.create_issue(
                'test_structure',
                'medium',
                'Missing describe blocks',
                'Test file should use describe blocks to group related tests',
                suggestion='Wrap tests in describe blocks to organize test suites'
            ))
        
        # Check for test case naming
        test_cases = re.findall(self.test_patterns['test_case'], content)
        for test_name in test_cases:
            if not self._is_good_test_name(test_name):
                issues.append(self.create_issue(
                    'test_naming',
                    'low',
                    'Poor test naming',
                    f'Test name "{test_name}" should describe the expected behavior',
                    suggestion='Use descriptive test names like "should render correctly when props are valid"'
                ))
        
        # Check for empty test cases
        for i, line in enumerate(lines, 1):
            if re.search(r'(?:test|it)\s*\([^)]+\)\s*=>\s*{\s*}', line):
                issues.append(self.create_issue(
                    'test_implementation',
                    'high',
                    'Empty test case',
                    'Test case has no implementation',
                    line_number=i,
                    suggestion='Implement the test or remove it'
                ))
        
        # Check for test file size
        test_count = len(test_cases)
        if test_count > 20:
            issues.append(self.create_issue(
                'test_organization',
                'medium',
                'Large test file',
                f'Test file contains {test_count} tests. Consider splitting into multiple files.',
                suggestion='Group related tests into separate test files'
            ))
        
        return issues
    
    async def _analyze_test_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze test patterns and practices"""
        issues = []
        lines = content.split('\n')
        
        # Check for proper setup and teardown
        has_cleanup = bool(re.search(self.test_patterns['cleanup'], content))
        has_after_each = bool(re.search(r'afterEach\s*\(', content))
        
        if not has_cleanup and not has_after_each and 'render(' in content:
            issues.append(self.create_issue(
                'test_cleanup',
                'medium',
                'Missing test cleanup',
                'Tests should clean up after themselves to prevent interference',
                suggestion='Add afterEach(() => cleanup()) or import cleanup from @testing-library/react'
            ))
        
        # Check for hardcoded waits
        for i, line in enumerate(lines, 1):
            if re.search(r'setTimeout|sleep|wait\(\d+\)', line):
                issues.append(self.create_issue(
                    'async_testing',
                    'high',
                    'Hardcoded wait detected',
                    'Avoid hardcoded waits in tests. Use waitFor or findBy* queries instead.',
                    line_number=i,
                    suggestion='Use waitFor() or findBy* queries for async behavior'
                ))
        
        # Check for implementation details testing
        impl_detail_patterns = [
            r'\.instance\(\)',
            r'\.state\(\)',
            r'\.props\(\)',
            r'wrapper\.find\(',
            r'component\.componentDidMount'
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in impl_detail_patterns:
                if re.search(pattern, line):
                    issues.append(self.create_issue(
                        'implementation_details',
                        'medium',
                        'Testing implementation details',
                        'Tests should focus on behavior, not implementation details',
                        line_number=i,
                        suggestion='Test user interactions and visible behavior instead'
                    ))
                    break
        
        return issues
    
    async def _analyze_assertions(self, content: str) -> List[Dict[str, Any]]:
        """Analyze test assertions quality"""
        issues = []
        lines = content.split('\n')
        
        # Check for tests without assertions
        test_blocks = self._extract_test_blocks(content)
        for test_name, test_content in test_blocks.items():
            if not re.search(self.test_patterns['expect_assertion'], test_content):
                issues.append(self.create_issue(
                    'missing_assertions',
                    'high',
                    'Test without assertions',
                    f'Test "{test_name}" has no assertions',
                    suggestion='Add expect() assertions to verify behavior'
                ))
        
        # Check for weak assertions
        weak_assertions = [
            r'expect\([^)]+\)\.toBeTruthy\(\)',
            r'expect\([^)]+\)\.toBeFalsy\(\)',
            r'expect\([^)]+\)\.toBeDefined\(\)'
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in weak_assertions:
                if re.search(pattern, line):
                    issues.append(self.create_issue(
                        'weak_assertion',
                        'low',
                        'Weak assertion detected',
                        'Consider using more specific assertions',
                        line_number=i,
                        suggestion='Use specific matchers like toEqual, toHaveTextContent, etc.'
                    ))
        
        # Check for multiple assertions in one test
        for test_name, test_content in test_blocks.items():
            assertion_count = len(re.findall(self.test_patterns['expect_assertion'], test_content))
            if assertion_count > 5:
                issues.append(self.create_issue(
                    'multiple_assertions',
                    'medium',
                    'Too many assertions in one test',
                    f'Test "{test_name}" has {assertion_count} assertions. Consider splitting.',
                    suggestion='Split into multiple focused tests'
                ))
        
        return issues
    
    async def _analyze_rtl_usage(self, content: str) -> List[Dict[str, Any]]:
        """Analyze React Testing Library usage patterns"""
        issues = []
        lines = content.split('\n')
        
        if '@testing-library/react' not in content:
            return issues
        
        # Check for discouraged query patterns
        for i, line in enumerate(lines, 1):
            for bad_pattern in self.rtl_best_practices['discouraged_queries']:
                if bad_pattern in line:
                    issues.append(self.create_issue(
                        'rtl_best_practices',
                        'medium',
                        'Discouraged query method',
                        f'Using {bad_pattern} goes against RTL best practices',
                        line_number=i,
                        suggestion='Use semantic queries like getByRole, getByLabelText instead'
                    ))
        
        # Check for getByTestId overuse
        testid_usage = len(re.findall(r'getByTestId|findByTestId|queryByTestId', content))
        total_queries = len(re.findall(self.test_patterns['rtl_queries'], content))
        
        if total_queries > 0 and testid_usage / total_queries > 0.5:
            issues.append(self.create_issue(
                'rtl_best_practices',
                'medium',
                'Overuse of getByTestId',
                'More than 50% of queries use getByTestId. Consider using semantic queries.',
                suggestion='Use getByRole, getByLabelText, or getByText when possible'
            ))
        
        # Check for proper async handling
        if 'findBy' in content and 'await' not in content:
            issues.append(self.create_issue(
                'async_queries',
                'high',
                'Missing await with findBy queries',
                'findBy* queries return promises and should be awaited',
                suggestion='Add await before findBy* queries'
            ))
        
        return issues
    
    async def _suggest_test_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest improvements for test quality"""
        suggestions = []
        
        # Suggest user-event over fireEvent
        if 'fireEvent' in content and '@testing-library/user-event' not in content:
            suggestions.append(self.create_suggestion(
                'testing_improvement',
                'Use user-event instead of fireEvent',
                'user-event provides more realistic user interactions than fireEvent',
                impact='medium',
                effort='low'
            ))
        
        # Suggest screen queries
        if 'render(' in content and 'screen.' not in content:
            suggestions.append(self.create_suggestion(
                'testing_improvement',
                'Use screen queries',
                'Using screen.getBy* is more convenient than destructuring from render()',
                impact='low',
                effort='low'
            ))
        
        # Suggest custom render function
        if content.count('render(') > 3:
            suggestions.append(self.create_suggestion(
                'test_organization',
                'Create custom render function',
                'Multiple render calls detected. Consider creating a custom render function with common providers.',
                impact='medium',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_coverage_improvements(self, content: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest improvements for test coverage"""
        suggestions = []
        
        # Get component info from context if available
        component_info = context.get('previous_results', {}).get('code_analysis', {})
        
        # Suggest testing hooks if component uses them
        if component_info:
            hooks_used = component_info.get('metadata', {}).get('hooks_used', [])
            if hooks_used and 'hook' not in content.lower():
                suggestions.append(self.create_suggestion(
                    'test_coverage',
                    'Test custom hooks',
                    f'Component uses hooks: {", ".join(hooks_used)}. Consider testing hook behavior.',
                    impact='high',
                    effort='medium'
                ))
        
        # Suggest edge case testing
        if 'error' not in content.lower() and 'invalid' not in content.lower():
            suggestions.append(self.create_suggestion(
                'test_coverage',
                'Add edge case tests',
                'Consider testing error states, invalid inputs, and edge cases',
                impact='high',
                effort='medium'
            ))
        
        # Suggest accessibility testing
        if 'toBeAccessible' not in content and 'axe' not in content.lower():
            suggestions.append(self.create_suggestion(
                'accessibility_testing',
                'Add accessibility tests',
                'Consider adding accessibility tests using jest-axe',
                impact='medium',
                effort='low'
            ))
        
        return suggestions
    
    async def _suggest_best_practices(self, content: str) -> List[Dict[str, Any]]:
        """Suggest testing best practices"""
        suggestions = []
        
        # Suggest snapshot testing limitations
        if 'toMatchSnapshot' in content:
            snapshot_count = content.count('toMatchSnapshot')
            if snapshot_count > 2:
                suggestions.append(self.create_suggestion(
                    'snapshot_testing',
                    'Limit snapshot testing',
                    f'Found {snapshot_count} snapshot tests. Use sparingly and prefer behavior testing.',
                    impact='medium',
                    effort='low'
                ))
        
        # Suggest mocking external dependencies
        if 'fetch(' in content and 'mock' not in content.lower():
            suggestions.append(self.create_suggestion(
                'mocking',
                'Mock external dependencies',
                'Consider mocking fetch calls and external APIs for reliable tests',
                impact='high',
                effort='medium'
            ))
        
        return suggestions
    
    async def generate_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive test cases for React components.
        
        Args:
            context: Context containing component information
            
        Returns:
            Dictionary containing generated test code and metadata
        """
        file_path = context.get('file_path', '')
        content = context.get('content', '')
        component_info = context.get('file_info', {})
        
        if not content:
            return {
                'test_code': '// No component content provided for test generation',
                'test_file_path': '',
                'coverage_areas': [],
                'explanation': 'Cannot generate tests without component content',
                'confidence_score': 0.0
            }
        
        # Extract component details
        component_name = self._extract_component_name(content)
        props = self._extract_props(content)
        hooks_used = self._extract_hooks(content)
        jsx_elements = self._extract_jsx_elements(content)
        
        # Generate test code
        test_code = self._generate_comprehensive_test_code(
            component_name, props, hooks_used, jsx_elements, content
        )
        
        # Determine test file path
        test_file_path = self._generate_test_file_path(file_path)
        
        # Define coverage areas
        coverage_areas = self._define_coverage_areas(content, hooks_used, props)
        
        return {
            'test_code': test_code,
            'test_file_path': test_file_path,
            'coverage_areas': coverage_areas,
            'explanation': f'Generated comprehensive test suite for {component_name} component',
            'confidence_score': self._calculate_generation_confidence(content),
            'metadata': {
                'component_name': component_name,
                'props_count': len(props),
                'hooks_count': len(hooks_used),
                'test_types': ['unit', 'integration', 'accessibility']
            }
        }
    
    def _extract_test_blocks(self, content: str) -> Dict[str, str]:
        """Extract individual test blocks for analysis"""
        test_blocks = {}
        lines = content.split('\n')
        current_test = None
        current_content = []
        brace_count = 0
        
        for line in lines:
            test_match = re.search(self.test_patterns['test_case'], line)
            if test_match:
                if current_test:
                    test_blocks[current_test] = '\n'.join(current_content)
                current_test = test_match.group(1)
                current_content = [line]
                brace_count = line.count('{') - line.count('}')
            elif current_test:
                current_content.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    test_blocks[current_test] = '\n'.join(current_content)
                    current_test = None
                    current_content = []
        
        return test_blocks
    
    def _is_good_test_name(self, test_name: str) -> bool:
        """Check if test name follows good practices"""
        good_indicators = ['should', 'when', 'given', 'renders', 'displays', 'handles', 'calls']
        bad_indicators = ['test', 'check', 'verify']
        
        test_lower = test_name.lower()
        
        # Check for good indicators
        has_good_indicator = any(indicator in test_lower for indicator in good_indicators)
        
        # Check for bad indicators
        has_bad_indicator = any(indicator in test_lower for indicator in bad_indicators)
        
        # Good test names are descriptive and use behavior-focused language
        return has_good_indicator and not has_bad_indicator and len(test_name) > 10
    
    def _categorize_tests(self, content: str) -> List[str]:
        """Categorize tests by type"""
        test_types = []
        
        if 'render(' in content:
            test_types.append('unit')
        
        if 'userEvent' in content or 'fireEvent' in content:
            test_types.append('integration')
        
        if 'toMatchSnapshot' in content:
            test_types.append('snapshot')
        
        if 'cy.' in content:
            test_types.append('e2e')
        
        if 'axe' in content.lower() or 'accessibility' in content.lower():
            test_types.append('accessibility')
        
        return test_types or ['unknown']
    
    def _extract_component_name(self, content: str) -> str:
        """Extract component name from source code"""
        # Look for export default patterns
        export_match = re.search(r'export\s+default\s+(?:function\s+)?([A-Z][a-zA-Z0-9]*)', content)
        if export_match:
            return export_match.group(1)
        
        # Look for function/const declarations
        func_match = re.search(r'(?:function|const)\s+([A-Z][a-zA-Z0-9]*)', content)
        if func_match:
            return func_match.group(1)
        
        return 'Component'
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract props from component"""
        props = []
        
        # Look for props destructuring
        destructure_match = re.search(r'{\s*([^}]+)\s*}\s*=\s*props', content)
        if destructure_match:
            props_str = destructure_match.group(1)
            props = [prop.strip() for prop in props_str.split(',')]
        
        # Look for TypeScript interface
        interface_match = re.search(r'interface\s+\w+Props\s*{\s*([^}]+)\s*}', content)
        if interface_match:
            interface_props = re.findall(r'(\w+)\s*[?:]', interface_match.group(1))
            props.extend(interface_props)
        
        return list(set([prop.strip() for prop in props if prop.strip()]))
    
    def _extract_hooks(self, content: str) -> List[str]:
        """Extract hooks used in component"""
        hook_matches = re.findall(r'(use[A-Z][a-zA-Z0-9]*)', content)
        return list(set(hook_matches))
    
    def _extract_jsx_elements(self, content: str) -> List[str]:
        """Extract JSX elements from component"""
        jsx_matches = re.findall(r'<([A-Z][a-zA-Z0-9]*)', content)
        return list(set(jsx_matches))
    
    def _generate_comprehensive_test_code(
        self, 
        component_name: str, 
        props: List[str], 
        hooks: List[str], 
        jsx_elements: List[str],
        content: str
    ) -> str:
        """Generate comprehensive test code for the component"""
        
        test_imports = f'''import React from 'react';
import {{ render, screen, fireEvent, waitFor }} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {{ axe, toHaveNoViolations }} from 'jest-axe';
import {component_name} from './{component_name}';

expect.extend(toHaveNoViolations);
'''
        
        basic_tests = f'''
describe('{component_name}', () => {{
  afterEach(() => {{
    jest.clearAllMocks();
  }});

  describe('Rendering', () => {{
    it('should render without crashing', () => {{
      render(<{component_name} />);
    }});

    it('should be accessible', async () => {{
      const {{ container }} = render(<{component_name} />);
      const results = await axe(container);
      expect(results).toHaveNoViolations();
    }});
  }});
'''
        
        props_tests = ""
        if props:
            props_tests = f'''
  describe('Props', () => {{
    {self._generate_props_tests(component_name, props)}
  }});
'''
        
        interaction_tests = ""
        if 'onClick' in content or 'onChange' in content or 'onSubmit' in content:
            interaction_tests = f'''
  describe('User Interactions', () => {{
    {self._generate_interaction_tests(component_name, content)}
  }});
'''
        
        hooks_tests = ""
        if hooks:
            hooks_tests = f'''
  describe('Hooks Behavior', () => {{
    {self._generate_hooks_tests(component_name, hooks, content)}
  }});
'''
        
        edge_case_tests = f'''
  describe('Edge Cases', () => {{
    it('should handle missing props gracefully', () => {{
      expect(() => render(<{component_name} />)).not.toThrow();
    }});

    it('should handle invalid props gracefully', () => {{
      const invalidProps = {{ invalid: 'value' }};
      expect(() => render(<{component_name} {{...invalidProps}} />)).not.toThrow();
    }});
  }});
'''
        
        return test_imports + basic_tests + props_tests + interaction_tests + hooks_tests + edge_case_tests + '});'
    
    def _generate_props_tests(self, component_name: str, props: List[str]) -> str:
        """Generate tests for component props"""
        tests = []
        
        for prop in props[:5]:  # Limit to first 5 props
            tests.append(f'''
    it('should handle {prop} prop correctly', () => {{
      const test{prop.capitalize()} = 'test-{prop}-value';
      render(<{component_name} {prop}={{test{prop.capitalize()}}} />);
      // Add specific assertions based on prop usage
    }});''')
        
        return '\n'.join(tests)
    
    def _generate_interaction_tests(self, component_name: str, content: str) -> str:
        """Generate tests for user interactions"""
        tests = []
        
        if 'onClick' in content:
            tests.append(f'''
    it('should handle click events', async () => {{
      const user = userEvent.setup();
      const mockClick = jest.fn();
      render(<{component_name} onClick={{mockClick}} />);
      
      const clickableElement = screen.getByRole('button'); // Adjust selector
      await user.click(clickableElement);
      
      expect(mockClick).toHaveBeenCalledTimes(1);
    }});''')
        
        if 'onChange' in content:
            tests.append(f'''
    it('should handle input changes', async () => {{
      const user = userEvent.setup();
      const mockChange = jest.fn();
      render(<{component_name} onChange={{mockChange}} />);
      
      const input = screen.getByRole('textbox'); // Adjust selector
      await user.type(input, 'test input');
      
      expect(mockChange).toHaveBeenCalled();
    }});''')
        
        return '\n'.join(tests)
    
    def _generate_hooks_tests(self, component_name: str, hooks: List[str], content: str) -> str:
        """Generate tests for hooks behavior"""
        tests = []
        
        if 'useState' in hooks:
            tests.append(f'''
    it('should manage state correctly', async () => {{
      const user = userEvent.setup();
      render(<{component_name} />);
      
      // Test initial state
      // Test state changes
      // Add specific assertions based on state usage
    }});''')
        
        if 'useEffect' in hooks:
            tests.append(f'''
    it('should handle side effects properly', () => {{
      render(<{component_name} />);
      
      // Test effect execution
      // Test cleanup if applicable
    }});''')
        
        return '\n'.join(tests)
    
    def _generate_test_file_path(self, source_file_path: str) -> str:
        """Generate appropriate test file path"""
        if not source_file_path:
            return ''
        
        path_parts = source_file_path.split('.')
        if len(path_parts) > 1:
            return f"{path_parts[0]}.test.{path_parts[1]}"
        return f"{source_file_path}.test.js"
    
    def _define_coverage_areas(self, content: str, hooks: List[str], props: List[str]) -> List[str]:
        """Define what areas the tests should cover"""
        coverage_areas = ['basic_rendering']
        
        if props:
            coverage_areas.append('props_handling')
        
        if hooks:
            coverage_areas.extend(['state_management', 'side_effects'])
        
        if 'onClick' in content or 'onChange' in content:
            coverage_areas.append('user_interactions')
        
        if 'async' in content or 'await' in content:
            coverage_areas.append('async_behavior')
        
        coverage_areas.extend(['accessibility', 'edge_cases'])
        
        return coverage_areas
    
    def _calculate_test_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for test analysis"""
        base_confidence = 0.7
        
        # Boost confidence for good test practices
        if 'describe(' in content:
            base_confidence += 0.1
        if 'expect(' in content:
            base_confidence += 0.1
        if '@testing-library' in content:
            base_confidence += 0.1
        
        # Reduce confidence for issues
        if len(issues) > 5:
            base_confidence -= 0.2
        
        return max(0.3, min(1.0, base_confidence))
    
    def _calculate_generation_confidence(self, content: str) -> float:
        """Calculate confidence for test generation"""
        confidence = 0.6
        
        # Increase confidence based on component complexity
        if 'export' in content:
            confidence += 0.1
        if 'props' in content:
            confidence += 0.1
        if 'useState' in content or 'useEffect' in content:
            confidence += 0.1
        if len(content.split('\n')) > 20:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle chat interactions for React testing assistance"""
        message = context.get('message', '').lower()
        
        if 'test' in message and ('component' in message or 'react' in message):
            return "I'm your React testing specialist! I can help you write tests for React components using Jest and React Testing Library. I focus on behavior-driven testing, accessibility, and best practices. What component would you like to test?"
        elif 'hook' in message and 'test' in message:
            return "Testing React hooks is tricky but important! I can help you test custom hooks using @testing-library/react-hooks or by testing them through components that use them. What hook are you trying to test?"
        elif 'rtl' in message or 'testing library' in message:
            return "React Testing Library is great for testing user behavior! I can help you use the right queries (getByRole, getByLabelText), handle async operations with waitFor, and follow RTL best practices. What RTL question do you have?"
        elif 'coverage' in message or 'edge case' in message:
            return "Test coverage and edge cases are crucial! I can suggest what to test: props validation, error states, user interactions, accessibility, and integration scenarios. What area needs better coverage?"
        elif 'jest' in message or 'mock' in message:
            return "Jest mocking and testing utilities are powerful! I can help with mocking functions, modules, timers, and API calls. I'll also suggest good assertion patterns. What do you need to mock or test?"
        else:
            return "I'm your React testing expert! I specialize in Jest, React Testing Library, component testing, hook testing, accessibility testing, and testing best practices. What testing challenge can I help you solve?" 