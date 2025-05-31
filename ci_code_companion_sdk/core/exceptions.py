"""
Custom Exception System for CI Code Companion SDK

This module defines a comprehensive hierarchy of exceptions used throughout the SDK.
It provides structured error handling with detailed context, error codes, and recovery
suggestions. The exception system is designed for both debugging and production use
with appropriate logging and error reporting capabilities.

Features:
- Hierarchical exception structure for granular error handling
- Error codes for automated error processing
- Context preservation for debugging
- Recovery suggestions for common issues
- Integration with logging and monitoring systems
- Support for error aggregation and batch processing
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import traceback
import json


class CICodeCompanionError(Exception):
    """
    Base exception class for all CI Code Companion SDK errors.
    Provides common functionality for error context, logging, and recovery suggestions.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        inner_exception: Optional[Exception] = None
    ):
        """
        Initialize base SDK exception with comprehensive error information.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for automated handling
            context: Additional context information about the error
            suggestions: List of suggested solutions or recovery actions
            inner_exception: Original exception that caused this error (if any)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self._get_default_error_code()
        self.context = context or {}
        self.suggestions = suggestions or []
        self.inner_exception = inner_exception
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc() if inner_exception else None
    
    def _get_default_error_code(self) -> str:
        """
        Generate default error code based on exception class name.
        Provides consistent error codes for automated error handling.
        
        Returns:
            Default error code string
        """
        class_name = self.__class__.__name__
        # Convert CamelCase to SNAKE_CASE
        error_code = ''.join(['_' + c.lower() if c.isupper() else c for c in class_name]).lstrip('_')
        return error_code.upper()
    
    def add_context(self, key: str, value: Any) -> 'CICodeCompanionError':
        """
        Add additional context information to the exception.
        Enables chaining of context additions for better error tracking.
        
        Args:
            key: Context key
            value: Context value
            
        Returns:
            Self for method chaining
        """
        self.context[key] = value
        return self
    
    def add_suggestion(self, suggestion: str) -> 'CICodeCompanionError':
        """
        Add a recovery suggestion to the exception.
        Helps users understand how to resolve the error.
        
        Args:
            suggestion: Recovery suggestion text
            
        Returns:
            Self for method chaining
        """
        self.suggestions.append(suggestion)
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary format for serialization.
        Useful for API responses and logging structured data.
        
        Returns:
            Exception data as dictionary
        """
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'context': self.context,
            'suggestions': self.suggestions,
            'timestamp': self.timestamp.isoformat(),
            'inner_exception': str(self.inner_exception) if self.inner_exception else None,
            'traceback': self.traceback_info
        }
    
    def to_json(self) -> str:
        """
        Convert exception to JSON string for logging and API responses.
        Provides structured error information in JSON format.
        
        Returns:
            JSON string representation of the exception
        """
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def get_user_message(self) -> str:
        """
        Get user-friendly error message with suggestions.
        Formats error message for end-user display.
        
        Returns:
            Formatted user-friendly error message
        """
        user_message = self.message
        
        if self.suggestions:
            user_message += "\n\nSuggested solutions:"
            for i, suggestion in enumerate(self.suggestions, 1):
                user_message += f"\n{i}. {suggestion}"
        
        return user_message
    
    def is_recoverable(self) -> bool:
        """
        Check if this error is potentially recoverable.
        Base implementation returns True if suggestions are provided.
        
        Returns:
            True if error might be recoverable, False otherwise
        """
        return len(self.suggestions) > 0


