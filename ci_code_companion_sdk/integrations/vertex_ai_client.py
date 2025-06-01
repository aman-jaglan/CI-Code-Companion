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
        model_name: str = "gemini-2.5-pro",
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the Vertex AI client with Gemini 2.5 Pro optimization.
        
        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_name: Model to use (default: gemini-2.5-pro)
            credentials_path: Optional path to service account JSON
        """
        if not VERTEX_AI_AVAILABLE:
            raise ImportError("Vertex AI SDK not available. Install with: pip install google-cloud-aiplatform")
        
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Set credentials if provided
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            
            # Initialize Gemini 2.5 Pro model
            self.model = GenerativeModel(
                model_name=model_name,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.1,  # Lower temperature for code analysis
                    "top_p": 0.8,
                    "top_k": 40
                }
            )
            
            self.logger.info(f"VertexAI client initialized successfully with {model_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize VertexAI client: {str(e)}")
            raise
    
    async def analyze_with_enhanced_prompt(
        self, 
        enhanced_prompt: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze code using enhanced prompts optimized for Gemini 2.5 Pro.
        
        Args:
            enhanced_prompt: Complete enhanced prompt from PromptLoader
            context: Context information for analysis
            
        Returns:
            Analysis results with metadata
        """
        try:
            start_time = datetime.now()
            
            # Prepare the prompt for Gemini 2.5 Pro
            gemini_prompt = self._prepare_gemini_prompt(enhanced_prompt, context)
            
            # Generate response using Gemini 2.5 Pro
            response = self.model.generate_content(
                gemini_prompt,
                generation_config={
                    "max_output_tokens": 8192,
                    "temperature": 0.1,
                    "top_p": 0.8
                }
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract and format the response
            analysis_text = response.text if response.text else "No analysis generated"
            
            return {
                'success': True,
                'analysis': analysis_text,
                'metadata': {
                    'model_used': self.model_name,
                    'processing_time_seconds': processing_time,
                    'prompt_length': len(enhanced_prompt),
                    'response_length': len(analysis_text),
                    'context_window_usage': self._calculate_context_usage(enhanced_prompt),
                    'gemini_optimized': True
                },
                'performance_metrics': {
                    'tokens_processed': self._estimate_tokens(enhanced_prompt + analysis_text),
                    'efficiency_score': self._calculate_efficiency_score(enhanced_prompt, analysis_text),
                    'response_time_ms': processing_time * 1000
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in enhanced analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'analysis': f"Analysis failed: {str(e)}",
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
        Generate conversational responses using enhanced prompts.
        
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
            
            # Generate conversational response
            response = self.model.generate_content(
                chat_prompt,
                generation_config={
                    "max_output_tokens": 4096,
                    "temperature": 0.2,  # Slightly higher for conversational tone
                    "top_p": 0.9
                }
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'response': response.text if response.text else "No response generated",
                'metadata': {
                    'model_used': self.model_name,
                    'processing_time_seconds': processing_time,
                    'chat_mode': True,
                    'conversation_length': len(conversation_history)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in chat response: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f"Chat response failed: {str(e)}"
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
            
            response = self.model.generate_content(
                suggestion_prompt,
                generation_config={
                    "max_output_tokens": 2048,
                    "temperature": 0.1,
                    "top_p": 0.8
                }
            )
            
            # Parse suggestions from response
            suggestions = self._parse_suggestions(response.text if response.text else "")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {str(e)}")
            return []
    
    def _prepare_gemini_prompt(self, enhanced_prompt: str, context: Dict[str, Any]) -> str:
        """Prepare the prompt for optimal Gemini 2.5 Pro processing"""
        
        # Add Gemini-specific optimization instructions
        gemini_instructions = """
## Gemini 2.5 Pro Analysis Instructions

You are a Gemini 2.5 Pro model with access to a 1M token context window. Use this comprehensive context to provide:

1. **Deep Analysis**: Leverage the full context to understand the codebase structure
2. **Cross-file Insights**: Consider relationships between files and components
3. **Contextual Recommendations**: Provide suggestions based on project patterns and history
4. **Performance Optimization**: Focus on React performance best practices
5. **Structured Output**: Provide clear, actionable insights with code examples

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
        """Calculate what percentage of the 1M context window is being used"""
        estimated_tokens = self._estimate_tokens(prompt)
        context_window_size = 1_000_000  # 1M tokens for Gemini 2.5 Pro
        return min(1.0, estimated_tokens / context_window_size)
    
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
            # Simple test to verify connectivity
            test_response = self.model.generate_content(
                "Hello, this is a connection test. Please respond with 'Connection successful.'",
                generation_config={
                    "max_output_tokens": 50,
                    "temperature": 0
                }
            )
            
            return {
                'status': 'healthy',
                'project_id': self.project_id,
                'location': self.location,
                'model': self.model_name,
                'test_response': test_response.text if test_response.text else 'No response',
                'gemini_2_5_pro_available': 'gemini-2.5-pro' in self.model_name,
                'enhanced_prompting_ready': True
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'project_id': self.project_id,
                'location': self.location,
                'model': self.model_name,
                'error': str(e)
            } 