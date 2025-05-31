"""DevOps Agent for Infrastructure and Configuration Analysis"""

import re
from typing import Dict, List, Any
from .base_agent import BaseAgent, AgentCapability


class DevOpsAgent(BaseAgent):
    """Specialized agent for DevOps and infrastructure analysis."""
    
    def _initialize(self):
        super()._initialize()
        self.name = "devops"
        
    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        return ['.yml', '.yaml', '.dockerfile', '.sh', '.tf', '.json']
    
    def get_supported_frameworks(self) -> List[str]:
        return ['docker', 'kubernetes', 'terraform', 'ansible']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        metadata = self.extract_metadata(file_path, content)
        
        if 'dockerfile' in file_path.lower():
            issues.extend(await self._analyze_dockerfile(content))
        elif file_path.endswith(('.yml', '.yaml')):
            issues.extend(await self._analyze_yaml(content))
        elif file_path.endswith('.tf'):
            issues.extend(await self._analyze_terraform(content))
        
        suggestions.extend(await self._suggest_optimizations(content))
        
        return self.format_result(issues, suggestions, metadata, 0.8)
    
    async def _analyze_dockerfile(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if line.strip().upper().startswith('FROM') and ':latest' in line:
                issues.append(self.create_issue(
                    'security', 'medium', 'Using latest tag',
                    'Using :latest can lead to inconsistent builds', line_number=i,
                    suggestion='Use specific version tags'
                ))
            
            if line.strip().upper().startswith('RUN') and 'sudo' in line:
                issues.append(self.create_issue(
                    'security', 'high', 'Using sudo in container',
                    'Containers should not need sudo', line_number=i,
                    suggestion='Run container as non-root user'
                ))
        
        return issues
    
    async def _analyze_yaml(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'password:' in line.lower() and any(char in line for char in ['"', "'"]):
                issues.append(self.create_issue(
                    'security', 'critical', 'Hardcoded password',
                    'Passwords should not be in YAML files', line_number=i,
                    suggestion='Use secrets management'
                ))
        
        return issues
    
    async def _analyze_terraform(self, content: str) -> List[Dict[str, Any]]:
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'source = "0.0.0.0/0"' in line:
                issues.append(self.create_issue(
                    'security', 'high', 'Open security group',
                    'Security group allows access from anywhere', line_number=i,
                    suggestion='Restrict to specific IP ranges'
                ))
        
        return issues
    
    async def _suggest_optimizations(self, content: str) -> List[Dict[str, Any]]:
        suggestions = []
        
        if 'FROM ubuntu' in content:
            suggestions.append(self.create_suggestion(
                'optimization', 'Use Alpine Linux',
                'Alpine Linux images are smaller and more secure',
                impact='medium', effort='low'
            ))
        
        return suggestions
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        return "I'm a DevOps expert. I can help with Docker optimization, Kubernetes configurations, Terraform best practices, and CI/CD pipeline improvements. What would you like to know?" 