class AnalysisError(CICodeCompanionError):
    """
    Exception raised during code analysis operations.
    Handles errors in file analysis, agent execution, and result processing.
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        agent_type: Optional[str] = None,
        analysis_step: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize analysis error with file and agent context.
        
        Args:
            message: Error message
            file_path: Path to file being analyzed (if applicable)
            agent_type: Type of agent that failed (if applicable)
            analysis_step: Specific analysis step that failed
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if file_path:
            context['file_path'] = file_path
        if agent_type:
            context['agent_type'] = agent_type
        if analysis_step:
            context['analysis_step'] = analysis_step
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add common suggestions for analysis errors
        if not self.suggestions:
            self._add_analysis_suggestions()
    
    def _add_analysis_suggestions(self):
        """Add common suggestions for analysis errors"""
        self.add_suggestion("Check if the file is accessible and not corrupted")
        self.add_suggestion("Verify that the file type is supported")
        self.add_suggestion("Try analyzing a smaller file or specific section")
        self.add_suggestion("Check agent configuration and timeout settings")


class FileOperationError(CICodeCompanionError):
    """
    Exception raised during file operations (read, write, access).
    Handles errors related to file system operations and permissions.
    """
    
    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize file operation error with file context.
        
        Args:
            message: Error message
            file_path: Path to file that caused the error
            operation: Type of operation that failed (read, write, etc.)
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add common suggestions for file operation errors
        if not self.suggestions:
            self._add_file_operation_suggestions()
    
    def _add_file_operation_suggestions(self):
        """Add common suggestions for file operation errors"""
        self.add_suggestion("Check if the file path exists and is accessible")
        self.add_suggestion("Verify file permissions and user access rights")
        self.add_suggestion("Ensure the file is not locked by another process")
        self.add_suggestion("Check available disk space if writing files")


class GitLabError(CICodeCompanionError):
    """
    Exception raised during GitLab API operations.
    Handles errors in GitLab integration including authentication, API limits, and network issues.
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        api_endpoint: Optional[str] = None,
        project_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize GitLab error with API context.
        
        Args:
            message: Error message
            status_code: HTTP status code from GitLab API
            api_endpoint: GitLab API endpoint that failed
            project_id: GitLab project ID (if applicable)
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if status_code:
            context['status_code'] = status_code
        if api_endpoint:
            context['api_endpoint'] = api_endpoint
        if project_id:
            context['project_id'] = project_id
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add status-specific suggestions
        self._add_gitlab_suggestions(status_code)
    
    def _add_gitlab_suggestions(self, status_code: Optional[int]):
        """
        Add status-specific suggestions for GitLab errors.
        
        Args:
            status_code: HTTP status code from GitLab API
        """
        if status_code == 401:
            self.add_suggestion("Check GitLab authentication token")
            self.add_suggestion("Verify token has required permissions")
        elif status_code == 403:
            self.add_suggestion("Check user permissions for the project")
            self.add_suggestion("Verify project access settings")
        elif status_code == 404:
            self.add_suggestion("Verify project ID and path are correct")
            self.add_suggestion("Check if project exists and is accessible")
        elif status_code == 429:
            self.add_suggestion("Reduce API request frequency")
            self.add_suggestion("Implement request throttling")
        elif status_code and status_code >= 500:
            self.add_suggestion("GitLab server error - try again later")
            self.add_suggestion("Check GitLab status page for outages")
        else:
            self.add_suggestion("Check GitLab URL and network connectivity")
            self.add_suggestion("Verify GitLab configuration settings")


class AgentError(CICodeCompanionError):
    """
    Exception raised during AI agent operations.
    Handles errors in agent initialization, execution, and result processing.
    """
    
    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        operation: Optional[str] = None,
        timeout_occurred: bool = False,
        **kwargs
    ):
        """
        Initialize agent error with agent context.
        
        Args:
            message: Error message
            agent_type: Type of agent that failed
            operation: Agent operation that failed
            timeout_occurred: Whether the error was due to timeout
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if agent_type:
            context['agent_type'] = agent_type
        if operation:
            context['operation'] = operation
        if timeout_occurred:
            context['timeout_occurred'] = timeout_occurred
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add agent-specific suggestions
        self._add_agent_suggestions(timeout_occurred)
    
    def _add_agent_suggestions(self, timeout_occurred: bool):
        """
        Add agent-specific suggestions based on error type.
        
        Args:
            timeout_occurred: Whether the error was due to timeout
        """
        if timeout_occurred:
            self.add_suggestion("Increase agent timeout in configuration")
            self.add_suggestion("Analyze smaller files or code sections")
            self.add_suggestion("Check system resources and performance")
        else:
            self.add_suggestion("Check agent configuration and dependencies")
            self.add_suggestion("Verify agent is properly initialized")
            self.add_suggestion("Try using a different agent type")


class ConfigurationError(CICodeCompanionError):
    """
    Exception raised for configuration-related errors.
    Handles errors in configuration loading, validation, and application.
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize configuration error with config context.
        
        Args:
            message: Error message
            config_key: Configuration key that caused the error
            config_file: Configuration file path (if applicable)
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if config_key:
            context['config_key'] = config_key
        if config_file:
            context['config_file'] = config_file
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add configuration-specific suggestions
        self._add_configuration_suggestions()
    
    def _add_configuration_suggestions(self):
        """Add common suggestions for configuration errors"""
        self.add_suggestion("Check configuration file syntax and format")
        self.add_suggestion("Verify all required configuration values are set")
        self.add_suggestion("Check environment variables and their values")
        self.add_suggestion("Review configuration documentation")


