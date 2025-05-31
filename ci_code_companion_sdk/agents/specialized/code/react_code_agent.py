"""
React Code Agent - Specialized for React Development

This agent focuses exclusively on React code development, component analysis,
and code optimization. It provides expert guidance for React best practices,
modern patterns, and performance optimization.
"""

import re
import ast
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class ReactCodeAgent(BaseAgent):
    """
    Specialized agent for React code development and analysis.
    Focuses on component architecture, hooks, performance, and modern React patterns.
    """
    
    def _initialize(self):
        """Initialize React Code Agent with specialized configuration"""
        super()._initialize()
        self.name = "react_code"
        self.version = "2.0.0"
        
        # React-specific patterns and rules
        self.component_patterns = {
            'functional_component': r'(?:const|function)\s+([A-Z][a-zA-Z0-9]*)\s*(?:=\s*)?(?:\([^)]*\))?\s*(?:=>\s*)?{',
            'class_component': r'class\s+([A-Z][a-zA-Z0-9]*)\s+extends\s+(?:React\.)?Component',
            'hook_usage': r'\buse[A-Z][a-zA-Z0-9]*\s*\(',
            'jsx_element': r'<[A-Z][a-zA-Z0-9]*(?:\s+[^>]*)?>',
            'props_destructuring': r'(?:const\s+)?{\s*([^}]+)\s*}\s*=\s*props',
            'state_hook': r'const\s+\[[^,]+,\s*set[A-Z][a-zA-Z0-9]*\]\s*=\s*useState'
        }
        
        self.performance_checks = {
            'memo_usage': r'React\.memo\s*\(',
            'callback_usage': r'useCallback\s*\(',
            'memo_hook': r'useMemo\s*\(',
            'effect_cleanup': r'return\s+\(\)\s*=>\s*{',
            'inline_objects': r'(?:style|className)\s*=\s*{{',
            'anonymous_functions': r'(?:onClick|onChange|onSubmit)\s*=\s*{\s*\([^)]*\)\s*=>'
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get React Code Agent capabilities"""
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CODE_OPTIMIZATION,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.REFACTORING,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported file types for React code analysis"""
        return ['.jsx', '.tsx', '.js', '.ts']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported React frameworks and libraries"""
        return ['react', 'next.js', 'gatsby', 'remix', 'vite']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze React code for development best practices and optimization opportunities.
        
        Args:
            file_path: Path to React file
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
        metadata.update(await self._extract_react_metadata(content))
        
        # Perform React-specific code analysis
        issues.extend(await self._analyze_component_structure(content))
        issues.extend(await self._analyze_hooks_usage(content))
        issues.extend(await self._analyze_props_handling(content))
        issues.extend(await self._analyze_state_management(content))
        issues.extend(await self._analyze_jsx_patterns(content))
        
        # Generate optimization suggestions
        suggestions.extend(await self._suggest_performance_optimizations(content))
        suggestions.extend(await self._suggest_code_improvements(content))
        suggestions.extend(await self._suggest_modern_patterns(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_react_metadata(self, content: str) -> Dict[str, Any]:
        """Extract React-specific metadata from file content"""
        metadata = {
            'react_version': 'unknown',
            'components': [],
            'hooks_used': [],
            'external_dependencies': [],
            'jsx_elements': [],
            'complexity_score': 0,
            'component_type': 'unknown'
        }
        
        # Detect React version and imports
        if 'import React' in content:
            metadata['react_version'] = 'classic'
        elif 'import {' in content and 'react' in content:
            metadata['react_version'] = 'modern'
        
        # Extract components
        for pattern_name, pattern in self.component_patterns.items():
            matches = re.findall(pattern, content)
            if pattern_name in ['functional_component', 'class_component']:
                metadata['components'].extend(matches)
                if matches:
                    metadata['component_type'] = pattern_name
        
        # Extract hooks
        hook_matches = re.findall(self.component_patterns['hook_usage'], content)
        metadata['hooks_used'] = list(set([match.split('(')[0] for match in hook_matches]))
        
        # Extract JSX elements
        jsx_matches = re.findall(self.component_patterns['jsx_element'], content)
        metadata['jsx_elements'] = list(set([match.strip('<').split()[0] for match in jsx_matches]))
        
        # Calculate basic complexity
        metadata['complexity_score'] = self._calculate_component_complexity(content)
        
        return metadata
    
    async def _analyze_component_structure(self, content: str) -> List[Dict[str, Any]]:
        """Analyze component structure and architecture"""
        issues = []
        lines = content.split('\n')
        
        # Check component size
        component_lines = [line for line in lines if line.strip() and not line.strip().startswith('//')]
        if len(component_lines) > 150:
            issues.append(self.create_issue(
                'component_structure',
                'medium',
                'Large component detected',
                f'Component has {len(component_lines)} lines of code. Consider breaking it into smaller, more focused components.',
                suggestion='Extract reusable logic into custom hooks or separate components'
            ))
        
        # Check for multiple components in one file
        component_count = len(re.findall(self.component_patterns['functional_component'], content)) + \
                         len(re.findall(self.component_patterns['class_component'], content))
        
        if component_count > 3:
            issues.append(self.create_issue(
                'component_structure',
                'low',
                'Multiple components in single file',
                f'Found {component_count} components in one file. Consider separating them for better maintainability.',
                suggestion='Create separate files for each component'
            ))
        
        # Check for proper component naming
        for i, line in enumerate(lines, 1):
            func_match = re.search(r'(?:const|function)\s+([a-z][a-zA-Z0-9]*)', line)
            if func_match and '<' in content[content.find(line):]:  # Likely a component
                component_name = func_match.group(1)
                issues.append(self.create_issue(
                    'naming_convention',
                    'medium',
                    'Component naming convention',
                    f'Component "{component_name}" should start with uppercase letter',
                    line_number=i,
                    suggestion=f'Rename to "{component_name.capitalize()}"'
                ))
        
        return issues
    
    async def _analyze_hooks_usage(self, content: str) -> List[Dict[str, Any]]:
        """Analyze React hooks usage and best practices"""
        issues = []
        lines = content.split('\n')
        
        # Check for hooks rules violations
        in_component = False
        component_depth = 0
        
        for i, line in enumerate(lines, 1):
            # Track component boundaries
            if re.search(self.component_patterns['functional_component'], line):
                in_component = True
                component_depth = 0
            
            # Track conditional statements
            if re.search(r'\b(?:if|else|for|while)\b', line.strip()):
                component_depth += 1
            
            # Check for hooks in conditionals
            hook_match = re.search(self.component_patterns['hook_usage'], line)
            if hook_match and component_depth > 0:
                hook_name = hook_match.group().split('(')[0]
                issues.append(self.create_issue(
                    'hooks_rules',
                    'high',
                    'Hook called conditionally',
                    f'Hook "{hook_name}" is called inside a conditional statement. Hooks must be called in the same order every time.',
                    line_number=i,
                    suggestion='Move hook to top level of component'
                ))
            
            # Check for missing dependency arrays in useEffect
            if 'useEffect(' in line:
                effect_block = self._extract_effect_block(content, i)
                if effect_block and not self._has_dependency_array(effect_block):
                    issues.append(self.create_issue(
                        'hooks_dependencies',
                        'medium',
                        'Missing useEffect dependency array',
                        'useEffect without dependency array runs on every render, which may cause performance issues',
                        line_number=i,
                        suggestion='Add dependency array to control when effect runs'
                    ))
                elif effect_block:
                    # Check for missing dependencies
                    missing_deps = self._find_missing_dependencies(effect_block)
                    if missing_deps:
                        issues.append(self.create_issue(
                            'hooks_dependencies',
                            'medium',
                            'Missing dependencies in useEffect',
                            f'Variables {missing_deps} are used but not included in dependency array',
                            line_number=i,
                            suggestion=f'Add {missing_deps} to dependency array'
                        ))
        
        return issues
    
    async def _analyze_props_handling(self, content: str) -> List[Dict[str, Any]]:
        """Analyze props handling and validation"""
        issues = []
        lines = content.split('\n')
        
        # Check for prop types or TypeScript interfaces
        has_prop_validation = bool(
            re.search(r'PropTypes|interface\s+\w+Props|type\s+\w+Props', content)
        )
        
        if not has_prop_validation and self._uses_props(content):
            issues.append(self.create_issue(
                'props_validation',
                'medium',
                'Missing prop validation',
                'Component uses props but has no PropTypes or TypeScript interface for validation',
                suggestion='Add PropTypes or TypeScript interface for better type safety'
            ))
        
        # Check for props destructuring best practices
        for i, line in enumerate(lines, 1):
            # Look for props parameter without destructuring
            if re.search(r'function\s+\w+\s*\(\s*props\s*\)', line) or \
               re.search(r'=\s*\(\s*props\s*\)\s*=>', line):
                # Check if props are accessed with dot notation
                following_lines = '\n'.join(lines[i:i+20])  # Check next 20 lines
                if 'props.' in following_lines:
                    issues.append(self.create_issue(
                        'props_destructuring',
                        'low',
                        'Props not destructured',
                        'Consider destructuring props for cleaner code',
                        line_number=i,
                        suggestion='Use destructuring: ({ prop1, prop2 }) => { ... }'
                    ))
        
        return issues
    
    async def _analyze_state_management(self, content: str) -> List[Dict[str, Any]]:
        """Analyze state management patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for state mutations
        for i, line in enumerate(lines, 1):
            # Look for direct state mutations
            if re.search(r'set\w+\([^)]*\.push\(|set\w+\([^)]*\.pop\(|set\w+\([^)]*\[.*\]\s*=', line):
                issues.append(self.create_issue(
                    'state_mutation',
                    'high',
                    'Direct state mutation detected',
                    'State should not be mutated directly. Use immutable update patterns.',
                    line_number=i,
                    suggestion='Use spread operator or immutable update methods'
                ))
            
            # Check for complex state objects without useReducer
            state_match = re.search(r'useState\s*\(\s*{[^}]*}', line)
            if state_match:
                # Count properties in state object
                state_obj = state_match.group()
                prop_count = state_obj.count(',') + 1
                if prop_count > 3:
                    issues.append(self.create_issue(
                        'state_complexity',
                        'medium',
                        'Complex state object',
                        f'State object has {prop_count} properties. Consider using useReducer for complex state.',
                        line_number=i,
                        suggestion='Refactor to use useReducer for better state management'
                    ))
        
        return issues
    
    async def _analyze_jsx_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze JSX patterns and best practices"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for missing keys in lists
            if re.search(r'\.map\s*\(\s*\([^)]*\)\s*=>\s*<', line) and 'key=' not in line:
                issues.append(self.create_issue(
                    'jsx_patterns',
                    'medium',
                    'Missing key prop in list rendering',
                    'Each item in a list should have a unique key prop for optimal React rendering',
                    line_number=i,
                    suggestion='Add unique key prop: <Component key={item.id} />'
                ))
            
            # Check for inline styles
            if re.search(r'style\s*=\s*{{', line):
                issues.append(self.create_issue(
                    'jsx_patterns',
                    'low',
                    'Inline styles detected',
                    'Inline styles create new objects on each render, which can impact performance',
                    line_number=i,
                    suggestion='Consider using CSS classes or styled-components'
                ))
            
            # Check for boolean attribute shorthand
            if re.search(r'\w+={true}', line):
                attr_match = re.search(r'(\w+)={true}', line)
                if attr_match:
                    attr_name = attr_match.group(1)
                    issues.append(self.create_issue(
                        'jsx_patterns',
                        'low',
                        'Redundant boolean attribute',
                        f'Attribute "{attr_name}={{true}}" can be simplified',
                        line_number=i,
                        suggestion=f'Use shorthand: {attr_name}'
                    ))
        
        return issues
    
    async def _suggest_performance_optimizations(self, content: str) -> List[Dict[str, Any]]:
        """Suggest performance optimizations for React code"""
        suggestions = []
        
        # Check for React.memo usage
        if not re.search(self.performance_checks['memo_usage'], content) and self._is_pure_component(content):
            suggestions.append(self.create_suggestion(
                'performance',
                'Consider using React.memo',
                'This component appears to be pure and could benefit from memoization to prevent unnecessary re-renders',
                impact='medium',
                effort='low'
            ))
        
        # Check for useCallback and useMemo usage
        if self._has_expensive_callbacks(content) and not re.search(self.performance_checks['callback_usage'], content):
            suggestions.append(self.create_suggestion(
                'performance',
                'Consider using useCallback',
                'Functions passed as props could be memoized with useCallback to prevent child re-renders',
                impact='medium',
                effort='low'
            ))
        
        if self._has_expensive_calculations(content) and not re.search(self.performance_checks['memo_hook'], content):
            suggestions.append(self.create_suggestion(
                'performance',
                'Consider using useMemo',
                'Expensive calculations detected that could be memoized with useMemo',
                impact='high',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_code_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest general code improvements"""
        suggestions = []
        
        # Suggest custom hooks for repeated logic
        if self._has_repeated_hook_patterns(content):
            suggestions.append(self.create_suggestion(
                'refactoring',
                'Extract custom hook',
                'Repeated hook patterns detected. Consider extracting into a custom hook for reusability',
                impact='medium',
                effort='medium'
            ))
        
        # Suggest component composition
        if self._has_prop_drilling(content):
            suggestions.append(self.create_suggestion(
                'architecture',
                'Consider component composition',
                'Deep prop passing detected. Consider using component composition or Context API',
                impact='high',
                effort='high'
            ))
        
        return suggestions
    
    async def _suggest_modern_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Suggest modern React patterns and practices"""
        suggestions = []
        
        # Suggest functional components over class components
        if re.search(self.component_patterns['class_component'], content):
            suggestions.append(self.create_suggestion(
                'modernization',
                'Convert to functional component',
                'Consider converting class component to functional component with hooks for better performance and simpler code',
                impact='medium',
                effort='high'
            ))
        
        # Suggest optional chaining
        if re.search(r'\w+\s*&&\s*\w+\.\w+', content):
            suggestions.append(self.create_suggestion(
                'modernization',
                'Use optional chaining',
                'Use optional chaining (?.) instead of conditional property access for cleaner code',
                impact='low',
                effort='low'
            ))
        
        return suggestions
    
    def _calculate_component_complexity(self, content: str) -> float:
        """Calculate component complexity score"""
        complexity_factors = {
            'lines': len(content.split('\n')),
            'hooks': len(re.findall(self.component_patterns['hook_usage'], content)),
            'jsx_elements': len(re.findall(self.component_patterns['jsx_element'], content)),
            'conditionals': len(re.findall(r'\?.*:', content)),
            'loops': len(re.findall(r'\.map\(|\.filter\(|\.reduce\(', content))
        }
        
        # Weighted complexity calculation
        score = (
            complexity_factors['lines'] * 0.1 +
            complexity_factors['hooks'] * 2 +
            complexity_factors['jsx_elements'] * 0.5 +
            complexity_factors['conditionals'] * 1.5 +
            complexity_factors['loops'] * 1
        )
        
        return min(score / 10, 10.0)  # Normalize to 0-10 scale
    
    def _extract_effect_block(self, content: str, line_num: int) -> str:
        """Extract useEffect block for analysis"""
        lines = content.split('\n')
        if line_num > len(lines):
            return ""
        
        start_line = line_num - 1
        brace_count = 0
        effect_lines = []
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            effect_lines.append(line)
            brace_count += line.count('{') - line.count('}')
            
            if brace_count == 0 and i > start_line:
                break
        
        return '\n'.join(effect_lines)
    
    def _has_dependency_array(self, effect_content: str) -> bool:
        """Check if useEffect has dependency array"""
        return bool(re.search(r'}\s*,\s*\[', effect_content))
    
    def _find_missing_dependencies(self, effect_content: str) -> List[str]:
        """Find variables used in effect but not in dependency array"""
        # This is a simplified implementation
        # In practice, this would require more sophisticated parsing
        variables_used = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', effect_content)
        dependency_array = re.search(r'\[(.*?)\]', effect_content)
        
        if dependency_array:
            dependencies = [dep.strip() for dep in dependency_array.group(1).split(',') if dep.strip()]
            missing = [var for var in set(variables_used) if var not in dependencies and var not in ['console', 'return']]
            return missing[:3]  # Return first 3 missing dependencies
        
        return []
    
    def _uses_props(self, content: str) -> bool:
        """Check if component uses props"""
        return bool(re.search(r'\bprops\.|{\s*\w+.*}\s*=\s*props', content))
    
    def _is_pure_component(self, content: str) -> bool:
        """Check if component appears to be pure (no side effects)"""
        side_effect_patterns = [
            r'useEffect\(',
            r'useState\(',
            r'useReducer\(',
            r'useContext\(',
            r'fetch\(',
            r'axios\.',
            r'localStorage\.',
            r'sessionStorage\.'
        ]
        
        return not any(re.search(pattern, content) for pattern in side_effect_patterns)
    
    def _has_expensive_callbacks(self, content: str) -> bool:
        """Check for functions that could benefit from useCallback"""
        return bool(re.search(r'(?:onClick|onChange|onSubmit)\s*=\s*{\s*\([^)]*\)\s*=>', content))
    
    def _has_expensive_calculations(self, content: str) -> bool:
        """Check for expensive calculations that could be memoized"""
        expensive_patterns = [
            r'\.sort\(',
            r'\.filter\(',
            r'\.reduce\(',
            r'\.find\(',
            r'JSON\.parse\(',
            r'new Date\(',
            r'Math\.\w+\('
        ]
        
        return any(re.search(pattern, content) for pattern in expensive_patterns)
    
    def _has_repeated_hook_patterns(self, content: str) -> bool:
        """Check for repeated hook usage patterns"""
        hook_lines = [line for line in content.split('\n') if 'use' in line and '(' in line]
        return len(set(hook_lines)) < len(hook_lines) * 0.8  # 80% uniqueness threshold
    
    def _has_prop_drilling(self, content: str) -> bool:
        """Check for prop drilling patterns"""
        prop_passing = re.findall(r'(\w+)={\w+}', content)
        return len(prop_passing) > 5  # More than 5 props might indicate drilling
    
    def _calculate_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score based on analysis completeness"""
        base_confidence = 0.8
        
        # Adjust based on file size and complexity
        lines = len(content.split('\n'))
        if lines < 50:
            base_confidence += 0.1
        elif lines > 200:
            base_confidence -= 0.1
        
        # Adjust based on issues found
        if len(issues) == 0:
            base_confidence += 0.1
        elif len(issues) > 10:
            base_confidence -= 0.1
        
        return max(0.5, min(1.0, base_confidence))
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle chat interactions for React code assistance"""
        message = context.get('message', '').lower()
        
        if 'component' in message:
            return "I can help you with React components! I specialize in analyzing component structure, optimizing performance, and suggesting modern React patterns. What specific component issue are you working on?"
        elif 'hook' in message:
            return "Great! I'm an expert on React hooks. I can help with useState, useEffect, custom hooks, and ensuring you're following the rules of hooks. What hook-related question do you have?"
        elif 'performance' in message:
            return "Performance optimization is one of my specialties! I can suggest React.memo, useCallback, useMemo usage, and identify performance bottlenecks in your React code. Share your code and I'll analyze it!"
        elif 'props' in message:
            return "I can help with props handling, validation, destructuring, and avoiding prop drilling. Are you having issues with prop types, passing props, or component communication?"
        else:
            return "I'm your React code specialist! I can help with component architecture, hooks, performance optimization, modern React patterns, and best practices. What React coding challenge are you facing?" 