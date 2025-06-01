"""
Enhanced React Code Agent with Cursor-style Prompting

This agent integrates with the PromptLoader system to provide Cursor-like functionality
for React development with optimizations for Gemini 2.5 Pro's 1M context window.
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability
from ....core.prompt_loader import PromptLoader


class EnhancedReactCodeAgent(BaseAgent):
    """
    Enhanced React Code Agent with Cursor-style prompting and RAG capabilities.
    Optimized for Gemini 2.5 Pro with comprehensive context utilization.
    """
    
    def __init__(self, config: Dict[str, Any], logger, prompt_loader: PromptLoader):
        super().__init__(config, logger)
        self.prompt_loader = prompt_loader
        self.conversation_history = []
        self.codebase_index = {}  # For RAG functionality
        
    def _initialize(self):
        """Initialize Enhanced React Code Agent"""
        super()._initialize()
        self.name = "enhanced_react_code"
        self.version = "3.0.0"
        
        # React-specific pattern detection for better context
        self.patterns = {
            'components': {
                'functional': r'(?:const|function)\s+([A-Z][a-zA-Z0-9]*)\s*(?:=\s*)?(?:\([^)]*\))?\s*(?:=>\s*)?{',
                'class': r'class\s+([A-Z][a-zA-Z0-9]*)\s+extends\s+(?:React\.)?Component',
                'arrow_function': r'const\s+([A-Z][a-zA-Z0-9]*)\s*=\s*\([^)]*\)\s*=>\s*{',
            },
            'hooks': {
                'state': r'const\s+\[[^,]+,\s*set[A-Z][a-zA-Z0-9]*\]\s*=\s*useState',
                'effect': r'useEffect\s*\(\s*\(\)\s*=>\s*{',
                'memo': r'useMemo\s*\(\s*\(\)\s*=>\s*{',
                'callback': r'useCallback\s*\(\s*\([^)]*\)\s*=>\s*{',
                'custom': r'use[A-Z][a-zA-Z0-9]*\s*\(',
            },
            'performance': {
                'memo_component': r'React\.memo\s*\(',
                'lazy_import': r'React\.lazy\s*\(',
                'suspense': r'<Suspense',
                'inline_styles': r'style\s*=\s*{{',
                'inline_functions': r'(?:onClick|onChange|onSubmit)\s*=\s*{\s*\([^)]*\)\s*=>',
            },
            'typescript': {
                'interface': r'interface\s+([A-Z][a-zA-Z0-9]*)',
                'type': r'type\s+([A-Z][a-zA-Z0-9]*)',
                'generic': r'<[A-Z][a-zA-Z0-9,\s|&]+>',
                'props_typing': r':\s*([A-Z][a-zA-Z0-9]*Props)',
            }
        }
    
    async def analyze_with_context(
        self, 
        file_path: str, 
        content: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze React code using enhanced prompting with full context.
        
        Args:
            file_path: Path to React file
            content: File content
            context: Full context including project info, related files, conversation history
            
        Returns:
            Comprehensive analysis with Cursor-style insights
        """
        
        # Build enhanced context for the agent
        enhanced_context = await self._build_enhanced_context(file_path, content, context)
        
        # Get enhanced prompt from prompt loader
        agent_prompt = self.prompt_loader.get_enhanced_prompt('react_code', enhanced_context)
        
        # Perform context-aware analysis
        analysis_result = await self._analyze_with_gemini_optimization(
            file_path, content, enhanced_context, agent_prompt
        )
        
        # Store conversation for future context
        self._update_conversation_history(context.get('user_message', ''), analysis_result)
        
        return analysis_result
    
    async def _build_enhanced_context(
        self, 
        file_path: str, 
        content: str, 
        base_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build comprehensive context for analysis"""
        
        enhanced_context = {
            'selected_file': {
                'path': file_path,
                'content': content,
                'language': self._detect_language(file_path),
                'last_modified': datetime.now().isoformat(),
                'metadata': await self._extract_comprehensive_metadata(content)
            },
            'project_info': base_context.get('project_info', {}),
            'conversation_history': self.conversation_history,
            'related_files': await self._find_related_files(file_path, content, base_context),
            'codebase_context': await self._get_codebase_context(file_path, content),
            'user_intent': base_context.get('user_intent', 'analysis'),
            'performance_context': {
                'gemini_model': 'gemini-2.5-pro',
                'context_window': '1M tokens',
                'optimization_level': 'maximum'
            }
        }
        
        return enhanced_context
    
    async def _analyze_with_gemini_optimization(
        self, 
        file_path: str, 
        content: str, 
        context: Dict[str, Any], 
        agent_prompt: str
    ) -> Dict[str, Any]:
        """Perform analysis optimized for Gemini 2.5 Pro"""
        
        # Extract comprehensive file analysis
        file_analysis = await self._comprehensive_file_analysis(content)
        
        # Perform pattern-based analysis
        pattern_analysis = await self._pattern_based_analysis(content)
        
        # Generate context-aware suggestions
        suggestions = await self._generate_contextual_suggestions(
            content, context, file_analysis
        )
        
        # Perform cross-file analysis if related files are available
        cross_file_insights = await self._cross_file_analysis(context.get('related_files', []))
        
        # Generate final response using the enhanced prompt
        response = await self._generate_enhanced_response(
            file_path, content, file_analysis, pattern_analysis, 
            suggestions, cross_file_insights, agent_prompt
        )
        
        return {
            'success': True,
            'analysis': response,
            'metadata': file_analysis.get('metadata', {}),
            'suggestions': suggestions,
            'cross_file_insights': cross_file_insights,
            'confidence_score': self._calculate_enhanced_confidence(
                file_analysis, pattern_analysis, context
            ),
            'context_used': True,
            'tokens_used': len(agent_prompt.split()) + len(content.split()),  # Rough estimate
            'processing_time': datetime.now().isoformat()
        }
    
    async def _comprehensive_file_analysis(self, content: str) -> Dict[str, Any]:
        """Perform comprehensive React file analysis"""
        
        analysis = {
            'components': self._analyze_components(content),
            'hooks': self._analyze_hooks_comprehensive(content),
            'typescript': self._analyze_typescript_usage(content),
            'performance': self._analyze_performance_patterns(content),
            'accessibility': self._analyze_accessibility(content),
            'testing': self._analyze_testability(content),
            'architecture': self._analyze_architecture_patterns(content),
            'metadata': {
                'lines_of_code': len([l for l in content.split('\n') if l.strip()]),
                'complexity_score': self._calculate_complexity_score(content),
                'maintainability_score': self._calculate_maintainability_score(content),
                'readability_score': self._calculate_readability_score(content)
            }
        }
        
        return analysis
    
    def _analyze_components(self, content: str) -> Dict[str, Any]:
        """Analyze React components in the file"""
        components = {
            'functional': [],
            'class': [],
            'total_count': 0,
            'naming_issues': [],
            'size_issues': []
        }
        
        # Find functional components
        func_matches = re.finditer(self.patterns['components']['functional'], content)
        for match in func_matches:
            component_name = match.group(1)
            components['functional'].append({
                'name': component_name,
                'line': content[:match.start()].count('\n') + 1,
                'properly_named': component_name[0].isupper()
            })
        
        # Find class components
        class_matches = re.finditer(self.patterns['components']['class'], content)
        for match in class_matches:
            component_name = match.group(1)
            components['class'].append({
                'name': component_name,
                'line': content[:match.start()].count('\n') + 1,
                'properly_named': component_name[0].isupper()
            })
        
        components['total_count'] = len(components['functional']) + len(components['class'])
        
        # Check for naming issues
        all_components = components['functional'] + components['class']
        for comp in all_components:
            if not comp['properly_named']:
                components['naming_issues'].append(comp['name'])
        
        return components
    
    def _analyze_hooks_comprehensive(self, content: str) -> Dict[str, Any]:
        """Comprehensive hooks analysis"""
        hooks_analysis = {
            'useState': [],
            'useEffect': [],
            'useMemo': [],
            'useCallback': [],
            'custom_hooks': [],
            'issues': [],
            'best_practices': []
        }
        
        # Analyze useState usage
        state_matches = re.finditer(self.patterns['hooks']['state'], content)
        for match in state_matches:
            line_num = content[:match.start()].count('\n') + 1
            hooks_analysis['useState'].append({
                'line': line_num,
                'declaration': match.group(0)
            })
        
        # Analyze useEffect usage
        effect_matches = re.finditer(self.patterns['hooks']['effect'], content)
        for match in effect_matches:
            line_num = content[:match.start()].count('\n') + 1
            effect_content = self._extract_effect_content(content, match.start())
            
            hooks_analysis['useEffect'].append({
                'line': line_num,
                'has_dependency_array': '], [' in effect_content or '], []' in effect_content,
                'has_cleanup': 'return () =>' in effect_content,
                'content_preview': effect_content[:100] + '...' if len(effect_content) > 100 else effect_content
            })
        
        # Analyze performance hooks
        memo_matches = re.finditer(self.patterns['hooks']['memo'], content)
        for match in memo_matches:
            line_num = content[:match.start()].count('\n') + 1
            hooks_analysis['useMemo'].append({'line': line_num})
        
        callback_matches = re.finditer(self.patterns['hooks']['callback'], content)
        for match in callback_matches:
            line_num = content[:match.start()].count('\n') + 1
            hooks_analysis['useCallback'].append({'line': line_num})
        
        # Find custom hooks
        custom_matches = re.finditer(self.patterns['hooks']['custom'], content)
        for match in custom_matches:
            hook_call = match.group(0)
            hook_name = hook_call.split('(')[0]
            if hook_name not in ['useState', 'useEffect', 'useMemo', 'useCallback', 'useContext', 'useReducer']:
                hooks_analysis['custom_hooks'].append(hook_name)
        
        return hooks_analysis
    
    def _analyze_typescript_usage(self, content: str) -> Dict[str, Any]:
        """Analyze TypeScript usage and patterns"""
        ts_analysis = {
            'interfaces': [],
            'types': [],
            'generics_usage': [],
            'props_typing': [],
            'type_safety_score': 0,
            'recommendations': []
        }
        
        # Find interfaces
        interface_matches = re.finditer(self.patterns['typescript']['interface'], content)
        for match in interface_matches:
            ts_analysis['interfaces'].append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Find type definitions
        type_matches = re.finditer(self.patterns['typescript']['type'], content)
        for match in type_matches:
            ts_analysis['types'].append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Check props typing
        props_typing_matches = re.finditer(self.patterns['typescript']['props_typing'], content)
        for match in props_typing_matches:
            ts_analysis['props_typing'].append(match.group(1))
        
        # Calculate type safety score
        ts_analysis['type_safety_score'] = self._calculate_type_safety_score(content)
        
        return ts_analysis
    
    def _analyze_performance_patterns(self, content: str) -> Dict[str, Any]:
        """Analyze performance-related patterns"""
        perf_analysis = {
            'memo_usage': bool(re.search(self.patterns['performance']['memo_component'], content)),
            'lazy_loading': bool(re.search(self.patterns['performance']['lazy_import'], content)),
            'suspense_usage': bool(re.search(self.patterns['performance']['suspense'], content)),
            'performance_issues': [],
            'optimization_opportunities': []
        }
        
        # Check for performance anti-patterns
        inline_styles = re.findall(self.patterns['performance']['inline_styles'], content)
        if inline_styles:
            perf_analysis['performance_issues'].append({
                'type': 'inline_styles',
                'count': len(inline_styles),
                'severity': 'medium'
            })
        
        inline_functions = re.findall(self.patterns['performance']['inline_functions'], content)
        if inline_functions:
            perf_analysis['performance_issues'].append({
                'type': 'inline_functions',
                'count': len(inline_functions),
                'severity': 'high'
            })
        
        return perf_analysis
    
    def _analyze_accessibility(self, content: str) -> Dict[str, Any]:
        """Analyze accessibility patterns"""
        a11y_patterns = {
            'aria_labels': r'aria-label\s*=',
            'aria_describedby': r'aria-describedby\s*=',
            'role_attributes': r'role\s*=',
            'alt_text': r'alt\s*=',
            'semantic_html': r'<(?:header|nav|main|section|article|aside|footer)',
            'focus_management': r'(?:autoFocus|tabIndex|onFocus|onBlur)',
        }
        
        a11y_analysis = {}
        for pattern_name, pattern in a11y_patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            a11y_analysis[pattern_name] = len(matches)
        
        a11y_analysis['accessibility_score'] = self._calculate_accessibility_score(a11y_analysis)
        
        return a11y_analysis
    
    def _analyze_testability(self, content: str) -> Dict[str, Any]:
        """Analyze code testability"""
        testability = {
            'test_friendly_patterns': [],
            'testing_challenges': [],
            'testability_score': 0
        }
        
        # Check for test-friendly patterns
        if 'data-testid' in content:
            testability['test_friendly_patterns'].append('data-testid attributes')
        
        if re.search(r'export\s+{.*}', content):
            testability['test_friendly_patterns'].append('named exports')
        
        # Check for testing challenges
        if re.search(self.patterns['performance']['inline_functions'], content):
            testability['testing_challenges'].append('inline functions make mocking difficult')
        
        if 'Math.random()' in content or 'Date.now()' in content:
            testability['testing_challenges'].append('non-deterministic functions')
        
        testability['testability_score'] = self._calculate_testability_score(content)
        
        return testability
    
    def _analyze_architecture_patterns(self, content: str) -> Dict[str, Any]:
        """Analyze architectural patterns"""
        patterns = {
            'container_presentational': False,
            'custom_hooks': len(re.findall(r'use[A-Z][a-zA-Z0-9]*\s*\(', content)) > 0,
            'context_usage': 'useContext' in content or 'createContext' in content,
            'state_management': 'useReducer' in content or 'useState' in content,
            'composition_patterns': '...props' in content or 'children' in content,
        }
        
        return patterns
    
    async def _find_related_files(
        self, 
        file_path: str, 
        content: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find files related to the current React component"""
        related_files = []
        
        # Extract imports to find related files
        import_matches = re.findall(r'import.*from\s+[\'"]([^\'"]+)[\'"]', content)
        
        for import_path in import_matches:
            if not import_path.startswith('.'):  # Skip node_modules
                continue
                
            related_files.append({
                'path': import_path,
                'relationship': 'import',
                'language': self._detect_language(import_path),
                'is_critical': True
            })
        
        # Find test files
        base_name = file_path.replace('.tsx', '').replace('.jsx', '').replace('.ts', '').replace('.js', '')
        test_patterns = [f"{base_name}.test.tsx", f"{base_name}.test.ts", f"{base_name}.spec.tsx"]
        
        for test_path in test_patterns:
            related_files.append({
                'path': test_path,
                'relationship': 'test_file',
                'language': 'typescript',
                'is_critical': False
            })
        
        return related_files[:20]  # Limit for context window optimization
    
    async def _get_codebase_context(self, file_path: str, content: str) -> Dict[str, Any]:
        """Get relevant codebase context for RAG functionality"""
        # This would integrate with a vector database or semantic search
        # For now, return basic context
        return {
            'similar_components': [],
            'common_patterns': [],
            'project_conventions': [],
            'reusable_hooks': []
        }
    
    async def _generate_contextual_suggestions(
        self, 
        content: str, 
        context: Dict[str, Any], 
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate context-aware suggestions"""
        suggestions = []
        
        # Performance suggestions
        if analysis['performance']['performance_issues']:
            for issue in analysis['performance']['performance_issues']:
                if issue['type'] == 'inline_functions':
                    suggestions.append({
                        'type': 'performance',
                        'priority': 'high',
                        'title': 'Extract inline functions',
                        'description': f'Found {issue["count"]} inline functions that should be extracted using useCallback',
                        'code_example': 'const handleClick = useCallback(() => { /* logic */ }, [dependencies]);'
                    })
        
        # TypeScript suggestions
        if context.get('selected_file', {}).get('language') == 'typescript':
            if analysis['typescript']['type_safety_score'] < 0.8:
                suggestions.append({
                    'type': 'typescript',
                    'priority': 'medium',
                    'title': 'Improve type safety',
                    'description': 'Add proper typing for props and state',
                    'code_example': 'interface ComponentProps { title: string; onClick: () => void; }'
                })
        
        # Accessibility suggestions
        if analysis['accessibility']['accessibility_score'] < 0.7:
            suggestions.append({
                'type': 'accessibility',
                'priority': 'high',
                'title': 'Improve accessibility',
                'description': 'Add ARIA labels and semantic HTML elements',
                'code_example': '<button aria-label="Close dialog" onClick={handleClose}>×</button>'
            })
        
        return suggestions
    
    async def _cross_file_analysis(self, related_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across related files"""
        return {
            'component_patterns': [],
            'shared_types': [],
            'common_imports': [],
            'architecture_insights': []
        }
    
    async def _generate_enhanced_response(
        self, 
        file_path: str, 
        content: str, 
        file_analysis: Dict[str, Any], 
        pattern_analysis: Dict[str, Any], 
        suggestions: List[Dict[str, Any]], 
        cross_file_insights: Dict[str, Any], 
        agent_prompt: str
    ) -> str:
        """Generate final enhanced response using the agent prompt"""
        
        # Build response sections based on analysis
        response_parts = []
        
        # File overview
        response_parts.append(f"## React Component Analysis: {file_path.split('/')[-1]}")
        response_parts.append("")
        
        # Component summary
        components = file_analysis.get('components', {})
        total_components = components.get('total_count', 0)
        
        if total_components > 0:
            response_parts.append(f"**Components Found**: {total_components}")
            if components.get('functional'):
                func_names = [c['name'] for c in components['functional']]
                response_parts.append(f"- Functional: {', '.join(func_names)}")
            if components.get('class'):
                class_names = [c['name'] for c in components['class']]
                response_parts.append(f"- Class: {', '.join(class_names)}")
            response_parts.append("")
        
        # Code quality metrics
        metadata = file_analysis.get('metadata', {})
        response_parts.append("### Code Quality Metrics")
        response_parts.append(f"- **Lines of Code**: {metadata.get('lines_of_code', 'N/A')}")
        response_parts.append(f"- **Complexity Score**: {metadata.get('complexity_score', 0):.1f}/10")
        response_parts.append(f"- **Maintainability**: {metadata.get('maintainability_score', 0):.1f}/10")
        response_parts.append(f"- **Type Safety**: {file_analysis.get('typescript', {}).get('type_safety_score', 0):.1f}/10")
        response_parts.append("")
        
        # Issues and suggestions
        if suggestions:
            response_parts.append("### Recommendations")
            for suggestion in suggestions[:5]:  # Top 5 suggestions
                priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(suggestion['priority'], "ℹ️")
                response_parts.append(f"**{priority_emoji} {suggestion['title']}** ({suggestion['type']})")
                response_parts.append(f"  {suggestion['description']}")
                if suggestion.get('code_example'):
                    response_parts.append(f"  ```javascript\n  {suggestion['code_example']}\n  ```")
                response_parts.append("")
        
        # Performance insights
        perf_analysis = file_analysis.get('performance', {})
        if perf_analysis.get('performance_issues'):
            response_parts.append("### Performance Analysis")
            for issue in perf_analysis['performance_issues']:
                response_parts.append(f"- **{issue['type']}**: {issue['count']} instances (Severity: {issue['severity']})")
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    def _update_conversation_history(self, user_message: str, agent_response: Dict[str, Any]):
        """Update conversation history for context"""
        self.conversation_history.append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        self.conversation_history.append({
            'role': 'assistant',
            'content': agent_response.get('analysis', ''),
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 20 messages for context management
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    # Helper methods for scoring
    def _calculate_complexity_score(self, content: str) -> float:
        """Calculate code complexity score (0-10)"""
        lines = content.split('\n')
        complexity_indicators = 0
        
        # Count complexity indicators
        for line in lines:
            if re.search(r'\b(if|else|while|for|switch|case|try|catch)\b', line):
                complexity_indicators += 1
            if '?' in line and ':' in line:  # Ternary operators
                complexity_indicators += 1
            if '&&' in line or '||' in line:  # Logical operators
                complexity_indicators += 0.5
        
        # Normalize to 0-10 scale
        normalized = min(10, complexity_indicators / max(1, len(lines)) * 100)
        return round(normalized, 1)
    
    def _calculate_maintainability_score(self, content: str) -> float:
        """Calculate maintainability score (0-10)"""
        score = 10.0
        
        # Deduct points for various issues
        if len(content.split('\n')) > 200:
            score -= 2  # Long files
        
        if len(re.findall(r'TODO|FIXME|HACK', content, re.IGNORECASE)) > 0:
            score -= 1  # Technical debt markers
        
        if content.count('any') > 3:  # TypeScript any usage
            score -= 1
        
        # Add points for good practices
        if re.search(r'interface\s+\w+Props', content):
            score += 0.5  # Proper prop typing
        
        if 'export default' in content or 'export {' in content:
            score += 0.5  # Proper exports
        
        return max(0, min(10, round(score, 1)))
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score (0-10)"""
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        # Check comment ratio
        comment_lines = len([l for l in lines if l.startswith('//') or l.startswith('/*')])
        comment_ratio = comment_lines / max(1, len(lines))
        
        # Check average line length
        avg_line_length = sum(len(l) for l in lines) / max(1, len(lines))
        
        score = 8.0  # Base score
        
        # Adjust based on metrics
        if comment_ratio > 0.1:
            score += 1  # Good commenting
        if avg_line_length < 80:
            score += 1  # Good line length
        else:
            score -= 1  # Lines too long
        
        return max(0, min(10, round(score, 1)))
    
    def _calculate_type_safety_score(self, content: str) -> float:
        """Calculate TypeScript type safety score (0-1)"""
        if not ('.tsx' in content or '.ts' in content or 'interface' in content):
            return 0.5  # Not TypeScript
        
        score = 0.0
        
        # Check for proper typing patterns
        if re.search(r'interface\s+\w+Props', content):
            score += 0.3
        
        if re.search(r':\s*\w+(\[\])?(?:\s*\|\s*\w+)*', content):
            score += 0.3  # Type annotations
        
        if 'any' not in content:
            score += 0.2  # No any usage
        
        if re.search(r'<[A-Z]\w*>', content):
            score += 0.2  # Generic usage
        
        return min(1.0, score)
    
    def _calculate_accessibility_score(self, a11y_analysis: Dict[str, Any]) -> float:
        """Calculate accessibility score (0-1)"""
        score = 0.0
        max_score = 6
        
        # Award points for accessibility features
        if a11y_analysis.get('aria_labels', 0) > 0:
            score += 1
        if a11y_analysis.get('semantic_html', 0) > 0:
            score += 1
        if a11y_analysis.get('alt_text', 0) > 0:
            score += 1
        if a11y_analysis.get('role_attributes', 0) > 0:
            score += 1
        if a11y_analysis.get('focus_management', 0) > 0:
            score += 1
        if a11y_analysis.get('aria_describedby', 0) > 0:
            score += 1
        
        return min(1.0, score / max_score)
    
    def _calculate_testability_score(self, content: str) -> float:
        """Calculate testability score (0-1)"""
        score = 0.5  # Base score
        
        # Good patterns
        if 'data-testid' in content:
            score += 0.2
        if re.search(r'export\s+{', content):
            score += 0.1
        if not re.search(r'Math\.random|Date\.now', content):
            score += 0.1
        
        # Bad patterns
        if re.search(self.patterns['performance']['inline_functions'], content):
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_enhanced_confidence(
        self, 
        file_analysis: Dict[str, Any], 
        pattern_analysis: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> float:
        """Calculate enhanced confidence score"""
        base_score = 0.8
        
        # Increase confidence based on context richness
        if context.get('related_files'):
            base_score += 0.1
        
        if context.get('conversation_history'):
            base_score += 0.05
        
        if file_analysis.get('metadata', {}).get('complexity_score', 0) < 5:
            base_score += 0.05  # Simpler files are easier to analyze
        
        return min(1.0, base_score)
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext = file_path.split('.')[-1].lower()
        return {
            'tsx': 'typescript',
            'ts': 'typescript', 
            'jsx': 'javascript',
            'js': 'javascript'
        }.get(ext, 'unknown')
    
    def _extract_effect_content(self, content: str, start_pos: int) -> str:
        """Extract useEffect content for analysis"""
        # Find the matching closing brace
        brace_count = 0
        pos = start_pos
        
        while pos < len(content):
            if content[pos] == '{':
                brace_count += 1
            elif content[pos] == '}':
                brace_count -= 1
                if brace_count == 0:
                    break
            pos += 1
        
        return content[start_pos:pos+1] 