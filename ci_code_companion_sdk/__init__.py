"""
CI Code Companion SDK - Streamlined Architecture

A comprehensive software development kit for intelligent code analysis, review, and repository management.
This SDK provides a unified interface for multi-technology code analysis, AI-powered insights,
and repository browsing capabilities with streamlined agent integration.

STREAMLINED ARCHITECTURE:
- Unified CICodeCompanionSDK interface (primary)
- StreamlinedAIService for direct AI operations with agent integration
- Specialized agents for React, Python, Node.js development
- Single Gemini model focus (no fallbacks)
- Reduced redundancy and optimized performance

Key Features:
- Multi-technology AI agents (React, Python, Node.js) with chat support
- Real-time code analysis and review using specialized agents
- Intelligent test generation with agent expertise
- Code optimization suggestions from domain experts
- Direct chat with specialized agents for context-aware assistance
- Repository browsing with Monaco editor integration
- GitLab integration for seamless workflow
- Production-ready error handling and logging

RECOMMENDED USAGE:
    from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig
    
    # Initialize the streamlined SDK
    sdk = CICodeCompanionSDK(config={
        'ai_provider': 'vertex_ai',
        'project_id': 'your-gcp-project',
        'region': 'us-central1'
    })
    
    # Analyze a React file (uses ReactCodeAgent)
    result = await sdk.analyze_file('component.jsx', file_content)
    
    # Chat with Python expert (uses PythonCodeAgent)
    response = await sdk.chat("How do I optimize this loop?", 
                             file_path='script.py', content=python_code)
    
    # Generate tests using appropriate agent
    tests = await sdk.generate_tests('utils.py', file_content)

STREAMLINED FLOW:
    Chatbot → CICodeCompanionSDK → StreamlinedAIService → Specialized Agents → VertexAI → Gemini Model
                                                      ↳ Direct AI (for unsupported file types)

Architecture Components:
- CICodeCompanionSDK: Primary user interface (replaces CICodeCompanionEngine)
- StreamlinedAIService: Intelligent routing between agents and direct AI
- Specialized Agents: Expert knowledge for specific technologies with chat support
- VertexAI Client: Direct connection to configured Gemini model (no fallbacks)
- Configuration: Simplified configuration management
- Exception System: Hierarchical exception handling with context

The SDK automatically routes requests to appropriate specialized agents based on file type and content,
falling back to direct AI processing for unsupported file types. All agents support chat interactions
for context-aware assistance.
"""

import logging
import sys
import platform
from typing import Optional, Union, Dict, Any, List

# Version information
__version__ = "1.0.0"
__author__ = "CI Code Companion Team"
__email__ = "support@codecompanion.dev"
__license__ = "MIT"

# Core exports
from .core.engine import CICodeCompanionEngine  # DEPRECATED: Use CICodeCompanionSDK instead
from .core.config import SDKConfig, load_config_from_file, merge_configs
from .core.exceptions import (
    CICodeCompanionError,
    AnalysisError,
    FileOperationError,
    GitLabError,
    AgentError,
    ConfigurationError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    ResourceError,
    aggregate_exceptions,
    handle_exception
)

# Model exports
from .models.analysis_model import (
    AnalysisResult,
    TestGenerationResult,
    OptimizationResult,
    CodeIssue,
    CodeSuggestion,
    CodeOptimization,
    AnalysisMetrics,
    IssueSeverity,
    IssueType,
    OptimizationType
)
from .models.file_model import FileInfo, ProjectInfo

# Agent exports (streamlined)
from .agents.base_agent import BaseAgent, AgentCapability
from .agents.agent_manager import AgentManager  # Legacy - use StreamlinedAIService

# Service exports (streamlined)
from .services.file_service import FileService
from .services.git_service import GitService
from .services.analysis_service import AnalysisService  # Legacy
from .services.ai_service import StreamlinedAIService  # New streamlined service

# Integration exports
from .integrations.gitlab_client import GitLabClient

# Utility functions
from .core.utils import (
    get_file_language,
    detect_framework,
    calculate_file_hash,
    format_file_size,
    sanitize_filename,
    validate_file_path
)

