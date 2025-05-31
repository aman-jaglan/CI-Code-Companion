"""Mobile Agent for Mobile Development Analysis"""

import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentCapability


class MobileAgent(BaseAgent):
    """Specialized agent for mobile development analysis."""
    
    def _initialize(self):
        super()._initialize()
        self.name = "mobile"
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        return ['.dart', '.swift', '.kt', '.java', '.tsx', '.ts', '.js']
    
    def get_supported_frameworks(self) -> List[str]:
        return ['react-native', 'flutter', 'ionic', 'xamarin']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        metadata = self.extract_metadata(file_path, content)
        
        if file_path.endswith('.dart'):
            issues.extend(await self._analyze_flutter(content))
        elif 'react-native' in content.lower():
            issues.extend(await self._analyze_react_native(content))
        
        suggestions.extend(await self._suggest_optimizations(content))
        
        return self.format_result(issues, suggestions, metadata, 0.7)
    
    async def _analyze_flutter(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'setState' in line and 'async' in ''.join(lines[max(0, i-3):i+3]):
                issues.append(self.create_issue(
                    'performance', 'medium', 'setState in async context',
                    'setState should not be called after async operations without checking mounted',
                    line_number=i, suggestion='Check if widget is still mounted'
                ))
        
        return issues
    
    async def _analyze_react_native(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'console.log' in line:
                issues.append(self.create_issue(
                    'performance', 'low', 'Console.log in production',
                    'Console statements can impact performance in production',
                    line_number=i, suggestion='Remove console.log statements for production'
                ))
        
        return issues
    
    async def _suggest_optimizations(self, content: str) -> List[Dict[str, Any]]:
        suggestions = []
        
        if 'FlatList' not in content and 'ListView' in content:
            suggestions.append(self.create_suggestion(
                'performance', 'Use FlatList instead of ListView',
                'FlatList provides better performance for large lists',
                impact='high', effort='medium'
            ))
        
        return suggestions
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        return "I'm a mobile development expert. I can help with React Native, Flutter, performance optimization, and mobile-specific best practices. What would you like to know?" 