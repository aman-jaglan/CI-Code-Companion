"""
AI Agent Management System

This module provides comprehensive management of AI agents for code analysis, test generation,
and optimization. It handles agent registration, intelligent routing based on file content,
parallel execution coordination, and agent lifecycle management for optimal performance.

Features:
- Dynamic agent registration and discovery
- Intelligent agent selection based on file content analysis
- Parallel agent execution with resource management
- Agent health monitoring and failover
- Extensible plugin system for custom agents
- Performance optimization and caching
- Configuration-driven agent behavior
"""

import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Type, Set, Callable
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import inspect
from datetime import datetime, timedelta
import threading

from ..core.config import SDKConfig
from ..core.exceptions import AgentError, ConfigurationError
from .base_agent import BaseAgent, AgentCapability
from ..models.analysis_model import AnalysisResult


class AgentManager:
    """
    Central manager for all AI agents in the SDK.
    Handles agent registration, routing, execution, and lifecycle management.
    """
    
    def __init__(self, config: SDKConfig, logger: logging.Logger):
        """
        Initialize the agent manager with configuration and logging.
        Sets up agent registry, detection patterns, and execution infrastructure.
        
        Args:
            config: SDK configuration instance
            logger: Logger instance for agent manager operations
        """
        self.config = config
        self.logger = logger
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_classes: Dict[str, Type[BaseAgent]] = {}
        self.detection_patterns: Dict[str, Dict[str, Any]] = {}
        self.agent_stats: Dict[str, Dict[str, Any]] = {}
        self.agent_locks: Dict[str, threading.Lock] = {}
        
        # Thread pool for agent operations
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="AgentManager"
        )
        
        # Initialize built-in agents
        self._initialize_builtin_agents()
        
        # Load custom agents if configured
        self._load_custom_agents()
        
        # Setup agent health monitoring
        self._setup_health_monitoring()
        
        self.logger.info(f"Agent Manager initialized with {len(self.agents)} agents")
    
    def _initialize_builtin_agents(self):
        """
        Initialize and register built-in agents.
        Note: Specialized agents are now handled by StreamlinedAIService.
        This AgentManager is maintained for backward compatibility.
        """
        # Legacy agent manager - specialized agents are handled by StreamlinedAIService
        # No builtin agents - all functionality moved to specialized agents
        builtin_agents = {}
        
        for agent_type, config in builtin_agents.items():
            try:
                self._register_agent_type(agent_type, config)
                self.logger.debug(f"Registered builtin agent: {agent_type}")
            except Exception as e:
                self.logger.warning(f"Failed to register builtin agent {agent_type}: {e}")
    
    def _register_agent_type(self, agent_type: str, agent_config: Dict[str, Any]):
        """
        Register an agent type with its configuration and detection patterns.
        
        Args:
            agent_type: Unique identifier for the agent type
            agent_config: Configuration dictionary containing module, class, and patterns
        """
        try:
            # Store detection patterns
            self.detection_patterns[agent_type] = agent_config.get('patterns', {})
            
            # Try to load and register the agent class
            module_name = agent_config['module']
            class_name = agent_config['class']
            
            try:
                module = importlib.import_module(module_name)
                agent_class = getattr(module, class_name)
                
                # Validate that it's a proper agent class
                if not issubclass(agent_class, BaseAgent):
                    raise ValueError(f"Agent class {class_name} must inherit from BaseAgent")
                
                self.agent_classes[agent_type] = agent_class
                
                # Initialize agent instance if enabled
                if self.config.is_agent_enabled(agent_type):
                    agent_instance = self._create_agent_instance(agent_type, agent_class)
                    self.agents[agent_type] = agent_instance
                    self.agent_locks[agent_type] = threading.Lock()
                    
                    # Initialize stats tracking
                    self.agent_stats[agent_type] = {
                        'created_at': datetime.now(),
                        'total_requests': 0,
                        'successful_requests': 0,
                        'failed_requests': 0,
                        'average_response_time': 0.0,
                        'last_used': None,
                        'health_status': 'healthy'
                    }
                
            except ImportError as e:
                # Agent module not available - store class info for lazy loading
                self.logger.warning(f"Agent module {module_name} not available: {e}")
                self.agent_classes[agent_type] = None
            
        except Exception as e:
            raise ConfigurationError(f"Failed to register agent type {agent_type}: {e}")
    
    def _create_agent_instance(self, agent_type: str, agent_class: Type[BaseAgent]) -> BaseAgent:
        """
        Create and initialize an agent instance with proper configuration.
        
        Args:
            agent_type: Type of agent to create
            agent_class: Agent class to instantiate
            
        Returns:
            Initialized agent instance
        """
        agent_config = self.config.get_agent_config(agent_type)
        
        # Create agent instance with configuration
        agent_instance = agent_class(
            config=agent_config,
            logger=self.logger.getChild(agent_type)
        )
        
        # Validate agent capabilities
        self._validate_agent_capabilities(agent_instance)
        
        return agent_instance
    
    def _validate_agent_capabilities(self, agent: BaseAgent):
        """
        Validate that an agent properly implements required capabilities.
        
        Args:
            agent: Agent instance to validate
        """
        required_methods = ['analyze_file', 'get_capabilities']
        
        for method_name in required_methods:
            if not hasattr(agent, method_name) or not callable(getattr(agent, method_name)):
                raise ConfigurationError(f"Agent {type(agent).__name__} missing required method: {method_name}")
    
    def _load_custom_agents(self):
        """
        Load custom agents from configured directories.
        Supports dynamic loading of user-defined agents.
        """
        custom_agent_dirs = self.config.agent_config.get('custom_agent_directories', [])
        
        for agent_dir in custom_agent_dirs:
            try:
                self._load_agents_from_directory(agent_dir)
            except Exception as e:
                self.logger.warning(f"Failed to load custom agents from {agent_dir}: {e}")
    
    def _load_agents_from_directory(self, agent_dir: str):
        """
        Load agents from a specific directory.
        
        Args:
            agent_dir: Directory path containing agent modules
        """
        agent_path = Path(agent_dir)
        if not agent_path.exists() or not agent_path.is_dir():
            self.logger.warning(f"Custom agent directory not found: {agent_dir}")
            return
        
        # Look for Python files that might contain agents
        for python_file in agent_path.glob("*.py"):
            if python_file.name.startswith("_"):
                continue
                
            try:
                self._load_agent_from_file(python_file)
            except Exception as e:
                self.logger.warning(f"Failed to load agent from {python_file}: {e}")
    
    def _load_agent_from_file(self, file_path: Path):
        """
        Load agent class from a Python file.
        
        Args:
            file_path: Path to Python file containing agent class
        """
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find agent classes in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseAgent) and obj != BaseAgent:
                agent_type = name.lower().replace('agent', '')
                self.agent_classes[agent_type] = obj
                
                # Create instance if enabled
                if self.config.is_agent_enabled(agent_type):
                    agent_instance = self._create_agent_instance(agent_type, obj)
                    self.agents[agent_type] = agent_instance
                    self.agent_locks[agent_type] = threading.Lock()
                
                self.logger.info(f"Loaded custom agent: {agent_type}")
    
    def _setup_health_monitoring(self):
        """
        Setup health monitoring for agents.
        Monitors agent performance and availability.
        """
        # Start background health check task if enabled
        if self.config.agent_config.get('health_monitoring', True):
            # This would typically start a background thread for health checks
            self.logger.debug("Agent health monitoring enabled")
    
    def detect_agent_type(self, file_path: str, content: str) -> str:
        """
        Detect the most appropriate agent type for a given file.
        Uses file extension, content analysis, and framework detection.
        
        Args:
            file_path: Path to the file being analyzed
            content: File content for analysis
            
        Returns:
            Agent type identifier (e.g., 'react', 'python', 'node')
        """
        file_ext = Path(file_path).suffix.lower()
        confidence_scores = {}
        
        for agent_type, patterns in self.detection_patterns.items():
            confidence = 0.0
            
            # Check file extension
            if file_ext in patterns.get('extensions', []):
                confidence += 30.0
            
            # Check content patterns
            content_patterns = patterns.get('content_patterns', [])
            if content:
                pattern_matches = 0
                for pattern in content_patterns:
                    if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                        pattern_matches += 1
                
                if content_patterns:
                    pattern_confidence = (pattern_matches / len(content_patterns)) * 50.0
                    confidence += pattern_confidence
            
            # Check framework indicators
            frameworks = patterns.get('frameworks', [])
            if content and frameworks:
                framework_matches = 0
                for framework in frameworks:
                    if framework.lower() in content.lower():
                        framework_matches += 1
                
                if frameworks:
                    framework_confidence = (framework_matches / len(frameworks)) * 20.0
                    confidence += framework_confidence
            
            if confidence > 0:
                confidence_scores[agent_type] = confidence
        
        if not confidence_scores:
            # Return default agent if no specific match
            return self.config.default_agent
        
        # Return agent type with highest confidence
        best_agent = max(confidence_scores.items(), key=lambda x: x[1])
        
        self.logger.debug(f"Agent detection for {file_path}: {best_agent[0]} (confidence: {best_agent[1]:.1f})")
        
        return best_agent[0]
    
    def get_applicable_agents(self, file_path: str, content: str) -> List[str]:
        """
        Get all agents that could potentially analyze the given file.
        Useful for parallel multi-agent analysis.
        
        Args:
            file_path: Path to the file being analyzed
            content: File content for analysis
            
        Returns:
            List of applicable agent type identifiers
        """
        file_ext = Path(file_path).suffix.lower()
        applicable_agents = []
        
        for agent_type, patterns in self.detection_patterns.items():
            is_applicable = False
            
            # Check if file extension matches
            if file_ext in patterns.get('extensions', []):
                is_applicable = True
            
            # Check if any content patterns match
            elif content and patterns.get('content_patterns'):
                for pattern in patterns['content_patterns']:
                    if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                        is_applicable = True
                        break
            
            # Check if agent is enabled and available
            if is_applicable and self.is_agent_available(agent_type):
                applicable_agents.append(agent_type)
        
        # Always include general agent as fallback
        if 'general' not in applicable_agents and self.is_agent_available('general'):
            applicable_agents.append('general')
        
        return applicable_agents
    
    def get_agent(self, agent_type: str) -> BaseAgent:
        """
        Get an agent instance by type.
        Handles lazy loading and agent creation as needed.
        
        Args:
            agent_type: Type of agent to retrieve
            
        Returns:
            Agent instance
            
        Raises:
            AgentError: If agent type is not available or failed to create
        """
        # Check if agent is already instantiated
        if agent_type in self.agents:
            return self.agents[agent_type]
        
        # Check if agent class is available for lazy loading
        if agent_type in self.agent_classes:
            agent_class = self.agent_classes[agent_type]
            if agent_class is None:
                raise AgentError(f"Agent type '{agent_type}' is not available (missing dependencies)")
            
            try:
                # Create and cache agent instance
                with self.agent_locks.get(agent_type, threading.Lock()):
                    # Double-check after acquiring lock
                    if agent_type not in self.agents:
                        agent_instance = self._create_agent_instance(agent_type, agent_class)
                        self.agents[agent_type] = agent_instance
                        self.agent_locks[agent_type] = threading.Lock()
                        
                        # Initialize stats
                        self.agent_stats[agent_type] = {
                            'created_at': datetime.now(),
                            'total_requests': 0,
                            'successful_requests': 0,
                            'failed_requests': 0,
                            'average_response_time': 0.0,
                            'last_used': None,
                            'health_status': 'healthy'
                        }
                
                return self.agents[agent_type]
                
            except Exception as e:
                raise AgentError(f"Failed to create agent '{agent_type}': {str(e)}")
        
        # Fallback to general agent or raise error
        if agent_type != 'general' and 'general' in self.agents:
            self.logger.warning(f"Agent type '{agent_type}' not found, falling back to general agent")
            return self.agents['general']
        
        raise AgentError(f"Agent type '{agent_type}' is not available")
    
    def is_agent_available(self, agent_type: str) -> bool:
        """
        Check if an agent type is available and can be instantiated.
        
        Args:
            agent_type: Type of agent to check
            
        Returns:
            True if agent is available, False otherwise
        """
        return (
            agent_type in self.agents or 
            (agent_type in self.agent_classes and self.agent_classes[agent_type] is not None)
        )
    
    def get_agent_capabilities(self, agent_type: str) -> List[AgentCapability]:
        """
        Get the capabilities of a specific agent type.
        
        Args:
            agent_type: Type of agent to query
            
        Returns:
            List of agent capabilities
        """
        try:
            agent = self.get_agent(agent_type)
            return agent.get_capabilities()
        except Exception as e:
            self.logger.warning(f"Failed to get capabilities for agent {agent_type}: {e}")
            return []
    
    def get_available_agents(self) -> List[str]:
        """
        Get list of all available agent types.
        
        Returns:
            List of agent type identifiers
        """
        return [
            agent_type for agent_type in self.agent_classes.keys()
            if self.is_agent_available(agent_type)
        ]
    
    def get_agent_stats(self, agent_type: str) -> Dict[str, Any]:
        """
        Get performance statistics for a specific agent.
        
        Args:
            agent_type: Type of agent to get stats for
            
        Returns:
            Dictionary containing agent statistics
        """
        return self.agent_stats.get(agent_type, {})
    
    def update_agent_stats(self, agent_type: str, success: bool, response_time: float):
        """
        Update performance statistics for an agent.
        
        Args:
            agent_type: Type of agent to update stats for
            success: Whether the operation was successful
            response_time: Time taken for the operation
        """
        if agent_type not in self.agent_stats:
            return
        
        stats = self.agent_stats[agent_type]
        stats['total_requests'] += 1
        stats['last_used'] = datetime.now()
        
        if success:
            stats['successful_requests'] += 1
        else:
            stats['failed_requests'] += 1
        
        # Update average response time
        total_requests = stats['total_requests']
        current_avg = stats['average_response_time']
        stats['average_response_time'] = ((current_avg * (total_requests - 1)) + response_time) / total_requests
    
    def register_custom_agent(
        self,
        agent_type: str,
        agent_class: Type[BaseAgent],
        detection_patterns: Optional[Dict[str, Any]] = None
    ):
        """
        Register a custom agent type at runtime.
        
        Args:
            agent_type: Unique identifier for the agent type
            agent_class: Agent class that inherits from BaseAgent
            detection_patterns: Optional detection patterns for the agent
        """
        if not issubclass(agent_class, BaseAgent):
            raise ValueError(f"Agent class must inherit from BaseAgent")
        
        try:
            # Register agent class
            self.agent_classes[agent_type] = agent_class
            
            # Register detection patterns
            if detection_patterns:
                self.detection_patterns[agent_type] = detection_patterns
            
            # Create instance if enabled
            if self.config.is_agent_enabled(agent_type):
                agent_instance = self._create_agent_instance(agent_type, agent_class)
                self.agents[agent_type] = agent_instance
                self.agent_locks[agent_type] = threading.Lock()
                
                # Initialize stats
                self.agent_stats[agent_type] = {
                    'created_at': datetime.now(),
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'average_response_time': 0.0,
                    'last_used': None,
                    'health_status': 'healthy'
                }
            
            self.logger.info(f"Registered custom agent: {agent_type}")
            
        except Exception as e:
            raise AgentError(f"Failed to register custom agent {agent_type}: {str(e)}")
    
    def cleanup(self):
        """
        Cleanup agent manager resources.
        Properly shuts down all agents and releases resources.
        """
        self.logger.info("Cleaning up Agent Manager")
        
        # Cleanup individual agents
        for agent_type, agent in self.agents.items():
            try:
                if hasattr(agent, 'cleanup'):
                    agent.cleanup()
            except Exception as e:
                self.logger.warning(f"Error cleaning up agent {agent_type}: {e}")
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Agent Manager cleanup complete")
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """
        Get overall manager statistics.
        
        Returns:
            Dictionary containing manager-level statistics
        """
        total_requests = sum(stats.get('total_requests', 0) for stats in self.agent_stats.values())
        total_successful = sum(stats.get('successful_requests', 0) for stats in self.agent_stats.values())
        
        return {
            'total_agents': len(self.agents),
            'available_agents': len(self.get_available_agents()),
            'total_requests': total_requests,
            'total_successful': total_successful,
            'success_rate': (total_successful / total_requests * 100) if total_requests > 0 else 0.0,
            'agent_stats': {agent_type: stats for agent_type, stats in self.agent_stats.items()}
        } 