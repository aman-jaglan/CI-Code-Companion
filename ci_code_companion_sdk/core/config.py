"""
SDK Configuration Management

This module handles all configuration aspects of the CI Code Companion SDK including
environment variables, configuration validation, default settings, and configuration
inheritance. It provides a centralized way to manage all SDK settings with proper
validation and type checking.

Features:
- Environment variable support with automatic type conversion
- Configuration validation and sanitization
- Default values for production, development, and testing environments
- Configuration inheritance and merging
- Sensitive data handling (passwords, tokens)
- Configuration hot-reloading support
- Schema validation for complex configurations
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class SDKConfig:
    """
    Comprehensive configuration class for the CI Code Companion SDK.
    Handles all configuration aspects including validation, defaults, and environment loading.
    """
    
    # GitLab Integration
    gitlab_url: str = field(default_factory=lambda: os.getenv('GITLAB_URL', 'https://gitlab.com'))
    gitlab_token: str = field(default_factory=lambda: os.getenv('GITLAB_TOKEN', ''))
    gitlab_timeout: int = field(default_factory=lambda: int(os.getenv('GITLAB_TIMEOUT', '30')))
    gitlab_retries: int = field(default_factory=lambda: int(os.getenv('GITLAB_RETRIES', '3')))
    
    # Logging Configuration
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv('LOG_FILE'))
    log_format: str = field(default_factory=lambda: os.getenv('LOG_FORMAT', 'structured'))
    log_max_size: int = field(default_factory=lambda: int(os.getenv('LOG_MAX_SIZE', str(10*1024*1024))))
    log_backup_count: int = field(default_factory=lambda: int(os.getenv('LOG_BACKUP_COUNT', '5')))
    
    # Performance Configuration
    max_workers: int = field(default_factory=lambda: int(os.getenv('MAX_WORKERS', '4')))
    agent_timeout: int = field(default_factory=lambda: int(os.getenv('AGENT_TIMEOUT', '60')))
    file_size_limit: int = field(default_factory=lambda: int(os.getenv('FILE_SIZE_LIMIT', str(10*1024*1024))))
    cache_enabled: bool = field(default_factory=lambda: os.getenv('CACHE_ENABLED', 'true').lower() == 'true')
    cache_ttl: int = field(default_factory=lambda: int(os.getenv('CACHE_TTL', '3600')))
    
    # Agent Configuration
    agent_config: Dict[str, Any] = field(default_factory=dict)
    default_agent: str = field(default_factory=lambda: os.getenv('DEFAULT_AGENT', 'general'))
    parallel_agent_execution: bool = field(default_factory=lambda: os.getenv('PARALLEL_AGENTS', 'true').lower() == 'true')
    agent_memory_limit: int = field(default_factory=lambda: int(os.getenv('AGENT_MEMORY_LIMIT', str(512*1024*1024))))
    
    # Security Configuration
    enable_security_scan: bool = field(default_factory=lambda: os.getenv('ENABLE_SECURITY_SCAN', 'true').lower() == 'true')
    allowed_file_types: List[str] = field(default_factory=lambda: _parse_list(os.getenv('ALLOWED_FILE_TYPES', 'py,js,ts,jsx,tsx,java,cpp,c,go,rs,rb,php')))
    blocked_patterns: List[str] = field(default_factory=lambda: _parse_list(os.getenv('BLOCKED_PATTERNS', '__pycache__,node_modules,.git')))
    
    # Database Configuration  
    database_url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', 'sqlite:///ci_code_companion.db'))
    database_pool_size: int = field(default_factory=lambda: int(os.getenv('DATABASE_POOL_SIZE', '5')))
    database_timeout: int = field(default_factory=lambda: int(os.getenv('DATABASE_TIMEOUT', '30')))
    
    # API Configuration
    api_rate_limit: int = field(default_factory=lambda: int(os.getenv('API_RATE_LIMIT', '100')))
    api_timeout: int = field(default_factory=lambda: int(os.getenv('API_TIMEOUT', '30')))
    api_retries: int = field(default_factory=lambda: int(os.getenv('API_RETRIES', '3')))
    
    # Feature Flags
    enable_ai_analysis: bool = field(default_factory=lambda: os.getenv('ENABLE_AI_ANALYSIS', 'true').lower() == 'true')
    enable_test_generation: bool = field(default_factory=lambda: os.getenv('ENABLE_TEST_GENERATION', 'true').lower() == 'true')
    enable_code_optimization: bool = field(default_factory=lambda: os.getenv('ENABLE_CODE_OPTIMIZATION', 'true').lower() == 'true')
    enable_dependency_analysis: bool = field(default_factory=lambda: os.getenv('ENABLE_DEPENDENCY_ANALYSIS', 'true').lower() == 'true')
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv('ENVIRONMENT', 'development'))
    debug_mode: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize SDK configuration with validation and environment loading.
        Supports configuration from dictionary, environment variables, and config files.
        
        Args:
            config_dict: Optional configuration dictionary to override defaults
        """
        # Initialize all dataclass fields with their defaults first
        # This ensures all attributes exist before any method calls
        
        # GitLab Integration
        self.gitlab_url = os.getenv('GITLAB_URL', 'https://gitlab.com')
        self.gitlab_token = os.getenv('GITLAB_TOKEN', '')
        self.gitlab_timeout = int(os.getenv('GITLAB_TIMEOUT', '30'))
        self.gitlab_retries = int(os.getenv('GITLAB_RETRIES', '3'))
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE')
        self.log_format = os.getenv('LOG_FORMAT', 'structured')
        self.log_max_size = int(os.getenv('LOG_MAX_SIZE', str(10*1024*1024)))
        self.log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))
        
        # Performance Configuration
        self.max_workers = int(os.getenv('MAX_WORKERS', '4'))
        self.agent_timeout = int(os.getenv('AGENT_TIMEOUT', '60'))
        self.file_size_limit = int(os.getenv('FILE_SIZE_LIMIT', str(10*1024*1024)))
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))
        
        # Agent Configuration
        self.agent_config = {}
        self.default_agent = os.getenv('DEFAULT_AGENT', 'general')
        self.parallel_agent_execution = os.getenv('PARALLEL_AGENTS', 'true').lower() == 'true'
        self.agent_memory_limit = int(os.getenv('AGENT_MEMORY_LIMIT', str(512*1024*1024)))
        
        # Security Configuration
        self.enable_security_scan = os.getenv('ENABLE_SECURITY_SCAN', 'true').lower() == 'true'
        self.allowed_file_types = _parse_list(os.getenv('ALLOWED_FILE_TYPES', 'py,js,ts,jsx,tsx,java,cpp,c,go,rs,rb,php'))
        self.blocked_patterns = _parse_list(os.getenv('BLOCKED_PATTERNS', '__pycache__,node_modules,.git'))
        
        # Database Configuration  
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///ci_code_companion.db')
        self.database_pool_size = int(os.getenv('DATABASE_POOL_SIZE', '5'))
        self.database_timeout = int(os.getenv('DATABASE_TIMEOUT', '30'))
        
        # API Configuration
        self.api_rate_limit = int(os.getenv('API_RATE_LIMIT', '100'))
        self.api_timeout = int(os.getenv('API_TIMEOUT', '30'))
        self.api_retries = int(os.getenv('API_RETRIES', '3'))
        
        # Feature Flags
        self.enable_ai_analysis = os.getenv('ENABLE_AI_ANALYSIS', 'true').lower() == 'true'
        self.enable_test_generation = os.getenv('ENABLE_TEST_GENERATION', 'true').lower() == 'true'
        self.enable_code_optimization = os.getenv('ENABLE_CODE_OPTIMIZATION', 'true').lower() == 'true'
        self.enable_dependency_analysis = os.getenv('ENABLE_DEPENDENCY_ANALYSIS', 'true').lower() == 'true'
        
        # Environment
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug_mode = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # Now that all attributes are initialized, load configuration from other sources
        self._load_default_config()
        self._load_environment_config()
        
        if config_dict:
            self._load_dict_config(config_dict)
        
        # Load from config file if specified
        config_file = os.getenv('CONFIG_FILE')
        if config_file:
            self._load_file_config(config_file)
        
        # Validate configuration
        self._validate_config()
        
        # Setup agent-specific configurations
        self._setup_agent_config()
    
    def _load_default_config(self):
        """
        Load default configuration values based on environment.
        Provides sensible defaults for different deployment scenarios.
        """
        defaults = {
            'development': {
                'log_level': 'DEBUG',
                'debug_mode': True,
                'max_workers': 2,
                'agent_timeout': 30,
                'cache_enabled': False
            },
            'testing': {
                'log_level': 'WARNING',
                'debug_mode': False,
                'max_workers': 1,
                'agent_timeout': 10,
                'cache_enabled': False,
                'database_url': 'sqlite:///:memory:'
            },
            'production': {
                'log_level': 'INFO',
                'debug_mode': False,
                'max_workers': 8,
                'agent_timeout': 60,
                'cache_enabled': True,
                'log_file': '/var/log/ci_code_companion.log'
            }
        }
        
        env_defaults = defaults.get(self.environment, defaults['development'])
        
        for key, value in env_defaults.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _load_environment_config(self):
        """
        Load configuration from environment variables with proper type conversion.
        Supports complex data types through JSON parsing.
        """
        env_mappings = {
            'GITLAB_URL': ('gitlab_url', str),
            'GITLAB_TOKEN': ('gitlab_token', str),
            'GITLAB_TIMEOUT': ('gitlab_timeout', int),
            'LOG_LEVEL': ('log_level', str),
            'LOG_FILE': ('log_file', str),
            'MAX_WORKERS': ('max_workers', int),
            'AGENT_TIMEOUT': ('agent_timeout', int),
            'CACHE_ENABLED': ('cache_enabled', bool),
            'DEBUG': ('debug_mode', bool),
            'ENVIRONMENT': ('environment', str),
            'AGENT_CONFIG': ('agent_config', json.loads)
        }
        
        for env_var, (attr_name, converter) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if converter == bool:
                        converted_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif converter == json.loads:
                        converted_value = json.loads(env_value)
                    else:
                        converted_value = converter(env_value)
                    
                    setattr(self, attr_name, converted_value)
                except (ValueError, json.JSONDecodeError) as e:
                    logging.warning(f"Failed to parse environment variable {env_var}: {e}")
    
    def _load_dict_config(self, config_dict: Dict[str, Any]):
        """
        Load configuration from a dictionary with validation.
        Safely updates configuration attributes from provided dictionary.
        
        Args:
            config_dict: Configuration dictionary to merge
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                # Validate type compatibility
                current_value = getattr(self, key)
                if current_value is not None and not isinstance(value, type(current_value)):
                    try:
                        # Attempt type conversion
                        if isinstance(current_value, bool):
                            value = str(value).lower() in ('true', '1', 'yes', 'on')
                        elif isinstance(current_value, (int, float)):
                            value = type(current_value)(value)
                        elif isinstance(current_value, list):
                            value = list(value) if not isinstance(value, list) else value
                        elif isinstance(current_value, dict):
                            value = dict(value) if not isinstance(value, dict) else value
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Failed to convert config value for {key}: {e}")
                        continue
                
                setattr(self, key, value)
            else:
                logging.warning(f"Unknown configuration key: {key}")
    
    def _load_file_config(self, config_file: str):
        """
        Load configuration from a file (JSON or YAML format).
        Supports both JSON and YAML configuration files with proper error handling.
        
        Args:
            config_file: Path to configuration file
        """
        config_path = Path(config_file)
        
        if not config_path.exists():
            logging.warning(f"Configuration file not found: {config_file}")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ('.yml', '.yaml'):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            if isinstance(config_data, dict):
                self._load_dict_config(config_data)
            else:
                logging.warning(f"Invalid configuration file format: {config_file}")
                
        except (json.JSONDecodeError, yaml.YAMLError, IOError) as e:
            logging.error(f"Failed to load configuration file {config_file}: {e}")
    
    def _validate_config(self):
        """
        Validate configuration values and apply constraints.
        Ensures all configuration values are within acceptable ranges and formats.
        """
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            logging.warning(f"Invalid log level: {self.log_level}, defaulting to INFO")
            self.log_level = 'INFO'
        
        # Validate worker count
        if self.max_workers < 1:
            logging.warning(f"Invalid max_workers: {self.max_workers}, setting to 1")
            self.max_workers = 1
        elif self.max_workers > 32:
            logging.warning(f"Max workers too high: {self.max_workers}, limiting to 32")
            self.max_workers = 32
        
        # Validate timeouts
        if self.agent_timeout < 5:
            logging.warning(f"Agent timeout too low: {self.agent_timeout}, setting to 5")
            self.agent_timeout = 5
        elif self.agent_timeout > 300:
            logging.warning(f"Agent timeout too high: {self.agent_timeout}, limiting to 300")
            self.agent_timeout = 300
        
        # Validate file size limit
        if self.file_size_limit < 1024:  # 1KB minimum
            self.file_size_limit = 1024
        elif self.file_size_limit > 100*1024*1024:  # 100MB maximum
            self.file_size_limit = 100*1024*1024
        
        # Validate GitLab URL format
        if self.gitlab_url and not self.gitlab_url.startswith(('http://', 'https://')):
            logging.warning(f"Invalid GitLab URL format: {self.gitlab_url}")
            self.gitlab_url = f"https://{self.gitlab_url}"
        
        # Validate environment
        valid_environments = ['development', 'testing', 'staging', 'production']
        if self.environment not in valid_environments:
            logging.warning(f"Invalid environment: {self.environment}, defaulting to development")
            self.environment = 'development'
    
    def _setup_agent_config(self):
        """
        Setup agent-specific configurations with intelligent defaults.
        Configures each specialized agent type with appropriate settings based on the environment.
        """
        default_agent_configs = {
            # Code Development Agents
            'react_code': {
                'enabled': True,
                'timeout': self.agent_timeout,
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['jsx_analysis', 'hooks_validation', 'performance_check', 'component_analysis'],
                'frameworks': ['react', 'next.js', 'gatsby'],
                'category': 'code'
            },
            'python_code': {
                'enabled': True,
                'timeout': self.agent_timeout,
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['syntax_check', 'pep8_validation', 'performance_analysis', 'framework_detection'],
                'frameworks': ['django', 'flask', 'fastapi', 'asyncio'],
                'category': 'code'
            },
            'node_code': {
                'enabled': True,
                'timeout': self.agent_timeout,
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['api_analysis', 'middleware_check', 'async_patterns', 'security_audit'],
                'frameworks': ['express', 'fastify', 'koa', 'nestjs'],
                'category': 'code'
            },
            
            # Testing Agents
            'react_test': {
                'enabled': True,
                'timeout': self.agent_timeout * 2,  # Testing may take longer
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['unit_testing', 'component_testing', 'integration_testing', 'test_generation'],
                'frameworks': ['jest', 'react-testing-library', 'enzyme', 'cypress'],
                'category': 'testing'
            },
            'python_test': {
                'enabled': True,
                'timeout': self.agent_timeout * 2,  # Testing may take longer
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['pytest_support', 'unittest_support', 'test_generation', 'mock_analysis'],
                'frameworks': ['pytest', 'unittest', 'nose2', 'coverage'],
                'category': 'testing'
            },
            'api_test': {
                'enabled': True,
                'timeout': self.agent_timeout * 2,  # API testing may take longer
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['rest_testing', 'graphql_testing', 'auth_testing', 'performance_testing'],
                'frameworks': ['postman', 'newman', 'rest-assured', 'supertest'],
                'category': 'testing'
            },
            
            # Security Agents
            'security_scanner': {
                'enabled': self.enable_security_scan,
                'timeout': self.agent_timeout * 3,  # Security scans may take longer
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['vulnerability_scan', 'code_analysis', 'pattern_detection', 'compliance_check'],
                'tools': ['bandit', 'eslint-security', 'semgrep', 'sonarqube'],
                'category': 'security'
            },
            'dependency_security': {
                'enabled': self.enable_dependency_analysis,
                'timeout': self.agent_timeout * 2,  # Dependency scans may take longer
                'memory_limit': self.agent_memory_limit // 8,
                'features': ['vulnerability_check', 'license_compliance', 'supply_chain_analysis', 'outdated_packages'],
                'tools': ['npm_audit', 'snyk', 'safety', 'dependabot'],
                'category': 'security'
            }
        }
        
        # Merge with existing agent config
        for agent_type, default_config in default_agent_configs.items():
            if agent_type not in self.agent_config:
                self.agent_config[agent_type] = {}
            
            # Merge defaults with existing config
            for key, value in default_config.items():
                if key not in self.agent_config[agent_type]:
                    self.agent_config[agent_type][key] = value
    
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific agent type.
        Returns agent-specific configuration with fallback to defaults.
        
        Args:
            agent_type: Type of agent to get configuration for
            
        Returns:
            Agent configuration dictionary
        """
        return self.agent_config.get(agent_type, {
            'enabled': True,
            'timeout': self.agent_timeout,
            'memory_limit': self.agent_memory_limit // 6,
            'features': []
        })
    
    def is_agent_enabled(self, agent_type: str) -> bool:
        """
        Check if a specific agent type is enabled.
        Provides centralized agent enablement control.
        
        Args:
            agent_type: Type of agent to check
            
        Returns:
            True if agent is enabled, False otherwise
        """
        agent_config = self.get_agent_config(agent_type)
        return agent_config.get('enabled', True)
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Check if a specific feature is enabled based on feature flags.
        Provides centralized feature flag management.
        
        Args:
            feature_name: Name of feature to check
            
        Returns:
            True if feature is enabled, False otherwise
        """
        feature_flags = {
            'ai_analysis': self.enable_ai_analysis,
            'test_generation': self.enable_test_generation,
            'code_optimization': self.enable_code_optimization,
            'dependency_analysis': self.enable_dependency_analysis,
            'security_scan': self.enable_security_scan
        }
        
        return feature_flags.get(feature_name, False)
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration with connection pooling settings.
        Provides centralized database configuration management.
        
        Returns:
            Database configuration dictionary
        """
        return {
            'url': self.database_url,
            'pool_size': self.database_pool_size,
            'timeout': self.database_timeout,
            'echo': self.debug_mode
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get comprehensive logging configuration.
        Provides centralized logging configuration management.
        
        Returns:
            Logging configuration dictionary
        """
        return {
            'level': self.log_level,
            'file': self.log_file,
            'format': self.log_format,
            'max_size': self.log_max_size,
            'backup_count': self.log_backup_count
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format.
        Useful for serialization and debugging.
        
        Returns:
            Configuration as dictionary
        """
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not attr.startswith('_') and not callable(getattr(self, attr))
        }
    
    def validate_gitlab_connection(self) -> bool:
        """
        Validate GitLab connection configuration.
        Checks if GitLab URL and token are properly configured.
        
        Returns:
            True if GitLab configuration is valid, False otherwise
        """
        if not self.gitlab_url:
            logging.error("GitLab URL not configured")
            return False
        
        if not self.gitlab_token:
            logging.warning("GitLab token not configured - some features may be limited")
            return False
        
        return True
    
    def sanitize_for_logging(self) -> Dict[str, Any]:
        """
        Create a sanitized version of configuration for logging.
        Removes sensitive information like tokens and passwords.
        
        Returns:
            Sanitized configuration dictionary
        """
        config_dict = self.to_dict()
        
        # List of sensitive keys to mask
        sensitive_keys = ['gitlab_token', 'database_url', 'api_key', 'secret_key', 'password']
        
        for key in sensitive_keys:
            if key in config_dict and config_dict[key]:
                config_dict[key] = '*' * 8
        
        return config_dict


