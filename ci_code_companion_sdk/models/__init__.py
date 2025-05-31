"""
CI Code Companion SDK Models

This module contains all data models used throughout the SDK for representing
analysis results, file information, and project structures.
"""

from .analysis_model import (
    AnalysisResult,
    CodeIssue,
    CodeSuggestion,
    TestGenerationResult,
    OptimizationResult
)

from .file_model import (
    FileInfo,
    ProjectInfo
)

__all__ = [
    # Analysis models
    'AnalysisResult',
    'CodeIssue', 
    'CodeSuggestion',
    'TestGenerationResult',
    'OptimizationResult',
    
    # File and project models
    'FileInfo',
    'ProjectInfo'
] 