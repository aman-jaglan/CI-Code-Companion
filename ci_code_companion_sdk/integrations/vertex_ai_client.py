"""
Vertex AI Client for CI Code Companion SDK

This module provides the interface to Google Cloud Vertex AI services,
specifically optimized for Gemini 2.5 Pro and enhanced prompting.
"""

import os
import logging
from typing import Dict, List, Any, Optional
import json
from datetime import datetime

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logging.warning("Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform")

# Import configuration error for better error handling
from ..core.exceptions import ConfigurationError

class VertexAIClient:
    """
    Enhanced Vertex AI client optimized for Gemini 2.5 Pro and enhanced prompting.
    
    Features:
    - Support for Gemini 2.5 Pro with 1M token context window
    - Integration with PromptLoader for enhanced prompting
    - Optimized response generation
    - Performance monitoring
    """
    
    def __init__(
        self, 
        project_id: str, 
        location: str = "us-central1",
        model_name: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the Vertex AI client with model from environment configuration.
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_name: Model to use (reads from GEMINI_MODEL env var if None)
            credentials_path: Optional path to service account JSON (if not using env var)
        """
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform")
        
        self.project_id = project_id
        self.location = location
        self.logger = logging.getLogger(__name__)
        
        # Read model name from environment - no fallbacks
        if model_name is None:
            model_name = os.getenv('GEMINI_MODEL')
            if not model_name:
                raise ConfigurationError(
                    "No model specified. Set GEMINI_MODEL environment variable.",
                    suggestions=[
                        "Set GEMINI_MODEL environment variable (e.g., 'gemini-2.0-flash-exp')",
                        "Pass model_name parameter when initializing VertexAIClient"
                    ]
                )
            else:
                self.logger.info(f"Using GEMINI_MODEL from environment: {model_name}")
        
        self.model_name = model_name
        
        # Set credentials if provided
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            self.logger.info(f"Using provided credentials file: {credentials_path}")
        elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            self.logger.info(f"Using GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        else:
            self.logger.info("No explicit credentials path provided, relying on default authentication")
        
        try:
            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            self.logger.info(f"Vertex AI initialized with project: {project_id}, location: {location}")
            
            # Initialize the specified model directly
            self.model = GenerativeModel(model_name)
            self.logger.info(f"Successfully initialized model: {model_name}")
            
            # Set generation config optimized for code analysis
            self.generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.1,  # Lower temperature for code analysis
                "top_p": 0.8,
                "top_k": 40
            }
            
            self.logger.info(f"VertexAI client initialized successfully with {self.model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize VertexAI client with model {model_name}: {str(e)}")
            raise ConfigurationError(
                f"Failed to initialize Vertex AI model '{model_name}'",
                context={"model_name": model_name, "project_id": project_id, "location": location},
                suggestions=[
                    f"Verify that model '{model_name}' is available in your project",
                    "Check your Google Cloud credentials and permissions",
                    f"Ensure the model is available in region '{location}'",
                    "Verify GEMINI_MODEL environment variable is set correctly"
                ],
                inner_exception=e
            )
    
    def _initialize_model_with_fallbacks(self, requested_model: str) -> GenerativeModel:
        """
        DEPRECATED: This method is no longer used. Model is initialized directly.
        Kept for backward compatibility but will be removed.
        """
        raise DeprecationWarning("Fallback model initialization is deprecated. Use direct model initialization.")
    
    def _handle_response_safely(self, response, operation_name: str = "generation"):
        """
        Safely handle Vertex AI response with proper error handling for different finish reasons.
        
        Args:
            response: The Vertex AI response object
            operation_name: Name of the operation for logging
            
        Returns:
            Tuple of (success: bool, text: str, metadata: dict)
        """
        try:
            # Check if response has candidates
            if not hasattr(response, 'candidates') or not response.candidates:
                return False, f"No candidates in {operation_name} response", {"finish_reason": "NO_CANDIDATES"}
            
            candidate = response.candidates[0]
            finish_reason = getattr(candidate, 'finish_reason', None)
            
            # Handle different finish reasons
            if finish_reason == "MAX_TOKENS":
                # Model hit token limit but may have partial response
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    partial_text = candidate.content.parts[0].text if candidate.content.parts[0].text else ""
                    if partial_text.strip():
                        self.logger.warning(f"{operation_name} hit MAX_TOKENS but got partial response")
                        return True, partial_text, {"finish_reason": "MAX_TOKENS", "partial": True}
                
                # No partial response, increase tokens and retry once
                self.logger.warning(f"{operation_name} hit MAX_TOKENS with no content, this suggests token limit too low")
                return False, f"{operation_name} response truncated due to token limit. Try increasing max_output_tokens.", {"finish_reason": "MAX_TOKENS", "retry_suggested": True}
            
            elif finish_reason in ["SAFETY", "RECITATION"]:
                return False, f"{operation_name} blocked by safety filters. Try rephrasing your request.", {"finish_reason": finish_reason}
            
            elif finish_reason == "OTHER":
                return False, f"{operation_name} stopped for unknown reasons.", {"finish_reason": "OTHER"}
            
            # Normal completion
            if hasattr(response, 'text') and response.text:
                return True, response.text, {"finish_reason": finish_reason or "STOP"}
            
            # Try alternative text extraction
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                if candidate.content.parts[0].text:
                    return True, candidate.content.parts[0].text, {"finish_reason": finish_reason or "STOP"}
            
            # Response exists but no text content
            return False, f"No text content in {operation_name} response", {"finish_reason": finish_reason or "NO_TEXT"}
            
        except Exception as e:
            self.logger.error(f"Error handling {operation_name} response: {e}")
            return False, f"Error processing {operation_name} response: {str(e)}", {"error": str(e)}

    async def analyze_with_enhanced_prompt(
        self, 
        enhanced_prompt: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze code using enhanced prompts optimized for Gemini 2.5 Pro's massive context window.
        
        Args:
            enhanced_prompt: Complete enhanced prompt from PromptLoader
            context: Context information for analysis
            
        Returns:
            Analysis results with metadata
        """
        try:
            start_time = datetime.now()
            
            # Prepare the prompt for Gemini 2.5 Pro with full context utilization
            gemini_prompt = self._prepare_gemini_prompt(enhanced_prompt, context)
            
            # Calculate optimal token allocation based on prompt size
            prompt_tokens = self._estimate_tokens(gemini_prompt)
            
            # Use the model's full capacity without artificial restrictions
            analysis_config = {
                "temperature": 0.1,  # Lower for code analysis precision
                "top_p": 0.8,
                "top_k": 40
            }
            
            self.logger.info(f"Using full model capacity for {prompt_tokens} prompt tokens (1M+ context window)")
            
            # Generate response
            response = self.model.generate_content(
                gemini_prompt,
                generation_config=analysis_config
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Handle response safely
            success, analysis_text, response_metadata = self._handle_response_safely(response, "analysis")
            
            if success:
                return {
                    'success': True,
                    'text': analysis_text,
                    'metadata': {
                        'model_used': self.model_name,
                        'processing_time_seconds': processing_time,
                        'prompt_length': len(enhanced_prompt),
                        'prompt_tokens': prompt_tokens,
                        'response_length': len(analysis_text),
                        'context_window_usage': self._calculate_context_usage(enhanced_prompt),
                        'gemini_2_5_pro_optimized': True,
                        'full_context_window_used': True,
                        'finish_reason': response_metadata.get('finish_reason', 'STOP'),
                        'partial_response': response_metadata.get('partial', False)
                    },
                    'performance_metrics': {
                        'tokens_processed': self._estimate_tokens(enhanced_prompt + analysis_text),
                        'efficiency_score': self._calculate_efficiency_score(enhanced_prompt, analysis_text),
                        'response_time_ms': processing_time * 1000,
                        'context_utilization': self._calculate_context_usage(enhanced_prompt)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': analysis_text,
                    'text': f"Analysis failed: {analysis_text}",
                    'metadata': {
                        'model_used': self.model_name,
                        'error_occurred': True,
                        'finish_reason': response_metadata.get('finish_reason', 'UNKNOWN'),
                        'processing_time_seconds': processing_time,
                        'prompt_tokens': prompt_tokens,
                        'full_context_window_available': True
                    }
                }
            
        except Exception as e:
            self.logger.error(f"Error in enhanced analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': f"Analysis failed: {str(e)}",
                'metadata': {
                    'model_used': self.model_name,
                    'error_occurred': True
                }
            }
    
    async def chat_with_context(
        self, 
        message: str, 
        enhanced_prompt: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate conversational responses using enhanced prompts with full Gemini 2.5 Pro context utilization.
        
        Args:
            message: User message
            enhanced_prompt: Enhanced prompt with context
            conversation_history: Previous conversation context
            
        Returns:
            Chat response with metadata
        """
        try:
            start_time = datetime.now()
            
            # Build chat prompt with conversation history
            chat_prompt = self._build_chat_prompt(message, enhanced_prompt, conversation_history)
            
            # Calculate optimal token allocation for chat
            prompt_tokens = self._estimate_tokens(chat_prompt)
            
            # Use full model capacity for conversational responses
            chat_config = {
                "temperature": 0.2,  # Slightly higher for conversational tone
                "top_p": 0.9
            }
            
            self.logger.info(f"Chat using full model capacity for {prompt_tokens} prompt tokens (1M+ context window)")
            
            response = self.model.generate_content(
                chat_prompt,
                generation_config=chat_config
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Handle response safely
            success, response_text, response_metadata = self._handle_response_safely(response, "chat")
            
            self.logger.info(f"🔍 CHAT RESPONSE DEBUG: success={success}")
            self.logger.info(f"🔍 CHAT RESPONSE DEBUG: response_text='{response_text[:200]}{'...' if len(response_text) > 200 else ''}'" if response_text else "🔍 CHAT RESPONSE DEBUG: response_text is empty/None")
            self.logger.info(f"🔍 CHAT RESPONSE DEBUG: response_metadata={response_metadata}")
            
            if success:
                chat_result = {
                    'success': True,
                    'text': response_text,
                    'metadata': {
                        'model_used': self.model_name,
                        'processing_time_seconds': processing_time,
                        'chat_mode': True,
                        'conversation_length': len(conversation_history),
                        'prompt_tokens': prompt_tokens,
                        'context_window_usage': self._calculate_context_usage(chat_prompt),
                        'gemini_2_5_pro_optimized': True,
                        'full_context_window_used': True,
                        'finish_reason': response_metadata.get('finish_reason', 'STOP'),
                        'partial_response': response_metadata.get('partial', False)
                    }
                }
                self.logger.info(f"✅ CHAT SUCCESS: Returning successful chat response with {len(response_text)} characters")
                return chat_result
            else:
                error_result = {
                    'success': False,
                    'error': response_text,
                    'text': f"I apologize, but I couldn't generate a proper response. {response_text}",
                    'metadata': {
                        'model_used': self.model_name,
                        'error_occurred': True,
                        'finish_reason': response_metadata.get('finish_reason', 'UNKNOWN'),
                        'prompt_tokens': prompt_tokens,
                        'full_context_window_available': True
                    }
                }
                self.logger.error(f"❌ CHAT FAILED: Returning error response - {response_text}")
                return error_result
            
        except Exception as e:
            self.logger.error(f"Error in chat response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'text': f"Chat response failed: {str(e)}"
            }
    
    async def generate_suggestions(
        self, 
        enhanced_prompt: str, 
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent code suggestions using enhanced prompts.
        
        Args:
            enhanced_prompt: Enhanced prompt for suggestions
            context: Context including cursor position, surrounding code
            
        Returns:
            List of intelligent suggestions
        """
        try:
            suggestion_prompt = self._build_suggestion_prompt(enhanced_prompt, context)
            
            # Use suggestion-optimized config
            suggestion_config = {
                "max_output_tokens": 2048,
                "temperature": 0.1,
                "top_p": 0.8
            }
            
            response = self.model.generate_content(
                suggestion_prompt,
                generation_config=suggestion_config
            )
            
            # Parse suggestions from response
            suggestions = self._parse_suggestions(response.text if response.text else "")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {str(e)}")
            return []
    
    def _prepare_gemini_prompt(self, enhanced_prompt: str, context: Dict[str, Any]) -> str:
        """Prepare the prompt for optimal Gemini 2.5 Pro processing with full context utilization"""
        
        # Add Gemini 2.5 Pro specific optimization instructions
        gemini_instructions = f"""
## Gemini 2.5 Pro Enhanced Analysis Instructions

You are Gemini 2.5 Pro with access to a 2M+ token context window. Use this comprehensive context to provide:

1. **Deep Comprehensive Analysis**: Leverage the full context to understand complex codebases
2. **Cross-file Pattern Recognition**: Identify patterns and relationships across multiple files
3. **Contextual Code Intelligence**: Provide insights based on project structure and history
4. **Performance-Optimized Responses**: Focus on actionable, detailed recommendations
5. **Structured Expert Output**: Provide clear, well-organized analysis with examples

**Model Capabilities Being Utilized:**
- Model: {self.model_name}
- Context Window: 1M+ tokens available
- Enhanced reasoning and code understanding
- Multi-turn conversation awareness
- Advanced pattern recognition

**Response Guidelines:**
- Provide comprehensive, detailed analysis
- Include specific code examples and improvements
- Explain reasoning behind recommendations
- Structure response with clear sections
- Focus on practical, implementable solutions

"""
        
        return f"{gemini_instructions}\n\n{enhanced_prompt}"
    
    def _build_chat_prompt(
        self, 
        message: str, 
        enhanced_prompt: str, 
        conversation_history: List[Dict[str, Any]]
    ) -> str:
        """Build a conversational prompt with history"""
        
        chat_prompt = f"{enhanced_prompt}\n\n## Conversation Context\n\n"
        
        # Add recent conversation history
        for entry in conversation_history[-5:]:  # Last 5 messages
            role = entry.get('role', 'user')
            content = entry.get('content', '')
            chat_prompt += f"**{role.upper()}**: {content}\n\n"
        
        chat_prompt += f"**USER**: {message}\n\n"
        chat_prompt += "Please provide a helpful, conversational response as a React code expert. Be specific and include code examples when relevant."
        
        return chat_prompt
    
    def _build_suggestion_prompt(self, enhanced_prompt: str, context: Dict[str, Any]) -> str:
        """Build a prompt for intelligent code suggestions"""
        
        cursor_position = context.get('cursor_position', {})
        current_line = context.get('current_line', '')
        surrounding_code = context.get('surrounding_code', '')
        
        suggestion_prompt = f"""
{enhanced_prompt}

## Code Completion Context

**Current Line**: {current_line}
**Cursor Position**: Line {cursor_position.get('line', 0)}, Column {cursor_position.get('column', 0)}
**Surrounding Code**:
```javascript
{surrounding_code}
```

Please provide intelligent code completion suggestions in the following JSON format:
```json
[
  {{
    "type": "completion",
    "text": "suggested code",
    "description": "description of suggestion",
    "priority": "high|medium|low"
  }}
]
```
"""
        
        return suggestion_prompt
    
    def _parse_suggestions(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse suggestions from Gemini response"""
        suggestions = []
        
        try:
            # Try to extract JSON from response
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
                suggestions = json.loads(json_text)
            else:
                # Fallback: create suggestions from text analysis
                suggestions = self._create_fallback_suggestions(response_text)
                
        except json.JSONDecodeError:
            # Fallback to simple text-based suggestions
            suggestions = self._create_fallback_suggestions(response_text)
        
        return suggestions[:5]  # Limit to top 5 suggestions
    
    def _create_fallback_suggestions(self, response_text: str) -> List[Dict[str, Any]]:
        """Create fallback suggestions when JSON parsing fails"""
        
        # Basic pattern-based suggestions
        suggestions = []
        
        if 'useState' in response_text:
            suggestions.append({
                'type': 'completion',
                'text': 'const [state, setState] = useState()',
                'description': 'React useState hook',
                'priority': 'high'
            })
        
        if 'useEffect' in response_text:
            suggestions.append({
                'type': 'completion',
                'text': 'useEffect(() => {\n  // effect logic\n}, [])',
                'description': 'React useEffect hook',
                'priority': 'high'
            })
        
        return suggestions
    
    def _calculate_context_usage(self, prompt: str) -> float:
        """Calculate what percentage of the 1M+ context window is being used"""
        estimated_tokens = self._estimate_tokens(prompt)
        # Gemini 2.5 Pro has approximately 1M tokens context window
        context_window_size = 1_000_000
        usage = estimated_tokens / context_window_size
        
        # Log context usage for optimization
        if usage > 0.8:
            self.logger.warning(f"High context usage: {usage:.2%} of 1M tokens")
        elif usage > 0.5:
            self.logger.info(f"Moderate context usage: {usage:.2%} of 1M tokens")
        else:
            self.logger.debug(f"Low context usage: {usage:.2%} of 1M tokens - plenty of capacity available")
        
        return min(1.0, usage)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def _calculate_efficiency_score(self, prompt: str, response: str) -> float:
        """Calculate efficiency score based on prompt/response ratio"""
        prompt_tokens = self._estimate_tokens(prompt)
        response_tokens = self._estimate_tokens(response)
        
        if prompt_tokens == 0:
            return 0.0
        
        # Good efficiency is high response-to-prompt ratio with meaningful content
        ratio = response_tokens / prompt_tokens
        
        # Normalize to 0-1 scale (optimal ratio is around 0.1-0.3)
        if 0.1 <= ratio <= 0.3:
            return 1.0
        elif ratio < 0.1:
            return ratio / 0.1
        else:
            return max(0.1, 1.0 - (ratio - 0.3) / 0.7)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the Vertex AI service is accessible and responding.
        
        Returns:
            Health status with connection details
        """
        try:
            # Simple test without restrictive token limits - let the model use its full capacity
            test_config = {
                "temperature": 0
            }
            
            test_response = self.model.generate_content(
                "Hello, please respond briefly.",  # Simple test message
                generation_config=test_config
            )
            
            # Handle response safely
            success, response_text, response_metadata = self._handle_response_safely(test_response, "health_check")
            
            if success:
                return {
                    'status': 'healthy',
                    'project_id': self.project_id,
                    'location': self.location,
                    'model': self.model_name,
                    'test_response': response_text[:50] + "..." if len(response_text) > 50 else response_text,
                    'gemini_available': True,
                    'enhanced_prompting_ready': True,
                    'initialization_successful': True,
                    'context_window': '1M+ tokens',
                    'finish_reason': response_metadata.get('finish_reason', 'STOP')
                }
            else:
                # Model initialized but test failed
                return {
                    'status': 'unhealthy',
                    'project_id': self.project_id,
                    'location': self.location,
                    'model': self.model_name,
                    'error': response_text,
                    'initialization_successful': True,
                    'finish_reason': response_metadata.get('finish_reason', 'UNKNOWN'),
                    'guidance': f"Model '{self.model_name}' initialized but health check failed: {response_text}",
                    'suggested_actions': [
                        "The model may still work for actual requests",
                        "Try using the model for real analysis tasks",
                        "Model has 1M+ context window available"
                    ]
                }
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Health check failed: {error_message}")
            
            # Provide helpful error information
            status = {
                'status': 'unhealthy',
                'project_id': self.project_id,
                'location': self.location,
                'model': self.model_name,
                'error': error_message,
                'initialization_successful': True  # Model init worked, but health check failed
            }
            
            # Add specific guidance for common errors
            if "404" in error_message and "not found" in error_message.lower():
                status['guidance'] = f"Model '{self.model_name}' initialized but health check failed. This may be normal - the model should still work for actual requests."
                status['suggested_actions'] = [
                    "Try using the model for actual requests",
                    "Check if the health check endpoint is different from the model endpoint",
                    "Model has 1M+ context window available"
                ]
            elif "permission" in error_message.lower() or "forbidden" in error_message.lower():
                status['guidance'] = "Check Google Cloud project permissions and Vertex AI API enablement"
            elif "credentials" in error_message.lower():
                status['guidance'] = "Check Google Cloud credentials configuration"
            
            return status 