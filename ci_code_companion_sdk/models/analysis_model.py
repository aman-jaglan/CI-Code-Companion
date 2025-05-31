"""
Analysis Data Models

This module defines data models for analysis results, test generation outputs, and code
optimization results. These models provide structured data representation with validation,
serialization capabilities, and comprehensive metadata tracking for all SDK operations.

Features:
- Structured data models with type safety
- Automatic validation and sanitization
- JSON serialization/deserialization support
- Comprehensive metadata tracking
- Performance metrics and confidence scoring
- Support for nested and complex data structures
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json
import uuid


class IssueSeverity(Enum):
    """Enumeration of issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high" 
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Enumeration of issue types"""
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    COMPATIBILITY = "compatibility"
    BEST_PRACTICE = "best_practice"


class OptimizationType(Enum):
    """Enumeration of optimization types"""
    PERFORMANCE = "performance"
    READABILITY = "readability"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    MEMORY = "memory"
    CONCURRENCY = "concurrency"


@dataclass
class CodeIssue:
    """
    Represents a single code issue found during analysis.
    Contains detailed information about the issue including location, severity, and suggestions.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: IssueType = IssueType.LOGIC_ERROR
    severity: IssueSeverity = IssueSeverity.MEDIUM
    title: str = ""
    description: str = ""
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    file_path: Optional[str] = None
    rule_id: Optional[str] = None
    category: str = "general"
    suggestion: Optional[str] = None
    fix_suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    confidence_score: float = 0.0
    source_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert issue to dictionary format for serialization.
        Handles enum conversion and datetime formatting.
        
        Returns:
            Dictionary representation of the issue
        """
        return {
            'id': self.id,
            'type': self.type.value if isinstance(self.type, IssueType) else self.type,
            'severity': self.severity.value if isinstance(self.severity, IssueSeverity) else self.severity,
            'title': self.title,
            'description': self.description,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'file_path': self.file_path,
            'rule_id': self.rule_id,
            'category': self.category,
            'suggestion': self.suggestion,
            'fix_suggestion': self.fix_suggestion,
            'code_snippet': self.code_snippet,
            'confidence_score': self.confidence_score,
            'source_agent': self.source_agent,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeIssue':
        """
        Create CodeIssue instance from dictionary data.
        Handles type conversion and validation.
        
        Args:
            data: Dictionary containing issue data
            
        Returns:
            CodeIssue instance
        """
        # Convert string enums back to enum types
        if 'type' in data and isinstance(data['type'], str):
            try:
                data['type'] = IssueType(data['type'])
            except ValueError:
                data['type'] = IssueType.LOGIC_ERROR
        
        if 'severity' in data and isinstance(data['severity'], str):
            try:
                data['severity'] = IssueSeverity(data['severity'])
            except ValueError:
                data['severity'] = IssueSeverity.MEDIUM
        
        # Convert datetime string back to datetime
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except ValueError:
                data['created_at'] = datetime.now()
        
        return cls(**data)


@dataclass
class CodeSuggestion:
    """
    Represents a code improvement suggestion.
    Contains actionable recommendations for code enhancement.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: OptimizationType = OptimizationType.READABILITY
    title: str = ""
    description: str = ""
    line_number: Optional[int] = None
    original_code: Optional[str] = None
    suggested_code: Optional[str] = None
    impact: str = "low"  # low, medium, high
    effort: str = "low"  # low, medium, high
    confidence_score: float = 0.0
    source_agent: Optional[str] = None
    applicable: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary format"""
        return {
            'id': self.id,
            'type': self.type.value if isinstance(self.type, OptimizationType) else self.type,
            'title': self.title,
            'description': self.description,
            'line_number': self.line_number,
            'original_code': self.original_code,
            'suggested_code': self.suggested_code,
            'impact': self.impact,
            'effort': self.effort,
            'confidence_score': self.confidence_score,
            'source_agent': self.source_agent,
            'applicable': self.applicable,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CodeSuggestion':
        """Create CodeSuggestion instance from dictionary data"""
        if 'type' in data and isinstance(data['type'], str):
            try:
                data['type'] = OptimizationType(data['type'])
            except ValueError:
                data['type'] = OptimizationType.READABILITY
        
        if 'created_at' in data and isinstance(data['created_at'], str):
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'])
            except ValueError:
                data['created_at'] = datetime.now()
        
        return cls(**data)


@dataclass
class AnalysisMetrics:
    """
    Contains performance and quality metrics from analysis.
    Tracks various quantitative measures of code quality and analysis performance.
    """
    lines_analyzed: int = 0
    total_issues: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    info_issues: int = 0
    code_coverage: float = 0.0
    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    technical_debt_minutes: int = 0
    analysis_duration: float = 0.0
    agent_execution_time: Dict[str, float] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_quality_score(self) -> float:
        """
        Calculate overall code quality score based on issues and metrics.
        Uses weighted scoring system considering severity distribution.
        
        Returns:
            Quality score between 0.0 and 100.0
        """
        if self.lines_analyzed == 0:
            return 0.0
        
        # Weight issues by severity
        weighted_issues = (
            self.critical_issues * 4 +
            self.high_issues * 3 +
            self.medium_issues * 2 +
            self.low_issues * 1 +
            self.info_issues * 0.5
        )
        
        # Calculate issue density (issues per 100 lines)
        issue_density = (weighted_issues / self.lines_analyzed) * 100
        
        # Convert to quality score (lower issue density = higher quality)
        base_score = max(0, 100 - issue_density * 10)
        
        # Factor in other metrics if available
        if self.maintainability_index > 0:
            base_score = (base_score + self.maintainability_index) / 2
        
        return min(100.0, max(0.0, base_score))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format"""
        return {
            'lines_analyzed': self.lines_analyzed,
            'total_issues': self.total_issues,
            'critical_issues': self.critical_issues,
            'high_issues': self.high_issues,
            'medium_issues': self.medium_issues,
            'low_issues': self.low_issues,
            'info_issues': self.info_issues,
            'code_coverage': self.code_coverage,
            'complexity_score': self.complexity_score,
            'maintainability_index': self.maintainability_index,
            'technical_debt_minutes': self.technical_debt_minutes,
            'analysis_duration': self.analysis_duration,
            'agent_execution_time': self.agent_execution_time,
            'custom_metrics': self.custom_metrics,
            'quality_score': self.calculate_quality_score()
        }


