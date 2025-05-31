"""
Specialized Agents Package

This package contains specialized agents organized by function:
- Code agents: Development, analysis, and optimization
- Testing agents: Test generation and quality assurance  
- Security agents: Security analysis and compliance

Each agent is focused on specific technologies, frameworks, or domains.
"""

# Import all specialized agents
from .code.react_code_agent import ReactCodeAgent
from .code.python_code_agent import PythonCodeAgent
from .code.node_code_agent import NodeCodeAgent

from .testing.react_test_agent import ReactTestAgent
from .testing.python_test_agent import PythonTestAgent
from .testing.api_test_agent import ApiTestAgent

from .security.security_scanner_agent import SecurityScannerAgent
from .security.dependency_security_agent import DependencySecurityAgent

__all__ = [
    # Code Agents
    'ReactCodeAgent',
    'PythonCodeAgent',
    'NodeCodeAgent',
    
    # Testing Agents
    'ReactTestAgent', 
    'PythonTestAgent',
    'ApiTestAgent',
    
    # Security Agents
    'SecurityScannerAgent',
    'DependencySecurityAgent'
] 