"""
CI Code Companion Engine

This is the main orchestration engine for the CI Code Companion SDK. It coordinates all operations
including multi-agent analysis, file operations, repository management, and parallel task execution.
The engine provides a unified interface for all SDK capabilities and manages the lifecycle of 
different components including AI agents, services, and integrations.

Architecture:
- Singleton pattern for engine instance management
- Async/await support for parallel operations
- Comprehensive error handling and retry mechanisms
- Plugin-based agent system for extensibility
- Event-driven architecture for real-time updates
- Resource pooling for optimal performance
"""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime
import uuid

from .config import SDKConfig
from .exceptions import (
    CICodeCompanionError, 
    AnalysisError, 
    FileOperationError,
    AgentError
)
from ..models.analysis_model import AnalysisResult, TestGenerationResult, OptimizationResult
from ..models.file_model import FileInfo, ProjectInfo
from ..services.file_service import FileService
from ..services.git_service import GitService
from ..services.analysis_service import AnalysisService
from ..agents.agent_manager import AgentManager
from ..integrations.gitlab_client import GitLabClient


class CICodeCompanionEngine:
    """
    Main SDK engine that orchestrates all operations and provides a unified interface
    for code analysis, repository management, and AI-powered development assistance.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config: Optional[Dict[str, Any]] = None):
        """
        Implement singleton pattern to ensure only one engine instance exists.
        This prevents resource conflicts and ensures consistent state management.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CI Code Companion Engine with configuration and all required services.
        Sets up logging, initializes services, and prepares the engine for operations.
        
        Args:
            config: Configuration dictionary containing SDK settings
        """
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self.config = SDKConfig(config or {})
        self.session_id = str(uuid.uuid4())
        
        # Initialize logging
        self._setup_logging()
        self.logger.info(f"Initializing CI Code Companion Engine (Session: {self.session_id})")
        
        # Initialize thread pool for parallel operations
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.max_workers,
            thread_name_prefix="CICodeCompanion"
        )
        
        # Initialize services
        self._initialize_services()
        
        # Initialize agent manager
        self.agent_manager = AgentManager(self.config, self.logger)
        
        # Track active operations
        self.active_operations = {}
        self.operation_lock = threading.Lock()
        
        # Event callbacks
        self.event_callbacks = {}
        
        self.logger.info("CI Code Companion Engine initialized successfully")
    
    def _setup_logging(self):
        """
        Configure comprehensive logging for the SDK with appropriate levels and formatting.
        Sets up both file and console logging with rotation and structured formatting.
        """
        self.logger = logging.getLogger('ci_code_companion_sdk')
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not self.logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # File handler with rotation
            if self.config.log_file:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.config.log_file,
                    maxBytes=10*1024*1024,  # 10MB
                    backupCount=5
                )
                file_handler.setLevel(logging.DEBUG)
                
                # Structured formatter
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - [%(session_id)s] - %(message)s'
                )
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            
            # Console formatter
            console_formatter = logging.Formatter(
                '%(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Add session ID to log records
        class SessionFilter(logging.Filter):
            def __init__(self, session_id):
                self.session_id = session_id
            
            def filter(self, record):
                record.session_id = self.session_id
                return True
        
        self.logger.addFilter(SessionFilter(self.session_id))
    
    def _initialize_services(self):
        """
        Initialize all required services including file operations, Git integration,
        and analysis services. Sets up proper error handling and service dependencies.
        """
        try:
            self.logger.info("Initializing SDK services...")
            
            # Initialize GitLab client
            self.gitlab_client = GitLabClient(
                url=self.config.gitlab_url,
                token=self.config.gitlab_token,
                logger=self.logger
            )
            
            # Initialize core services
            self.file_service = FileService(self.config, self.logger)
            self.git_service = GitService(self.gitlab_client, self.logger)
            self.analysis_service = AnalysisService(self.config, self.logger)
            
            self.logger.info("All services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize services: {str(e)}")
            raise CICodeCompanionError(f"Service initialization failed: {str(e)}")
    
    async def analyze_file(
        self,
        file_path: str,
        content: str,
        agent_type: Optional[str] = None,
        project_context: Optional[Dict[str, Any]] = None,
        parallel: bool = True
    ) -> AnalysisResult:
        """
        Perform comprehensive file analysis using appropriate AI agents.
        Supports parallel execution and intelligent agent selection based on file type.
        
        Args:
            file_path: Path to the file being analyzed
            content: File content to analyze
            agent_type: Specific agent to use (optional, auto-detected if not provided)
            project_context: Additional project context for better analysis
            parallel: Whether to run multiple agents in parallel
            
        Returns:
            AnalysisResult containing all analysis findings and suggestions
        """
        operation_id = str(uuid.uuid4())
        self.logger.info(f"Starting file analysis: {file_path} (Operation: {operation_id})")
        
        try:
            # Register operation
            with self.operation_lock:
                self.active_operations[operation_id] = {
                    'type': 'file_analysis',
                    'file_path': file_path,
                    'started_at': datetime.now(),
                    'status': 'running'
                }
            
            # Emit start event
            await self._emit_event('analysis_started', {
                'operation_id': operation_id,
                'file_path': file_path,
                'agent_type': agent_type
            })
            
            # Detect or validate agent type
            if not agent_type:
                agent_type = self.agent_manager.detect_agent_type(file_path, content)
                self.logger.info(f"Auto-detected agent type: {agent_type}")
            
            # Get file info
            file_info = FileInfo.from_path(file_path, content)
            
            # Prepare context
            analysis_context = {
                'file_info': file_info,
                'project_context': project_context or {},
                'operation_id': operation_id
            }
            
            # Perform analysis
            if parallel and agent_type == 'multi':
                # Run multiple agents in parallel
                results = await self._analyze_with_multiple_agents(
                    file_path, content, analysis_context
                )
            else:
                # Run single agent
                agent = self.agent_manager.get_agent(agent_type)
                results = await agent.analyze_file(file_path, content, analysis_context)
            
            # Create analysis result
            analysis_result = AnalysisResult(
                operation_id=operation_id,
                file_path=file_path,
                agent_type=agent_type,
                issues=results.get('issues', []),
                suggestions=results.get('suggestions', []),
                metrics=results.get('metrics', {}),
                confidence_score=results.get('confidence_score', 0.0),
                execution_time=results.get('execution_time', 0.0),
                metadata=results.get('metadata', {})
            )
            
            # Update operation status
            with self.operation_lock:
                self.active_operations[operation_id]['status'] = 'completed'
                self.active_operations[operation_id]['completed_at'] = datetime.now()
            
            # Emit completion event
            await self._emit_event('analysis_completed', {
                'operation_id': operation_id,
                'result': analysis_result
            })
            
            self.logger.info(f"File analysis completed: {file_path} (Operation: {operation_id})")
            return analysis_result
            
        except Exception as e:
            # Update operation status
            with self.operation_lock:
                self.active_operations[operation_id]['status'] = 'failed'
                self.active_operations[operation_id]['error'] = str(e)
            
            # Emit error event
            await self._emit_event('analysis_failed', {
                'operation_id': operation_id,
                'error': str(e)
            })
            
            self.logger.error(f"File analysis failed: {file_path} - {str(e)}")
            raise AnalysisError(f"Analysis failed for {file_path}: {str(e)}")
    
    async def _analyze_with_multiple_agents(
        self,
        file_path: str,
        content: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run multiple AI agents in parallel to provide comprehensive analysis.
        Aggregates results from different specialized agents for maximum coverage.
        
        Args:
            file_path: Path to the file being analyzed
            content: File content to analyze
            context: Analysis context and metadata
            
        Returns:
            Aggregated results from all agents
        """
        self.logger.info(f"Running parallel multi-agent analysis for: {file_path}")
        
        # Determine applicable agents
        applicable_agents = self.agent_manager.get_applicable_agents(file_path, content)
        
        if not applicable_agents:
            raise AnalysisError(f"No applicable agents found for file: {file_path}")
        
        # Create tasks for parallel execution
        tasks = []
        for agent_type in applicable_agents:
            agent = self.agent_manager.get_agent(agent_type)
            task = asyncio.create_task(
                self._run_agent_with_timeout(agent, file_path, content, context)
            )
            tasks.append((agent_type, task))
        
        # Wait for all tasks to complete
        results = {}
        errors = {}
        
        for agent_type, task in tasks:
            try:
                result = await task
                results[agent_type] = result
                self.logger.debug(f"Agent {agent_type} completed successfully")
            except Exception as e:
                errors[agent_type] = str(e)
                self.logger.warning(f"Agent {agent_type} failed: {str(e)}")
        
        # Aggregate results
        aggregated_result = self._aggregate_agent_results(results, errors)
        
        self.logger.info(f"Multi-agent analysis completed. Success: {len(results)}, Errors: {len(errors)}")
        return aggregated_result
    
    async def _run_agent_with_timeout(
        self,
        agent,
        file_path: str,
        content: str,
        context: Dict[str, Any],
        timeout: int = None
    ):
        """
        Run an individual agent with timeout protection to prevent hanging operations.
        Provides graceful handling of agent failures and timeout scenarios.
        
        Args:
            agent: The agent instance to run
            file_path: Path to the file being analyzed
            content: File content to analyze
            context: Analysis context
            timeout: Timeout in seconds (uses config default if not provided)
            
        Returns:
            Agent analysis results
        """
        timeout = timeout or self.config.agent_timeout
        
        try:
            return await asyncio.wait_for(
                agent.analyze_file(file_path, content, context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise AgentError(f"Agent {agent.__class__.__name__} timed out after {timeout}s")
        except Exception as e:
            raise AgentError(f"Agent {agent.__class__.__name__} failed: {str(e)}")
    
    def _aggregate_agent_results(
        self,
        results: Dict[str, Any],
        errors: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple agents into a comprehensive analysis result.
        Handles deduplication, scoring, and result prioritization.
        
        Args:
            results: Dictionary of successful agent results
            errors: Dictionary of agent errors
            
        Returns:
            Aggregated analysis results
        """
        aggregated = {
            'issues': [],
            'suggestions': [],
            'metrics': {},
            'confidence_score': 0.0,
            'execution_time': 0.0,
            'metadata': {
                'agents_used': list(results.keys()),
                'agent_errors': errors,
                'aggregation_method': 'parallel_weighted'
            }
        }
        
        # Aggregate issues and suggestions
        seen_issues = set()
        seen_suggestions = set()
        total_confidence = 0.0
        total_execution_time = 0.0
        
        for agent_type, result in results.items():
            # Process issues
            for issue in result.get('issues', []):
                issue_key = f"{issue.get('type', '')}:{issue.get('line_number', 0)}:{issue.get('description', '')}"
                if issue_key not in seen_issues:
                    issue['source_agent'] = agent_type
                    aggregated['issues'].append(issue)
                    seen_issues.add(issue_key)
            
            # Process suggestions
            for suggestion in result.get('suggestions', []):
                suggestion_key = f"{suggestion.get('type', '')}:{suggestion.get('description', '')}"
                if suggestion_key not in seen_suggestions:
                    suggestion['source_agent'] = agent_type
                    aggregated['suggestions'].append(suggestion)
                    seen_suggestions.add(suggestion_key)
            
            # Aggregate metrics
            for metric_name, metric_value in result.get('metrics', {}).items():
                if metric_name not in aggregated['metrics']:
                    aggregated['metrics'][metric_name] = []
                aggregated['metrics'][metric_name].append({
                    'agent': agent_type,
                    'value': metric_value
                })
            
            # Aggregate confidence and execution time
            total_confidence += result.get('confidence_score', 0.0)
            total_execution_time = max(total_execution_time, result.get('execution_time', 0.0))
        
        # Calculate final scores
        if results:
            aggregated['confidence_score'] = total_confidence / len(results)
        aggregated['execution_time'] = total_execution_time
        
        return aggregated
    
    async def generate_tests(
        self,
        file_path: str,
        content: str,
        test_type: str = 'unit',
        coverage_config: Optional[Dict[str, Any]] = None,
        agent_type: Optional[str] = None
    ) -> TestGenerationResult:
        """
        Generate comprehensive test cases for the specified file using AI agents.
        Supports different test types and provides intelligent test coverage analysis.
        
        Args:
            file_path: Path to the file for which tests will be generated
            content: File content to analyze for test generation
            test_type: Type of tests to generate (unit, integration, e2e)
            coverage_config: Configuration for test coverage requirements
            agent_type: Specific agent to use (auto-detected if not provided)
            
        Returns:
            TestGenerationResult containing generated test code and metadata
        """
        operation_id = str(uuid.uuid4())
        self.logger.info(f"Starting test generation: {file_path} (Operation: {operation_id})")
        
        try:
            # Detect agent type if not provided
            if not agent_type:
                agent_type = self.agent_manager.detect_agent_type(file_path, content)
            
            # Get appropriate agent
            agent = self.agent_manager.get_agent(agent_type)
            
            # Prepare test generation context
            test_context = {
                'file_path': file_path,
                'content': content,
                'test_type': test_type,
                'coverage_config': coverage_config or {},
                'operation_id': operation_id
            }
            
            # Generate tests
            test_result = await agent.generate_tests(test_context)
            
            # Create result object
            generation_result = TestGenerationResult(
                operation_id=operation_id,
                file_path=file_path,
                test_type=test_type,
                agent_type=agent_type,
                test_code=test_result.get('test_code', ''),
                test_file_path=test_result.get('test_file_path', ''),
                coverage_areas=test_result.get('coverage_areas', []),
                explanation=test_result.get('explanation', ''),
                confidence_score=test_result.get('confidence_score', 0.0),
                metadata=test_result.get('metadata', {})
            )
            
            self.logger.info(f"Test generation completed: {file_path} (Operation: {operation_id})")
            return generation_result
            
        except Exception as e:
            self.logger.error(f"Test generation failed: {file_path} - {str(e)}")
            raise AnalysisError(f"Test generation failed for {file_path}: {str(e)}")
    
    async def optimize_code(
        self,
        file_path: str,
        content: str,
        optimization_type: str = 'performance',
        apply_automatically: bool = False,
        agent_type: Optional[str] = None
    ) -> OptimizationResult:
        """
        Generate code optimization suggestions and optionally apply them automatically.
        Provides performance, readability, and maintainability improvements.
        
        Args:
            file_path: Path to the file to optimize
            content: Current file content
            optimization_type: Type of optimization (performance, readability, maintainability)
            apply_automatically: Whether to apply optimizations automatically
            agent_type: Specific agent to use (auto-detected if not provided)
            
        Returns:
            OptimizationResult containing optimization suggestions and applied changes
        """
        operation_id = str(uuid.uuid4())
        self.logger.info(f"Starting code optimization: {file_path} (Operation: {operation_id})")
        
        try:
            # Detect agent type if not provided
            if not agent_type:
                agent_type = self.agent_manager.detect_agent_type(file_path, content)
            
            # Get appropriate agent
            agent = self.agent_manager.get_agent(agent_type)
            
            # Prepare optimization context
            optimization_context = {
                'file_path': file_path,
                'content': content,
                'optimization_type': optimization_type,
                'apply_automatically': apply_automatically,
                'operation_id': operation_id
            }
            
            # Generate optimizations
            optimization_result = await agent.optimize_code(optimization_context)
            
            # Apply optimizations if requested
            optimized_content = content
            applied_optimizations = []
            
            if apply_automatically and optimization_result.get('optimizations'):
                for optimization in optimization_result['optimizations']:
                    if optimization.get('auto_applicable', False):
                        optimized_content = self._apply_optimization(
                            optimized_content, optimization
                        )
                        applied_optimizations.append(optimization)
            
            # Create result object
            result = OptimizationResult(
                operation_id=operation_id,
                file_path=file_path,
                optimization_type=optimization_type,
                agent_type=agent_type,
                original_content=content,
                optimized_content=optimized_content,
                optimizations=optimization_result.get('optimizations', []),
                applied_optimizations=applied_optimizations,
                metrics=optimization_result.get('metrics', {}),
                confidence_score=optimization_result.get('confidence_score', 0.0),
                metadata=optimization_result.get('metadata', {})
            )
            
            self.logger.info(f"Code optimization completed: {file_path} (Operation: {operation_id})")
            return result
            
        except Exception as e:
            self.logger.error(f"Code optimization failed: {file_path} - {str(e)}")
            raise AnalysisError(f"Code optimization failed for {file_path}: {str(e)}")
    
    def _apply_optimization(self, content: str, optimization: Dict[str, Any]) -> str:
        """
        Apply a single optimization to the content safely with validation.
        Provides rollback capability in case of application failures.
        
        Args:
            content: Current file content
            optimization: Optimization details including line numbers and changes
            
        Returns:
            Updated content with optimization applied
        """
        try:
            # Implementation depends on optimization type
            # This is a simplified version - production would have more sophisticated logic
            if 'line_number' in optimization and 'new_content' in optimization:
                lines = content.split('\n')
                line_num = optimization['line_number'] - 1  # Convert to 0-based index
                
                if 0 <= line_num < len(lines):
                    lines[line_num] = optimization['new_content']
                    return '\n'.join(lines)
            
            return content
            
        except Exception as e:
            self.logger.warning(f"Failed to apply optimization: {str(e)}")
            return content
    
    async def chat_with_agent(
        self,
        message: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        agent_type: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Interactive chat with AI agents for code-related questions and assistance.
        Maintains conversation context and provides intelligent responses.
        
        Args:
            message: User message or question
            file_path: Optional file path for context
            content: Optional file content for context
            agent_type: Specific agent to chat with (auto-detected if not provided)
            conversation_history: Previous conversation messages
            
        Returns:
            Agent response string
        """
        self.logger.info(f"Starting agent chat session")
        
        try:
            # Detect agent type if file context is provided
            if not agent_type and file_path and content:
                agent_type = self.agent_manager.detect_agent_type(file_path, content)
            elif not agent_type:
                agent_type = 'general'  # Default to general agent
            
            # Get appropriate agent
            agent = self.agent_manager.get_agent(agent_type)
            
            # Prepare chat context
            chat_context = {
                'message': message,
                'file_path': file_path,
                'content': content,
                'conversation_history': conversation_history or [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Get agent response
            response = await agent.chat(chat_context)
            
            self.logger.info(f"Agent chat completed with {agent_type} agent")
            return response
            
        except Exception as e:
            self.logger.error(f"Agent chat failed: {str(e)}")
            raise AgentError(f"Chat failed: {str(e)}")
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """
        Emit events to registered callbacks for real-time updates and monitoring.
        Supports asynchronous event handling and error isolation.
        
        Args:
            event_type: Type of event being emitted
            data: Event data payload
        """
        if event_type in self.event_callbacks:
            for callback in self.event_callbacks[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    self.logger.warning(f"Event callback failed for {event_type}: {str(e)}")
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """
        Register callback function for specific event types.
        Enables real-time monitoring and custom event handling.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a running or completed operation.
        Provides real-time operation monitoring and progress tracking.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Operation status dictionary or None if not found
        """
        with self.operation_lock:
            return self.active_operations.get(operation_id)
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel a running operation if possible.
        Provides graceful operation cancellation and cleanup.
        
        Args:
            operation_id: Unique identifier for the operation to cancel
            
        Returns:
            True if operation was cancelled, False otherwise
        """
        with self.operation_lock:
            if operation_id in self.active_operations:
                operation = self.active_operations[operation_id]
                if operation['status'] == 'running':
                    operation['status'] = 'cancelled'
                    operation['cancelled_at'] = datetime.now()
                    self.logger.info(f"Operation cancelled: {operation_id}")
                    return True
        return False
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        Get list of all currently active operations.
        Useful for monitoring and management of ongoing tasks.
        
        Returns:
            List of active operation dictionaries
        """
        with self.operation_lock:
            return [
                {**op, 'operation_id': op_id} 
                for op_id, op in self.active_operations.items()
                if op['status'] == 'running'
            ]
    
    def cleanup(self):
        """
        Cleanup resources and shutdown the engine gracefully.
        Ensures proper resource deallocation and operation cleanup.
        """
        self.logger.info("Shutting down CI Code Companion Engine")
        
        # Cancel all active operations
        with self.operation_lock:
            for operation_id in list(self.active_operations.keys()):
                self.cancel_operation(operation_id)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Cleanup services
        if hasattr(self, 'agent_manager'):
            self.agent_manager.cleanup()
        
        self.logger.info("CI Code Companion Engine shutdown complete")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup"""
        self.cleanup() 