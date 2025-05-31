"""
Analysis Service

This module provides core analysis functionality for the CI Code Companion SDK,
including result aggregation, caching, and performance monitoring.
"""

import asyncio
import time
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import asdict

from ..models.analysis_model import AnalysisResult, CodeIssue, CodeSuggestion
from ..models.file_model import FileInfo
from ..core.exceptions import AnalysisError, ValidationError


class AnalysisService:
    """
    Service for managing analysis operations, caching, and result processing.
    Provides centralized analysis management and performance optimization.
    """
    
    def __init__(self, config, logger: Optional[logging.Logger] = None):
        """
        Initialize Analysis service.
        
        Args:
            config: SDK configuration object
            logger: Logger instance for service operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Analysis cache
        self.cache = {}
        self.cache_ttl = getattr(config, 'cache_ttl', 3600)  # 1 hour default
        self.enable_caching = getattr(config, 'enable_caching', True)
        
        # Performance tracking
        self.performance_metrics = {
            'total_analyses': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'average_execution_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        # Active operations tracking
        self.active_operations = {}
        
    async def analyze_file_with_caching(
        self,
        file_info: FileInfo,
        agent,
        context: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Perform file analysis with caching support.
        
        Args:
            file_info: File information object
            agent: Analysis agent to use
            context: Analysis context
            
        Returns:
            AnalysisResult with analysis findings
        """
        start_time = time.time()
        operation_id = context.get('operation_id', 'unknown')
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(file_info, agent.__class__.__name__, context)
            
            if self.enable_caching and cache_key in self.cache:
                cached_result = self.cache[cache_key]
                if self._is_cache_valid(cached_result['timestamp']):
                    self.performance_metrics['cache_hits'] += 1
                    self.logger.debug(f"Cache hit for file: {file_info.path}")
                    return cached_result['result']
                else:
                    # Remove expired cache entry
                    del self.cache[cache_key]
            
            self.performance_metrics['cache_misses'] += 1
            
            # Track active operation
            self.active_operations[operation_id] = {
                'file_path': file_info.path,
                'agent': agent.__class__.__name__,
                'started_at': datetime.now(),
                'status': 'analyzing'
            }
            
            # Perform analysis
            self.logger.info(f"Starting analysis of {file_info.path} with {agent.__class__.__name__}")
            
            raw_result = await agent.analyze_file(file_info.path, file_info.content, context)
            
            # Process and validate result
            analysis_result = self._process_analysis_result(
                raw_result, file_info, agent.__class__.__name__, start_time, operation_id
            )
            
            # Cache result if enabled
            if self.enable_caching:
                self.cache[cache_key] = {
                    'result': analysis_result,
                    'timestamp': datetime.now()
                }
            
            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(True, execution_time)
            
            # Remove from active operations
            self.active_operations.pop(operation_id, None)
            
            self.logger.info(f"Analysis completed for {file_info.path} in {execution_time:.2f}s")
            return analysis_result
            
        except Exception as e:
            # Update metrics
            execution_time = time.time() - start_time
            self._update_performance_metrics(False, execution_time)
            
            # Remove from active operations
            self.active_operations.pop(operation_id, None)
            
            self.logger.error(f"Analysis failed for {file_info.path}: {str(e)}")
            raise AnalysisError(f"Analysis failed for {file_info.path}: {str(e)}")
    
    def _process_analysis_result(
        self,
        raw_result: Dict[str, Any],
        file_info: FileInfo,
        agent_type: str,
        start_time: float,
        operation_id: str
    ) -> AnalysisResult:
        """
        Process raw analysis result into structured AnalysisResult.
        
        Args:
            raw_result: Raw result from agent
            file_info: File information
            agent_type: Name of the agent that performed analysis
            start_time: Analysis start time
            operation_id: Operation identifier
            
        Returns:
            Structured AnalysisResult
        """
        try:
            # Extract issues
            issues = []
            raw_issues = raw_result.get('issues', [])
            for i, issue_data in enumerate(raw_issues):
                if isinstance(issue_data, dict):
                    issue = CodeIssue(
                        id=issue_data.get('id', f"{operation_id}-issue-{i}"),
                        title=issue_data.get('title', 'Unknown Issue'),
                        description=issue_data.get('description', ''),
                        severity=issue_data.get('severity', 'medium'),
                        category=issue_data.get('category', 'general'),
                        line_number=issue_data.get('line_number'),
                        column_number=issue_data.get('column_number'),
                        suggestion=issue_data.get('suggestion'),
                        fix_code=issue_data.get('fix_code'),
                        confidence_score=issue_data.get('confidence_score', 0.8),
                        documentation_url=issue_data.get('documentation_url')
                    )
                    issues.append(issue)
            
            # Extract suggestions
            suggestions = []
            raw_suggestions = raw_result.get('suggestions', [])
            for i, suggestion_data in enumerate(raw_suggestions):
                if isinstance(suggestion_data, dict):
                    suggestion = CodeSuggestion(
                        id=suggestion_data.get('id', f"{operation_id}-suggestion-{i}"),
                        title=suggestion_data.get('title', 'Improvement Suggestion'),
                        description=suggestion_data.get('description', ''),
                        impact=suggestion_data.get('impact', 'medium'),
                        effort=suggestion_data.get('effort', 'medium'),
                        category=suggestion_data.get('category', 'improvement'),
                        confidence_score=suggestion_data.get('confidence_score', 0.7),
                        example_code=suggestion_data.get('example_code'),
                        documentation_url=suggestion_data.get('documentation_url')
                    )
                    suggestions.append(suggestion)
            
            # Create AnalysisResult
            result = AnalysisResult(
                operation_id=operation_id,
                file_path=file_info.path,
                agent_type=agent_type,
                issues=issues,
                suggestions=suggestions,
                confidence_score=raw_result.get('confidence_score', 0.8),
                execution_time=time.time() - start_time,
                metadata=raw_result.get('metadata', {})
            )
            
            return result
            
        except Exception as e:
            raise ValidationError(f"Failed to process analysis result: {str(e)}")
    
    async def analyze_multiple_files(
        self,
        files: List[FileInfo],
        agent_manager,
        context: Dict[str, Any],
        max_concurrent: int = None
    ) -> List[AnalysisResult]:
        """
        Analyze multiple files concurrently.
        
        Args:
            files: List of FileInfo objects to analyze
            agent_manager: Agent manager instance
            context: Analysis context
            max_concurrent: Maximum concurrent operations
            
        Returns:
            List of AnalysisResult objects
        """
        max_concurrent = max_concurrent or getattr(self.config, 'max_concurrent_operations', 5)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single_file(file_info: FileInfo) -> AnalysisResult:
            async with semaphore:
                agent = agent_manager.get_agent_for_file(file_info.path)
                return await self.analyze_file_with_caching(file_info, agent, context)
        
        # Execute analyses concurrently
        tasks = [analyze_single_file(file_info) for file_info in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to analyze {files[i].path}: {str(result)}")
                # Create error result
                error_result = AnalysisResult(
                    operation_id=f"error-{i}",
                    file_path=files[i].path,
                    agent_type="error",
                    issues=[CodeIssue(
                        id=f"error-{i}",
                        title="Analysis Failed",
                        description=str(result),
                        severity="high",
                        category="system"
                    )],
                    suggestions=[],
                    confidence_score=0.0,
                    execution_time=0.0,
                    metadata={'error': True}
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def aggregate_results(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """
        Aggregate multiple analysis results into a summary.
        
        Args:
            results: List of AnalysisResult objects
            
        Returns:
            Aggregated analysis summary
        """
        if not results:
            return {
                'total_files': 0,
                'total_issues': 0,
                'total_suggestions': 0,
                'average_quality_score': 0.0,
                'severity_breakdown': {},
                'category_breakdown': {},
                'agent_breakdown': {},
                'overall_confidence': 0.0
            }
        
        # Initialize counters
        total_files = len(results)
        total_issues = sum(len(r.issues) for r in results)
        total_suggestions = sum(len(r.suggestions) for r in results)
        
        # Severity breakdown
        severity_counts = {}
        for result in results:
            for issue in result.issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        # Category breakdown
        category_counts = {}
        for result in results:
            for issue in result.issues:
                category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        # Agent breakdown
        agent_counts = {}
        for result in results:
            agent_counts[result.agent_type] = agent_counts.get(result.agent_type, 0) + 1
        
        # Calculate averages
        quality_scores = [r.calculate_quality_score() for r in results]
        average_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        confidence_scores = [r.confidence_score for r in results]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_files': total_files,
            'total_issues': total_issues,
            'total_suggestions': total_suggestions,
            'average_quality_score': average_quality_score,
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'agent_breakdown': agent_counts,
            'overall_confidence': overall_confidence,
            'execution_time': sum(r.execution_time for r in results),
            'results': [asdict(r) for r in results]
        }
    
    def _generate_cache_key(self, file_info: FileInfo, agent_type: str, context: Dict[str, Any]) -> str:
        """
        Generate cache key for analysis result.
        
        Args:
            file_info: File information
            agent_type: Agent type name
            context: Analysis context
            
        Returns:
            Cache key string
        """
        # Create hash from file content, agent type, and relevant context
        content_hash = hashlib.md5(file_info.content.encode('utf-8')).hexdigest()
        context_str = str(sorted(context.items()))
        
        cache_input = f"{file_info.path}:{content_hash}:{agent_type}:{context_str}"
        return hashlib.sha256(cache_input.encode('utf-8')).hexdigest()
    
    def _is_cache_valid(self, cache_timestamp: datetime) -> bool:
        """
        Check if cached result is still valid.
        
        Args:
            cache_timestamp: When the result was cached
            
        Returns:
            True if cache is still valid
        """
        return (datetime.now() - cache_timestamp).total_seconds() < self.cache_ttl
    
    def _update_performance_metrics(self, success: bool, execution_time: float):
        """
        Update performance tracking metrics.
        
        Args:
            success: Whether the analysis was successful
            execution_time: Time taken for analysis
        """
        self.performance_metrics['total_analyses'] += 1
        
        if success:
            self.performance_metrics['successful_analyses'] += 1
        else:
            self.performance_metrics['failed_analyses'] += 1
        
        # Update average execution time
        total = self.performance_metrics['total_analyses']
        current_avg = self.performance_metrics['average_execution_time']
        new_avg = ((current_avg * (total - 1)) + execution_time) / total
        self.performance_metrics['average_execution_time'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.
        
        Returns:
            Dictionary containing performance statistics
        """
        metrics = self.performance_metrics.copy()
        
        # Calculate additional metrics
        total = metrics['total_analyses']
        if total > 0:
            metrics['success_rate'] = metrics['successful_analyses'] / total
            metrics['failure_rate'] = metrics['failed_analyses'] / total
            metrics['cache_hit_rate'] = metrics['cache_hits'] / (metrics['cache_hits'] + metrics['cache_misses'])
        else:
            metrics['success_rate'] = 0.0
            metrics['failure_rate'] = 0.0
            metrics['cache_hit_rate'] = 0.0
        
        metrics['active_operations'] = len(self.active_operations)
        metrics['cache_size'] = len(self.cache)
        
        return metrics
    
    def clear_cache(self, older_than: Optional[timedelta] = None):
        """
        Clear analysis cache.
        
        Args:
            older_than: Only clear entries older than this timedelta
        """
        if older_than is None:
            self.cache.clear()
            self.logger.info("Analysis cache cleared")
        else:
            cutoff_time = datetime.now() - older_than
            keys_to_remove = []
            
            for key, value in self.cache.items():
                if value['timestamp'] < cutoff_time:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            self.logger.info(f"Removed {len(keys_to_remove)} expired cache entries")
    
    def get_active_operations(self) -> Dict[str, Any]:
        """
        Get information about currently active analysis operations.
        
        Returns:
            Dictionary containing active operation details
        """
        return {
            'count': len(self.active_operations),
            'operations': [
                {
                    'operation_id': op_id,
                    'file_path': details['file_path'],
                    'agent': details['agent'],
                    'duration': (datetime.now() - details['started_at']).total_seconds(),
                    'status': details['status']
                }
                for op_id, details in self.active_operations.items()
            ]
        }
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel an active analysis operation.
        
        Args:
            operation_id: ID of the operation to cancel
            
        Returns:
            True if operation was found and marked for cancellation
        """
        if operation_id in self.active_operations:
            self.active_operations[operation_id]['status'] = 'cancelled'
            self.logger.info(f"Operation {operation_id} marked for cancellation")
            return True
        return False 