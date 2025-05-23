"""
Vertex AI Client for CI Code Companion

This module provides the interface to Google Cloud Vertex AI services
for code generation and analysis tasks.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from google.cloud import aiplatform
from google.cloud.aiplatform.gapic.schema import predict
from vertexai.language_models import CodeGenerationModel, CodeChatModel

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Client for interacting with Google Cloud Vertex AI Codey models."""
    
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the Vertex AI client.
        
        Args:
            project_id: Google Cloud project ID
            location: Google Cloud region
            credentials_path: Path to service account JSON file (optional)
        """
        self.project_id = project_id
        self.location = location
        
        # Set up authentication
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)
        
        # Initialize models
        self.code_generation_model = CodeGenerationModel.from_pretrained("code-bison@001")
        self.code_chat_model = CodeChatModel.from_pretrained("codechat-bison@001")
        
        logger.info(f"Initialized Vertex AI client for project {project_id}")
    
    def generate_code(
        self,
        prompt: str,
        max_output_tokens: int = 1024,
        temperature: float = 0.2,
        candidate_count: int = 1
    ) -> str:
        """
        Generate code using the Codey code generation model.
        
        Args:
            prompt: The prompt for code generation
            max_output_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            candidate_count: Number of response candidates to generate
            
        Returns:
            Generated code as a string
        """
        try:
            response = self.code_generation_model.predict(
                prompt=prompt,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                candidate_count=candidate_count
            )
            
            generated_code = response.text
            logger.info(f"Successfully generated code ({len(generated_code)} characters)")
            return generated_code
            
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise
    
    def analyze_code(
        self,
        code: str,
        analysis_type: str = "review",
        context: Optional[str] = None
    ) -> str:
        """
        Analyze code using the Codey chat model.
        
        Args:
            code: The code to analyze
            analysis_type: Type of analysis ('review', 'security', 'performance')
            context: Additional context for the analysis
            
        Returns:
            Analysis results as a string
        """
        try:
            # Create analysis prompt based on type
            if analysis_type == "review":
                prompt = f"""Please review the following code and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Suggestions for improvement
4. Security considerations

Code to review:
```
{code}
```

{f"Additional context: {context}" if context else ""}

Please provide a structured review with clear recommendations."""

            elif analysis_type == "security":
                prompt = f"""Please analyze the following code for security vulnerabilities:

Code to analyze:
```
{code}
```

Focus on:
- Input validation issues
- Authentication/authorization problems
- Data exposure risks
- Injection vulnerabilities
- Other security concerns"""

            elif analysis_type == "performance":
                prompt = f"""Please analyze the following code for performance issues:

Code to analyze:
```
{code}
```

Focus on:
- Algorithmic complexity
- Memory usage
- Inefficient operations
- Optimization opportunities"""
            
            else:
                prompt = f"Please analyze this code: ```{code}```"
            
            chat_session = self.code_chat_model.start_chat()
            response = chat_session.send_message(prompt)
            
            logger.info(f"Successfully analyzed code ({analysis_type})")
            return response.text
            
        except Exception as e:
            logger.error(f"Error analyzing code: {str(e)}")
            raise
    
    def generate_unit_tests(
        self,
        function_code: str,
        language: str = "python",
        test_framework: str = "pytest",
        include_edge_cases: bool = True
    ) -> str:
        """
        Generate unit tests for a given function.
        
        Args:
            function_code: The function code to test
            language: Programming language
            test_framework: Testing framework to use
            include_edge_cases: Whether to include edge case tests
            
        Returns:
            Generated test code
        """
        edge_case_instruction = "Include edge cases and error conditions." if include_edge_cases else ""
        
        prompt = f"""Generate comprehensive unit tests for the following {language} function using {test_framework}.

Function to test:
```{language}
{function_code}
```

Requirements:
1. Test normal/typical use cases
2. {edge_case_instruction}
3. Test error handling and invalid inputs
4. Use proper assertions and test structure
5. Include docstrings for test methods
6. Follow {test_framework} best practices

Generate complete, runnable test code:"""

        return self.generate_code(prompt, max_output_tokens=2048)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the Vertex AI connection.
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Simple test with the code generation model
            test_prompt = "# Generate a simple Python hello world function"
            response = self.generate_code(test_prompt, max_output_tokens=100)
            
            return {
                "status": "healthy",
                "project_id": self.project_id,
                "location": self.location,
                "test_response_length": len(response),
                "models_available": {
                    "code_generation": True,
                    "code_chat": True
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "project_id": self.project_id,
                "location": self.location
            } 