# All public exports
__all__ = [
    # Version info
    '__version__',
    '__author__',
    '__email__',
    '__license__',
    
    # Core components
    'CICodeCompanionEngine',  # DEPRECATED
    'CICodeCompanionSDK',     # Primary interface
    'SDKConfig',
    'load_config_from_file',
    'merge_configs',
    
    # Exceptions
    'CICodeCompanionError',
    'AnalysisError',
    'FileOperationError',
    'GitLabError',
    'AgentError',
    'ConfigurationError',
    'AuthenticationError',
    'ValidationError',
    'RateLimitError',
    'ResourceError',
    'aggregate_exceptions',
    'handle_exception',
    
    # Models
    'AnalysisResult',
    'TestGenerationResult',
    'OptimizationResult',
    'CodeIssue',
    'CodeSuggestion',
    'CodeOptimization',
    'AnalysisMetrics',
    'IssueSeverity',
    'IssueType',
    'OptimizationType',
    'FileInfo',
    'ProjectInfo',
    
    # Agents (streamlined)
    'BaseAgent',
    'AgentCapability',
    'AgentManager',  # Legacy
    
    # Services (streamlined)
    'FileService',
    'GitService',
    'AnalysisService',      # Legacy
    'StreamlinedAIService', # Primary AI service
    
    # Integrations
    'GitLabClient',
    
    # Utilities
    'get_file_language',
    'detect_framework',
    'calculate_file_hash',
    'format_file_size',
    'sanitize_filename',
    'validate_file_path',
]


def create_engine(config=None, **kwargs):
    """
    Convenience function to create and configure a CI Code Companion Engine.
    
    Args:
        config: Configuration dictionary or SDKConfig instance
        **kwargs: Additional configuration options passed as keyword arguments
        
    Returns:
        Configured CICodeCompanionEngine instance
        
    Example:
        engine = create_engine(
            gitlab_url='https://gitlab.company.com',
            gitlab_token='your-token',
            log_level='DEBUG',
            max_workers=8
        )
    """
    if config is None:
        config = {}
    
    # Merge kwargs into config
    if kwargs:
        if isinstance(config, dict):
            config.update(kwargs)
        else:
            # If config is SDKConfig instance, create new dict
            config_dict = config.to_dict() if hasattr(config, 'to_dict') else {}
            config_dict.update(kwargs)
            config = config_dict
    
    return CICodeCompanionEngine(config)


def get_version_info():
    """
    Get detailed version information about the SDK.
    
    Returns:
        Dictionary containing version details
    """
    return {
        'version': __version__,
        'author': __author__,
        'email': __email__,
        'license': __license__,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'platform': platform.platform(),
        'architecture': platform.architecture()[0]
    }


def check_dependencies():
    """
    Check if all required dependencies are available.
    
    Returns:
        Dictionary with dependency status
    """
    dependencies = {
        'required': [
            'asyncio', 'logging', 'threading', 'dataclasses', 
            'typing', 'datetime', 'pathlib', 'json', 'uuid'
        ],
        'optional': [
            'yaml', 'requests', 'aiohttp', 'gitpython'
        ]
    }
    
    status = {
        'all_required_available': True,
        'required_status': {},
        'optional_status': {}
    }
    
    # Check required dependencies
    for dep in dependencies['required']:
        try:
            __import__(dep)
            status['required_status'][dep] = True
        except ImportError:
            status['required_status'][dep] = False
            status['all_required_available'] = False
    
    # Check optional dependencies
    for dep in dependencies['optional']:
        try:
            __import__(dep)
            status['optional_status'][dep] = True
        except ImportError:
            status['optional_status'][dep] = False
    
    return status


def configure_logging(level='INFO', format_type='structured', file_path=None):
    """
    Configure logging for the SDK with sensible defaults.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ('simple', 'structured', 'json')
        file_path: Optional file path for logging output
        
    Returns:
        Configured logger instance
    """
    import logging
    import sys
    
    # Create logger
    logger = logging.getLogger('ci_code_companion_sdk')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter based on type
    if format_type == 'json':
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(name)s", "message": "%(message)s"}'
        )
    elif format_type == 'structured':
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    else:  # simple
        formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if specified
    if file_path:
        try:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    return logger


# Import required modules for version info
# Removed duplicate imports: import sys, import platform (moved to top)

# Initialize default logging
_default_logger = configure_logging()

# SDK initialization message
_default_logger.info(f"CI Code Companion SDK v{__version__} initialized")

