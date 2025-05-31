"""
Agent Orchestrator for Specialized Agents

This module coordinates specialized agents (code, testing, security) to provide
comprehensive analysis and development assistance. It manages agent workflows,
combines results, and provides unified interfaces for different use cases.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Union
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

from ..core.config import SDKConfig
from ..core.exceptions import AgentError
from .base_agent import BaseAgent, AgentCapability
from .agent_manager import AgentManager


class WorkflowType(Enum):
    """Types of agent workflows"""
    CODE_DEVELOPMENT = "code_development"
    TESTING_ANALYSIS = "testing_analysis"
    SECURITY_AUDIT = "security_audit"
    FULL_ANALYSIS = "full_analysis"
    CHAT_ASSISTANCE = "chat_assistance"


class AgentCategory(Enum):
    """Categories of specialized agents"""
    CODE = "code"
    TESTING = "testing"
    SECURITY = "security"


@dataclass
class WorkflowResult:
    """Result from an agent workflow"""
    workflow_type: WorkflowType
    success: bool
    results: Dict[str, Any]
    agents_used: List[str]
    execution_time: float
    timestamp: datetime
    errors: List[str] = None


class AgentOrchestrator:
    """
    Orchestrates specialized agents for comprehensive code analysis and development.
    Manages workflows between code, testing, and security agents.
    """
    
    def __init__(self, config: SDKConfig, logger: logging.Logger):
        """
        Initialize the agent orchestrator.
        
        Args:
            config: SDK configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.agent_manager = AgentManager(config, logger)
        
        # Specialized agent registry
        self.specialized_agents: Dict[AgentCategory, Dict[str, BaseAgent]] = {
            AgentCategory.CODE: {},
            AgentCategory.TESTING: {},
            AgentCategory.SECURITY: {}
        }
        
        # Workflow templates
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Execution statistics
        self.workflow_stats: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("Agent Orchestrator initialized")
    
    def _initialize_workflow_templates(self) -> Dict[WorkflowType, Dict[str, Any]]:
        """Initialize workflow templates for different use cases."""
        return {
            WorkflowType.CODE_DEVELOPMENT: {
                'required_categories': [AgentCategory.CODE],
                'optional_categories': [AgentCategory.TESTING],
                'parallel_execution': False,
                'max_execution_time': 300,  # 5 minutes
                'quality_gates': ['code_quality', 'syntax_validation']
            },
            WorkflowType.TESTING_ANALYSIS: {
                'required_categories': [AgentCategory.TESTING],
                'optional_categories': [AgentCategory.CODE],
                'parallel_execution': True,
                'max_execution_time': 180,  # 3 minutes
                'quality_gates': ['test_coverage', 'test_quality']
            },
            WorkflowType.SECURITY_AUDIT: {
                'required_categories': [AgentCategory.SECURITY],
                'optional_categories': [AgentCategory.CODE],
                'parallel_execution': True,
                'max_execution_time': 600,  # 10 minutes
                'quality_gates': ['security_compliance', 'vulnerability_scan']
            },
            WorkflowType.FULL_ANALYSIS: {
                'required_categories': [AgentCategory.CODE, AgentCategory.TESTING, AgentCategory.SECURITY],
                'optional_categories': [],
                'parallel_execution': True,
                'max_execution_time': 900,  # 15 minutes
                'quality_gates': ['code_quality', 'test_coverage', 'security_compliance']
            },
            WorkflowType.CHAT_ASSISTANCE: {
                'required_categories': [],  # Determined by chat context
                'optional_categories': [AgentCategory.CODE, AgentCategory.TESTING, AgentCategory.SECURITY],
                'parallel_execution': False,
                'max_execution_time': 60,  # 1 minute
                'quality_gates': []
            }
        }
    
    def register_specialized_agent(
        self, 
        category: AgentCategory, 
        agent_name: str, 
        agent: BaseAgent
    ):
        """
        Register a specialized agent in a specific category.
        
        Args:
            category: Agent category (CODE, TESTING, SECURITY)
            agent_name: Unique name for the agent
            agent: Agent instance
        """
        if category not in self.specialized_agents:
            self.specialized_agents[category] = {}
        
        self.specialized_agents[category][agent_name] = agent
        self.logger.info(f"Registered {category.value} agent: {agent_name}")
    
    async def execute_workflow(
        self,
        workflow_type: WorkflowType,
        file_path: str,
        content: str,
        context: Dict[str, Any] = None
    ) -> WorkflowResult:
        """
        Execute a specialized workflow with appropriate agents.
        
        Args:
            workflow_type: Type of workflow to execute
            file_path: Path to file being analyzed
            content: File content
            context: Additional context for analysis
            
        Returns:
            WorkflowResult containing combined results from all agents
        """
        start_time = datetime.now()
        context = context or {}
        
        # Get workflow template
        template = self.workflow_templates.get(workflow_type)
        if not template:
            raise AgentError(f"Unknown workflow type: {workflow_type}")
        
        # Determine required agents
        agents_to_use = self._select_agents_for_workflow(
            workflow_type, file_path, content, template
        )
        
        if not agents_to_use:
            raise AgentError(f"No suitable agents found for workflow: {workflow_type}")
        
        try:
            # Execute workflow
            if template['parallel_execution']:
                results = await self._execute_parallel_workflow(
                    agents_to_use, file_path, content, context, template
                )
            else:
                results = await self._execute_sequential_workflow(
                    agents_to_use, file_path, content, context, template
                )
            
            # Combine and validate results
            combined_results = self._combine_workflow_results(results, workflow_type)
            
            # Apply quality gates
            quality_check = self._apply_quality_gates(
                combined_results, template['quality_gates']
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return WorkflowResult(
                workflow_type=workflow_type,
                success=quality_check['passed'],
                results=combined_results,
                agents_used=list(agents_to_use.keys()),
                execution_time=execution_time,
                timestamp=start_time,
                errors=quality_check.get('errors', [])
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Workflow execution failed: {str(e)}")
            
            return WorkflowResult(
                workflow_type=workflow_type,
                success=False,
                results={},
                agents_used=list(agents_to_use.keys()) if 'agents_to_use' in locals() else [],
                execution_time=execution_time,
                timestamp=start_time,
                errors=[str(e)]
            )
    
    def _select_agents_for_workflow(
        self,
        workflow_type: WorkflowType,
        file_path: str,
        content: str,
        template: Dict[str, Any]
    ) -> Dict[str, BaseAgent]:
        """Select appropriate agents for the workflow based on file content and type."""
        selected_agents = {}
        
        # Detect technology stack
        tech_stack = self._detect_technology_stack(file_path, content)
        
        # Select agents based on required categories
        for category in template['required_categories']:
            agent = self._select_best_agent_for_category(category, tech_stack, file_path, content)
            if agent:
                selected_agents[f"{category.value}_{agent[0]}"] = agent[1]
        
        # Select agents from optional categories if available
        for category in template['optional_categories']:
            agent = self._select_best_agent_for_category(category, tech_stack, file_path, content)
            if agent:
                selected_agents[f"{category.value}_{agent[0]}"] = agent[1]
        
        return selected_agents
    
    def _detect_technology_stack(self, file_path: str, content: str) -> Dict[str, Any]:
        """Detect technology stack from file path and content."""
        tech_stack = {
            'language': None,
            'framework': None,
            'file_type': None,
            'testing_framework': None
        }
        
        # Use existing agent manager detection
        agent_type = self.agent_manager.detect_agent_type(file_path, content)
        
        # Extract technology details
        if agent_type == 'react':
            tech_stack['language'] = 'javascript'
            tech_stack['framework'] = 'react'
            tech_stack['testing_framework'] = 'jest'
        elif agent_type == 'python':
            tech_stack['language'] = 'python'
            tech_stack['testing_framework'] = 'pytest'
        elif agent_type == 'node':
            tech_stack['language'] = 'javascript'
            tech_stack['framework'] = 'node'
            tech_stack['testing_framework'] = 'jest'
        
        # Detect file type
        if file_path.endswith(('.test.js', '.test.ts', '.spec.js', '.spec.ts')):
            tech_stack['file_type'] = 'test'
        elif file_path.endswith(('.py')):
            tech_stack['file_type'] = 'source'
        
        return tech_stack
    
    def _select_best_agent_for_category(
        self,
        category: AgentCategory,
        tech_stack: Dict[str, Any],
        file_path: str,
        content: str
    ) -> Optional[tuple]:
        """Select the best agent for a category based on technology stack."""
        available_agents = self.specialized_agents.get(category, {})
        
        if not available_agents:
            return None
        
        # Priority matching logic
        language = tech_stack.get('language')
        framework = tech_stack.get('framework')
        
        # Look for exact matches first
        for agent_name, agent in available_agents.items():
            if language and language in agent_name.lower():
                if framework and framework in agent_name.lower():
                    return (agent_name, agent)
        
        # Look for language matches
        for agent_name, agent in available_agents.items():
            if language and language in agent_name.lower():
                return (agent_name, agent)
        
        # Return first available agent as fallback
        if available_agents:
            return next(iter(available_agents.items()))
        
        return None
    
    async def _execute_parallel_workflow(
        self,
        agents: Dict[str, BaseAgent],
        file_path: str,
        content: str,
        context: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents in parallel for faster processing."""
        tasks = []
        
        for agent_name, agent in agents.items():
            task = asyncio.create_task(
                self._execute_agent_with_timeout(
                    agent, file_path, content, context, template['max_execution_time']
                )
            )
            tasks.append((agent_name, task))
        
        results = {}
        for agent_name, task in tasks:
            try:
                result = await task
                results[agent_name] = result
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {str(e)}")
                results[agent_name] = {'error': str(e)}
        
        return results
    
    async def _execute_sequential_workflow(
        self,
        agents: Dict[str, BaseAgent],
        file_path: str,
        content: str,
        context: Dict[str, Any],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agents sequentially, allowing each to use previous results."""
        results = {}
        
        for agent_name, agent in agents.items():
            try:
                # Add previous results to context
                agent_context = {**context, 'previous_results': results}
                
                result = await self._execute_agent_with_timeout(
                    agent, file_path, content, agent_context, template['max_execution_time']
                )
                results[agent_name] = result
                
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {str(e)}")
                results[agent_name] = {'error': str(e)}
        
        return results
    
    async def _execute_agent_with_timeout(
        self,
        agent: BaseAgent,
        file_path: str,
        content: str,
        context: Dict[str, Any],
        timeout: int
    ) -> Dict[str, Any]:
        """Execute an agent with timeout protection."""
        try:
            return await asyncio.wait_for(
                agent.analyze_file(file_path, content, context),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise AgentError(f"Agent {agent.name} timed out after {timeout}s")
    
    def _combine_workflow_results(
        self, 
        results: Dict[str, Any], 
        workflow_type: WorkflowType
    ) -> Dict[str, Any]:
        """Combine results from multiple agents into a unified format."""
        combined = {
            'issues': [],
            'suggestions': [],
            'test_results': {},
            'security_findings': {},
            'code_analysis': {},
            'metadata': {
                'workflow_type': workflow_type.value,
                'agents_used': list(results.keys()),
                'timestamp': datetime.now().isoformat()
            }
        }
        
        for agent_name, result in results.items():
            if 'error' in result:
                combined['metadata'][f'{agent_name}_error'] = result['error']
                continue
            
            # Merge issues and suggestions
            combined['issues'].extend(result.get('issues', []))
            combined['suggestions'].extend(result.get('suggestions', []))
            
            # Categorize results by agent type
            if 'code' in agent_name.lower():
                combined['code_analysis'][agent_name] = result
            elif 'test' in agent_name.lower():
                combined['test_results'][agent_name] = result
            elif 'security' in agent_name.lower():
                combined['security_findings'][agent_name] = result
        
        return combined
    
    def _apply_quality_gates(
        self, 
        results: Dict[str, Any], 
        quality_gates: List[str]
    ) -> Dict[str, Any]:
        """Apply quality gates to validate results."""
        gate_results = {'passed': True, 'errors': []}
        
        for gate in quality_gates:
            if gate == 'code_quality':
                high_severity_issues = [
                    issue for issue in results['issues'] 
                    if issue.get('severity') == 'high'
                ]
                if len(high_severity_issues) > 5:
                    gate_results['passed'] = False
                    gate_results['errors'].append(
                        f"Code quality gate failed: {len(high_severity_issues)} high-severity issues"
                    )
            
            elif gate == 'security_compliance':
                security_issues = [
                    issue for issue in results['issues']
                    if issue.get('issue_type') in ['security', 'vulnerability']
                ]
                if security_issues:
                    gate_results['passed'] = False
                    gate_results['errors'].append(
                        f"Security gate failed: {len(security_issues)} security issues found"
                    )
            
            elif gate == 'test_coverage':
                # This would be implemented based on actual test coverage data
                pass
        
        return gate_results
    
    async def chat_with_agents(
        self,
        message: str,
        chat_type: str = "code",  # "code" or "analysis"
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Handle chat interactions with appropriate specialized agents.
        
        Args:
            message: User message
            chat_type: Type of chat ("code" or "analysis")
            context: Chat context including history
            
        Returns:
            Response from appropriate agents
        """
        context = context or {}
        
        # Determine which agents to use based on chat type
        if chat_type == "code":
            target_categories = [AgentCategory.CODE]
        elif chat_type == "analysis":
            target_categories = [AgentCategory.TESTING, AgentCategory.SECURITY]
        else:
            target_categories = [AgentCategory.CODE, AgentCategory.TESTING, AgentCategory.SECURITY]
        
        # Find relevant agents based on message content
        relevant_agents = self._find_relevant_agents_for_chat(message, target_categories)
        
        if not relevant_agents:
            return {
                'response': "I couldn't find a suitable agent to help with your request.",
                'agents_used': [],
                'success': False
            }
        
        # Execute chat with relevant agents
        chat_context = {
            **context,
            'message': message,
            'chat_type': chat_type
        }
        
        responses = []
        agents_used = []
        
        for agent_name, agent in relevant_agents.items():
            try:
                if hasattr(agent, 'chat'):
                    response = await agent.chat(chat_context)
                    responses.append(f"**{agent_name}**: {response}")
                    agents_used.append(agent_name)
            except Exception as e:
                self.logger.error(f"Chat failed with agent {agent_name}: {str(e)}")
        
        combined_response = "\n\n".join(responses) if responses else "No agents could respond to your message."
        
        return {
            'response': combined_response,
            'agents_used': agents_used,
            'success': len(responses) > 0,
            'chat_type': chat_type
        }
    
    def _find_relevant_agents_for_chat(
        self, 
        message: str, 
        target_categories: List[AgentCategory]
    ) -> Dict[str, BaseAgent]:
        """Find agents relevant to the chat message."""
        relevant_agents = {}
        message_lower = message.lower()
        
        # Keywords that help identify relevant agents
        keywords = {
            'react': ['react', 'jsx', 'tsx', 'component', 'hook', 'state'],
            'python': ['python', 'django', 'flask', 'fastapi', 'pytest'],
            'node': ['node', 'express', 'api', 'server', 'backend'],
            'testing': ['test', 'testing', 'unit test', 'integration', 'coverage'],
            'security': ['security', 'vulnerability', 'auth', 'permission', 'encrypt']
        }
        
        for category in target_categories:
            available_agents = self.specialized_agents.get(category, {})
            
            for agent_name, agent in available_agents.items():
                # Check if message mentions agent-specific keywords
                for tech, tech_keywords in keywords.items():
                    if tech in agent_name.lower():
                        if any(keyword in message_lower for keyword in tech_keywords):
                            relevant_agents[agent_name] = agent
                            break
        
        # If no specific agents found, return the first available agent from each category
        if not relevant_agents:
            for category in target_categories:
                available_agents = self.specialized_agents.get(category, {})
                if available_agents:
                    first_agent = next(iter(available_agents.items()))
                    relevant_agents[first_agent[0]] = first_agent[1]
        
        return relevant_agents
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get orchestrator performance statistics."""
        return {
            'registered_agents': {
                category.value: len(agents) 
                for category, agents in self.specialized_agents.items()
            },
            'workflow_stats': self.workflow_stats,
            'supported_workflows': list(self.workflow_templates.keys())
        } 