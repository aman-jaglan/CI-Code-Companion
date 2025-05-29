"""
Vertex AI Client for CI Code Companion

This module provides the interface to Google Cloud Vertex AI services
for code generation and analysis tasks.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union
import re # Added for regex-based JSON extraction

from google.cloud import aiplatform
from google.cloud.aiplatform_v1.services import prediction_service
from google.protobuf import json_format
from google.protobuf.struct_pb2 import Value
from vertexai import init
from vertexai.generative_models import GenerativeModel, GenerationConfig
import json

logger = logging.getLogger(__name__)

class VertexAIClient:
    """Client for interacting with Google Cloud Vertex AI services."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        temperature: float = 0.2,
        top_p: float = 0.8,
        top_k: int = 40,
        max_tokens: int = 8192
    ):
        """
        Initialize the Vertex AI client with model parameters.

        Args:
            project_id: Google Cloud project ID
            location: Model location/region
            temperature: Controls randomness (0.0-1.0, lower = more focused)
            top_p: Nucleus sampling parameter
            top_k: Number of highest probability tokens to consider
            max_tokens: Maximum number of tokens in response
        """
        try:
            if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

            self.project_id = project_id
            self.location = location
            self.temperature = temperature
            self.top_p = top_p
            self.top_k = top_k
            self.max_tokens = max_tokens
            
            # Initialize Vertex AI
            init(project=project_id, location=location)

            # Use Gemini 2.5 Pro for all tasks
            self.model_name = "gemini-2.5-pro-preview-05-06"
            
            # Define stop sequences for better response control
            self.stop_sequences = [
                "\n\n###",  # Marks end of a complete thought
                "```\n\n",  # Marks end of code block
                "\nHuman:",  # Prevents model from continuing conversation
            ]
            
            logger.info(
                f"VertexAIClient initialized in {location} using model {self.model_name}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize VertexAIClient: {str(e)}")
            raise

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
            model = GenerativeModel(self.model_name)
            
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
            
            # Create a code generation prompt
            code_prompt = f"""Generate Python code for the following request:

{prompt_text}

Please provide clean, well-documented code with type hints."""

            response = model.generate_content(
                code_prompt,
                generation_config=generation_config
            )
            
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
        prompt: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze code using the Vertex AI model.
        
        Args:
            prompt: The formatted prompt containing code and instructions
            analysis_type: Type of analysis (review, security, performance)
            context: Additional context for the analysis
            
        Returns:
            Dictionary containing the analysis results
        """
        try:
            # Use Gemini model for code analysis
            model = GenerativeModel(self.model_name)
            
            # Estimate token count (rough estimate: 4 chars = 1 token)
            estimated_tokens = len(prompt) // 4
            
            # If we expect the total tokens (input + output) to exceed 20k, use chunking
            if estimated_tokens > 10000:  # Increased threshold since Gemini can handle larger contexts
                logger.info(f"Large input detected ({estimated_tokens} estimated tokens). Using chunked analysis.")
                return self._analyze_large_input(prompt, analysis_type, context)
            
            generation_config = GenerationConfig(
                temperature=0.1,  # Lower temperature for more focused, precise responses
                max_output_tokens=16384,  # Increased to better utilize Gemini's capacity
                top_p=0.9,  # Higher top_p for better quality while maintaining determinism
                top_k=20,  # Lower top_k for more focused responses
                candidate_count=1,
                stop_sequences=["```\n\nLet me", "```\n\n**", "```\n\nNow"]  # Stop before explanations
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=False
            )
            
            # Check for MAX_TOKENS error
            if (hasattr(response, 'candidates') and response.candidates and
                hasattr(response.candidates[0], 'finish_reason') and
                response.candidates[0].finish_reason == "MAX_TOKENS"):
                logger.warning(f"Response truncated due to MAX_TOKENS. Using chunked analysis...")
                return self._analyze_large_input(prompt, analysis_type, context)
            
            # Extract text from response, handling all possible response formats
            response_text = self._extract_response_text(response)
            
            if not response_text:
                raise ValueError("No valid text in model response")
                
            # Validate and parse the response
            parsed_response = self._parse_and_validate_response(response_text, analysis_type)
            
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error during code analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "analysis": None
            }

    def _analyze_large_input(
        self,
        prompt: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle analysis of large inputs by splitting them into chunks.
        
        Args:
            prompt: The large prompt to analyze
            analysis_type: Type of analysis
            context: Additional context
            
        Returns:
            Combined analysis results
        """
        try:
            # Extract the code block from the prompt
            code_start = prompt.find("```")
            code_end = prompt.rfind("```")
            
            if code_start == -1 or code_end == -1:
                raise ValueError("Could not find code block in prompt")
            
            header = prompt[:code_start]
            code = prompt[code_start+3:code_end].strip()
            footer = prompt[code_end+3:].strip()
            
            # Split code into larger chunks since Gemini can handle it
            chunk_size = 24000  # Increased chunk size
            code_chunks = [code[i:i + chunk_size] 
                         for i in range(0, len(code), chunk_size)]
            
            logger.info(f"Split code into {len(code_chunks)} chunks for analysis")
            
            all_issues = []
            for i, chunk in enumerate(code_chunks):
                chunk_prompt = f"{header}\n```\n{chunk}\n```\n{footer}"
                chunk_prompt += f"\nAnalyzing part {i + 1} of {len(code_chunks)}."
                
                model = GenerativeModel(self.model_name)
                generation_config = GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=16384,  # Increased to match analyze_code
                    top_p=self.top_p,
                    top_k=self.top_k
                )
                
                response = model.generate_content(
                    chunk_prompt,
                    generation_config=generation_config,
                    stream=False
                )
                
                response_text = self._extract_response_text(response)
                if response_text:
                    chunk_result = self._parse_and_validate_response(
                        response_text, 
                        analysis_type
                    )
                    if chunk_result.get("status") == "success":
                        all_issues.extend(
                            chunk_result.get("analysis", {}).get("issues", [])
                        )
                else:
                    logger.warning(f"No valid response for chunk {i + 1}")
            
            if not all_issues:
                raise ValueError("No valid results from any chunk")
            
            return {
                "status": "success",
                "analysis": {
                    "type": analysis_type,
                    "issues": all_issues
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing large input: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "analysis": None
            }

    def _extract_response_text(self, response: Any) -> Optional[str]:
        """Safely extract text from a Gemini response.
        
        Args:
            response: Response object from Gemini model
            
        Returns:
            Extracted text or None if no valid text found
        """
        try:
            # First try the simple .text attribute
            if hasattr(response, 'text') and isinstance(response.text, str):
                return response.text
            
            # If no direct text, try to extract from candidates
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Check for MAX_TOKENS error
                if (hasattr(candidate, 'finish_reason') and 
                    candidate.finish_reason == "MAX_TOKENS"):
                    logger.warning("Response truncated due to MAX_TOKENS")
                
                # Try to get text from content
                if hasattr(candidate, 'content'):
                    content = candidate.content
                    
                    # Check for text in parts
                    if hasattr(content, 'parts') and content.parts:
                        part = content.parts[0]
                        
                        # Handle different part formats
                        if isinstance(part, str):
                            return part
                        elif isinstance(part, dict) and 'text' in part:
                            return part['text']
                        elif hasattr(part, 'text'):
                            return part.text
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting response text: {str(e)}")
            return None

    def _parse_and_validate_response(
        self,
        response_text: str,
        analysis_type: str
    ) -> Dict[str, Any]:
        """Parse and validate the model's response.
        
        Args:
            response_text: Raw response from the model
            analysis_type: Type of analysis performed
            
        Returns:
            Validated and structured response dictionary
        """
        try:
            # Ensure response_text is a string
            if not isinstance(response_text, str):
                logger.error(f"_parse_and_validate_response: Expected string response, got {type(response_text)}")
                raise ValueError(f"Expected string response, got {type(response_text)}")
            
            logger.debug(f"_parse_and_validate_response: Raw response text:\n{response_text}")
            # Extract JSON objects from the response
            json_objects = self._extract_json_objects(response_text.strip())
            
            if not json_objects:
                logger.warning("_parse_and_validate_response: No JSON objects extracted from response.")
                raise ValueError("No valid suggestions found in response")
            
            logger.info(f"_parse_and_validate_response: Extracted {len(json_objects)} JSON object(s).")
            # Validate each suggestion
            validated_suggestions = []
            seen_issues = set()  # Track unique issues to prevent duplicates
            
            for i, suggestion in enumerate(json_objects):
                logger.debug(f"_parse_and_validate_response: Validating suggestion #{i+1}: {suggestion}")
                
                if self._validate_suggestion_format(suggestion):
                    # Create a unique identifier for this issue to check for duplicates
                    issue_key = (
                        suggestion.get("line_number", ""),
                        suggestion.get("issue_description", "").lower().strip(),
                        suggestion.get("category", "")
                    )
                    
                    # Check for duplicate issues
                    if issue_key in seen_issues:
                        logger.warning(f"_parse_and_validate_response: Duplicate issue detected, skipping suggestion #{i+1}: {suggestion}")
                        continue
                    
                    # Check for similar solutions (comparing new_content)
                    new_content = suggestion.get("new_content", "").strip()
                    is_duplicate_solution = False
                    
                    for existing_suggestion in validated_suggestions:
                        existing_content = existing_suggestion.get("new_content", "").strip()
                        
                        # Simple similarity check - if solutions are very similar, it's likely a duplicate
                        if len(new_content) > 10 and len(existing_content) > 10:
                            similarity = self._calculate_content_similarity(new_content, existing_content)
                            if similarity > 0.85:  # 85% similarity threshold
                                logger.warning(f"_parse_and_validate_response: Similar solution detected (similarity: {similarity:.2f}), skipping suggestion #{i+1}")
                                is_duplicate_solution = True
                                break
                    
                    if not is_duplicate_solution:
                        seen_issues.add(issue_key)
                        validated_suggestions.append(suggestion)
                        logger.debug(f"_parse_and_validate_response: Added unique suggestion #{i+1}")
                    
                else:
                    logger.warning(f"_parse_and_validate_response: Suggestion #{i+1} failed validation: {suggestion}")

            if not validated_suggestions:
                logger.warning("_parse_and_validate_response: No suggestions passed validation.")
                raise ValueError("No valid suggestions after validation")
            
            logger.info(f"_parse_and_validate_response: {len(validated_suggestions)} unique suggestions passed validation.")
            return {
                "status": "success",
                "analysis": {
                    "type": analysis_type,
                    "issues": validated_suggestions
                }
            }
            
        except Exception as e:
            logger.error(f"_parse_and_validate_response: Error during validation: {str(e)}. Response text: {response_text}")
            return {
                "status": "error",
                "error": f"Failed to parse model response: {str(e)}",
                "analysis": None
            }

    def _extract_json_objects(self, text: str) -> List[Dict[str, Any]]:
        """Extract JSON objects from the response text, expecting them to be in ```json ... ``` blocks.
        
        Args:
            text: Response text potentially containing JSON objects in markdown code blocks.
            
        Returns:
            List of parsed JSON objects
        """
        # Regex to find JSON objects within ```json ... ``` blocks
        # It captures the content between the ```json and ``` markers.
        # re.DOTALL allows . to match newlines, important for multi-line JSON.
        json_block_pattern = re.compile(r'```json\s*([\s\S]*?)\s*```')
        
        json_objects = []
        for match in json_block_pattern.finditer(text):
            json_str = match.group(1).strip() # Get the content and strip whitespace
            try:
                json_obj = json.loads(json_str)
                json_objects.append(json_obj)
                logger.debug(f"_extract_json_objects: Successfully parsed JSON object: {json_str}")
            except json.JSONDecodeError as e:
                logger.warning(f"_extract_json_objects: Failed to parse JSON string from block: '{json_str}'. Error: {e}")
        
        if not json_objects:
            logger.warning(f"_extract_json_objects: No JSON objects found in ```json ... ``` blocks. Full text: {text}")
            
        return json_objects

    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two code content strings.
        
        Args:
            content1: First content string
            content2: Second content string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        try:
            # Normalize the content (remove extra whitespace, convert to lowercase)
            normalized1 = ' '.join(content1.lower().split())
            normalized2 = ' '.join(content2.lower().split())
            
            if not normalized1 or not normalized2:
                return 0.0
            
            # Simple character-based similarity using set intersection
            set1 = set(normalized1)
            set2 = set(normalized2)
            
            if not set1 and not set2:
                return 1.0
            if not set1 or not set2:
                return 0.0
            
            intersection = len(set1.intersection(set2))
            union = len(set1.union(set2))
            
            return intersection / union if union > 0 else 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating content similarity: {str(e)}")
            return 0.0

    def _validate_suggestion_format(self, suggestion: Dict[str, Any]) -> bool:
        """Validate that a suggestion has all required fields and correct format.
        
        Args:
            suggestion: Suggestion dictionary to validate
            
        Returns:
            True if suggestion is valid, False otherwise
        """
        required_fields = {
            "issue_description": str,
            "line_number": (int, str),  # Allow both int and str
            "old_content": str,
            "new_content": str,
            "explanation": str,
            "impact": list,
            "severity": str,
            "category": str
        }
        
        try:
            # Check all required fields exist and have correct types
            for field, expected_type in required_fields.items():
                if field not in suggestion:
                    logger.warning(f"_validate_suggestion_format: Missing required field '{field}' in suggestion: {suggestion}")
                    return False
                
                current_value = suggestion[field]
                if field == "line_number":
                    # Handle line number specially
                    line_num = current_value
                    if isinstance(line_num, int):
                        # Single line number as integer is fine
                        pass
                    elif isinstance(line_num, str):
                        # Handle string line numbers
                        if "-" in line_num:
                            # Handle range format (e.g., "1-5")
                            try:
                                start, end = line_num.split("-")
                                int(start.strip())  # Verify start is a number
                                int(end.strip())    # Verify end is a number
                            except ValueError:
                                logger.warning(f"_validate_suggestion_format: Invalid line number range format '{line_num}' in suggestion: {suggestion}")
                                return False
                        else:
                            # Handle single line number as string
                            try:
                                int(line_num.strip())
                            except ValueError:
                                logger.warning(f"_validate_suggestion_format: Invalid line number format '{line_num}' in suggestion: {suggestion}")
                                return False
                    else:
                        logger.warning(f"_validate_suggestion_format: Invalid line number type '{type(line_num)}' in suggestion: {suggestion}")
                        return False
                else:
                    # Handle other fields normally
                    if isinstance(expected_type, tuple):
                        if not isinstance(current_value, expected_type):
                            logger.warning(f"_validate_suggestion_format: Invalid type for field '{field}'. Expected one of {expected_type}, got {type(current_value)}. Suggestion: {suggestion}")
                            return False
                    else:
                        if not isinstance(current_value, expected_type):
                            logger.warning(f"_validate_suggestion_format: Invalid type for field '{field}'. Expected {expected_type}, got {type(current_value)}. Suggestion: {suggestion}")
                            return False
            
            # Enhanced validation for content quality
            
            # Validate issue description is meaningful
            if len(suggestion["issue_description"].strip()) < 10:
                logger.warning(f"_validate_suggestion_format: Issue description too short: {suggestion}")
                return False
            
            # Validate explanation is meaningful
            if len(suggestion["explanation"].strip()) < 15:
                logger.warning(f"_validate_suggestion_format: Explanation too short: {suggestion}")
                return False
            
            # Validate severity
            if suggestion["severity"] not in ["critical", "high", "medium", "low"]:
                logger.warning(f"_validate_suggestion_format: Invalid severity level '{suggestion['severity']}' in suggestion: {suggestion}")
                return False
            
            # Validate category
            valid_categories = {
                "style", "security", "performance", "reliability",
                "maintainability", "best_practice", "bug"
            }
            if suggestion["category"] not in valid_categories:
                logger.warning(f"_validate_suggestion_format: Invalid category '{suggestion['category']}' in suggestion: {suggestion}")
                return False
            
            # Validate impact list is not empty and contains meaningful content
            if not suggestion["impact"] or len(suggestion["impact"]) == 0:
                logger.warning(f"_validate_suggestion_format: Empty impact list in suggestion: {suggestion}")
                return False
            
            for impact_item in suggestion["impact"]:
                if not isinstance(impact_item, str) or len(impact_item.strip()) < 3:
                    logger.warning(f"_validate_suggestion_format: Invalid impact item '{impact_item}' in suggestion: {suggestion}")
                    return False
            
            # Validate code content is substantial
            old_content = suggestion["old_content"].strip()
            new_content = suggestion["new_content"].strip()
            
            if not old_content or not new_content:
                logger.warning(f"_validate_suggestion_format: Empty code content in suggestion: {suggestion}")
                return False
            
            # Check that new_content is different from old_content (unless it's a style fix)
            if old_content == new_content and suggestion["category"] not in ["style", "best_practice"]:
                logger.warning(f"_validate_suggestion_format: Identical old and new content for non-style issue: {suggestion}")
                return False
            
            # Basic Python syntax validation for new_content (if it looks like Python code)
            if suggestion["category"] in ["bug", "security", "performance", "reliability"]:
                try:
                    # Try to parse the new_content as Python (if it contains Python-like syntax)
                    if any(keyword in new_content for keyword in ["def ", "class ", "import ", "from ", "if ", "for ", "while "]):
                        import ast
                        # Wrap in a function if it's just a code snippet
                        test_code = new_content
                        if not (test_code.strip().startswith(("def ", "class ", "import ", "from "))):
                            test_code = f"def temp_func():\n    {new_content.replace(chr(10), chr(10) + '    ')}"
                        
                        try:
                            ast.parse(test_code)
                        except SyntaxError as e:
                            logger.warning(f"_validate_suggestion_format: New content has syntax errors: {e}. Content: {new_content}")
                            return False
                except Exception:
                    # If we can't validate syntax, that's okay - continue
                    pass
            
            logger.debug(f"_validate_suggestion_format: Suggestion passed enhanced validation: {suggestion}")
            return True
            
        except Exception as e:
            logger.error(f"_validate_suggestion_format: Error during validation: {str(e)}. Suggestion: {suggestion}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check if the Vertex AI service is accessible and responding.
        
        Returns:
            Dictionary with status information
        """
        try:
            # Test connection by making a simple request
            model = GenerativeModel(self.model_name)
            response = model.generate_content("Test connection")
            
            if response:
                return {
                    "status": "healthy",
                    "message": "Successfully connected to Vertex AI",
                    "model": self.model_name
                }
            else:
                return {
                    "status": "error",
                    "message": "No response from model",
                    "model": self.model_name
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "model": self.model_name
            } 