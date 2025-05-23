"""
CI Code Companion: AI-Driven Code Generation Assistant for GitLab CI/CD

This package provides AI-powered code generation capabilities for GitLab CI/CD pipelines,
including automated test generation, code review, and pipeline configuration assistance.
"""

__version__ = "0.1.0"
__author__ = "CI Code Companion Team"
__email__ = "team@ci-code-companion.dev"

from .vertex_ai_client import VertexAIClient
from .test_generator import TestGenerator
from .code_reviewer import CodeReviewer
from .gitlab_integration import GitLabIntegration

__all__ = [
    "VertexAIClient",
    "TestGenerator", 
    "CodeReviewer",
    "GitLabIntegration"
] 