class AuthenticationError(CICodeCompanionError):
    """
    Exception raised for authentication and authorization errors.
    Handles errors in token validation, permission checks, and access control.
    """
    
    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        required_permission: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize authentication error with auth context.
        
        Args:
            message: Error message
            auth_type: Type of authentication that failed
            required_permission: Required permission that was missing
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if auth_type:
            context['auth_type'] = auth_type
        if required_permission:
            context['required_permission'] = required_permission
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add authentication-specific suggestions
        self._add_authentication_suggestions()
    
    def _add_authentication_suggestions(self):
        """Add common suggestions for authentication errors"""
        self.add_suggestion("Check authentication credentials")
        self.add_suggestion("Verify token is valid and not expired")
        self.add_suggestion("Ensure user has required permissions")
        self.add_suggestion("Contact administrator for access")


class ValidationError(CICodeCompanionError):
    """
    Exception raised for data validation errors.
    Handles errors in input validation, schema validation, and data format errors.
    """
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
        **kwargs
    ):
        """
        Initialize validation error with validation context.
        
        Args:
            message: Error message
            field_name: Name of field that failed validation
            expected_type: Expected data type or format
            actual_value: Actual value that failed validation
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if field_name:
            context['field_name'] = field_name
        if expected_type:
            context['expected_type'] = expected_type
        if actual_value is not None:
            context['actual_value'] = str(actual_value)
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add validation-specific suggestions
        self._add_validation_suggestions()
    
    def _add_validation_suggestions(self):
        """Add common suggestions for validation errors"""
        self.add_suggestion("Check input data format and type")
        self.add_suggestion("Verify all required fields are provided")
        self.add_suggestion("Review API documentation for expected format")
        self.add_suggestion("Validate data against schema requirements")


class RateLimitError(CICodeCompanionError):
    """
    Exception raised when rate limits are exceeded.
    Handles API rate limiting and resource throttling scenarios.
    """
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize rate limit error with timing context.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            limit_type: Type of rate limit (API, resource, etc.)
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if retry_after:
            context['retry_after'] = retry_after
        if limit_type:
            context['limit_type'] = limit_type
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add rate limit specific suggestions
        self._add_rate_limit_suggestions(retry_after)
    
    def _add_rate_limit_suggestions(self, retry_after: Optional[int]):
        """
        Add rate limit specific suggestions.
        
        Args:
            retry_after: Seconds to wait before retrying
        """
        if retry_after:
            self.add_suggestion(f"Wait {retry_after} seconds before retrying")
        self.add_suggestion("Implement exponential backoff for retries")
        self.add_suggestion("Reduce request frequency")
        self.add_suggestion("Consider upgrading API limits if available")


class ResourceError(CICodeCompanionError):
    """
    Exception raised for resource-related errors.
    Handles errors in memory allocation, disk space, and system resources.
    """
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        current_usage: Optional[str] = None,
        limit: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize resource error with resource context.
        
        Args:
            message: Error message
            resource_type: Type of resource (memory, disk, etc.)
            current_usage: Current resource usage
            limit: Resource limit that was exceeded
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if resource_type:
            context['resource_type'] = resource_type
        if current_usage:
            context['current_usage'] = current_usage
        if limit:
            context['limit'] = limit
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add resource-specific suggestions
        self._add_resource_suggestions()
    
    def _add_resource_suggestions(self):
        """Add common suggestions for resource errors"""
        self.add_suggestion("Check available system resources")
        self.add_suggestion("Free up memory or disk space")
        self.add_suggestion("Reduce file size or complexity")
        self.add_suggestion("Increase resource limits in configuration")


class EngineError(CICodeCompanionError):
    """
    Exception raised during engine operations.
    Handles errors in engine initialization, workflow execution, and orchestration.
    """
    
    def __init__(
        self,
        message: str,
        engine_component: Optional[str] = None,
        workflow_type: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize engine error with engine context.
        
        Args:
            message: Error message
            engine_component: Engine component that failed (if applicable)
            workflow_type: Type of workflow that failed (if applicable)
            operation: Specific operation that failed
            **kwargs: Additional arguments for base exception
        """
        context = kwargs.get('context', {})
        if engine_component:
            context['engine_component'] = engine_component
        if workflow_type:
            context['workflow_type'] = workflow_type
        if operation:
            context['operation'] = operation
        
        kwargs['context'] = context
        super().__init__(message, **kwargs)
        
        # Add common suggestions for engine errors
        if not self.suggestions:
            self._add_engine_suggestions()
    
    def _add_engine_suggestions(self):
        """Add common suggestions for engine errors"""
        self.add_suggestion("Check engine initialization and configuration")
        self.add_suggestion("Verify that all required agents are registered")
        self.add_suggestion("Check system resources and memory availability")
        self.add_suggestion("Review error logs for detailed troubleshooting")


