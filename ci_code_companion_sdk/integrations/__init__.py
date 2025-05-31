"""
CI Code Companion SDK Integrations

This module contains integrations with external services and platforms
including GitLab, GitHub, and other CI/CD systems.
"""

from .gitlab_client import GitLabClient

__all__ = [
    'GitLabClient'
] 