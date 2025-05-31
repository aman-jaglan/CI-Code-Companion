"""
CI Code Companion SDK

A comprehensive software development kit for intelligent code analysis, review, and repository management.
This SDK provides a unified interface for multi-technology code analysis, AI-powered insights,
and repository browsing capabilities.

Key Features:
- Multi-technology AI agents (React, Python, Node.js, Database, DevOps, Mobile)
- Real-time code analysis and review
- Intelligent test generation
- Code optimization suggestions
- Repository browsing with Monaco editor integration
- GitLab integration for seamless workflow
- Production-ready error handling and logging

Example Usage:
    from ci_code_companion_sdk import CICodeCompanionEngine
    
    # Initialize the SDK
    engine = CICodeCompanionEngine(config={
        'gitlab_url': 'https://gitlab.com',
        'gitlab_token': 'your-token-here',
        'log_level': 'INFO'
    })
    
    # Analyze a file
    result = await engine.analyze_file('path/to/file.py', file_content)
    
    # Generate tests
    test_result = await engine.generate_tests('path/to/file.py', file_content)
    
    # Optimize code
    optimization = await engine.optimize_code('path/to/file.py', file_content)
    
    # Chat with AI agents
    response = await engine.chat_with_agent("How can I improve this function?", 
                                           file_path='path/to/file.py', 
                                           content=file_content)

Architecture:
- Core Engine: Orchestrates all operations and provides unified interface
- Agent System: Specialized AI agents for different technologies and frameworks
- Service Layer: File operations, Git integration, and analysis services
- Models: Structured data models for results and metadata
- Configuration: Comprehensive configuration management
- Exception System: Hierarchical exception handling with context

The SDK is designed for production use with comprehensive error handling,
logging, monitoring, and performance optimization.
"""

import logging
import sys
import platform

# Version information
__version__ = "1.0.0"
__author__ = "CI Code Companion Team"
__email__ = "support@codecompanion.dev"
__license__ = "MIT"

# Core exports
from .core.engine import CICodeCompanionEngine
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

# Agent exports
from .agents.base_agent import BaseAgent, AgentCapability
from .agents.agent_manager import AgentManager

# Service exports
from .services.file_service import FileService
from .services.git_service import GitService
from .services.analysis_service import AnalysisService

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
    'CICodeCompanionEngine',
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
    
    # Agents
    'BaseAgent',
    'AgentCapability',
    'AgentManager',
    
    # Services
    'FileService',
    'GitService',
    'AnalysisService',
    
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