def aggregate_exceptions(exceptions: List[Exception]) -> CICodeCompanionError:
    """
    Aggregate multiple exceptions into a single comprehensive error.
    Useful for batch operations where multiple errors may occur.
    
    Args:
        exceptions: List of exceptions to aggregate
        
    Returns:
        Aggregated exception with combined context and suggestions
    """
    if not exceptions:
        return CICodeCompanionError("No exceptions to aggregate")
    
    if len(exceptions) == 1:
        return exceptions[0] if isinstance(exceptions[0], CICodeCompanionError) else CICodeCompanionError(str(exceptions[0]))
    
    # Create aggregate exception
    message = f"Multiple errors occurred ({len(exceptions)} total)"
    context = {
        'exception_count': len(exceptions),
        'exception_types': [type(e).__name__ for e in exceptions],
        'individual_errors': []
    }
    
    suggestions = set()
    
    for i, exc in enumerate(exceptions):
        if isinstance(exc, CICodeCompanionError):
            context['individual_errors'].append({
                'index': i,
                'type': type(exc).__name__,
                'message': exc.message,
                'error_code': exc.error_code,
                'context': exc.context
            })
            suggestions.update(exc.suggestions)
        else:
            context['individual_errors'].append({
                'index': i,
                'type': type(exc).__name__,
                'message': str(exc)
            })
    
    aggregate_error = CICodeCompanionError(
        message=message,
        error_code='MULTIPLE_ERRORS',
        context=context,
        suggestions=list(suggestions)
    )
    
    return aggregate_error


def handle_exception(func):
    """
    Decorator for automatic exception handling and conversion.
    Converts standard exceptions to SDK exceptions with appropriate context.
    
    Args:
        func: Function to wrap with exception handling
        
    Returns:
        Decorated function with exception handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CICodeCompanionError:
            # Re-raise SDK exceptions as-is
            raise
        except FileNotFoundError as e:
            raise FileOperationError(
                message=f"File not found: {str(e)}",
                operation="read",
                inner_exception=e
            )
        except PermissionError as e:
            raise FileOperationError(
                message=f"Permission denied: {str(e)}",
                operation="access",
                inner_exception=e
            )
        except ValueError as e:
            raise ValidationError(
                message=f"Invalid value: {str(e)}",
                inner_exception=e
            )
        except TimeoutError as e:
            raise AgentError(
                message=f"Operation timed out: {str(e)}",
                timeout_occurred=True,
                inner_exception=e
            )
        except Exception as e:
            # Convert all other exceptions to generic SDK errors
            raise CICodeCompanionError(
                message=f"Unexpected error: {str(e)}",
                error_code="UNEXPECTED_ERROR",
                inner_exception=e
            )
    
    return wrapper 