@dataclass
class AnalysisResult:
    """
    Comprehensive analysis result containing all findings and metadata.
    Main result object returned by file analysis operations.
    """
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    agent_type: str = "general"
    issues: List[CodeIssue] = field(default_factory=list)
    suggestions: List[CodeSuggestion] = field(default_factory=list)
    metrics: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    confidence_score: float = 0.0
    execution_time: float = 0.0
    analysis_version: str = "1.0.0"
    language: Optional[str] = None
    framework: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[CodeIssue]:
        """
        Get all issues of a specific severity level.
        
        Args:
            severity: Severity level to filter by
            
        Returns:
            List of issues with the specified severity
        """
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_critical_issues(self) -> List[CodeIssue]:
        """Get all critical issues"""
        return self.get_issues_by_severity(IssueSeverity.CRITICAL)
    
    def get_high_issues(self) -> List[CodeIssue]:
        """Get all high severity issues"""
        return self.get_issues_by_severity(IssueSeverity.HIGH)
    
    def has_blocking_issues(self) -> bool:
        """
        Check if analysis found any blocking issues (critical or high severity).
        
        Returns:
            True if blocking issues found, False otherwise
        """
        return len(self.get_critical_issues()) > 0 or len(self.get_high_issues()) > 0
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of analysis results.
        
        Returns:
            Summary dictionary with key metrics and counts
        """
        severity_counts = {}
        for severity in IssueSeverity:
            severity_counts[severity.value] = len(self.get_issues_by_severity(severity))
        
        return {
            'total_issues': len(self.issues),
            'total_suggestions': len(self.suggestions),
            'severity_breakdown': severity_counts,
            'has_blocking_issues': self.has_blocking_issues(),
            'quality_score': self.metrics.calculate_quality_score(),
            'confidence_score': self.confidence_score,
            'execution_time': self.execution_time,
            'agent_type': self.agent_type,
            'success': self.success
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis result to dictionary format"""
        return {
            'operation_id': self.operation_id,
            'file_path': self.file_path,
            'agent_type': self.agent_type,
            'issues': [issue.to_dict() for issue in self.issues],
            'suggestions': [suggestion.to_dict() for suggestion in self.suggestions],
            'metrics': self.metrics.to_dict(),
            'confidence_score': self.confidence_score,
            'execution_time': self.execution_time,
            'analysis_version': self.analysis_version,
            'language': self.language,
            'framework': self.framework,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'summary': self.get_summary()
        }
    
    def to_json(self) -> str:
        """Convert analysis result to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class TestGenerationResult:
    """
    Result of test generation operations.
    Contains generated test code and comprehensive metadata about test coverage.
    """
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    test_type: str = "unit"
    agent_type: str = "general"
    test_code: str = ""
    test_file_path: str = ""
    coverage_areas: List[str] = field(default_factory=list)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    explanation: str = ""
    confidence_score: float = 0.0
    estimated_coverage: float = 0.0
    framework: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    setup_instructions: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_test_count(self) -> int:
        """
        Get total number of generated test cases.
        
        Returns:
            Number of test cases
        """
        return len(self.test_cases)
    
    def get_coverage_summary(self) -> Dict[str, Any]:
        """
        Get summary of test coverage information.
        
        Returns:
            Coverage summary dictionary
        """
        return {
            'coverage_areas': self.coverage_areas,
            'test_count': self.get_test_count(),
            'estimated_coverage': self.estimated_coverage,
            'framework': self.framework,
            'test_type': self.test_type
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert test generation result to dictionary format"""
        return {
            'operation_id': self.operation_id,
            'file_path': self.file_path,
            'test_type': self.test_type,
            'agent_type': self.agent_type,
            'test_code': self.test_code,
            'test_file_path': self.test_file_path,
            'coverage_areas': self.coverage_areas,
            'test_cases': self.test_cases,
            'explanation': self.explanation,
            'confidence_score': self.confidence_score,
            'estimated_coverage': self.estimated_coverage,
            'framework': self.framework,
            'dependencies': self.dependencies,
            'setup_instructions': self.setup_instructions,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'coverage_summary': self.get_coverage_summary()
        }
    
    def to_json(self) -> str:
        """Convert test generation result to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class CodeOptimization:
    """
    Represents a single code optimization suggestion.
    Contains before/after code and impact analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: OptimizationType = OptimizationType.PERFORMANCE
    title: str = ""
    description: str = ""
    line_number: Optional[int] = None
    before: str = ""
    after: str = ""
    impact: str = "medium"  # low, medium, high
    effort: str = "medium"  # low, medium, high
    auto_applicable: bool = False
    performance_gain: Optional[float] = None
    risk_level: str = "low"  # low, medium, high
    confidence_score: float = 0.0
    source_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def calculate_priority_score(self) -> float:
        """
        Calculate priority score based on impact, effort, and confidence.
        Higher score indicates higher priority for implementation.
        
        Returns:
            Priority score between 0.0 and 100.0
        """
        impact_weights = {'low': 1, 'medium': 2, 'high': 3}
        effort_weights = {'low': 3, 'medium': 2, 'high': 1}  # Lower effort = higher score
        
        impact_score = impact_weights.get(self.impact, 2)
        effort_score = effort_weights.get(self.effort, 2)
        
        # Base score from impact and effort
        base_score = (impact_score * effort_score) * 10
        
        # Factor in confidence
        confidence_factor = self.confidence_score / 100
        
        # Auto-applicable optimizations get bonus
        auto_bonus = 10 if self.auto_applicable else 0
        
        return min(100.0, base_score * confidence_factor + auto_bonus)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert optimization to dictionary format"""
        return {
            'id': self.id,
            'type': self.type.value if isinstance(self.type, OptimizationType) else self.type,
            'title': self.title,
            'description': self.description,
            'line_number': self.line_number,
            'before': self.before,
            'after': self.after,
            'impact': self.impact,
            'effort': self.effort,
            'auto_applicable': self.auto_applicable,
            'performance_gain': self.performance_gain,
            'risk_level': self.risk_level,
            'confidence_score': self.confidence_score,
            'source_agent': self.source_agent,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'priority_score': self.calculate_priority_score()
        }


@dataclass
class OptimizationResult:
    """
    Result of code optimization operations.
    Contains optimization suggestions and applied changes.
    """
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str = ""
    optimization_type: str = "performance"
    agent_type: str = "general"
    original_content: str = ""
    optimized_content: str = ""
    optimizations: List[CodeOptimization] = field(default_factory=list)
    applied_optimizations: List[CodeOptimization] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    estimated_improvement: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_high_priority_optimizations(self) -> List[CodeOptimization]:
        """
        Get optimizations with high priority scores.
        
        Returns:
            List of high-priority optimizations (priority > 70)
        """
        return [opt for opt in self.optimizations if opt.calculate_priority_score() > 70]
    
    def get_auto_applicable_optimizations(self) -> List[CodeOptimization]:
        """
        Get optimizations that can be applied automatically.
        
        Returns:
            List of auto-applicable optimizations
        """
        return [opt for opt in self.optimizations if opt.auto_applicable]
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """
        Get summary of optimization results.
        
        Returns:
            Summary dictionary with key metrics
        """
        return {
            'total_optimizations': len(self.optimizations),
            'applied_optimizations': len(self.applied_optimizations),
            'high_priority_count': len(self.get_high_priority_optimizations()),
            'auto_applicable_count': len(self.get_auto_applicable_optimizations()),
            'optimization_type': self.optimization_type,
            'estimated_improvement': self.estimated_improvement,
            'confidence_score': self.confidence_score
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert optimization result to dictionary format"""
        return {
            'operation_id': self.operation_id,
            'file_path': self.file_path,
            'optimization_type': self.optimization_type,
            'agent_type': self.agent_type,
            'original_content': self.original_content,
            'optimized_content': self.optimized_content,
            'optimizations': [opt.to_dict() for opt in self.optimizations],
            'applied_optimizations': [opt.to_dict() for opt in self.applied_optimizations],
            'metrics': self.metrics,
            'confidence_score': self.confidence_score,
            'estimated_improvement': self.estimated_improvement,
            'success': self.success,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'summary': self.get_optimization_summary()
        }
    
    def to_json(self) -> str:
        """Convert optimization result to JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str) 