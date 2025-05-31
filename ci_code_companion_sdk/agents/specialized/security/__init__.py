"""
Specialized Security Agents

This module contains specialized agents focused on security analysis,
vulnerability assessment, and compliance checking for various aspects of software development.
"""

from .security_scanner_agent import SecurityScannerAgent
from .dependency_security_agent import DependencySecurityAgent

__all__ = [
    'SecurityScannerAgent',
    'DependencySecurityAgent'
] 