# Check dependencies on import
_dep_status = check_dependencies()
if not _dep_status['all_required_available']:
    missing_deps = [dep for dep, available in _dep_status['required_status'].items() if not available]
    _default_logger.warning(f"Missing required dependencies: {missing_deps}")

# Optional: Display welcome message in debug mode
if _default_logger.level <= logging.DEBUG:
    _default_logger.debug("SDK Features Available:")
    _default_logger.debug("  ✓ Multi-technology AI agents")
    _default_logger.debug("  ✓ Real-time code analysis")
    _default_logger.debug("  ✓ Intelligent test generation")
    _default_logger.debug("  ✓ Code optimization suggestions")
    _default_logger.debug("  ✓ GitLab integration")
    _default_logger.debug("  ✓ Production-ready error handling")

class CICodeCompanionSDK:
    """
    Simplified SDK interface that provides direct access to AI capabilities.
    Streamlined for better performance and clearer model usage.
    """
    
    def __init__(self, config: Optional[Union[Dict[str, Any], SDKConfig]] = None):
        """
        Initialize the CI Code Companion SDK.
        
        Args:
            config: Configuration dictionary or SDKConfig instance
        """
        if isinstance(config, SDKConfig):
            self.config = config
        else:
            self.config = SDKConfig(config or {})
        
        self.logger = logging.getLogger('ci_code_companion_sdk')
        
        # Initialize streamlined AI service directly
        try:
            from .services.ai_service import StreamlinedAIService
            self.ai_service = StreamlinedAIService(self.config, self.logger)
            self.logger.info(f"SDK initialized with model: {self.ai_service.vertex_client.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize SDK: {e}")
            self.ai_service = None
            raise
        
    async def analyze_file(self, file_path: str, content: str, **kwargs) -> AnalysisResult:
        """Analyze a file using AI."""
        self.logger.info(f"📊 SDK METHOD: analyze_file() called for {file_path}")
        
        if not self.ai_service:
            self.logger.error("❌ SDK ERROR: AI service not initialized")
            raise ConfigurationError("AI service not initialized")
        
        analysis_type = kwargs.get('analysis_type', 'comprehensive')
        self.logger.info(f"🔄 SDK ROUTING: Delegating to StreamlinedAIService.analyze_code()")
        
        return await self.ai_service.analyze_code(file_path, content, analysis_type)
    
    async def generate_tests(self, file_path: str, content: str, **kwargs) -> TestGenerationResult:
        """Generate tests for a file."""
        self.logger.info(f"🧪 SDK METHOD: generate_tests() called for {file_path}")
        
        if not self.ai_service:
            self.logger.error("❌ SDK ERROR: AI service not initialized")
            raise ConfigurationError("AI service not initialized")
        
        test_type = kwargs.get('test_type', 'unit')
        self.logger.info(f"🔄 SDK ROUTING: Delegating to StreamlinedAIService.generate_tests()")
        
        return await self.ai_service.generate_tests(file_path, content, test_type)
    
    async def optimize_code(self, file_path: str, content: str, **kwargs) -> OptimizationResult:
        """Optimize code in a file."""
        self.logger.info(f"⚡ SDK METHOD: optimize_code() called for {file_path}")
        
        if not self.ai_service:
            self.logger.error("❌ SDK ERROR: AI service not initialized")
            raise ConfigurationError("AI service not initialized")
        
        optimization_type = kwargs.get('optimization_type', 'performance')
        self.logger.info(f"🔄 SDK ROUTING: Delegating to StreamlinedAIService.optimize_code()")
        
        return await self.ai_service.optimize_code(file_path, content, optimization_type)
    
    async def chat(self, message: str, file_path: Optional[str] = None, content: Optional[str] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Chat with AI."""
        self.logger.info(f"💬 SDK METHOD: chat() called with message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
        
        if not self.ai_service:
            self.logger.error("❌ SDK ERROR: AI service not initialized")
            raise ConfigurationError("AI service not initialized")
        
        self.logger.info(f"🔄 SDK ROUTING: Delegating to StreamlinedAIService.chat()")
        
        return await self.ai_service.chat(message, file_path, content, conversation_history)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check SDK health status."""
        if not self.ai_service:
            return {
                "status": "unhealthy",
                "error": "AI service not initialized"
            }
        
        return await self.ai_service.health_check() 