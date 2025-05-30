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
from vertexai.generative_models import (
    GenerativeModel, GenerationConfig,
    SafetySetting, HarmCategory, HarmBlockThreshold,
    FinishReason
)
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
        max_tokens: int = 16384
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
        max_output_tokens: int = 4096,
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
                max_output_tokens=max_output_tokens,
                stop_sequences=self.stop_sequences
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

    def _get_safety_settings(self) -> List[SafetySetting]:
        """Get safety settings optimized for code review tasks.
        
        Returns:
            List of safety settings that are permissive for code analysis
        """
        return [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE
            ),
        ]

    def _calculate_dynamic_tokens(self, prompt: str) -> Dict[str, int]:
        """Calculate dynamic token limits based on input size and model capacity using real token counts.
        
        Args:
            prompt: The input prompt
            
        Returns:
            Dictionary with calculated token limits
        """
        # Hard limits from the model card
        MAX_INPUT_TOKENS  = 1_048_576          # Gemini 2.5 Pro
        MAX_OUTPUT_TOKENS = 65_535
        
        def dynamic_token_plan(prompt: str,
                               # Target ~16K tokens for comprehensive analysis of larger files
                               target_output_for_task: int = 16384, 
                               soft_context: int = 256_000,  # Increased from 128K to 256K
                               min_output: int = 1024) -> dict: # Increased min for better quality responses
            """
            Returns a dict with:
              input_tokens, max_output_tokens, needs_chunking, chunk_size_chars
            """
            # 1️⃣  Get the real token count – no guessing
            model = GenerativeModel(self.model_name)
            input_tokens = model.count_tokens([prompt]).total_tokens
        
            # 2️⃣  Pick an output budget with safety buffer
            remaining   = soft_context - input_tokens      # Space left in our 256 K soft tier
            
            # Aim for target_output_for_task, but respect remaining space and absolute MAX_OUTPUT_TOKENS
            output_tok  = max(min(target_output_for_task,
                                  remaining,
                                  MAX_OUTPUT_TOKENS),
                              min_output)
            
            # Add safety buffer - never allocate the full amount
            # This prevents truncation that makes responses unusable
            safety_buffer = max(64, output_tok // 20)  # 5% buffer (reduced from 10%), minimum 64 tokens
            output_tok = max(output_tok - safety_buffer, min_output)
        
            # 3️⃣  Decide whether we need chunking
            # Chunk if input + calculated output exceeds 95% of soft_context (increased from 90%)
            needs_chunk = input_tokens + output_tok > soft_context * 0.95 
            if needs_chunk:
                # Aim to keep each chunk's input ≤ 50% of soft_context allowing room for larger outputs
                chunk_input_tok  = int(soft_context * 0.5)  # Reduced from 0.6 to 0.5 for larger outputs
                # crude char approximation (3 char ≈ 1 token)
                chunk_size_chars = chunk_input_tok * 3
            else:
                chunk_size_chars = len(prompt) # No chunking needed, chunk is the whole prompt
        
            return {
                "input_tokens":      input_tokens,
                "max_output_tokens": output_tok,
                "needs_chunking":    needs_chunk,
                "chunk_size_chars":  chunk_size_chars,
                "total_estimated":   input_tokens + output_tok
            }
        
        # Use the new dynamic token planning
        result = dynamic_token_plan(prompt)
        
        # Convert to the expected format (keeping compatibility)
        return {
            "estimated_input_tokens": result["input_tokens"],
            "max_output_tokens": result["max_output_tokens"],
            "needs_chunking": result["needs_chunking"],
            "chunk_size_chars": result["chunk_size_chars"],
            "total_estimated": result["total_estimated"]
        }

    def analyze_code(
        self,
        prompt: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze code using the Vertex AI model with dynamic token management.
        
        Args:
            prompt: The formatted prompt containing code and instructions
            analysis_type: Type of analysis (review, security, performance)
            context: Additional context for the analysis
            
        Returns:
            Dictionary containing the analysis results
        """
        try:
            # Calculate dynamic token limits
            token_config = self._calculate_dynamic_tokens(prompt)
            
            logger.info(f"Dynamic token analysis: {token_config}")
            
            # Use chunking only if needed
            if token_config["needs_chunking"]:
                logger.info(f"Large input detected ({token_config['estimated_input_tokens']} tokens). Using dynamic chunked analysis.")
                return self._analyze_large_input_dynamic(prompt, analysis_type, context, token_config)
            
            # Use the full prompt with dynamic output limit
            model = GenerativeModel(self.model_name)
            
            generation_config = GenerationConfig(
                temperature=0.1,
                max_output_tokens=token_config["max_output_tokens"],
                stop_sequences=self.stop_sequences
            )
            
            # Get safety settings to prevent blocking of code review content
            safety_settings = self._get_safety_settings()
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings,
                stream=False
            )
            
            # Check for MAX_TOKENS error and adapt
            if (hasattr(response, 'candidates') and response.candidates and
                hasattr(response.candidates[0], 'finish_reason') and
                response.candidates[0].finish_reason is FinishReason.MAX_TOKENS):
                logger.warning(f"Hit MAX_TOKENS with {token_config['max_output_tokens']} limit ({response.usage_metadata.total_token_count - response.usage_metadata.prompt_token_count} tokens generated). Switching to chunked analysis as a fallback...")
                # Force chunking by creating a token_config that ensures it
                # We use a small chunk size here because the single prompt failed.
                forced_chunk_config = token_config.copy()
                forced_chunk_config['needs_chunking'] = True 
                # Make chunk_size_chars smaller to ensure multiple chunks if possible, e.g., 50% of soft_context for input tokens per chunk
                # but we need to calculate a character count from this. Soft context is 256k.
                # Let target_chunk_input_tokens be 50% of 256k, then convert to chars.
                target_chunk_input_tokens = int(256000 * 0.5) # 256k * 0.5 = 128000 tokens
                forced_chunk_config['chunk_size_chars'] = target_chunk_input_tokens * 3 # Approx 384k chars

                # However, if the original prompt is smaller than this, just use a fraction of it.
                if len(prompt) < forced_chunk_config['chunk_size_chars']:
                     forced_chunk_config['chunk_size_chars'] = len(prompt) // 2 if len(prompt) // 2 > 100 else len(prompt)

                logger.info(f"Forcing chunked analysis with config: {forced_chunk_config}")
                return self._analyze_large_input_dynamic(prompt, analysis_type, context, forced_chunk_config)
            
            # Extract and validate response
            response_text = self._extract_response_text(response)
            
            if not response_text:
                raise ValueError("No valid text in model response")
                
            parsed_response = self._parse_and_validate_response(response_text, analysis_type)
            return parsed_response
            
        except Exception as e:
            logger.error(f"Error during dynamic code analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "analysis": None
            }

    def _analyze_large_input_dynamic(
        self,
        prompt: str,
        analysis_type: str,
        context: Optional[Dict[str, Any]] = None,
        token_config: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Handle analysis of large inputs using dynamic chunking.
        
        Args:
            prompt: The large prompt to analyze
            analysis_type: Type of analysis
            context: Additional context
            token_config: Pre-calculated token configuration
            
        Returns:
            Combined analysis results
        """
        try:
            if not token_config:
                token_config = self._calculate_dynamic_tokens(prompt)
            
            # Extract the code block from the prompt
            code_start = prompt.find("```")
            code_end = prompt.rfind("```")
            
            if code_start == -1 or code_end == -1:
                raise ValueError("Could not find code block in prompt")
            
            header = prompt[:code_start]
            code = prompt[code_start+3:code_end].strip()
            footer = prompt[code_end+3:].strip()
            
            # Use dynamic chunk size
            chunk_size = token_config["chunk_size_chars"]
            code_chunks = [code[i:i + chunk_size] 
                         for i in range(0, len(code), chunk_size)]
            
            logger.info(f"Dynamic chunking: {len(code_chunks)} chunks with {chunk_size} chars each")
            
            all_issues = []
            successful_chunks = 0
            
            for i, chunk in enumerate(code_chunks):
                # Calculate dynamic tokens for this specific chunk
                chunk_prompt = f"""You are an expert code reviewer analyzing a code chunk ({i + 1}/{len(code_chunks)}). Use systematic analysis to identify the most critical issues.

**FOCUSED ANALYSIS PROCESS:**

1. **CHUNK CONTEXT**: Understand this code segment:
   - What is the primary purpose of this code?
   - What patterns and structures are present?
   - How does this likely fit into the larger system?

2. **CRITICAL ISSUE DETECTION**: Look for high-impact problems:
   - Security vulnerabilities (injection, validation bypass, exposure)
   - Logic errors that cause incorrect behavior
   - Performance bottlenecks (inefficient algorithms, resource leaks)
   - Reliability issues (error handling, edge cases)

3. **QUALITY ASSESSMENT**: Evaluate code quality:
   - Maintainability and readability
   - Adherence to best practices
   - Proper error handling
   - Code organization and structure

**ANALYSIS FOCUS:**
Since this is a chunk analysis, prioritize:
- Issues that have immediate impact on correctness or security
- Problems that affect system stability
- Clear optimization opportunities
- Maintainability improvements that reduce technical debt

**CHUNK ANALYSIS:**

<thinking>
Let me analyze this code chunk systematically:

1. CHUNK CONTEXT:
[Understanding the code's purpose and structure]

2. CRITICAL ISSUE DETECTION:
[Identifying high-impact problems]

3. QUALITY ASSESSMENT:
[Evaluating code quality and best practices]
</thinking>

**CODE CHUNK ({i + 1}/{len(code_chunks)}):**
```python
{chunk}
```

**IDENTIFIED ISSUES:**
Based on my analysis, here are the most critical issues found (up to 3, prioritized by impact).

**IMPORTANT**: Keep explanations brief and to the point (max 1-2 sentences). Focus on the core problem and solution.

**STRICT JSON FORMAT REQUIREMENT:**
You MUST use EXACTLY this JSON format with EXACTLY these field names. Do NOT create your own format.
Do NOT use fields like "file", "title", "description", "suggestion", "line_start", "line_end".

**JSON FORMAT:**
{{"issue_description":"Clear description","line_number":"X","old_content":"current code","new_content":"fixed code","explanation":"Brief reason (1-2 sentences max)","impact":["benefit1","benefit2"],"severity":"critical|high|medium|low","category":"security|bug|performance|maintainability|style"}}

Each issue must be a separate JSON object on its own line.

```json"""
                
                # Calculate dynamic output for this chunk
                chunk_token_config = self._calculate_dynamic_tokens(chunk_prompt)
                
                model = GenerativeModel(self.model_name)
                generation_config = GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=chunk_token_config["max_output_tokens"],
                    stop_sequences=self.stop_sequences
                )
                
                # Get safety settings to prevent blocking
                safety_settings = self._get_safety_settings()
                
                try:
                    response = model.generate_content(
                        chunk_prompt,
                        generation_config=generation_config,
                        safety_settings=safety_settings,
                        stream=False
                    )
                    
                    # Handle MAX_TOKENS by reducing output for this chunk
                    if (hasattr(response, 'candidates') and response.candidates and
                        hasattr(response.candidates[0], 'finish_reason') and
                        response.candidates[0].finish_reason is FinishReason.MAX_TOKENS):
                        
                        logger.warning(f"Chunk {i+1} hit MAX_TOKENS, retrying with smaller output...")
                        
                        # Retry with smaller output
                        smaller_config = GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=max(1024, chunk_token_config["max_output_tokens"] // 2),  # Increased from 256 to 1024
                            stop_sequences=self.stop_sequences
                        )
                        
                        response = model.generate_content(
                            chunk_prompt,
                            generation_config=smaller_config,
                            safety_settings=safety_settings,
                            stream=False
                        )
                    
                    response_text = self._extract_response_text(response)
                    if response_text:
                        chunk_result = self._parse_and_validate_response(
                            response_text, 
                            analysis_type
                        )
                        if chunk_result.get("status") == "success":
                            chunk_issues = chunk_result.get("analysis", {}).get("issues", [])
                            all_issues.extend(chunk_issues)
                            successful_chunks += 1
                            logger.info(f"Chunk {i+1} processed successfully: {len(chunk_issues)} issues found")
                        else:
                            logger.warning(f"Chunk {i+1} failed validation")
                    else:
                        logger.warning(f"No valid response for chunk {i + 1}")
                        
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i+1}: {str(chunk_error)}")
                    continue
            
            if not all_issues and successful_chunks == 0:
                raise ValueError("No valid results from any chunk")
            
            logger.info(f"Dynamic chunking completed: {successful_chunks}/{len(code_chunks)} chunks successful, {len(all_issues)} total issues found")
            
            return {
                "status": "success",
                "analysis": {
                    "type": analysis_type,
                    "issues": all_issues,
                    "chunks_processed": successful_chunks,
                    "total_chunks": len(code_chunks)
                }
            }
            
        except Exception as e:
            logger.error(f"Error in dynamic large input analysis: {str(e)}")
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
                # Iterate through all candidates to find one with valid content
                for candidate_idx, candidate in enumerate(response.candidates):
                    
                    # Check for MAX_TOKENS error (but still try to extract text)
                    if (hasattr(candidate, 'finish_reason') and 
                        candidate.finish_reason is FinishReason.MAX_TOKENS):
                        logger.warning(f"Candidate {candidate_idx} truncated due to MAX_TOKENS")
                    
                    # Try to get text from content
                    if hasattr(candidate, 'content'):
                        content = candidate.content
                        
                        # Check for text in parts
                        if hasattr(content, 'parts') and content.parts:
                            part = content.parts[0]
                            
                            # Handle different part formats
                            if isinstance(part, str):
                                logger.info(f"Found valid text in candidate {candidate_idx}")
                                return part
                            elif isinstance(part, dict) and 'text' in part:
                                logger.info(f"Found valid text in candidate {candidate_idx}")
                                return part['text']
                            elif hasattr(part, 'text'):
                                logger.info(f"Found valid text in candidate {candidate_idx}")
                                return part.text
                        else:
                            logger.warning(f"Candidate {candidate_idx} has empty parts (likely safety-filtered)")
            
            logger.warning("No valid text found in any candidate")
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
        """Extract JSON objects from the response text, supporting both ```json blocks and individual JSON objects.
        
        Args:
            text: Response text potentially containing JSON objects in various formats.
            
        Returns:
            List of parsed JSON objects
        """
        json_objects = []
        
        # First, try to find JSON objects within ```json ... ``` blocks
        json_block_pattern = re.compile(r'```json\s*([\s\S]*?)\s*```', re.DOTALL)
        
        for match in json_block_pattern.finditer(text):
            json_content = match.group(1).strip()
            
            # Try to parse as a single JSON object first
            try:
                json_obj = json.loads(json_content)
                
                # Check if it's a list (array) of objects
                if isinstance(json_obj, list):
                    for item in json_obj:
                        if isinstance(item, dict):
                            # Convert wrong format to expected format if needed
                            converted_item = self._convert_wrong_format_to_expected(item)
                            if converted_item:
                                json_objects.append(converted_item)
                            else:
                                json_objects.append(item)
                else:
                    # Single object
                    converted_obj = self._convert_wrong_format_to_expected(json_obj)
                    if converted_obj:
                        json_objects.append(converted_obj)
                    else:
                        json_objects.append(json_obj)
                
                logger.debug(f"_extract_json_objects: Successfully parsed JSON object from block: {json_content}")
                continue
            except json.JSONDecodeError:
                pass
            
            # If single JSON parsing failed, try to parse multiple JSON objects separated by newlines
            for line in json_content.split('\n'):
                line = line.strip()
                if line and (line.startswith('{') or line.startswith('[')):
                    try:
                        json_obj = json.loads(line)
                        converted_obj = self._convert_wrong_format_to_expected(json_obj)
                        if converted_obj:
                            json_objects.append(converted_obj)
                        else:
                            json_objects.append(json_obj)
                        logger.debug(f"_extract_json_objects: Successfully parsed JSON object from line: {line}")
                    except json.JSONDecodeError as e:
                        logger.debug(f"_extract_json_objects: Failed to parse JSON line: '{line}'. Error: {e}")
        
        # If no JSON blocks found, try to find individual JSON objects in the text
        if not json_objects:
            logger.debug("_extract_json_objects: No JSON blocks found, searching for individual JSON objects")
            
            # Look for lines that start with { and try to parse them as JSON
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        json_obj = json.loads(line)
                        converted_obj = self._convert_wrong_format_to_expected(json_obj)
                        if converted_obj:
                            json_objects.append(converted_obj)
                        else:
                            json_objects.append(json_obj)
                        logger.debug(f"_extract_json_objects: Successfully parsed standalone JSON object: {line}")
                    except json.JSONDecodeError as e:
                        logger.debug(f"_extract_json_objects: Failed to parse standalone JSON: '{line}'. Error: {e}")
            
            # Try to find JSON objects using a more flexible regex pattern
            if not json_objects:
                # Look for JSON-like structures with curly braces
                json_pattern = re.compile(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}')
                
                for match in json_pattern.finditer(text):
                    potential_json = match.group(0).strip()
                    try:
                        json_obj = json.loads(potential_json)
                        converted_obj = self._convert_wrong_format_to_expected(json_obj)
                        if converted_obj:
                            json_objects.append(converted_obj)
                        else:
                            json_objects.append(json_obj)
                        logger.debug(f"_extract_json_objects: Successfully parsed JSON object with regex: {potential_json}")
                    except json.JSONDecodeError:
                        continue
        
        if not json_objects:
            logger.warning(f"_extract_json_objects: No valid JSON objects found in text. Full text: {text}")
        else:
            logger.info(f"_extract_json_objects: Successfully extracted {len(json_objects)} JSON objects")
            
        return json_objects

    def _convert_wrong_format_to_expected(self, json_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert AI's wrong JSON format to the expected format.
        
        Args:
            json_obj: JSON object that might be in wrong format
            
        Returns:
            Converted object in expected format, or None if no conversion needed
        """
        # Check if this looks like the wrong format (has fields like 'file', 'title', 'description', 'suggestion')
        wrong_format_fields = ['file', 'title', 'description', 'suggestion', 'line_start', 'line_end']
        has_wrong_fields = any(field in json_obj for field in wrong_format_fields)
        
        # Check if it already has the expected format
        expected_fields = ['issue_description', 'line_number', 'old_content', 'new_content', 'explanation', 'impact', 'severity', 'category']
        has_expected_fields = any(field in json_obj for field in expected_fields)
        
        if has_wrong_fields and not has_expected_fields:
            logger.info("_convert_wrong_format_to_expected: Converting AI's wrong format to expected format")
            
            # Convert the wrong format to expected format
            converted = {}
            
            # Map fields
            converted['issue_description'] = json_obj.get('title', json_obj.get('description', 'Unknown issue'))
            
            # Handle line numbers
            if 'line_start' in json_obj and 'line_end' in json_obj:
                line_start = json_obj['line_start']
                line_end = json_obj['line_end']
                if line_start == line_end:
                    converted['line_number'] = str(line_start)
                else:
                    converted['line_number'] = f"{line_start}-{line_end}"
            elif 'line_start' in json_obj:
                converted['line_number'] = str(json_obj['line_start'])
            else:
                converted['line_number'] = "1"  # Default
            
            # Extract old content (this might be tricky to auto-generate)
            converted['old_content'] = "# Code needs review"  # Placeholder
            
            # Use suggestion as new content
            converted['new_content'] = json_obj.get('suggestion', 'See suggestion for improvement')
            
            # Use description as explanation
            converted['explanation'] = json_obj.get('description', 'See issue description')
            
            # Create impact based on severity and description
            severity = json_obj.get('severity', 'medium').lower()
            if 'critical' in severity:
                converted['impact'] = ['Fixes critical issue', 'Prevents system failure']
            elif 'high' in severity:
                converted['impact'] = ['Improves code quality', 'Reduces bugs']
            else:
                converted['impact'] = ['Code improvement', 'Better maintainability']
            
            # Map severity
            converted['severity'] = severity if severity in ['critical', 'high', 'medium', 'low'] else 'medium'
            
            # Infer category based on content
            description_lower = json_obj.get('description', '').lower()
            if any(keyword in description_lower for keyword in ['security', 'injection', 'vulnerability', 'attack']):
                converted['category'] = 'security'
            elif any(keyword in description_lower for keyword in ['performance', 'slow', 'efficient', 'optimization']):
                converted['category'] = 'performance'
            elif any(keyword in description_lower for keyword in ['bug', 'error', 'exception', 'crash']):
                converted['category'] = 'bug'
            else:
                converted['category'] = 'maintainability'
            
            logger.debug(f"_convert_wrong_format_to_expected: Converted {json_obj} to {converted}")
            return converted
        
        return None  # No conversion needed

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
            
            # Validate code content is substantial and MUST have solution
            old_content = suggestion["old_content"].strip()
            new_content = suggestion["new_content"].strip()
            
            if not old_content:
                logger.warning(f"_validate_suggestion_format: Empty old_content in suggestion: {suggestion}")
                return False
            
            # EVERY issue MUST have a solution - no exceptions
            if not new_content:
                logger.warning(f"_validate_suggestion_format: Every issue must have a solution. Empty new_content in suggestion: {suggestion}")
                return False
            
            # Ensure the solution is meaningful and different
            if old_content == new_content:
                logger.warning(f"_validate_suggestion_format: Solution must be different from the problem. Identical old and new content: {suggestion}")
                return False
            
            # Check that the solution is substantial (more than trivial changes)
            similarity = self._calculate_content_similarity(old_content, new_content)
            if similarity > 0.95:  # Too similar, probably not a real fix
                logger.warning(f"_validate_suggestion_format: Solution too similar to original code (similarity: {similarity}): {suggestion}")
                return False
            
            # Ensure the new content is meaningful (not just whitespace changes)
            if len(new_content.strip()) < 3:
                logger.warning(f"_validate_suggestion_format: Solution too short or trivial: {suggestion}")
                return False
            
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