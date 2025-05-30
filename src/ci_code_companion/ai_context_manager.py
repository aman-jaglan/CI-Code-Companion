"""
AI Context Manager for CI Code Companion

This module manages AI context caching, learning accumulation, and provides
enhanced context to AI models for better analysis results.
"""

import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from .models import (
    Repository, Commit, CodeFile, FileChange, AIAnalysis, CodeIssue,
    AIContextCache, AILearning, PerformanceMetrics,
    get_repository_context, update_ai_context_cache, invalidate_context_cache
)

logger = logging.getLogger(__name__)

class AIContextManager:
    """Manages AI context caching and provides enhanced context for analysis"""
    
    def __init__(self, db_session: Session):
        """Initialize AI Context Manager with database session"""
        self.db_session = db_session
        self.context_expiry_hours = 24  # Default cache expiry
        
    def build_comprehensive_context(
        self, 
        repository_id: int, 
        commit_sha: Optional[str] = None,
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive AI context for analysis including:
        - Repository architecture understanding
        - Historical patterns and learnings
        - File relationships and dependencies
        - Previous analysis insights
        """
        try:
            logger.info(f"Building comprehensive context for repository {repository_id}")
            
            # Get base repository context
            base_context = get_repository_context(self.db_session, repository_id)
            if not base_context:
                raise ValueError(f"Repository {repository_id} not found")
            
            # Build enhanced context
            context = {
                'repository_info': self._get_repository_info(base_context['repository']),
                'architecture_context': self._get_architecture_context(repository_id),
                'historical_patterns': self._get_historical_patterns(repository_id),
                'file_relationships': self._get_file_relationships(repository_id, file_paths),
                'previous_insights': self._get_previous_insights(repository_id),
                'code_quality_trends': self._get_quality_trends(repository_id),
                'security_context': self._get_security_context(repository_id),
                'performance_context': self._get_performance_context(repository_id),
                'ai_learnings': self._get_relevant_ai_learnings(repository_id),
                'context_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'commit_sha': commit_sha,
                    'files_analyzed': file_paths or [],
                    'cache_keys_used': []
                }
            }
            
            logger.info(f"Successfully built comprehensive context with {len(context)} sections")
            return context
            
        except Exception as e:
            logger.error(f"Error building comprehensive context: {str(e)}")
            raise
    
    def _get_repository_info(self, repository: Repository) -> Dict[str, Any]:
        """Get basic repository information"""
        return {
            'name': repository.name,
            'full_name': repository.full_name,
            'description': repository.description,
            'primary_language': repository.language,
            'default_branch': repository.default_branch,
            'size_kb': repository.size,
            'is_private': repository.is_private,
            'ai_context_summary': repository.ai_context_summary,
            'architecture_summary': repository.architecture_summary,
            'last_analyzed': repository.last_analyzed_at.isoformat() if repository.last_analyzed_at else None
        }
    
    def _get_architecture_context(self, repository_id: int) -> Dict[str, Any]:
        """Get or build architecture context from cache"""
        cache_key = "architecture_context"
        cached = self._get_from_cache(repository_id, cache_key)
        
        if cached and not self._is_cache_stale(cached, repository_id):
            cached['access_count'] += 1
            return cached['context_data']
        
        # Build architecture context
        architecture_context = self._analyze_repository_architecture(repository_id)
        
        # Cache the result
        self._update_cache(repository_id, cache_key, architecture_context, 0.85)
        
        return architecture_context
    
    def _analyze_repository_architecture(self, repository_id: int) -> Dict[str, Any]:
        """Analyze repository architecture and file organization"""
        files = self.db_session.query(CodeFile).filter_by(
            repository_id=repository_id
        ).all()
        
        # Analyze file structure
        directories = {}
        file_types = {}
        language_distribution = {}
        
        for file in files:
            # Directory analysis
            path_parts = file.path.split('/')
            if len(path_parts) > 1:
                dir_name = path_parts[0]
                directories[dir_name] = directories.get(dir_name, 0) + 1
            
            # File type analysis
            if file.extension:
                file_types[file.extension] = file_types.get(file.extension, 0) + 1
            
            # Language distribution
            if file.language:
                language_distribution[file.language] = language_distribution.get(file.language, 0) + 1
        
        # Identify patterns
        patterns = self._identify_architecture_patterns(files, directories)
        
        return {
            'directory_structure': directories,
            'file_types': file_types,
            'language_distribution': language_distribution,
            'architecture_patterns': patterns,
            'total_files': len(files),
            'complexity_metrics': self._calculate_repository_complexity(files),
            'dependencies': self._extract_dependencies(files)
        }
    
    def _identify_architecture_patterns(
        self, 
        files: List[CodeFile], 
        directories: Dict[str, int]
    ) -> Dict[str, Any]:
        """Identify common architecture patterns in the repository"""
        patterns = {
            'mvc_pattern': False,
            'microservices_pattern': False,
            'layered_architecture': False,
            'monolithic_structure': False,
            'test_driven': False,
            'api_focused': False
        }
        
        # Check for MVC pattern
        mvc_dirs = {'models', 'views', 'controllers', 'model', 'view', 'controller'}
        if any(dir_name.lower() in mvc_dirs for dir_name in directories.keys()):
            patterns['mvc_pattern'] = True
        
        # Check for microservices
        service_indicators = {'service', 'services', 'microservice', 'api', 'gateway'}
        if any(indicator in dir_name.lower() for dir_name in directories.keys() 
               for indicator in service_indicators):
            patterns['microservices_pattern'] = True
        
        # Check for layered architecture
        layer_indicators = {'domain', 'application', 'infrastructure', 'presentation', 'data'}
        if any(indicator in dir_name.lower() for dir_name in directories.keys() 
               for indicator in layer_indicators):
            patterns['layered_architecture'] = True
        
        # Check for test-driven development
        test_files = [f for f in files if 'test' in f.path.lower() or f.path.startswith('test')]
        if len(test_files) > len(files) * 0.3:  # More than 30% test files
            patterns['test_driven'] = True
        
        # Check for API-focused architecture
        api_files = [f for f in files if any(keyword in f.path.lower() 
                     for keyword in ['api', 'endpoint', 'route', 'handler'])]
        if len(api_files) > len(files) * 0.2:  # More than 20% API files
            patterns['api_focused'] = True
        
        # Determine if monolithic (simple structure with many files)
        if len(directories) < 5 and len(files) > 50:
            patterns['monolithic_structure'] = True
        
        return patterns
    
    def _calculate_repository_complexity(self, files: List[CodeFile]) -> Dict[str, float]:
        """Calculate repository-wide complexity metrics"""
        total_complexity = sum(f.complexity_score or 0 for f in files)
        total_maintainability = sum(f.maintainability_index or 0 for f in files)
        total_loc = sum(f.lines_of_code or 0 for f in files)
        total_cyclomatic = sum(f.cyclomatic_complexity or 0 for f in files)
        
        file_count = len(files)
        
        return {
            'average_complexity': total_complexity / file_count if file_count > 0 else 0,
            'average_maintainability': total_maintainability / file_count if file_count > 0 else 0,
            'total_lines_of_code': total_loc,
            'average_cyclomatic_complexity': total_cyclomatic / file_count if file_count > 0 else 0,
            'complexity_distribution': self._get_complexity_distribution(files)
        }
    
    def _get_complexity_distribution(self, files: List[CodeFile]) -> Dict[str, int]:
        """Get distribution of complexity scores across files"""
        distribution = {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
        
        for file in files:
            complexity = file.complexity_score or 0
            if complexity < 2:
                distribution['low'] += 1
            elif complexity < 5:
                distribution['medium'] += 1
            elif complexity < 10:
                distribution['high'] += 1
            else:
                distribution['very_high'] += 1
        
        return distribution
    
    def _extract_dependencies(self, files: List[CodeFile]) -> Dict[str, List[str]]:
        """Extract and analyze dependencies from files"""
        all_dependencies = {}
        
        for file in files:
            if file.dependencies:
                file_deps = file.dependencies if isinstance(file.dependencies, list) else []
                all_dependencies[file.path] = file_deps
        
        # Analyze dependency patterns
        dependency_analysis = {
            'internal_dependencies': {},
            'external_dependencies': {},
            'circular_dependencies': [],
            'dependency_count': len(all_dependencies)
        }
        
        # TODO: Implement more sophisticated dependency analysis
        return dependency_analysis
    
    def _get_historical_patterns(self, repository_id: int) -> Dict[str, Any]:
        """Get historical patterns and trends from previous analyses"""
        cache_key = "historical_patterns"
        cached = self._get_from_cache(repository_id, cache_key)
        
        if cached and not self._is_cache_stale(cached, repository_id):
            return cached['context_data']
        
        # Analyze historical data
        recent_analyses = self.db_session.query(AIAnalysis).filter_by(
            repository_id=repository_id
        ).order_by(desc(AIAnalysis.created_at)).limit(20).all()
        
        patterns = {
            'recurring_issues': self._find_recurring_issues(repository_id),
            'quality_trends': self._analyze_quality_trends(recent_analyses),
            'common_fix_patterns': self._analyze_fix_patterns(repository_id),
            'seasonal_patterns': self._analyze_seasonal_patterns(recent_analyses)
        }
        
        # Cache the result
        self._update_cache(repository_id, cache_key, patterns, 0.8)
        
        return patterns
    
    def _find_recurring_issues(self, repository_id: int) -> List[Dict[str, Any]]:
        """Find issues that appear repeatedly across analyses"""
        # Group issues by similarity
        all_issues = self.db_session.query(CodeIssue).join(AIAnalysis).filter(
            AIAnalysis.repository_id == repository_id
        ).all()
        
        issue_patterns = {}
        for issue in all_issues:
            # Group by category and description similarity
            key = f"{issue.category.value}_{issue.title[:50]}"
            if key not in issue_patterns:
                issue_patterns[key] = {
                    'pattern': issue.title,
                    'category': issue.category.value,
                    'count': 0,
                    'severity_distribution': {},
                    'files_affected': set()
                }
            
            issue_patterns[key]['count'] += 1
            severity = issue.severity.value
            issue_patterns[key]['severity_distribution'][severity] = \
                issue_patterns[key]['severity_distribution'].get(severity, 0) + 1
            issue_patterns[key]['files_affected'].add(issue.code_file.path)
        
        # Convert to list and sort by frequency
        recurring = []
        for pattern_data in issue_patterns.values():
            if pattern_data['count'] > 2:  # Only patterns that occur more than twice
                pattern_data['files_affected'] = list(pattern_data['files_affected'])
                recurring.append(pattern_data)
        
        return sorted(recurring, key=lambda x: x['count'], reverse=True)[:10]
    
    def _analyze_quality_trends(self, analyses: List[AIAnalysis]) -> Dict[str, Any]:
        """Analyze quality trends over time"""
        if not analyses:
            return {}
        
        scores = [a.overall_score for a in analyses if a.overall_score is not None]
        issue_counts = [a.issues_found for a in analyses]
        
        return {
            'average_score': sum(scores) / len(scores) if scores else 0,
            'score_trend': 'improving' if len(scores) > 1 and scores[0] > scores[-1] else 'declining',
            'average_issues': sum(issue_counts) / len(issue_counts) if issue_counts else 0,
            'latest_score': scores[0] if scores else 0,
            'score_variance': self._calculate_variance(scores),
            'analysis_frequency': len(analyses)
        }
    
    def _analyze_fix_patterns(self, repository_id: int) -> List[Dict[str, Any]]:
        """Analyze common patterns in how issues are fixed"""
        # Get resolved issues with their fixes
        resolved_issues = self.db_session.query(CodeIssue).join(AIAnalysis).filter(
            AIAnalysis.repository_id == repository_id,
            CodeIssue.status == 'resolved'
        ).all()
        
        fix_patterns = []
        for issue in resolved_issues[:50]:  # Limit to recent 50 resolved issues
            if issue.suggested_fix and issue.resolution_note:
                fix_patterns.append({
                    'issue_category': issue.category.value,
                    'fix_type': self._classify_fix_type(issue.suggested_fix),
                    'effort_level': issue.effort_estimate,
                    'resolution_time': (issue.resolved_at - issue.created_at).days if issue.resolved_at else None
                })
        
        return fix_patterns
    
    def _classify_fix_type(self, fix_content: str) -> str:
        """Classify the type of fix based on content"""
        fix_lower = fix_content.lower()
        
        if any(keyword in fix_lower for keyword in ['refactor', 'restructure', 'reorganize']):
            return 'refactoring'
        elif any(keyword in fix_lower for keyword in ['add', 'implement', 'create']):
            return 'addition'
        elif any(keyword in fix_lower for keyword in ['remove', 'delete', 'eliminate']):
            return 'removal'
        elif any(keyword in fix_lower for keyword in ['replace', 'substitute', 'change']):
            return 'replacement'
        elif any(keyword in fix_lower for keyword in ['optimize', 'improve', 'enhance']):
            return 'optimization'
        else:
            return 'modification'
    
    def _analyze_seasonal_patterns(self, analyses: List[AIAnalysis]) -> Dict[str, Any]:
        """Analyze patterns based on timing (day of week, time of day, etc.)"""
        if not analyses:
            return {}
        
        # Group by day of week
        day_patterns = {}
        hour_patterns = {}
        
        for analysis in analyses:
            if analysis.created_at:
                day = analysis.created_at.strftime('%A')
                hour = analysis.created_at.hour
                
                day_patterns[day] = day_patterns.get(day, 0) + 1
                hour_patterns[hour] = hour_patterns.get(hour, 0) + 1
        
        return {
            'most_active_day': max(day_patterns.items(), key=lambda x: x[1])[0] if day_patterns else None,
            'most_active_hour': max(hour_patterns.items(), key=lambda x: x[1])[0] if hour_patterns else None,
            'day_distribution': day_patterns,
            'hour_distribution': hour_patterns
        }
    
    def _get_file_relationships(self, repository_id: int, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get relationships between files and their dependencies"""
        cache_key = f"file_relationships_{hash(str(file_paths)) if file_paths else 'all'}"
        cached = self._get_from_cache(repository_id, cache_key)
        
        if cached and not self._is_cache_stale(cached, repository_id):
            return cached['context_data']
        
        # Build file relationships
        query = self.db_session.query(CodeFile).filter_by(repository_id=repository_id)
        if file_paths:
            query = query.filter(CodeFile.path.in_(file_paths))
        
        files = query.all()
        relationships = self._analyze_file_relationships(files)
        
        # Cache with shorter expiry for file-specific contexts
        expiry = datetime.utcnow() + timedelta(hours=6)
        self._update_cache(repository_id, cache_key, relationships, 0.7, expiry)
        
        return relationships
    
    def _analyze_file_relationships(self, files: List[CodeFile]) -> Dict[str, Any]:
        """Analyze relationships between files"""
        relationships = {
            'dependency_graph': {},
            'file_clusters': [],
            'critical_files': [],
            'isolated_files': []
        }
        
        # Build dependency graph
        for file in files:
            file_path = file.path
            dependencies = file.dependencies or []
            
            relationships['dependency_graph'][file_path] = {
                'depends_on': dependencies,
                'depended_by': [],
                'complexity': file.complexity_score or 0,
                'size': file.lines_of_code or 0,
                'language': file.language
            }
        
        # Calculate reverse dependencies
        for file_path, data in relationships['dependency_graph'].items():
            for dep in data['depends_on']:
                if dep in relationships['dependency_graph']:
                    relationships['dependency_graph'][dep]['depended_by'].append(file_path)
        
        # Identify critical files (high dependency count)
        for file_path, data in relationships['dependency_graph'].items():
            dependency_count = len(data['depended_by'])
            if dependency_count > 3:  # Threshold for critical files
                relationships['critical_files'].append({
                    'path': file_path,
                    'dependency_count': dependency_count,
                    'complexity': data['complexity']
                })
        
        # Identify isolated files (no dependencies)
        for file_path, data in relationships['dependency_graph'].items():
            if not data['depends_on'] and not data['depended_by']:
                relationships['isolated_files'].append(file_path)
        
        return relationships
    
    def _get_previous_insights(self, repository_id: int) -> Dict[str, Any]:
        """Get insights from previous AI analyses"""
        recent_analyses = self.db_session.query(AIAnalysis).filter_by(
            repository_id=repository_id
        ).order_by(desc(AIAnalysis.created_at)).limit(5).all()
        
        insights = {
            'key_recommendations': [],
            'successful_patterns': [],
            'persistent_issues': [],
            'improvement_areas': []
        }
        
        for analysis in recent_analyses:
            if analysis.insights:
                insights_data = analysis.insights if isinstance(analysis.insights, dict) else {}
                
                # Accumulate recommendations
                if 'recommendations' in insights_data:
                    insights['key_recommendations'].extend(insights_data['recommendations'])
                
                # Track successful patterns
                if analysis.overall_score and analysis.overall_score > 8.0:
                    insights['successful_patterns'].append({
                        'score': analysis.overall_score,
                        'type': analysis.analysis_type.value,
                        'date': analysis.created_at.isoformat()
                    })
        
        # Deduplicate and limit results
        insights['key_recommendations'] = list(set(insights['key_recommendations']))[:10]
        
        return insights
    
    def _get_quality_trends(self, repository_id: int) -> Dict[str, Any]:
        """Get code quality trends over time"""
        # Get quality metrics over time
        quality_metrics = self.db_session.query(PerformanceMetrics).filter_by(
            repository_id=repository_id
        ).filter(
            PerformanceMetrics.metric_name.in_(['code_quality_score', 'maintainability_index'])
        ).order_by(desc(PerformanceMetrics.recorded_at)).limit(30).all()
        
        trends = {
            'quality_scores': [],
            'trend_direction': 'stable',
            'improvement_rate': 0,
            'current_score': 0
        }
        
        quality_scores = [m.metric_value for m in quality_metrics if m.metric_name == 'code_quality_score']
        
        if quality_scores:
            trends['quality_scores'] = quality_scores
            trends['current_score'] = quality_scores[0]
            
            if len(quality_scores) > 1:
                recent_avg = sum(quality_scores[:5]) / 5
                older_avg = sum(quality_scores[-5:]) / 5
                
                if recent_avg > older_avg * 1.05:
                    trends['trend_direction'] = 'improving'
                elif recent_avg < older_avg * 0.95:
                    trends['trend_direction'] = 'declining'
                
                trends['improvement_rate'] = ((recent_avg - older_avg) / older_avg) * 100
        
        return trends
    
    def _get_security_context(self, repository_id: int) -> Dict[str, Any]:
        """Get security-specific context"""
        security_issues = self.db_session.query(CodeIssue).join(AIAnalysis).filter(
            AIAnalysis.repository_id == repository_id,
            CodeIssue.category == 'security'
        ).order_by(desc(CodeIssue.created_at)).limit(20).all()
        
        context = {
            'recent_vulnerabilities': [],
            'security_patterns': {},
            'risk_assessment': 'low'
        }
        
        for issue in security_issues:
            context['recent_vulnerabilities'].append({
                'type': issue.title,
                'severity': issue.severity.value,
                'file': issue.code_file.path,
                'status': issue.status
            })
        
        # Assess overall risk
        critical_count = sum(1 for issue in security_issues if issue.severity.value == 'critical')
        high_count = sum(1 for issue in security_issues if issue.severity.value == 'high')
        
        if critical_count > 0:
            context['risk_assessment'] = 'critical'
        elif high_count > 2:
            context['risk_assessment'] = 'high'
        elif len(security_issues) > 5:
            context['risk_assessment'] = 'medium'
        
        return context
    
    def _get_performance_context(self, repository_id: int) -> Dict[str, Any]:
        """Get performance-specific context"""
        perf_issues = self.db_session.query(CodeIssue).join(AIAnalysis).filter(
            AIAnalysis.repository_id == repository_id,
            CodeIssue.category == 'performance'
        ).order_by(desc(CodeIssue.created_at)).limit(15).all()
        
        context = {
            'performance_bottlenecks': [],
            'optimization_opportunities': [],
            'complexity_hotspots': []
        }
        
        # Get high complexity files
        complex_files = self.db_session.query(CodeFile).filter_by(
            repository_id=repository_id
        ).filter(
            CodeFile.complexity_score > 8.0
        ).order_by(desc(CodeFile.complexity_score)).limit(10).all()
        
        for file in complex_files:
            context['complexity_hotspots'].append({
                'path': file.path,
                'complexity': file.complexity_score,
                'lines_of_code': file.lines_of_code
            })
        
        for issue in perf_issues:
            if 'bottleneck' in issue.description.lower():
                context['performance_bottlenecks'].append(issue.title)
            else:
                context['optimization_opportunities'].append(issue.title)
        
        return context
    
    def _get_relevant_ai_learnings(self, repository_id: int) -> List[Dict[str, Any]]:
        """Get relevant AI learnings for this repository"""
        # Get repository languages
        repo_languages = self.db_session.query(CodeFile.language).filter_by(
            repository_id=repository_id
        ).distinct().all()
        languages = [lang[0] for lang in repo_languages if lang[0]]
        
        # Get relevant learnings
        learnings = self.db_session.query(AILearning).filter(
            AILearning.languages.op('?&')(languages)  # JSON overlap operator
        ).order_by(desc(AILearning.confidence_score)).limit(10).all()
        
        return [{
            'pattern_name': learning.pattern_name,
            'pattern_type': learning.pattern_type,
            'description': learning.description,
            'confidence': learning.confidence_score,
            'applicable_languages': learning.languages
        } for learning in learnings]
    
    def _get_from_cache(self, repository_id: int, cache_key: str) -> Optional[AIContextCache]:
        """Get cached context if available and valid"""
        return self.db_session.query(AIContextCache).filter_by(
            repository_id=repository_id,
            context_key=cache_key
        ).first()
    
    def _is_cache_stale(self, cache_entry: AIContextCache, repository_id: int) -> bool:
        """Check if cache entry is stale and needs refresh"""
        if cache_entry.is_expired():
            return True
        
        # Check if repository has been updated since cache creation
        repo = self.db_session.query(Repository).filter_by(id=repository_id).first()
        if repo and repo.updated_at > cache_entry.updated_at:
            return True
        
        return False
    
    def _update_cache(
        self, 
        repository_id: int, 
        cache_key: str, 
        context_data: Dict[str, Any], 
        confidence_score: float,
        expires_at: Optional[datetime] = None
    ):
        """Update cache with new context data"""
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(hours=self.context_expiry_hours)
        
        update_ai_context_cache(
            self.db_session, 
            repository_id, 
            cache_key, 
            context_data, 
            confidence_score
        )
        
        # Update expiry
        cache_entry = self.db_session.query(AIContextCache).filter_by(
            repository_id=repository_id,
            context_key=cache_key
        ).first()
        
        if cache_entry:
            cache_entry.expires_at = expires_at
            self.db_session.commit()
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def invalidate_cache_for_commit(self, repository_id: int, commit_sha: str):
        """Invalidate relevant cache entries when new commit is analyzed"""
        invalidate_context_cache(self.db_session, repository_id, commit_sha)
        logger.info(f"Invalidated cache for repository {repository_id} after commit {commit_sha}")
    
    def get_context_summary_for_ai(self, repository_id: int, analysis_type: str = 'comprehensive') -> str:
        """Get a formatted context summary optimized for AI consumption"""
        context = self.build_comprehensive_context(repository_id)
        
        summary_parts = [
            "# Repository Context Summary",
            f"Repository: {context['repository_info']['name']}",
            f"Primary Language: {context['repository_info']['primary_language']}",
            f"Architecture: {context['architecture_context'].get('architecture_patterns', {})}",
        ]
        
        # Add relevant sections based on analysis type
        if analysis_type == 'security':
            security_ctx = context.get('security_context', {})
            summary_parts.extend([
                f"Security Risk Level: {security_ctx.get('risk_assessment', 'unknown')}",
                f"Recent Vulnerabilities: {len(security_ctx.get('recent_vulnerabilities', []))}"
            ])
        
        elif analysis_type == 'performance':
            perf_ctx = context.get('performance_context', {})
            summary_parts.extend([
                f"Complexity Hotspots: {len(perf_ctx.get('complexity_hotspots', []))}",
                f"Performance Issues: {len(perf_ctx.get('performance_bottlenecks', []))}"
            ])
        
        # Add historical insights
        insights = context.get('previous_insights', {})
        if insights.get('key_recommendations'):
            summary_parts.append(f"Key Recommendations: {insights['key_recommendations'][:3]}")
        
        return "\n".join(summary_parts) 