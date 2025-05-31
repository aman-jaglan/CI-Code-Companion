"""Database Agent for SQL and Database Analysis"""

import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentCapability


class DatabaseAgent(BaseAgent):
    """Specialized agent for database and SQL analysis."""
    
    def _initialize(self):
        super()._initialize()
        self.name = "database"
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        return ['.sql', '.py', '.js', '.ts']
    
    def get_supported_frameworks(self) -> List[str]:
        return ['sqlalchemy', 'sequelize', 'prisma', 'mongoose']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        metadata = self.extract_metadata(file_path, content)
        
        issues.extend(await self._analyze_sql_security(content))
        issues.extend(await self._analyze_performance(content))
        suggestions.extend(await self._suggest_optimizations(content))
        
        return self.format_result(issues, suggestions, metadata, 0.75)
    
    async def _analyze_sql_security(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if re.search(r'(SELECT|INSERT|UPDATE|DELETE).*\+.*[\'"]', line, re.IGNORECASE):
                issues.append(self.create_issue(
                    'security', 'critical', 'SQL Injection Risk',
                    'Dynamic SQL construction detected', line_number=i,
                    suggestion='Use parameterized queries'
                ))
        
        return issues
    
    async def _analyze_performance(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if re.search(r'SELECT\s+\*\s+FROM', line, re.IGNORECASE):
                issues.append(self.create_issue(
                    'performance', 'medium', 'SELECT * usage',
                    'Selecting all columns can impact performance', line_number=i,
                    suggestion='Select only needed columns'
                ))
        
        return issues
    
    async def _suggest_optimizations(self, content: str) -> List[Dict[str, Any]]:
        suggestions = []
        
        if re.search(r'WHERE.*LIKE.*%.*%', content, re.IGNORECASE):
            suggestions.append(self.create_suggestion(
                'performance', 'Consider full-text search',
                'LIKE queries with leading wildcards are slow',
                impact='high', effort='medium'
            ))
        
        return suggestions
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        return "I'm a database expert. I can help with SQL optimization, security, indexing strategies, and database design patterns. What would you like to know?" 