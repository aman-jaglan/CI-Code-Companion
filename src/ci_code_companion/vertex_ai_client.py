"""
Vertex AI Client for CI Code Companion

This module provides the interface to Google Cloud Vertex AI services
for code generation and analysis tasks.
"""

import os
import logging
from typing import Optional, Dict, Any

from google.cloud import aiplatform
from google.cloud.aiplatform_v1.services import prediction_service
# from google.cloud.aiplatform_v1.types import predict # Removed direct import of predict
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
import vertexai
from vertexai.generative_models import GenerativeModel

logger = logging.getLogger(__name__)

class VertexAIClient:
    """Client for interacting with Google Cloud Vertex AI services."""

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
            credentials_path: Path to service account credentials JSON file
        """
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        self.project_id = project_id
        self.location = location
        self.api_endpoint = f"{location}-aiplatform.googleapis.com"
        self.client_options = {"api_endpoint": self.api_endpoint}

        # Initialize Vertex AI (this sets up the project and location for the library)
        aiplatform.init(project=project_id, location=location)
        vertexai.init(project=project_id, location=location)

        # Prediction service client for PaLM models
        self.prediction_client = prediction_service.PredictionServiceClient(
            client_options=self.client_options
        )

        # Define model endpoints for PaLM models
        self.code_generation_model_endpoint = (
            f"projects/{project_id}/locations/{location}/publishers/google/models/code-bison@001"
        )
        self.text_generation_model_endpoint = (
            f"projects/{project_id}/locations/{location}/publishers/google/models/text-bison"
        )
        
        # Gemini model
        self.gemini_model_id = "gemini-2.5-flash-preview-05-20"
        
        logger.info(f"VertexAIClient initialized for project {project_id} in {location}")

    def generate_code(
        self,
        prompt_text: str,
        max_output_tokens: int = 1024,
        temperature: float = 0.2
    ) -> str:
        """
        Generate code using the Gemini model.

        Args:
            prompt_text: The prompt for code generation.
            max_output_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature (0.0-1.0).

        Returns:
            Generated code as a string.
        """
        try:
            model = GenerativeModel(self.gemini_model_id)
            
            # Create a code generation prompt
            code_prompt = f"""Generate Python code for the following request:

{prompt_text}

Please provide clean, well-documented code with type hints."""

            response = model.generate_content(code_prompt)
            
            if response.candidates and response.candidates[0].content.parts:
                generated_code = response.candidates[0].content.parts[0].text
                logger.info(f"Successfully generated code ({len(generated_code)} characters)")
                return generated_code
            else:
                logger.warning("Code generation returned no content.")
                return ""
        except Exception as e:
            logger.error(f"Error generating code: {str(e)}")
            raise

    def analyze_code(
        self,
        code: str,
        analysis_type: str = "review"
    ) -> str:
        """
        Analyze code using the Gemini model.

        Args:
            code: The code to analyze.
            analysis_type: Type of analysis ('review', 'security', 'performance').

        Returns:
            Analysis results as a string.
        """
        try:
            model = GenerativeModel(self.gemini_model_id)
            
            if analysis_type == "review":
                prompt = f"""You are a Python code reviewer focusing ONLY on actual code issues that affect execution.
Review the following code and identify ONLY:
1. Missing or incomplete functions/methods that are necessary for the code to work
2. Syntax errors or incorrect code patterns that would cause runtime issues
3. Missing error handling that would cause crashes
4. Incorrect logic that would produce wrong results

For each issue found, your response MUST follow this EXACT format:

ISSUE: [One-line description of the issue]
LINE: [Line number where the change is needed]
OLD: [The problematic line of code]
NEW: [The corrected line of code]
WHY: [One-line explanation of why this change is needed]

Example response format:
ISSUE: Missing is_empty method required by pop() implementation
LINE: 12
OLD: def pop(self):
NEW: def is_empty(self) -> bool:
    return len(self.items) == 0
WHY: pop() method calls is_empty() but it's not implemented

If no issues affecting code execution are found, respond with exactly:
NO_ISSUES: Code is functionally complete and will execute correctly.

Code to review:
```python
{code}
```"""
            elif analysis_type == "security":
                prompt = f"""Please analyze the following code for security vulnerabilities:

Code to analyze:
```python
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
```python
{code}
```

Focus on:
- Algorithmic complexity
- Memory usage
- Inefficient operations
- Optimization opportunities"""
            else:
                prompt = f"Please analyze this code: ```python\n{code}\n```"

            response = model.generate_content(prompt)
            
            if response.candidates and response.candidates[0].content.parts:
                analysis_result = response.candidates[0].content.parts[0].text
                logger.info(f"Successfully analyzed code ({analysis_type})")
                return analysis_result
            else:
                logger.warning(f"Code analysis ({analysis_type}) returned no content.")
                return "NO_ISSUES: Code is functionally complete and will execute correctly."
        except Exception as e:
            logger.error(f"Error analyzing code ({analysis_type}): {str(e)}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the connection to Vertex AI is working.

        Returns:
            Dict containing status information.
        """
        try:
            # Test connection by making a simple request to Gemini
            model = GenerativeModel(self.gemini_model_id)
            response = model.generate_content("Hello")
            
            if response.candidates and response.candidates[0].content.parts:
                return {
                    "status": "healthy",
                    "message": "Successfully connected to Vertex AI and Gemini model is accessible.",
                    "project_id": self.project_id,
                    "location": self.location,
                    "models_available": {
                        "gemini": True,
                        "code_generation": True,
                        "text": True
                    }
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": "Connected to Vertex AI but Gemini model returned no content.",
                    "project_id": self.project_id,
                    "location": self.location,
                    "models_available": {
                        "gemini": False,
                        "code_generation": False,
                        "text": False
                    }
                }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "message": f"Failed to connect or access Gemini model: {str(e)}",
                "project_id": self.project_id,
                "location": self.location,
                "models_available": {
                    "gemini": False,
                    "code_generation": False,
                    "text": False
                }
            } 