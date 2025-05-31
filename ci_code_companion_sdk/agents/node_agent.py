"""
Node.js Agent for Backend JavaScript/TypeScript Analysis

This agent specializes in analyzing Node.js applications including Express, NestJS, and other
Node.js frameworks. It provides analysis for JavaScript/TypeScript backend code with focus
on performance, security, and Node.js best practices.
"""

import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentCapability


class NodeAgent(BaseAgent):
    """Specialized agent for Node.js backend analysis."""
    
    def _initialize(self):
        super()._initialize()
        self.name = "node"
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.CODE_OPTIMIZATION,
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        return ['.js', '.ts', '.mjs']
    
    def get_supported_frameworks(self) -> List[str]:
        return ['express', 'nestjs', 'koa', 'fastify', 'hapi']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        metadata = self.extract_metadata(file_path, content)
        
        # Node.js specific analysis
        issues.extend(await self._analyze_security(content))
        issues.extend(await self._analyze_performance(content))
        issues.extend(await self._analyze_async_patterns(content))
        
        suggestions.extend(await self._suggest_optimizations(content))
        
        confidence_score = 0.8
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _analyze_security(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for eval usage
            if re.search(r'\beval\s*\(', line):
                issues.append(self.create_issue(
                    'security', 'critical', 'Use of eval()',
                    'eval() can execute arbitrary code', line_number=i,
                    suggestion='Use JSON.parse() for JSON or safer alternatives'
                ))
            
            # Check for SQL injection risks
            if re.search(r'query.*\+.*[\'"`]', line):
                issues.append(self.create_issue(
                    'security', 'high', 'Potential SQL injection',
                    'SQL query concatenation detected', line_number=i,
                    suggestion='Use parameterized queries'
                ))
        
        return issues
    
    async def _analyze_performance(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for synchronous file operations
            if re.search(r'fs\.(readFileSync|writeFileSync)', line):
                issues.append(self.create_issue(
                    'performance', 'medium', 'Synchronous file operation',
                    'Synchronous operations block the event loop', line_number=i,
                    suggestion='Use async versions: fs.readFile, fs.writeFile'
                ))
        
        return issues
    
    async def _analyze_async_patterns(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for missing await
            if re.search(r'(?<!await\s)(?<!return\s)[a-zA-Z_$][a-zA-Z0-9_$]*\.[a-zA-Z_$][a-zA-Z0-9_$]*\s*\([^)]*\)\s*(?!\.|;)', line):
                if 'async' in ''.join(lines[max(0, i-5):i]):
                    issues.append(self.create_issue(
                        'async', 'medium', 'Possible missing await',
                        'Async operation might need await', line_number=i,
                        suggestion='Add await if this returns a Promise'
                    ))
        
        return issues
    
    async def _suggest_optimizations(self, content: str) -> List[Dict[str, Any]]:
        suggestions = []
        
        if 'require(' in content and 'import ' not in content:
            suggestions.append(self.create_suggestion(
                'modernization', 'Use ES6 imports',
                'ES6 imports provide better tree shaking and static analysis',
                impact='medium', effort='low'
            ))
        
        return suggestions
    
    async def _generate_tests_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'test_code': '// Node.js test code would be generated here',
            'test_file_path': context.get('file_path', '').replace('.js', '.test.js'),
            'coverage_areas': ['unit_tests', 'integration_tests'],
            'explanation': 'Generated Node.js unit tests',
            'confidence_score': 0.75,
            'framework': 'jest',
            'dependencies': ['jest', 'supertest'],
            'metadata': {}
        }
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        return "I'm a Node.js expert. I can help with Express apps, async patterns, performance optimization, and security best practices. What would you like to know?" 