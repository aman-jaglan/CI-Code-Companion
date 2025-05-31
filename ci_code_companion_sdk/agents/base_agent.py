"""
Base Agent Interface for CI Code Companion SDK

This module defines the base agent class that all specialized AI agents inherit from.
It provides a common interface, capability definitions, and shared functionality
for all agent implementations in the SDK.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class AgentCapability(Enum):
    """Enumeration of agent capabilities"""
    CODE_ANALYSIS = "code_analysis"
    TEST_GENERATION = "test_generation"
    CODE_OPTIMIZATION = "code_optimization"
    SECURITY_ANALYSIS = "security_analysis"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    STYLE_CHECK = "style_check"
    DOCUMENTATION_GENERATION = "documentation_generation"
    REFACTORING = "refactoring"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    CHAT_SUPPORT = "chat_support"


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the SDK.
    Defines the common interface and shared functionality.
    """
    
    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the base agent with configuration and logging.
        
        Args:
            config: Agent-specific configuration
            logger: Logger instance for the agent
        """
        self.config = config
        self.logger = logger
        self.name = self.__class__.__name__.lower().replace('agent', '')
        self.version = "1.0.0"
        self.initialized_at = datetime.now()
        
        # Agent statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'last_used': None
        }
        
        # Initialize agent-specific setup
        self._initialize()
    
    def _initialize(self):
        """
        Agent-specific initialization. Override in subclasses if needed.
        """
        self.logger.debug(f"Initializing {self.name} agent")
    
    @abstractmethod
    async def analyze_file(
        self, 
        file_path: str, 
        content: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a file and return analysis results.
        
        Args:
            file_path: Path to the file being analyzed
            content: File content to analyze
            context: Additional context for analysis
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[AgentCapability]:
        """
        Get list of capabilities supported by this agent.
        
        Returns:
            List of AgentCapability enums
        """
        pass
    
    async def generate_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate test cases for code. Override in agents that support test generation.
        
        Args:
            context: Test generation context
            
        Returns:
            Dictionary containing test generation results
        """
        if AgentCapability.TEST_GENERATION not in self.get_capabilities():
            raise NotImplementedError(f"{self.name} agent does not support test generation")
        
        return await self._generate_tests_impl(context)
    
    async def optimize_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize code and suggest improvements. Override in agents that support optimization.
        
        Args:
            context: Optimization context
            
        Returns:
            Dictionary containing optimization results
        """
        if AgentCapability.CODE_OPTIMIZATION not in self.get_capabilities():
            raise NotImplementedError(f"{self.name} agent does not support code optimization")
        
        return await self._optimize_code_impl(context)
    
    async def chat(self, context: Dict[str, Any]) -> str:
        """
        Handle chat/conversation requests. Override in agents that support chat.
        
        Args:
            context: Chat context including message and history
            
        Returns:
            Agent response string
        """
        if AgentCapability.CHAT_SUPPORT not in self.get_capabilities():
            raise NotImplementedError(f"{self.name} agent does not support chat")
        
        return await self._chat_impl(context)
    
    async def _generate_tests_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default test generation implementation. Override in subclasses.
        """
        return {
            'test_code': '# No test generation implementation available',
            'test_file_path': '',
            'coverage_areas': [],
            'explanation': 'Test generation not implemented for this agent',
            'confidence_score': 0.0,
            'metadata': {}
        }
    
    async def _optimize_code_impl(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Default code optimization implementation. Override in subclasses.
        """
        return {
            'optimizations': [],
            'metrics': {},
            'confidence_score': 0.0,
            'metadata': {}
        }
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """
        Default chat implementation. Override in subclasses.
        """
        message = context.get('message', '')
        return f"I'm a {self.name} agent. I can help with code analysis, but I don't have specific chat capabilities for: {message}"
    
    def update_stats(self, success: bool, response_time: float):
        """
        Update agent performance statistics.
        
        Args:
            success: Whether the operation was successful
            response_time: Time taken for the operation
        """
        self.stats['total_requests'] += 1
        self.stats['last_used'] = datetime.now()
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        # Update average response time
        total = self.stats['total_requests']
        current_avg = self.stats['average_response_time']
        self.stats['average_response_time'] = ((current_avg * (total - 1)) + response_time) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get agent performance statistics.
        
        Returns:
            Dictionary containing agent statistics
        """
        return {
            **self.stats,
            'name': self.name,
            'version': self.version,
            'initialized_at': self.initialized_at.isoformat(),
            'capabilities': [cap.value for cap in self.get_capabilities()]
        }
    
    def is_capable_of(self, capability: AgentCapability) -> bool:
        """
        Check if agent has a specific capability.
        
        Args:
            capability: Capability to check
            
        Returns:
            True if agent has the capability
        """
        return capability in self.get_capabilities()
    
    def get_supported_file_types(self) -> List[str]:
        """
        Get list of file extensions this agent can analyze.
        Override in subclasses to specify supported file types.
        
        Returns:
            List of file extensions (e.g., ['.py', '.pyx'])
        """
        return []
    
    def get_supported_frameworks(self) -> List[str]:
        """
        Get list of frameworks this agent specializes in.
        Override in subclasses to specify supported frameworks.
        
        Returns:
            List of framework names
        """
        return []
    
    async def validate_input(self, file_path: str, content: str) -> bool:
        """
        Validate input before processing. Override in subclasses for specific validation.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            True if input is valid
        """
        if not file_path or not content:
            return False
        
        # Check if file type is supported
        supported_types = self.get_supported_file_types()
        if supported_types:
            from pathlib import Path
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in supported_types:
                return False
        
        # Check file size limits
        max_size = self.config.get('max_file_size', 10 * 1024 * 1024)  # 10MB default
        if len(content.encode('utf-8')) > max_size:
            self.logger.warning(f"File {file_path} exceeds size limit ({max_size} bytes)")
            return False
        
        return True
    
    def extract_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Extract metadata from file content. Override in subclasses for specific metadata.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Dictionary containing extracted metadata
        """
        from pathlib import Path
        from ..core.utils import get_file_language, detect_framework, count_lines_of_code
        
        path = Path(file_path)
        language = get_file_language(file_path)
        frameworks = detect_framework(file_path, content) if language else []
        
        metadata = {
            'file_name': path.name,
            'file_extension': path.suffix.lower(),
            'file_size': len(content.encode('utf-8')),
            'language': language,
            'frameworks': frameworks,
            'agent_name': self.name,
            'agent_version': self.version,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # Add line count information if language is detected
        if language:
            line_counts = count_lines_of_code(content, language)
            metadata.update(line_counts)
        
        return metadata
    
    def format_result(
        self, 
        issues: List[Dict[str, Any]], 
        suggestions: List[Dict[str, Any]], 
        metadata: Dict[str, Any],
        confidence_score: float = 0.0
    ) -> Dict[str, Any]:
        """
        Format analysis results in a consistent structure.
        
        Args:
            issues: List of detected issues
            suggestions: List of improvement suggestions
            metadata: Analysis metadata
            confidence_score: Confidence in the analysis results
            
        Returns:
            Formatted result dictionary
        """
        return {
            'issues': issues,
            'suggestions': suggestions,
            'metrics': {
                'total_issues': len(issues),
                'total_suggestions': len(suggestions),
                'agent_confidence': confidence_score
            },
            'confidence_score': confidence_score,
            'metadata': metadata,
            'agent_info': {
                'name': self.name,
                'version': self.version,
                'capabilities': [cap.value for cap in self.get_capabilities()]
            }
        }
    
    def create_issue(
        self,
        issue_type: str,
        severity: str,
        title: str,
        description: str,
        line_number: Optional[int] = None,
        suggestion: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a standardized issue dictionary.
        
        Args:
            issue_type: Type of issue
            severity: Issue severity (critical, high, medium, low, info)
            title: Short issue title
            description: Detailed description
            line_number: Line number where issue occurs
            suggestion: Suggested fix
            **kwargs: Additional issue properties
            
        Returns:
            Standardized issue dictionary
        """
        issue = {
            'type': issue_type,
            'severity': severity,
            'title': title,
            'description': description,
            'source_agent': self.name,
            'confidence_score': kwargs.get('confidence_score', 0.8),
            **kwargs
        }
        
        if line_number is not None:
            issue['line_number'] = line_number
        
        if suggestion:
            issue['suggestion'] = suggestion
        
        return issue
    
    def create_suggestion(
        self,
        suggestion_type: str,
        title: str,
        description: str,
        impact: str = 'medium',
        effort: str = 'medium',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a standardized suggestion dictionary.
        
        Args:
            suggestion_type: Type of suggestion
            title: Short suggestion title
            description: Detailed description
            impact: Expected impact (low, medium, high)
            effort: Implementation effort (low, medium, high)
            **kwargs: Additional suggestion properties
            
        Returns:
            Standardized suggestion dictionary
        """
        return {
            'type': suggestion_type,
            'title': title,
            'description': description,
            'impact': impact,
            'effort': effort,
            'source_agent': self.name,
            'confidence_score': kwargs.get('confidence_score', 0.8),
            **kwargs
        }
    
    def cleanup(self):
        """
        Cleanup agent resources. Override in subclasses if needed.
        """
        self.logger.debug(f"Cleaning up {self.name} agent")
    
    def __str__(self) -> str:
        """String representation of the agent"""
        return f"{self.__class__.__name__}(name={self.name}, version={self.version})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        capabilities = [cap.value for cap in self.get_capabilities()]
        return f"{self.__class__.__name__}(name={self.name}, capabilities={capabilities})" 