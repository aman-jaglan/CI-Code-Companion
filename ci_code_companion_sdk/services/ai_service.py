"""
Streamlined AI Service

This module provides a direct interface to AI models and agents for code analysis, chat, and generation tasks.
Integrates with the specialized agent system while eliminating unnecessary abstraction layers.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..integrations.vertex_ai_client import VertexAIClient
from ..agents.agent_manager import AgentManager
from ..agents.specialized.code.react_code_agent import ReactCodeAgent
from ..agents.specialized.code.python_code_agent import PythonCodeAgent
from ..agents.specialized.code.node_code_agent import NodeCodeAgent
from ..core.config import SDKConfig
from ..core.prompt_loader import PromptLoader
from ..core.exceptions import AnalysisError, ConfigurationError
from ..models.analysis_model import AnalysisResult, TestGenerationResult, OptimizationResult


class StreamlinedAIService:
    """
    Streamlined AI service that integrates agents with direct Vertex AI access.
    Provides efficient operations while maintaining agent expertise.
    """
    
    def __init__(self, config: SDKConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the streamlined AI service with agent integration.
        
        Args:
            config: SDK configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize Vertex AI client directly
        try:
            self.vertex_client = VertexAIClient(
                project_id=config.get('project_id'),
                location=config.get('region', 'us-central1'),
                model_name=None,  # Will read from GEMINI_MODEL env var
            )
            self.logger.info(f"AI service initialized with model: {self.vertex_client.model_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize AI service: {e}")
            raise ConfigurationError(
                "Failed to initialize AI service",
                suggestions=[
                    "Verify GEMINI_MODEL environment variable is set",
                    "Check Google Cloud credentials and permissions",
                    "Ensure Vertex AI is enabled in your project"
                ],
                inner_exception=e
            )
        
        # Initialize specialized agents for chat and analysis
        self.agents = {}
        try:
            # Initialize PromptLoader for enhanced agent capabilities
            self.prompt_loader = PromptLoader(config, self.logger.getChild('prompt_loader'))
            self.logger.info(f"📚 PROMPT LOADER: Successfully initialized PromptLoader")
            
            # Initialize agents with proper parameters including PromptLoader
            agent_config = config.to_dict() if hasattr(config, 'to_dict') else {}
            
            self.agents['react'] = ReactCodeAgent(
                config=agent_config,
                logger=self.logger.getChild('react_agent'),
                prompt_loader=self.prompt_loader
            )
            self.agents['python'] = PythonCodeAgent(
                config=agent_config,
                logger=self.logger.getChild('python_agent'),
                prompt_loader=self.prompt_loader
            )
            self.agents['node'] = NodeCodeAgent(
                config=agent_config,
                logger=self.logger.getChild('node_agent'),
                prompt_loader=self.prompt_loader
            )
            self.logger.info(f"✅ AGENTS INITIALIZED: Successfully initialized {len(self.agents)} specialized agents with PromptLoader")
        except Exception as e:
            self.logger.error(f"❌ AGENT INITIALIZATION FAILED: {e}")
            self.agents = {}
            self.prompt_loader = None
    
    def _detect_agent_type(self, file_path: str, content: str) -> str:
        """Detect the appropriate agent based on file and content."""
        self.logger.info(f"🔍 AGENT DETECTION: Starting detection for file: {file_path}")
        
        if not file_path:
            self.logger.info("📄 AGENT DETECTION: No file path provided, using 'general'")
            return 'general'
        
        file_ext = file_path.split('.')[-1].lower()
        self.logger.info(f"📄 AGENT DETECTION: File extension detected: .{file_ext}")
        
        # React/TypeScript files
        if file_ext in ['jsx', 'tsx'] or 'react' in content.lower():
            self.logger.info("⚛️ AGENT DETECTION: React/JSX content detected → Selecting REACT AGENT")
            return 'react'
        
        # Python files
        elif file_ext in ['py'] or 'python' in content.lower():
            self.logger.info("🐍 AGENT DETECTION: Python content detected → Selecting PYTHON AGENT")
            return 'python'
        
        # Node.js files
        elif file_ext in ['js', 'ts'] and ('require(' in content or 'import' in content):
            self.logger.info("🟢 AGENT DETECTION: Node.js content detected → Selecting NODE AGENT")
            return 'node'
        
        # Default to general AI processing
        self.logger.info("🤖 AGENT DETECTION: No specific agent match → Using DIRECT AI")
        return 'general'
    
    async def analyze_code(
        self, 
        file_path: str, 
        content: str, 
        analysis_type: str = "comprehensive"
    ) -> AnalysisResult:
        """
        Analyze code using appropriate agents or direct AI.
        
        Args:
            file_path: Path to the file
            content: File content
            analysis_type: Type of analysis
            
        Returns:
            AnalysisResult with findings
        """
        try:
            self.logger.info(f"🚀 ANALYSIS REQUEST: Starting analysis for {file_path} (type: {analysis_type})")
            self.logger.info(f"📏 ANALYSIS REQUEST: Content length: {len(content)} characters")
            
            # Detect appropriate agent
            agent_type = self._detect_agent_type(file_path, content)
            
            if agent_type in self.agents:
                self.logger.info(f"✅ AGENT ROUTING: Found specialized agent '{agent_type}' → Using AGENT-BASED ANALYSIS")
                
                # Use specialized agent
                agent = self.agents[agent_type]
                self.logger.info(f"🎯 AGENT INVOCATION: Invoking {agent.__class__.__name__} for analysis")
                
                context = {
                    'analysis_type': analysis_type,
                    'file_path': file_path,
                    'user_intent': 'analysis'
                }
                
                # Use agent's analysis method
                self.logger.info(f"⚙️ AGENT PROCESSING: {agent_type} agent processing file...")
                agent_result = await agent.analyze_file(file_path, content, context)
                
                self.logger.info(f"✨ AGENT COMPLETED: {agent_type} agent analysis completed successfully")
                self.logger.info(f"📊 AGENT RESULTS: Found {len(agent_result.get('issues', []))} issues, {len(agent_result.get('suggestions', []))} suggestions")
                
                # Convert to AnalysisResult format
                result = self._convert_agent_result_to_analysis_result(agent_result, file_path, agent_type)
                self.logger.info(f"🎉 ANALYSIS COMPLETE: Returning agent-based analysis result")
                return result
            else:
                self.logger.info(f"🤖 DIRECT AI ROUTING: No specialized agent for '{agent_type}' → Using DIRECT AI ANALYSIS")
                
                # Use direct AI analysis for unsupported file types
                result = await self._direct_ai_analysis(file_path, content, analysis_type)
                self.logger.info(f"🎉 ANALYSIS COMPLETE: Returning direct AI analysis result")
                return result
            
        except Exception as e:
            self.logger.error(f"❌ ANALYSIS ERROR: Analysis failed for {file_path}: {e}")
            raise AnalysisError(f"Failed to analyze {file_path}: {str(e)}")
    
    async def chat(
        self, 
        message: str, 
        file_path: Optional[str] = None, 
        content: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Chat using appropriate agents or direct AI.
        
        Args:
            message: User message
            file_path: Optional file context
            content: Optional file content
            conversation_history: Previous conversation
            
        Returns:
            AI response
        """
        try:
            self.logger.info(f"💬 CHAT REQUEST: User message: '{message[:100]}{'...' if len(message) > 100 else ''}'")
            self.logger.info(f"📁 CHAT CONTEXT: File context: {file_path if file_path else 'None'}")
            
            # Detect appropriate agent if file context is provided
            if file_path and content:
                self.logger.info(f"🔍 CHAT ROUTING: File context provided, detecting appropriate agent...")
                agent_type = self._detect_agent_type(file_path, content)
                
                if agent_type in self.agents:
                    self.logger.info(f"✅ AGENT CHAT: Found specialized agent '{agent_type}' → Using AGENT-BASED CHAT")
                    
                    # Use specialized agent chat
                    agent = self.agents[agent_type]
                    self.logger.info(f"🎯 CHAT INVOCATION: Invoking {agent.__class__.__name__} chat method")
                    
                    context = {
                        'message': message,
                        'file_path': file_path,
                        'content': content,
                        'conversation_history': conversation_history or [],
                        'user_intent': 'chat'
                    }
                    
                    # Use agent's chat method
                    self.logger.info(f"⚙️ AGENT CHAT PROCESSING: {agent_type} agent processing chat request...")
                    response = await agent.chat(context)
                    
                    self.logger.info(f"✨ AGENT CHAT COMPLETED: {agent_type} agent chat completed successfully")
                    self.logger.info(f"📝 CHAT RESPONSE: Response length: {len(response)} characters")
                    return response
                else:
                    self.logger.info(f"🤖 DIRECT AI CHAT: No specialized agent for '{agent_type}' → Using DIRECT AI CHAT")
            else:
                self.logger.info(f"🤖 GENERAL CHAT: No file context provided → Using DIRECT AI CHAT")
            
            # Use direct AI chat for general queries or unsupported file types
            response = await self._direct_ai_chat(message, file_path, content, conversation_history)
            self.logger.info(f"🎉 CHAT COMPLETE: Returning direct AI chat response")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ CHAT ERROR: Chat failed: {e}")
            raise AnalysisError(f"Chat failed: {str(e)}")
    
    async def generate_tests(
        self, 
        file_path: str, 
        content: str, 
        test_type: str = "unit"
    ) -> TestGenerationResult:
        """
        Generate tests using agents or direct AI.
        """
        try:
            # Detect appropriate agent
            agent_type = self._detect_agent_type(file_path, content)
            
            if agent_type in self.agents:
                agent = self.agents[agent_type]
                context = {
                    'file_path': file_path,
                    'content': content,
                    'test_type': test_type,
                    'user_intent': 'test_generation'
                }
                
                # Try agent test generation
                try:
                    agent_result = await agent.generate_tests(context)
                    return self._convert_agent_result_to_test_result(agent_result, file_path, test_type)
                except NotImplementedError:
                    # Agent doesn't support test generation, fall back to direct AI
                    pass
            
            # Use direct AI for test generation
            return await self._direct_ai_test_generation(file_path, content, test_type)
            
        except Exception as e:
            self.logger.error(f"Test generation failed for {file_path}: {e}")
            raise AnalysisError(f"Failed to generate tests for {file_path}: {str(e)}")
    
    async def optimize_code(
        self, 
        file_path: str, 
        content: str, 
        optimization_type: str = "performance"
    ) -> OptimizationResult:
        """
        Optimize code using agents or direct AI.
        """
        try:
            # Detect appropriate agent
            agent_type = self._detect_agent_type(file_path, content)
            
            if agent_type in self.agents:
                agent = self.agents[agent_type]
                context = {
                    'file_path': file_path,
                    'content': content,
                    'optimization_type': optimization_type,
                    'user_intent': 'optimization'
                }
                
                # Try agent optimization
                try:
                    agent_result = await agent.optimize_code(context)
                    return self._convert_agent_result_to_optimization_result(agent_result, file_path, optimization_type)
                except NotImplementedError:
                    # Agent doesn't support optimization, fall back to direct AI
                    pass
            
            # Use direct AI for optimization
            return await self._direct_ai_optimization(file_path, content, optimization_type)
            
        except Exception as e:
            self.logger.error(f"Code optimization failed for {file_path}: {e}")
            raise AnalysisError(f"Failed to optimize {file_path}: {str(e)}")
    
    async def _direct_ai_analysis(self, file_path: str, content: str, analysis_type: str) -> AnalysisResult:
        """Direct AI analysis for unsupported file types."""
        self.logger.info(f"🤖 DIRECT AI: Starting direct AI analysis (no specialized agent available)")
        self.logger.info(f"🔧 DIRECT AI: Using Vertex AI model: {self.vertex_client.model_name}")
        
        prompt = self._create_analysis_prompt(file_path, content, analysis_type)
        
        response = await self.vertex_client.analyze_with_enhanced_prompt(
            enhanced_prompt=prompt,
            context={"file_path": file_path, "analysis_type": analysis_type}
        )
        
        self.logger.info(f"✅ DIRECT AI: Direct AI analysis completed")
        return self._parse_analysis_response(response, file_path)
    
    async def _direct_ai_chat(self, message: str, file_path: Optional[str], content: Optional[str], conversation_history: Optional[List[Dict[str, str]]]) -> str:
        """Direct AI chat for general queries."""
        self.logger.info(f"🤖 DIRECT AI CHAT: Starting direct AI chat (no specialized agent available)")
        self.logger.info(f"🔧 DIRECT AI CHAT: Using Vertex AI model: {self.vertex_client.model_name}")
        
        prompt = self._create_chat_prompt(message, file_path, content)
        self.logger.info(f"📝 DIRECT AI CHAT: Generated prompt length: {len(prompt)} characters")
        
        try:
            response = await self.vertex_client.chat_with_context(
                message=message,
                enhanced_prompt=prompt,
                conversation_history=conversation_history or []
            )
            
            self.logger.info(f"🔍 VERTEX AI RESPONSE DEBUG: Full response: {response}")
            self.logger.info(f"🔍 VERTEX AI RESPONSE KEYS: Available keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
            
            # Check different possible response formats
            if isinstance(response, dict):
                # Try different field names
                text_response = None
                if 'text' in response:
                    text_response = response['text']
                    self.logger.info(f"✅ FOUND 'text' field: '{text_response[:100]}{'...' if len(text_response) > 100 else ''}'" if text_response else "❌ 'text' field is empty")
                elif 'response' in response:
                    text_response = response['response']
                    self.logger.info(f"✅ FOUND 'response' field: '{text_response[:100]}{'...' if len(text_response) > 100 else ''}'" if text_response else "❌ 'response' field is empty")
                elif 'content' in response:
                    text_response = response['content']
                    self.logger.info(f"✅ FOUND 'content' field: '{text_response[:100]}{'...' if len(text_response) > 100 else ''}'" if text_response else "❌ 'content' field is empty")
                else:
                    self.logger.warning(f"⚠️ NO TEXT FIELD FOUND: Available fields: {list(response.keys())}")
                
                # Check success status
                success_status = response.get('success', True)  # Default to True if not specified
                self.logger.info(f"📊 RESPONSE STATUS: Success = {success_status}")
                
                if text_response:
                    self.logger.info(f"✅ DIRECT AI CHAT: Direct AI chat completed successfully")
                    return text_response
                else:
                    error_msg = response.get('error', 'Unknown error')
                    self.logger.error(f"❌ DIRECT AI CHAT: No text response - Error: {error_msg}")
                    return f"I apologize, but I couldn't generate a proper response. Error: {error_msg}"
            else:
                self.logger.error(f"❌ DIRECT AI CHAT: Response is not a dictionary: {type(response)}")
                return f"Unexpected response format: {type(response)}"
            
        except Exception as e:
            self.logger.error(f"❌ DIRECT AI CHAT ERROR: Exception during chat: {e}")
            raise
    
    async def _direct_ai_test_generation(self, file_path: str, content: str, test_type: str) -> TestGenerationResult:
        """Direct AI test generation."""
        prompt = self._create_test_prompt(file_path, content, test_type)
        
        response = await self.vertex_client.analyze_with_enhanced_prompt(
            enhanced_prompt=prompt,
            context={"file_path": file_path, "test_type": test_type}
        )
        
        return self._parse_test_response(response, file_path, test_type)
    
    async def _direct_ai_optimization(self, file_path: str, content: str, optimization_type: str) -> OptimizationResult:
        """Direct AI optimization."""
        prompt = self._create_optimization_prompt(file_path, content, optimization_type)
        
        response = await self.vertex_client.analyze_with_enhanced_prompt(
            enhanced_prompt=prompt,
            context={"file_path": file_path, "optimization_type": optimization_type}
        )
        
        return self._parse_optimization_response(response, file_path, optimization_type)
    
    def _convert_agent_result_to_analysis_result(self, agent_result: Dict[str, Any], file_path: str, agent_type: str) -> AnalysisResult:
        """Convert agent result to AnalysisResult format."""
        from ..models.analysis_model import CodeIssue, CodeSuggestion, AnalysisMetrics
        import uuid
        
        # Convert agent issues to CodeIssue objects
        issues = []
        for issue_data in agent_result.get('issues', []):
            if isinstance(issue_data, dict):
                issues.append(CodeIssue(
                    id=issue_data.get('id', str(uuid.uuid4())),
                    title=issue_data.get('title', 'Unknown Issue'),
                    description=issue_data.get('description', ''),
                    severity=issue_data.get('severity', 'medium'),
                    category=issue_data.get('category', 'general'),
                    line_number=issue_data.get('line_number'),
                    column_number=issue_data.get('column_number'),
                    suggestion=issue_data.get('suggestion'),
                    fix_code=issue_data.get('fix_code'),
                    confidence_score=issue_data.get('confidence_score', 0.8)
                ))
        
        # Convert agent suggestions to CodeSuggestion objects
        suggestions = []
        for suggestion_data in agent_result.get('suggestions', []):
            if isinstance(suggestion_data, dict):
                suggestions.append(CodeSuggestion(
                    id=suggestion_data.get('id', str(uuid.uuid4())),
                    title=suggestion_data.get('title', 'Improvement Suggestion'),
                    description=suggestion_data.get('description', ''),
                    impact=suggestion_data.get('impact', 'medium'),
                    effort=suggestion_data.get('effort', 'medium'),
                    category=suggestion_data.get('category', 'improvement'),
                    confidence_score=suggestion_data.get('confidence_score', 0.7)
                ))
        
        return AnalysisResult(
            operation_id=str(uuid.uuid4()),
            file_path=file_path,
            agent_type=f"{agent_type}_agent",
            issues=issues,
            suggestions=suggestions,
            metrics=AnalysisMetrics(),
            confidence_score=agent_result.get('confidence_score', 0.8),
            execution_time=agent_result.get('execution_time', 0.0),
            metadata={
                'agent_used': agent_type,
                'model_used': self.vertex_client.model_name,
                'agent_integrated': True
            }
        )
    
    def _convert_agent_result_to_test_result(self, agent_result: Dict[str, Any], file_path: str, test_type: str) -> TestGenerationResult:
        """Convert agent result to TestGenerationResult format."""
        import uuid
        
        return TestGenerationResult(
            operation_id=str(uuid.uuid4()),
            file_path=file_path,
            test_type=test_type,
            test_code=agent_result.get('test_code', ''),
            test_cases=[],
            coverage_estimate=agent_result.get('coverage_estimate', 0.8),
            execution_time=agent_result.get('execution_time', 0.0),
            metadata={
                'agent_used': 'specialized',
                'model_used': self.vertex_client.model_name
            }
        )
    
    def _convert_agent_result_to_optimization_result(self, agent_result: Dict[str, Any], file_path: str, optimization_type: str) -> OptimizationResult:
        """Convert agent result to OptimizationResult format."""
        import uuid
        
        return OptimizationResult(
            operation_id=str(uuid.uuid4()),
            file_path=file_path,
            optimization_type=optimization_type,
            original_code="",
            optimized_code=agent_result.get('optimized_code', ''),
            optimizations=[],
            performance_impact="medium",
            execution_time=agent_result.get('execution_time', 0.0),
            metadata={
                'agent_used': 'specialized',
                'model_used': self.vertex_client.model_name
            }
        )
    
    # Keep existing prompt methods for direct AI usage
    def _create_analysis_prompt(self, file_path: str, content: str, analysis_type: str) -> str:
        """Create prompt for code analysis."""
        file_ext = file_path.split('.')[-1] if '.' in file_path else 'unknown'
        
        prompt = f"""
Analyze the following {file_ext} code for {analysis_type} issues:

File: {file_path}
Code:
```{file_ext}
{content}
```

Please provide:
1. Code quality issues with severity levels
2. Security vulnerabilities if any
3. Performance optimization opportunities
4. Best practice recommendations
5. Specific line-by-line suggestions

Format the response as structured JSON with 'issues', 'suggestions', and 'metrics' sections.
"""
        return prompt
    
    def _create_test_prompt(self, file_path: str, content: str, test_type: str) -> str:
        """Create prompt for test generation."""
        file_ext = file_path.split('.')[-1] if '.' in file_path else 'unknown'
        
        prompt = f"""
Generate {test_type} tests for the following {file_ext} code:

File: {file_path}
Code:
```{file_ext}
{content}
```

Please generate:
1. Comprehensive test cases covering all functions/methods
2. Edge case tests
3. Error handling tests
4. Mock data and setup code if needed
5. Test assertions and expected outcomes

Provide the complete test code that can be run immediately.
"""
        return prompt
    
    def _create_optimization_prompt(self, file_path: str, content: str, optimization_type: str) -> str:
        """Create prompt for code optimization."""
        file_ext = file_path.split('.')[-1] if '.' in file_path else 'unknown'
        
        prompt = f"""
Optimize the following {file_ext} code for {optimization_type}:

File: {file_path}
Code:
```{file_ext}
{content}
```

Please provide:
1. Optimized version of the code
2. Explanation of changes made
3. Performance improvements expected
4. Any trade-offs or considerations
5. Best practices applied

Provide the complete optimized code that can be used as a direct replacement.
"""
        return prompt
    
    def _create_chat_prompt(self, message: str, file_path: Optional[str], content: Optional[str]) -> str:
        """Create prompt for chat interaction."""
        context_part = ""
        if file_path and content:
            file_ext = file_path.split('.')[-1] if '.' in file_path else 'unknown'
            context_part = f"""
Context - File: {file_path}
```{file_ext}
{content}
```
"""
        
        prompt = f"""
You are an expert code assistant. Help the user with their question.

{context_part}

User Question: {message}

Please provide a helpful, accurate response focused on code and development topics.
"""
        return prompt
    
    def _parse_analysis_response(self, response: Dict[str, Any], file_path: str) -> AnalysisResult:
        """Parse AI response into AnalysisResult."""
        response_text = response.get('text', '')
        
        from ..models.analysis_model import CodeIssue, CodeSuggestion, AnalysisMetrics
        import uuid
        
        return AnalysisResult(
            operation_id=str(uuid.uuid4()),
            file_path=file_path,
            agent_type="direct_ai",
            issues=[],
            suggestions=[],
            metrics=AnalysisMetrics(),
            confidence_score=0.8,
            execution_time=response.get('execution_time', 0.0),
            metadata={
                'model_used': self.vertex_client.model_name,
                'agent_integrated': False,
                'raw_response': response_text[:500]
            }
        )
    
    def _parse_test_response(self, response: Dict[str, Any], file_path: str, test_type: str) -> TestGenerationResult:
        """Parse AI response into TestGenerationResult."""
        response_text = response.get('text', '')
        
        import uuid
        
        return TestGenerationResult(
            operation_id=str(uuid.uuid4()),
            file_path=file_path,
            test_type=test_type,
            test_code=response_text,
            test_cases=[],
            coverage_estimate=0.8,
            execution_time=response.get('execution_time', 0.0),
            metadata={
                'model_used': self.vertex_client.model_name,
                'agent_integrated': False
            }
        )
    
    def _parse_optimization_response(self, response: Dict[str, Any], file_path: str, optimization_type: str) -> OptimizationResult:
        """Parse AI response into OptimizationResult."""
        response_text = response.get('text', '')
        
        import uuid
        
        return OptimizationResult(
            operation_id=str(uuid.uuid4()),
            file_path=file_path,
            optimization_type=optimization_type,
            original_code="",
            optimized_code=response_text,
            optimizations=[],
            performance_impact="medium",
            execution_time=response.get('execution_time', 0.0),
            metadata={
                'model_used': self.vertex_client.model_name,
                'agent_integrated': False
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the AI service and its components."""
        try:
            # Check Vertex AI client
            vertex_health = self.vertex_client.health_check()
            
            # Check agents
            agent_status = {}
            for agent_name, agent in self.agents.items():
                try:
                    agent_status[agent_name] = "healthy"
                except Exception as e:
                    agent_status[agent_name] = f"error: {str(e)}"
            
            return {
                'status': 'healthy',
                'vertex_ai': vertex_health,
                'agents': agent_status,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # API Handler Methods - Called by web_dashboard/routes/api.py
    
    async def handle_code_analysis(self, message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Handle code analysis requests from API layer.
        This method detects the appropriate agent and delegates processing.
        """
        self.logger.info(f"🎯 API HANDLER: Code analysis request received")
        self.logger.info(f"💬 USER MESSAGE: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        try:
            # Extract file information from context
            selected_file = context.get('selectedFile', {})
            file_path = selected_file.get('path', '')
            file_content = selected_file.get('content', '')
            
            if not file_path:
                self.logger.error("❌ NO FILE: No file selected for analysis")
                return {
                    'success': False,
                    'error': 'No file selected for analysis',
                    'message': 'Please select a file to analyze',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Detect appropriate agent
            agent_type = self._detect_agent_type(file_path, file_content)
            
            if agent_type in self.agents:
                self.logger.info(f"🤖 AGENT ROUTING: Using {agent_type} agent for code analysis")
                
                # Use agent for chat-based analysis
                agent = self.agents[agent_type]
                
                # Build context for agent
                agent_context = {
                    'user_message': message,
                    'file_path': file_path,
                    'file_content': file_content,
                    'project_info': context.get('project_info', {}),
                    'chat_mode': True
                }
                
                # Let agent handle the chat
                response_text = await agent.chat(agent_context)
                
                self.logger.info(f"✅ AGENT SUCCESS: {agent_type} agent completed analysis")
                
                return {
                    'success': True,
                    'response': response_text,
                    'metadata': {
                        'agent': agent_type,
                        'model': model,
                        'file_analyzed': file_path,
                        'agent_powered': True
                    },
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.info(f"🤖 DIRECT AI: No agent for {agent_type}, using direct AI")
                
                # Use direct AI for unsupported file types
                response_text = await self._direct_ai_chat(message, file_path, file_content, [])
                
                return {
                    'success': True,
                    'response': response_text,
                    'metadata': {
                        'agent': 'direct_ai',
                        'model': model,
                        'file_analyzed': file_path,
                        'direct_ai_powered': True
                    },
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ CODE ANALYSIS ERROR: {str(e)}")
            return {
                'success': False,
                'error': f'Code analysis failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def handle_test_generation(self, message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Handle test generation requests from API layer.
        Routes to appropriate agent based on file types.
        """
        self.logger.info(f"🧪 API HANDLER: Test generation request received")
        
        try:
            selected_files = context.get('selectedFiles', [])
            
            if not selected_files:
                self.logger.error("❌ NO FILES: No files selected for test generation")
                return {
                    'success': False,
                    'error': 'No files selected for test generation',
                    'message': 'Please select files to generate tests for',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Detect agent based on first file (can be enhanced later)
            first_file = selected_files[0]
            agent_type = self._detect_agent_type(first_file, '')
            
            if agent_type in self.agents:
                self.logger.info(f"🤖 AGENT ROUTING: Using {agent_type} agent for test generation")
                
                agent = self.agents[agent_type]
                
                # Build context for agent
                agent_context = {
                    'user_message': message,
                    'selected_files': selected_files,
                    'test_config': context.get('testConfig', {}),
                    'test_mode': True
                }
                
                # Let agent generate tests
                response_text = await agent.generate_tests_chat(agent_context)
                
                self.logger.info(f"✅ AGENT SUCCESS: {agent_type} agent completed test generation")
                
                return {
                    'success': True,
                    'response': response_text,
                    'metadata': {
                        'agent': agent_type,
                        'model': model,
                        'files_processed': len(selected_files),
                        'test_generation': True
                    },
                    'timestamp': datetime.now().isoformat()
                }
            else:
                self.logger.error(f"❌ NO AGENT: No agent available for file type")
                return {
                    'success': False,
                    'error': 'No agent available for test generation',
                    'message': 'Unsupported file types for test generation',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ TEST GENERATION ERROR: {str(e)}")
            return {
                'success': False,
                'error': f'Test generation failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def handle_security_analysis(self, message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Handle security analysis requests from API layer.
        Currently routes to general AI until security agent is implemented.
        """
        self.logger.info(f"🔒 API HANDLER: Security analysis request received")
        
        try:
            # For now, use direct AI for security analysis
            # TODO: Implement dedicated security agent
            
            selected_files = context.get('selectedFiles', [])
            
            security_prompt = f"""
            Security Analysis Request: {message}
            
            Files to analyze: {', '.join(selected_files) if selected_files else 'None specified'}
            
            Please perform a comprehensive security analysis focusing on:
            - Vulnerability detection
            - Input validation issues  
            - Authentication/authorization flaws
            - Data exposure risks
            - Dependency security
            
            Provide specific, actionable security recommendations.
            """
            
            response_text = await self._direct_ai_chat(security_prompt, None, None, [])
            
            self.logger.info(f"✅ SECURITY SUCCESS: Security analysis completed")
            
            return {
                'success': True,
                'response': response_text,
                'metadata': {
                    'agent': 'security_ai',
                    'model': model,
                    'files_scanned': len(selected_files),
                    'security_analysis': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ SECURITY ERROR: {str(e)}")
            return {
                'success': False,
                'error': f'Security analysis failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    async def handle_general_chat(self, message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
        """
        Handle general chat requests from API layer.
        Uses direct AI for general conversations.
        """
        self.logger.info(f"💬 API HANDLER: General chat request received")
        
        try:
            # Use direct AI for general chat
            response_text = await self._direct_ai_chat(message, None, None, [])
            
            self.logger.info(f"✅ CHAT SUCCESS: General chat completed")
            
            return {
                'success': True,
                'response': response_text,
                'metadata': {
                    'agent': 'general_ai',
                    'model': model,
                    'general_chat': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ CHAT ERROR: {str(e)}")
            return {
                'success': False,
                'error': f'General chat failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            } 