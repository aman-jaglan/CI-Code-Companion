"""
React Agent for Frontend Code Analysis

This agent specializes in analyzing React, Next.js, and other React-based frontend applications.
It provides comprehensive analysis including JSX/TSX syntax, React hooks, component structure,
performance optimization, and modern React best practices.
"""

import re
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent, AgentCapability


class ReactAgent(BaseAgent):
    """
    Specialized agent for React and frontend JavaScript/TypeScript analysis.
    """
    
    def _initialize(self):
        """Initialize React-specific configurations"""
        super()._initialize()
        self.name = "react"
        
    def get_capabilities(self) -> List[AgentCapability]:
        """Get React agent capabilities"""
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.CODE_OPTIMIZATION,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.STYLE_CHECK,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported file types for React analysis"""
        return ['.jsx', '.tsx', '.js', '.ts']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported React frameworks"""
        return ['react', 'next.js', 'gatsby', 'remix']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze React file for issues and suggestions.
        
        Args:
            file_path: Path to React file
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
        
        # Perform React-specific analysis
        issues.extend(await self._analyze_jsx_syntax(content))
        issues.extend(await self._analyze_hooks(content))
        issues.extend(await self._analyze_component_structure(content))
        issues.extend(await self._analyze_performance(content))
        
        # Generate suggestions
        suggestions.extend(await self._suggest_optimizations(content))
        suggestions.extend(await self._suggest_best_practices(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _analyze_jsx_syntax(self, content: str) -> List[Dict[str, Any]]:
        """Analyze JSX/TSX syntax for common issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for missing key props in lists
            if re.search(r'\.map\s*\(\s*\([^)]*\)\s*=>\s*<', line):
                if 'key=' not in line:
                    issues.append(self.create_issue(
                        'jsx_syntax',
                        'medium',
                        'Missing key prop in list item',
                        'Each item in a list should have a unique key prop for optimal rendering',
                        line_number=i,
                        suggestion='Add a unique key prop: <Component key={item.id} />'
                    ))
            
            # Check for inline styles
            if re.search(r'style\s*=\s*\{\{', line):
                issues.append(self.create_issue(
                    'performance',
                    'low',
                    'Inline styles detected',
                    'Inline styles create new objects on each render, affecting performance',
                    line_number=i,
                    suggestion='Consider using CSS classes or styled-components'
                ))
            
            # Check for direct DOM manipulation
            if re.search(r'document\.(getElementById|querySelector|createElement)', line):
                issues.append(self.create_issue(
                    'best_practice',
                    'medium',
                    'Direct DOM manipulation',
                    'React components should use refs instead of direct DOM manipulation',
                    line_number=i,
                    suggestion='Use useRef() hook for DOM references'
                ))
        
        return issues
    
    async def _analyze_hooks(self, content: str) -> List[Dict[str, Any]]:
        """Analyze React hooks usage for best practices"""
        issues = []
        lines = content.split('\n')
        
        # Check for hooks in wrong places
        in_component = False
        component_name = None
        
        for i, line in enumerate(lines, 1):
            # Detect component boundaries
            component_match = re.search(r'(?:function|const)\s+([A-Z][a-zA-Z0-9]*)', line)
            if component_match:
                in_component = True
                component_name = component_match.group(1)
            
            # Check for hooks outside components
            hook_match = re.search(r'\buse[A-Z][a-zA-Z0-9]*\s*\(', line)
            if hook_match and not in_component:
                issues.append(self.create_issue(
                    'hooks',
                    'high',
                    'Hook called outside component',
                    'React hooks must be called inside React components or custom hooks',
                    line_number=i,
                    suggestion='Move hook call inside component function'
                ))
            
            # Check for missing dependency arrays
            if 'useEffect(' in line and 'useEffect(' in line:
                effect_content = self._extract_useEffect_content(content, i)
                if effect_content and not self._has_dependency_array(effect_content):
                    issues.append(self.create_issue(
                        'hooks',
                        'medium',
                        'Missing useEffect dependency array',
                        'useEffect should include a dependency array to control when it runs',
                        line_number=i,
                        suggestion='Add dependency array: useEffect(() => {}, [])'
                    ))
            
            # Check for state mutations
            if re.search(r'set[A-Z][a-zA-Z0-9]*\s*\([^)]*\.push\(', line):
                issues.append(self.create_issue(
                    'hooks',
                    'high',
                    'Direct state mutation',
                    'State should not be mutated directly. Use immutable updates.',
                    line_number=i,
                    suggestion='Use spread operator: setState([...items, newItem])'
                ))
        
        return issues
    
    async def _analyze_component_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze component structure and organization"""
        issues = []
        
        # Check component size
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        if len(non_empty_lines) > 200:
            issues.append(self.create_issue(
                'maintainability',
                'medium',
                'Large component detected',
                f'Component has {len(non_empty_lines)} lines. Consider breaking it into smaller components.',
                suggestion='Extract reusable parts into separate components'
            ))
        
        # Check for prop drilling (more than 3 levels)
        prop_depth = self._calculate_prop_depth(content)
        if prop_depth > 3:
            issues.append(self.create_issue(
                'architecture',
                'medium',
                'Deep prop drilling detected',
                f'Props are passed through {prop_depth} levels. Consider using Context API.',
                suggestion='Use React Context or state management library'
            ))
        
        return issues
    
    async def _analyze_performance(self, content: str) -> List[Dict[str, Any]]:
        """Analyze performance-related issues"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for missing React.memo on large components
            if re.search(r'export\s+(?:default\s+)?(?:function|const)\s+[A-Z]', line):
                if 'React.memo' not in content and 'memo(' not in content:
                    component_size = len([l for l in lines[i:] if l.strip()])
                    if component_size > 50:
                        issues.append(self.create_issue(
                            'performance',
                            'low',
                            'Consider memoization for large component',
                            'Large components might benefit from React.memo to prevent unnecessary re-renders',
                            line_number=i,
                            suggestion='Wrap component with React.memo()'
                        ))
            
            # Check for expensive operations in render
            if re.search(r'(sort|filter|map|reduce)\s*\(.*\{', line) and 'useMemo' not in content:
                issues.append(self.create_issue(
                    'performance',
                    'medium',
                    'Expensive operation in render',
                    'Array operations in render can cause performance issues',
                    line_number=i,
                    suggestion='Consider using useMemo() for expensive calculations'
                ))
        
        return issues
    
    async def _suggest_optimizations(self, content: str) -> List[Dict[str, Any]]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Suggest lazy loading for large components
        if len(content.split('\n')) > 100 and 'lazy(' not in content:
            suggestions.append(self.create_suggestion(
                'performance',
                'Implement code splitting',
                'Consider using React.lazy() for code splitting to reduce bundle size',
                impact='high',
                effort='low'
            ))
        
        # Suggest TypeScript if using JavaScript
        if content.endswith('.js') or content.endswith('.jsx'):
            suggestions.append(self.create_suggestion(
                'maintainability',
                'Migrate to TypeScript',
                'TypeScript provides better type safety and developer experience',
                impact='high',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_best_practices(self, content: str) -> List[Dict[str, Any]]:
        """Generate best practice suggestions"""
        suggestions = []
        
        # Suggest error boundaries
        if 'class ' in content and 'componentDidCatch' not in content:
            suggestions.append(self.create_suggestion(
                'reliability',
                'Add error boundary',
                'Implement error boundaries to gracefully handle component errors',
                impact='medium',
                effort='low'
            ))
        
        # Suggest accessibility improvements
        if '<button' in content and 'aria-' not in content:
            suggestions.append(self.create_suggestion(
                'accessibility',
                'Improve accessibility',
                'Add ARIA attributes for better accessibility',
                impact='medium',
                effort='low'
            ))
        
        return suggestions
    
    async def _generate_tests_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate React component tests"""
        file_path = context.get('file_path', '')
        content = context.get('content', '')
        
        # Extract component information
        component_name = self._extract_component_name(content)
        props = self._extract_props(content)
        hooks = self._extract_hooks(content)
        
        # Generate test code
        test_code = self._generate_react_test_code(component_name, props, hooks)
        test_file_path = file_path.replace('.jsx', '.test.jsx').replace('.tsx', '.test.tsx')
        
        coverage_areas = ['component_rendering', 'props_handling']
        if hooks:
            coverage_areas.append('hooks_behavior')
        
        return {
            'test_code': test_code,
            'test_file_path': test_file_path,
            'coverage_areas': coverage_areas,
            'test_cases': self._generate_test_cases(component_name, props, hooks),
            'explanation': f'Generated comprehensive tests for {component_name} component',
            'confidence_score': 0.85,
            'framework': 'jest',
            'dependencies': ['@testing-library/react', '@testing-library/jest-dom'],
            'metadata': {
                'component_name': component_name,
                'props_count': len(props),
                'hooks_count': len(hooks)
            }
        }
    
    async def _optimize_code_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate React-specific optimizations"""
        content = context.get('content', '')
        optimizations = []
        
        # Performance optimizations
        if 'useMemo' not in content and self._has_expensive_calculations(content):
            optimizations.append({
                'type': 'performance',
                'title': 'Add useMemo for expensive calculations',
                'description': 'Wrap expensive calculations in useMemo to prevent unnecessary recalculations',
                'before': '// Expensive calculation in render',
                'after': 'const expensiveValue = useMemo(() => expensiveCalculation(), [dependencies]);',
                'impact': 'high',
                'effort': 'low',
                'auto_applicable': False
            })
        
        return {
            'optimizations': optimizations,
            'metrics': {'potential_performance_gain': '15-30%'},
            'confidence_score': 0.8,
            'metadata': {'optimization_type': 'react_performance'}
        }
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle React-specific chat requests"""
        message = context.get('message', '').lower()
        content = context.get('content', '')
        
        if 'hooks' in message:
            return self._generate_hooks_advice(content)
        elif 'performance' in message:
            return self._generate_performance_advice(content)
        elif 'testing' in message:
            return self._generate_testing_advice(content)
        else:
            return f"As a React expert, I can help with component optimization, hooks best practices, testing strategies, and performance improvements. What specific aspect would you like to discuss?"
    
    def _extract_useEffect_content(self, content: str, line_num: int) -> str:
        """Extract useEffect block content"""
        lines = content.split('\n')
        if line_num > len(lines):
            return ""
        
        # Simple extraction - in production would need proper AST parsing
        start = line_num - 1
        brace_count = 0
        effect_lines = []
        
        for i in range(start, len(lines)):
            line = lines[i]
            effect_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and '{' in lines[start]:
                break
        
        return '\n'.join(effect_lines)
    
    def _has_dependency_array(self, effect_content: str) -> bool:
        """Check if useEffect has dependency array"""
        return ']' in effect_content.split(',')[-1] if ',' in effect_content else False
    
    def _calculate_prop_depth(self, content: str) -> int:
        """Calculate prop drilling depth"""
        # Simplified prop depth calculation
        prop_patterns = re.findall(r'(\w+)=\{(\w+)\}', content)
        return len(set(prop[1] for prop in prop_patterns))
    
    def _extract_component_name(self, content: str) -> str:
        """Extract main component name"""
        match = re.search(r'(?:export\s+default\s+)?(?:function|const)\s+([A-Z][a-zA-Z0-9]*)', content)
        return match.group(1) if match else 'Component'
    
    def _extract_props(self, content: str) -> List[str]:
        """Extract component props"""
        props_match = re.search(r'function\s+\w+\s*\(\s*\{\s*([^}]+)\s*\}', content)
        if props_match:
            return [prop.strip() for prop in props_match.group(1).split(',')]
        return []
    
    def _extract_hooks(self, content: str) -> List[str]:
        """Extract used hooks"""
        hook_pattern = r'\buse[A-Z][a-zA-Z0-9]*\s*\('
        return list(set(re.findall(r'\b(use[A-Z][a-zA-Z0-9]*)', content)))
    
    def _generate_react_test_code(self, component_name: str, props: List[str], hooks: List[str]) -> str:
        """Generate React test code"""
        return f"""import {{ render, screen }} from '@testing-library/react';
import {{ {component_name} }} from './{component_name}';

describe('{component_name}', () => {{
  it('renders without crashing', () => {{
    render(<{component_name} />);
  }});

  it('displays correct content', () => {{
    render(<{component_name} />);
    // Add assertions here
  }});
  
  {self._generate_props_tests(component_name, props)}
  
  {self._generate_hooks_tests(hooks)}
}});"""
    
    def _generate_test_cases(self, component_name: str, props: List[str], hooks: List[str]) -> List[Dict[str, Any]]:
        """Generate test case descriptions"""
        test_cases = [
            {'name': 'renders_without_crashing', 'description': 'Component renders without errors'},
            {'name': 'displays_content', 'description': 'Component displays expected content'}
        ]
        
        for prop in props:
            test_cases.append({
                'name': f'handles_{prop}_prop',
                'description': f'Component handles {prop} prop correctly'
            })
        
        return test_cases
    
    def _generate_props_tests(self, component_name: str, props: List[str]) -> str:
        """Generate props-specific tests"""
        if not props:
            return ""
        
        tests = []
        for prop in props[:3]:  # Limit to first 3 props
            tests.append(f"""
  it('handles {prop} prop', () => {{
    const test{prop.title()} = 'test-value';
    render(<{component_name} {prop}={{test{prop.title()}}} />);
    // Add specific assertions for {prop}
  }});""")
        
        return '\n'.join(tests)
    
    def _generate_hooks_tests(self, hooks: List[str]) -> str:
        """Generate hooks-specific tests"""
        if 'useState' not in hooks:
            return ""
        
        return """
  it('handles state changes', () => {
    render(<Component />);
    // Add state change tests
  });"""
    
    def _has_expensive_calculations(self, content: str) -> bool:
        """Check if content has expensive calculations"""
        expensive_patterns = [
            r'\.sort\s*\(',
            r'\.filter\s*\(',
            r'\.reduce\s*\(',
            r'\.map\s*\([^)]*\)\s*\.filter'
        ]
        return any(re.search(pattern, content) for pattern in expensive_patterns)
    
    def _generate_hooks_advice(self, content: str) -> str:
        """Generate hooks-specific advice"""
        advice = "React Hooks Best Practices:\n"
        advice += "• Always call hooks at the top level of your function component\n"
        advice += "• Use useEffect with proper dependency arrays\n"
        advice += "• Consider useMemo for expensive calculations\n"
        advice += "• Use useCallback for function props to prevent unnecessary re-renders"
        return advice
    
    def _generate_performance_advice(self, content: str) -> str:
        """Generate performance advice"""
        advice = "React Performance Tips:\n"
        advice += "• Use React.memo() for components that render often\n"
        advice += "• Implement code splitting with React.lazy()\n"
        advice += "• Avoid inline objects and functions in JSX\n"
        advice += "• Use production builds for deployment"
        return advice
    
    def _generate_testing_advice(self, content: str) -> str:
        """Generate testing advice"""
        advice = "React Testing Strategy:\n"
        advice += "• Test component behavior, not implementation\n"
        advice += "• Use React Testing Library for user-centric tests\n"
        advice += "• Mock external dependencies and API calls\n"
        advice += "• Test accessibility with screen readers in mind"
        return advice
    
    def _calculate_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for analysis"""
        base_score = 0.7
        
        # Higher confidence for files with clear React patterns
        if 'jsx' in content.lower() or 'react' in content.lower():
            base_score += 0.2
        
        # Adjust based on file size and complexity
        lines = len(content.split('\n'))
        if lines > 50:
            base_score += 0.1
        
        return min(base_score, 1.0) 