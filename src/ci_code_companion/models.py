"""
Database Models for CI Code Companion

This module defines the database models for storing commits, code files,
AI analysis results, and context cache for enhanced AI understanding.
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, JSON, 
    ForeignKey, Index, Float, LargeBinary, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from datetime import datetime
import enum
import hashlib
import json

Base = declarative_base()

class AnalysisType(enum.Enum):
    """Types of AI analysis performed"""
    COMPREHENSIVE = "comprehensive"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    STYLE = "style"

class IssueSeverity(enum.Enum):
    """Severity levels for identified issues"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IssueCategory(enum.Enum):
    """Categories of code issues"""
    SECURITY = "security"
    BUG = "bug"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    STYLE = "style"
    BEST_PRACTICE = "best_practice"

class Repository(Base):
    """Repository information and metadata"""
    __tablename__ = 'repositories'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(500), nullable=False)  # e.g., "owner/repo"
    gitlab_id = Column(Integer, unique=True, nullable=True)
    github_id = Column(Integer, unique=True, nullable=True)
    url = Column(String(500), nullable=False)
    description = Column(Text)
    default_branch = Column(String(100), default='main')
    
    # Metadata
    language = Column(String(50))
    size = Column(Integer)  # Repository size in KB
    is_private = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_analyzed_at = Column(DateTime)
    
    # AI Context
    ai_context_summary = Column(Text)  # High-level AI understanding of the repository
    architecture_summary = Column(Text)  # AI-generated architecture overview
    
    # Relationships
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan")
    files = relationship("CodeFile", back_populates="repository", cascade="all, delete-orphan")
    analyses = relationship("AIAnalysis", back_populates="repository", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Repository(name='{self.name}', url='{self.url}')>"

class Commit(Base):
    """Git commit information"""
    __tablename__ = 'commits'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    
    # Git metadata
    sha = Column(String(40), nullable=False)  # Git SHA hash
    message = Column(Text, nullable=False)
    author_name = Column(String(255))
    author_email = Column(String(255))
    committer_name = Column(String(255))
    committer_email = Column(String(255))
    
    # Timestamps
    committed_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Analysis metadata
    files_changed = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    
    # AI Context
    commit_summary = Column(Text)  # AI-generated summary of changes
    impact_assessment = Column(Text)  # AI assessment of commit impact
    
    # Relationships
    repository = relationship("Repository", back_populates="commits")
    file_changes = relationship("FileChange", back_populates="commit", cascade="all, delete-orphan")
    analyses = relationship("AIAnalysis", back_populates="commit")
    
    # Indexes
    __table_args__ = (
        Index('idx_commit_repo_sha', 'repository_id', 'sha'),
        Index('idx_commit_date', 'committed_at'),
    )
    
    def __repr__(self):
        return f"<Commit(sha='{self.sha[:8]}', message='{self.message[:50]}...')>"

class CodeFile(Base):
    """Code file information and content"""
    __tablename__ = 'code_files'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    
    # File metadata
    path = Column(String(1000), nullable=False)
    filename = Column(String(255), nullable=False)
    extension = Column(String(10))
    language = Column(String(50))
    size_bytes = Column(Integer)
    
    # Content
    content = Column(Text)  # Latest file content
    content_hash = Column(String(64))  # SHA-256 hash of content
    
    # Analysis metadata
    complexity_score = Column(Float)
    maintainability_index = Column(Float)
    lines_of_code = Column(Integer)
    cyclomatic_complexity = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_analyzed_at = Column(DateTime)
    
    # AI Context
    purpose_summary = Column(Text)  # AI understanding of file purpose
    dependencies = Column(JSON)  # List of dependencies identified by AI
    key_functions = Column(JSON)  # Important functions/classes identified by AI
    
    # Relationships
    repository = relationship("Repository", back_populates="files")
    file_changes = relationship("FileChange", back_populates="code_file")
    issues = relationship("CodeIssue", back_populates="code_file")
    
    # Indexes
    __table_args__ = (
        Index('idx_file_repo_path', 'repository_id', 'path'),
        Index('idx_file_hash', 'content_hash'),
        Index('idx_file_language', 'language'),
    )
    
    def calculate_content_hash(self):
        """Calculate SHA-256 hash of file content"""
        if self.content:
            return hashlib.sha256(self.content.encode('utf-8')).hexdigest()
        return None
    
    def __repr__(self):
        return f"<CodeFile(path='{self.path}', language='{self.language}')>"

class FileChange(Base):
    """Changes to files in specific commits"""
    __tablename__ = 'file_changes'

    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False)
    code_file_id = Column(Integer, ForeignKey('code_files.id'), nullable=False)
    
    # Change metadata
    change_type = Column(String(20), nullable=False)  # added, modified, deleted, renamed
    old_path = Column(String(1000))  # For renamed files
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    
    # Content changes
    diff_content = Column(Text)  # Git diff for this file
    old_content = Column(Text)  # Content before change
    new_content = Column(Text)  # Content after change
    
    # AI Analysis
    change_summary = Column(Text)  # AI summary of what changed
    impact_analysis = Column(Text)  # AI analysis of change impact
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    commit = relationship("Commit", back_populates="file_changes")
    code_file = relationship("CodeFile", back_populates="file_changes")
    
    def __repr__(self):
        return f"<FileChange(type='{self.change_type}', file='{self.code_file.path if self.code_file else 'Unknown'}')>"