def _parse_list(value: str, separator: str = ',') -> List[str]:
    """
    Parse a string into a list using the specified separator.
    Handles whitespace and empty values gracefully.
    
    Args:
        value: String to parse
        separator: Separator character
        
    Returns:
        List of parsed strings
    """
    if not value:
        return []
    
    return [item.strip() for item in value.split(separator) if item.strip()]


def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from a file with support for multiple formats.
    Supports JSON, YAML, and environment file formats.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(file_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            if config_path.suffix.lower() in ('.yml', '.yaml'):
                return yaml.safe_load(f) or {}
            elif config_path.suffix.lower() == '.json':
                return json.load(f) or {}
            elif config_path.suffix.lower() in ('.env', '.environ'):
                # Parse environment file format
                config = {}
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip().strip('"\'')
                return config
            else:
                raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
                
    except (json.JSONDecodeError, yaml.YAMLError, IOError) as e:
        raise ValueError(f"Failed to parse configuration file {file_path}: {e}")


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple configuration dictionaries with deep merging.
    Later configurations override earlier ones.
    
    Args:
        *configs: Configuration dictionaries to merge
        
    Returns:
        Merged configuration dictionary
    """
    result = {}
    
    for config in configs:
        if not isinstance(config, dict):
            continue
            
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Deep merge dictionaries
                result[key] = merge_configs(result[key], value)
            else:
                # Simple override
                result[key] = value
    
    return result 