class AIAnalysis(Base):
    """AI analysis results for commits or files"""
    __tablename__ = 'ai_analyses'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=True)
    
    # Analysis metadata
    analysis_type = Column(Enum(AnalysisType), nullable=False)
    model_name = Column(String(100))  # AI model used
    model_version = Column(String(50))
    
    # Analysis results
    overall_score = Column(Float)  # Overall quality/security/performance score
    summary = Column(Text)  # AI-generated summary
    recommendations = Column(JSON)  # List of recommendations
    
    # Metrics
    issues_found = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_issues = Column(Integer, default=0)
    medium_issues = Column(Integer, default=0)
    low_issues = Column(Integer, default=0)
    
    # Processing metadata
    processing_time_ms = Column(Integer)  # Time taken for analysis
    tokens_used = Column(Integer)  # AI tokens consumed
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # AI Context
    context_used = Column(JSON)  # Context information provided to AI
    insights = Column(JSON)  # Key insights from analysis
    
    # Relationships
    repository = relationship("Repository", back_populates="analyses")
    commit = relationship("Commit", back_populates="analyses")
    issues = relationship("CodeIssue", back_populates="analysis", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AIAnalysis(type='{self.analysis_type.value}', score={self.overall_score})>"

class CodeIssue(Base):
    """Individual code issues identified by AI"""
    __tablename__ = 'code_issues'

    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('ai_analyses.id'), nullable=False)
    code_file_id = Column(Integer, ForeignKey('code_files.id'), nullable=False)
    
    # Issue details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(IssueSeverity), nullable=False)
    category = Column(Enum(IssueCategory), nullable=False)
    
    # Location information
    line_start = Column(Integer)
    line_end = Column(Integer)
    column_start = Column(Integer)
    column_end = Column(Integer)
    
    # Code content
    problematic_code = Column(Text)
    suggested_fix = Column(Text)
    explanation = Column(Text)
    
    # Impact and effort
    impact_description = Column(JSON)  # List of impacts
    effort_estimate = Column(String(20))  # low, medium, high
    
    # Status
    status = Column(String(20), default='open')  # open, resolved, ignored, false_positive
    resolved_at = Column(DateTime)
    resolution_note = Column(Text)
    
    # AI metadata
    confidence_score = Column(Float)  # AI confidence in this issue (0-1)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    analysis = relationship("AIAnalysis", back_populates="issues")
    code_file = relationship("CodeFile", back_populates="issues")
    
    # Indexes
    __table_args__ = (
        Index('idx_issue_severity', 'severity'),
        Index('idx_issue_category', 'category'),
        Index('idx_issue_status', 'status'),
        Index('idx_issue_file', 'code_file_id'),
    )
    
    def __repr__(self):
        return f"<CodeIssue(title='{self.title[:50]}...', severity='{self.severity.value}')>"

class AIContextCache(Base):
    """Cache for AI context and learnings about codebases"""
    __tablename__ = 'ai_context_cache'

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=False)
    
    # Cache key and content
    context_key = Column(String(100), nullable=False)  # e.g., "architecture", "patterns", "dependencies"
    context_data = Column(JSON, nullable=False)  # Cached AI understanding
    
    # Metadata
    data_version = Column(String(20), default='1.0')
    confidence_score = Column(Float)  # How confident AI is in this context
    
    # Invalidation tracking
    files_hash = Column(String(64))  # Hash of relevant files for cache invalidation
    last_commit_sha = Column(String(40))  # Last commit this context is valid for
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)  # Optional expiration
    
    # Relationships
    repository = relationship("Repository")
    
    # Indexes
    __table_args__ = (
        Index('idx_context_repo_key', 'repository_id', 'context_key'),
        Index('idx_context_expires', 'expires_at'),
    )
    
    def is_expired(self):
        """Check if cache entry is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def __repr__(self):
        return f"<AIContextCache(key='{self.context_key}', repo_id={self.repository_id})>"

class AILearning(Base):
    """AI learnings and patterns identified across repositories"""
    __tablename__ = 'ai_learnings'

    id = Column(Integer, primary_key=True)
    
    # Learning metadata
    pattern_type = Column(String(50), nullable=False)  # e.g., "anti_pattern", "best_practice"
    pattern_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Pattern details
    code_pattern = Column(Text)  # Code pattern or snippet
    languages = Column(JSON)  # Programming languages this applies to
    contexts = Column(JSON)  # Contexts where this pattern is relevant
    
    # Evidence and confidence
    examples_count = Column(Integer, default=0)  # Number of examples found
    repositories_count = Column(Integer, default=0)  # Number of repos with this pattern
    confidence_score = Column(Float)  # Confidence in this learning
    
    # Impact assessment
    severity_impact = Column(String(20))  # How severely this affects code quality
    frequency = Column(String(20))  # How often this pattern appears
    
    # Learning evolution
    version = Column(String(20), default='1.0')
    supersedes_id = Column(Integer, ForeignKey('ai_learnings.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_seen_at = Column(DateTime)
    
    # Relationships
    superseded_by = relationship("AILearning", remote_side=[id])
    
    def __repr__(self):
        return f"<AILearning(name='{self.pattern_name}', type='{self.pattern_type}')>"

class PerformanceMetrics(Base):
    """Performance metrics for monitoring system health"""
    __tablename__ = 'performance_metrics'

    id = Column(Integer, primary_key=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(20))  # e.g., "ms", "tokens", "percentage"
    
    # Context
    repository_id = Column(Integer, ForeignKey('repositories.id'), nullable=True)
    analysis_id = Column(Integer, ForeignKey('ai_analyses.id'), nullable=True)
    
    # Additional data
    additional_data = Column(JSON)  # Additional metric data
    
    # Timestamp
    recorded_at = Column(DateTime, default=func.now())
    
    # Relationships
    repository = relationship("Repository")
    analysis = relationship("AIAnalysis")
    
    # Indexes
    __table_args__ = (
        Index('idx_metrics_name_date', 'metric_name', 'recorded_at'),
        Index('idx_metrics_repo', 'repository_id'),
    )
    
    def __repr__(self):
        return f"<PerformanceMetrics(name='{self.metric_name}', value={self.metric_value})>"

# Database initialization and helper functions
def create_database_schema(engine):
    """Create all database tables"""
    Base.metadata.create_all(engine)

def get_repository_context(session, repository_id):
    """Get comprehensive AI context for a repository"""
    repo = session.query(Repository).filter_by(id=repository_id).first()
    if not repo:
        return None
    
    # Get cached context
    cached_contexts = session.query(AIContextCache).filter_by(
        repository_id=repository_id
    ).all()
    
    # Get recent analyses
    recent_analyses = session.query(AIAnalysis).filter_by(
        repository_id=repository_id
    ).order_by(AIAnalysis.created_at.desc()).limit(10).all()
    
    # Get file statistics
    file_stats = session.query(CodeFile).filter_by(
        repository_id=repository_id
    ).all()
    
    return {
        'repository': repo,
        'cached_contexts': {ctx.context_key: ctx.context_data for ctx in cached_contexts},
        'recent_analyses': recent_analyses,
        'file_statistics': {
            'total_files': len(file_stats),
            'languages': list(set(f.language for f in file_stats if f.language)),
            'total_lines': sum(f.lines_of_code or 0 for f in file_stats),
            'avg_complexity': sum(f.complexity_score or 0 for f in file_stats) / len(file_stats) if file_stats else 0
        }
    }

def update_ai_context_cache(session, repository_id, context_key, context_data, confidence_score=0.8):
    """Update or create AI context cache entry"""
    existing = session.query(AIContextCache).filter_by(
        repository_id=repository_id,
        context_key=context_key
    ).first()
    
    if existing:
        existing.context_data = context_data
        existing.confidence_score = confidence_score
        existing.updated_at = func.now()
        existing.access_count += 1
    else:
        new_cache = AIContextCache(
            repository_id=repository_id,
            context_key=context_key,
            context_data=context_data,
            confidence_score=confidence_score
        )
        session.add(new_cache)
    
    session.commit()

def invalidate_context_cache(session, repository_id, commit_sha):
    """Invalidate context cache entries for a repository after new commit"""
    session.query(AIContextCache).filter_by(
        repository_id=repository_id
    ).update({
        'last_commit_sha': commit_sha,
        'updated_at': func.now()
    })
    session.commit() 