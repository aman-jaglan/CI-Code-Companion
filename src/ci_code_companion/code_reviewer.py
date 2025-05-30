"""
Code Reviewer for CI Code Companion

This module handles AI-powered code review and analysis.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from .vertex_ai_client import VertexAIClient
import json
import ast
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CodeSuggestion:
    """Represents a single code suggestion from the AI model."""
    issue_description: str
    line_number: Union[int, str]
    old_content: str
    new_content: str
    explanation: str
    impact: List[str]
    severity: str
    category: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert suggestion to dictionary format."""
        return {
            "issue_description": self.issue_description,
            "line_number": self.line_number,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "explanation": self.explanation,
            "impact": self.impact,
            "severity": self.severity,
            "category": self.category
        }

class CodeReviewer:
    """Handles code review operations using AI models."""
    
    def __init__(
        self,
        ai_client: VertexAIClient,
        review_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the code reviewer.
        
        Args:
            ai_client: Instance of VertexAIClient for AI operations
            review_config: Optional configuration for review behavior
        """
        self.ai_client = ai_client
        self.review_config = review_config or self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for code review."""
        return {
            "max_lines_per_review": 500,
            "min_confidence_score": 0.7,
            "severity_thresholds": {
                "critical": 0.9,
                "high": 0.8,
                "medium": 0.6,
                "low": 0.4
            },
            "review_aspects": [
                "security",
                "performance",
                "reliability",
                "maintainability",
                "best_practices"
            ]
        }
    
    def _get_review_prompt(self, code: str, file_path: str) -> str:
        """Generate a comprehensive Chain of Thought prompt for thorough code review."""
        
        return f"""You are an expert software engineer performing a comprehensive code review. Think through this systematically using the following chain of thought process.

**THINKING PROCESS:**

1. **INITIAL ANALYSIS**: First, scan the entire codebase to understand:
   - Overall architecture and design patterns used
   - Dependencies and imports
   - Main functionality and purpose
   - Code complexity and structure

2. **DETAILED EXAMINATION**: For each function, class, and code block, analyze:
   - Logic correctness and edge cases
   - Error handling and exception management
   - Input validation and sanitization
   - Resource management (memory, files, connections)
   - Concurrency and thread safety considerations

3. **SECURITY ASSESSMENT**: Look for:
   - SQL injection vulnerabilities (parameterized queries)
   - Input validation bypasses
   - Authentication and authorization flaws
   - Data exposure and privacy issues
   - Cryptographic weaknesses
   - Path traversal vulnerabilities
   - Command injection risks

4. **PERFORMANCE EVALUATION**: Identify:
   - Algorithmic complexity issues (O(n²) vs O(n))
   - Database query optimization opportunities
   - Memory usage patterns and potential leaks
   - Network call efficiency
   - Caching opportunities
   - Loop optimizations and redundant operations

5. **MAINTAINABILITY REVIEW**: Assess:
   - Code readability and clarity
   - Naming conventions and consistency
   - Function/class size and single responsibility
   - Code duplication and refactoring opportunities
   - Documentation and comments quality
   - Testability and modularity

6. **BEST PRACTICES CHECK**: Verify adherence to:
   - Language-specific conventions (PEP 8 for Python)
   - Design principles (SOLID, DRY, KISS)
   - Error handling patterns
   - Logging and monitoring practices
   - Type hints and documentation
   - Package structure and imports

**ANALYSIS INSTRUCTIONS:**

Think step-by-step through each section above. For each potential issue you identify:
- Determine the root cause and impact
- Assess the severity (critical/high/medium/low)
- Consider the effort required to fix
- Think about the best solution approach
- Verify your reasoning is sound

**OUTPUT REQUIREMENTS:**

Based on your analysis, provide up to 5 most critical issues in JSON format. Prioritize issues by:
1. Security vulnerabilities (critical)
2. Logic bugs that cause incorrect behavior (high)
3. Performance bottlenecks (high/medium)
4. Maintainability problems (medium/low)
5. Style and convention issues (low)

For each issue, provide:
- Clear, actionable description
- Exact line number(s) affected
- Current problematic code
- Improved code solution
- Brief explanation of why the change is needed (max 1-2 sentences)
- Specific benefits/impact of the fix
- Appropriate severity and category

**CRITICAL ISSUES IDENTIFIED:**
Based on my systematic analysis, here are the most important issues (up to 5, prioritized by severity).

**IMPORTANT**: Keep explanations brief and to the point (max 1-2 sentences). Focus on the core problem and solution.

**STRICT JSON FORMAT REQUIREMENT:**
You MUST use EXACTLY this JSON format with EXACTLY these field names. Do NOT create your own format.
Do NOT use fields like "file", "title", "description", "suggestion", "line_start", "line_end".

**CRITICAL REQUIREMENT: EVERY VULNERABILITY MUST HAVE A SOLUTION**
- The "new_content" field is MANDATORY and must contain actual secure code
- Do NOT leave "new_content" empty - provide concrete security fixes
- If you identify a vulnerability, you MUST provide a working secure solution
- If no fix is possible, do NOT report the vulnerability

**JSON FORMAT:**
{{"issue_description":"Security vulnerability description","line_number":"X","old_content":"vulnerable code","new_content":"secure code","explanation":"Brief security reason (1-2 sentences max)","impact":["security benefit1","benefit2"],"severity":"critical|high|medium","category":"security"}}

Each issue must be a separate JSON object on its own line.

**CODE TO REVIEW ({file_path}):**
```python
{code}
```

**YOUR ANALYSIS:**
Think through each step systematically, then provide your findings:

<thinking>
Let me analyze this code step by step:

1. INITIAL ANALYSIS:
[Your systematic analysis of overall structure]

2. DETAILED EXAMINATION:
[Your line-by-line analysis of logic and functionality]

3. SECURITY ASSESSMENT:
[Your security vulnerability analysis]

4. PERFORMANCE EVALUATION:
[Your performance bottleneck analysis]

5. MAINTAINABILITY REVIEW:
[Your code quality and maintainability analysis]

6. BEST PRACTICES CHECK:
[Your standards and conventions analysis]
</thinking>

**CRITICAL ISSUES IDENTIFIED:**
Based on my systematic analysis, here are the most important issues (up to 5, prioritized by severity).

**IMPORTANT**: Keep explanations brief and to the point (max 1-2 sentences). Focus on the core problem and solution.

```json"""

    def _build_review_prompt(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the comprehensive prompt for code review with additional context."""
        # Extract file type and relevant context
        file_type = Path(file_path).suffix if file_path else ".py"
        
        base_prompt = self._get_review_prompt(code, file_path or "unknown.py")

        if context:
            context_section = "\n\n**ADDITIONAL CONTEXT:**\n"
            context_section += f"```json\n{json.dumps(context, indent=2)}\n```\n"
            context_section += "\nConsider this context in your analysis, especially for understanding the broader system impact.\n"
            
            # Insert context before the code section
            code_marker = "**CODE TO REVIEW"
            if code_marker in base_prompt:
                parts = base_prompt.split(code_marker, 1)
                base_prompt = parts[0] + context_section + code_marker + parts[1]
            else:
                base_prompt += context_section
            
        return base_prompt
    
    def _validate_python_syntax(self, code: str) -> List[Dict[str, Any]]:
        """Validate Python syntax and collect errors.
        
        Args:
            code: Python code to validate
            
        Returns:
            List of syntax errors found
        """
        syntax_errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            syntax_errors.append({
                "issue_description": "Syntax Error",
                "line_number": e.lineno,
                "old_content": e.text.strip() if e.text else "",
                "new_content": "",  # AI will provide the fix
                "explanation": str(e),
                "impact": ["Code will not execute", "Runtime error"],
                "severity": "critical",
                "category": "bug"
            })
        return syntax_errors
    
    def review_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Review code and provide suggestions.
        
        Args:
            code: The code to review
            file_path: Optional path to the file being reviewed
            context: Optional additional context
            
        Returns:
            Dictionary containing review results and suggestions
        """
        try:
            # First check for syntax errors
            syntax_errors = self._validate_python_syntax(code)
            if syntax_errors:
                return {
                    "status": "error",
                    "issues": syntax_errors,
                    "message": "Syntax errors found in code"
                }
            
            # Build and send prompt to AI
            prompt = self._build_review_prompt(code, file_path, context)
            response = self.ai_client.analyze_code(
                prompt=prompt,
                analysis_type="review",
                context=context
            )
            
            if response["status"] == "error":
                return response
            
            # Process and validate suggestions
            suggestions = []
            for issue in response["analysis"]["issues"]:
                try:
                    suggestion = CodeSuggestion(**issue)
                    suggestions.append(suggestion.to_dict())
                except Exception as e:
                    logger.warning(f"Invalid suggestion format: {str(e)}")
                    continue
            
            return {
                "status": "success",
                "file_path": file_path,
                "issues": suggestions,
                "message": f"Found {len(suggestions)} issue(s) to address"
            }
            
        except Exception as e:
            logger.error(f"Error during code review: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to complete code review: {str(e)}",
                "issues": []
            }
    
    def apply_suggestion(
        self,
        code: str,
        suggestion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply a suggested code change.
        
        Args:
            code: Original code
            suggestion: Suggestion to apply
            
        Returns:
            Dictionary with updated code and status
        """
        try:
            lines = code.splitlines()
            raw_line_num = suggestion["line_number"]
            start_line_num = -1

            if isinstance(raw_line_num, str) and "-" in raw_line_num:
                try:
                    start_str, _ = raw_line_num.split("-", 1)
                    start_line_num = int(start_str.strip()) - 1  # Use the start of the range, 0-indexed
                except ValueError:
                    logger.error(f"Invalid line number range format in suggestion: {raw_line_num}")
                    return {
                        "status": "error",
                        "message": f"Invalid line number format: {raw_line_num}",
                        "code": code
                    }
            elif isinstance(raw_line_num, (int, str)):
                try:
                    start_line_num = int(raw_line_num) - 1  # Convert to 0-based index
                except ValueError:
                    logger.error(f"Invalid line number string format in suggestion: {raw_line_num}")
                    return {
                        "status": "error",
                        "message": f"Invalid line number format: {raw_line_num}",
                        "code": code
                    }
            else:
                logger.error(f"Invalid line_number type in suggestion: {type(raw_line_num)}")
                return {
                    "status": "error",
                    "message": f"Invalid line_number type: {type(raw_line_num)}",
                    "code": code
                }

            if start_line_num < 0 or start_line_num >= len(lines):
                return {
                    "status": "error",
                    "message": f"Invalid line number: {start_line_num + 1} (original: {raw_line_num})",
                    "code": code
                }
            
            # Handle multi-line changes
            old_lines = suggestion["old_content"].splitlines()
            new_lines = suggestion["new_content"].splitlines()
            
            # Remove old lines
            for _ in range(len(old_lines)):
                if start_line_num < len(lines):
                    lines.pop(start_line_num)
            
            # Insert new lines
            for i, new_line in enumerate(new_lines):
                lines.insert(start_line_num + i, new_line)
            
            updated_code = "\n".join(lines)
            
            # Validate the updated code
            try:
                ast.parse(updated_code)
                return {
                    "status": "success",
                    "message": "Successfully applied suggestion",
                    "code": updated_code
                }
            except SyntaxError as e:
                return {
                    "status": "error",
                    "message": f"Applied change resulted in syntax error: {str(e)}",
                    "code": code  # Return original code
                }
            
        except Exception as e:
            logger.error(f"Error applying suggestion: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to apply suggestion: {str(e)}",
                "code": code
            }
    
    def review_code_diff(
        self,
        diff_content: str,
        review_type: str = "comprehensive",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Review a code diff using AI.
        
        Args:
            diff_content: The git diff content
            review_type: Type of review ('comprehensive', 'security', 'performance')
            context: Additional context for the review
            
        Returns:
            Dictionary containing review results
        """
        try:
            # Prepare context information
            context_info = ""
            if context:
                context_info = f"""
Additional Context:
- Files changed: {context.get('files_changed', 'Unknown')}
- Lines added: {context.get('lines_added', 'Unknown')}
- Lines removed: {context.get('lines_removed', 'Unknown')}
- Branch: {context.get('branch', 'Unknown')}
- Author: {context.get('author', 'Unknown')}
"""
            
            if review_type == "comprehensive":
                analysis = self._comprehensive_review(diff_content, context_info)
            elif review_type == "security":
                analysis = self._security_review(diff_content, context_info)
            elif review_type == "performance":
                analysis = self._performance_review(diff_content, context_info)
            else:
                analysis = self._comprehensive_review(diff_content, context_info)
            
            # Parse the AI response into structured format
            return self._parse_review_response(analysis, review_type)
            
        except Exception as e:
            logger.error(f"Error reviewing code diff: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "recommendations": [],
                "severity": "unknown"
            }
    
    def _comprehensive_review(self, diff_content: str, context_info: str) -> str:
        """Perform comprehensive code review with Chain of Thought analysis."""
        prompt = f"""You are an expert software engineer performing a comprehensive code review of a git diff. Use systematic analysis to identify critical issues.

**CHAIN OF THOUGHT ANALYSIS:**

1. **DIFF UNDERSTANDING**: First understand what changed:
   - What files were modified/added/removed?
   - What functionality is being added or changed?
   - Are there any breaking changes?
   - What is the scope and impact of these changes?

2. **CHANGE IMPACT ANALYSIS**: For each change, consider:
   - Does this affect existing functionality?
   - Are there potential integration issues?
   - Could this introduce regression bugs?
   - What edge cases might be affected?

3. **SECURITY IMPLICATIONS**: Examine for:
   - New attack vectors introduced
   - Data validation on new inputs
   - Authentication/authorization changes
   - Exposure of sensitive information
   - Injection vulnerabilities in modified queries/commands

4. **LOGIC AND CORRECTNESS**: Verify:
   - Algorithm correctness in modified functions
   - Proper error handling for new code paths
   - Boundary conditions and edge cases
   - State management and data consistency

5. **PERFORMANCE CONSIDERATIONS**: Check for:
   - New inefficient operations (N+1 queries, nested loops)
   - Memory usage increases
   - Database/network operation changes
   - Caching implications

6. **MAINTAINABILITY FACTORS**: Assess:
   - Code clarity and readability of changes
   - Consistency with existing codebase
   - Documentation updates needed
   - Test coverage for new functionality

**ANALYSIS PROCESS:**
Think through each modification systematically. For each potential issue:
- Identify the specific problem and its root cause
- Assess severity based on potential impact
- Consider likelihood of the issue manifesting
- Think about the best fix approach
- Verify the fix doesn't introduce new problems

{context_info}

**CODE CHANGES:**
```diff
{diff_content}
```

**SYSTEMATIC ANALYSIS:**

<thinking>
Let me analyze these changes step by step:

1. DIFF UNDERSTANDING:
[Analysis of what's changing and why]

2. CHANGE IMPACT ANALYSIS: 
[Assessment of how changes affect the system]

3. SECURITY IMPLICATIONS:
[Security vulnerability analysis]

4. LOGIC AND CORRECTNESS:
[Correctness and edge case analysis]

5. PERFORMANCE CONSIDERATIONS:
[Performance impact analysis]

6. MAINTAINABILITY FACTORS:
[Code quality and maintainability analysis]
</thinking>

**CRITICAL ISSUES IDENTIFIED:**
Based on my systematic analysis, here are the most important issues (up to 5, prioritized by severity).

**IMPORTANT**: Keep explanations brief and to the point (max 1-2 sentences). Focus on the core problem and solution.

**STRICT JSON FORMAT REQUIREMENT:**
You MUST use EXACTLY this JSON format with EXACTLY these field names. Do NOT create your own format.
Do NOT use fields like "file", "title", "description", "suggestion", "line_start", "line_end".

**CRITICAL REQUIREMENT: EVERY PERFORMANCE ISSUE MUST HAVE A SOLUTION**
- The "new_content" field is MANDATORY and must contain actual optimized code
- Do NOT leave "new_content" empty - provide concrete performance optimizations
- If you identify a performance issue, you MUST provide a working optimized solution
- If no optimization is possible, do NOT report the issue

**JSON FORMAT:**
{{"issue_description":"Performance issue description","line_number":"X","old_content":"slow code","new_content":"optimized code","explanation":"Brief performance reason (1-2 sentences max)","impact":["performance benefit1","benefit2"],"severity":"high|medium|low","category":"performance"}}

Each issue must be a separate JSON object on its own line.

```json"""
        
        return self.ai_client.analyze_code(prompt, "review")
    
    def _security_review(self, diff_content: str, context_info: str) -> str:
        """Perform security-focused code review with specialized threat analysis."""
        prompt = f"""You are a cybersecurity expert performing a security-focused code review. Use systematic threat analysis to identify vulnerabilities.

**SECURITY ANALYSIS FRAMEWORK:**

1. **OWASP TOP 10 ASSESSMENT**: Check for:
   - A01: Broken Access Control (authorization bypasses)
   - A02: Cryptographic Failures (weak encryption, exposed secrets)
   - A03: Injection (SQL, NoSQL, Command, LDAP injection)
   - A04: Insecure Design (missing security controls)
   - A05: Security Misconfiguration (default configs, verbose errors)
   - A06: Vulnerable Components (outdated dependencies)
   - A07: Authentication Failures (weak auth, session issues)
   - A08: Software Integrity Failures (unsigned/unverified packages)
   - A09: Logging Failures (insufficient logging/monitoring)
   - A10: Server-Side Request Forgery (SSRF)

2. **INPUT VALIDATION ANALYSIS**: For all inputs, check:
   - Are inputs properly sanitized and validated?
   - Is there proper length/type/format checking?
   - Are there bypass opportunities for validation?
   - Is input encoding/decoding handled securely?

3. **AUTHENTICATION & AUTHORIZATION**: Examine:
   - Are authentication mechanisms properly implemented?
   - Is authorization checked at all access points?
   - Are there privilege escalation opportunities?
   - Is session management secure?

4. **DATA PROTECTION**: Verify:
   - Are sensitive data properly encrypted at rest/transit?
   - Is PII/PHI handled according to regulations?
   - Are secrets/keys properly managed?
   - Is data exposure minimized?

5. **INJECTION VULNERABILITIES**: Look for:
   - SQL injection in database queries
   - Command injection in system calls
   - LDAP injection in directory queries
   - NoSQL injection in document databases
   - Script injection in dynamic code execution

6. **BUSINESS LOGIC FLAWS**: Identify:
   - Race conditions in critical operations
   - State manipulation vulnerabilities
   - Workflow bypass opportunities
   - Economic/financial logic flaws

**THREAT MODELING PROCESS:**
For each code change:
- Identify what new attack surface is created
- Determine what assets are at risk
- Assess potential threat actors and their capabilities
- Evaluate existing security controls
- Calculate risk based on likelihood × impact

{context_info}

**CODE CHANGES:**
```diff
{diff_content}
```

**SECURITY THREAT ANALYSIS:**

<thinking>
Let me perform systematic security analysis:

1. OWASP TOP 10 ASSESSMENT:
[Check each category against the code changes]

2. INPUT VALIDATION ANALYSIS:
[Examine all input handling for vulnerabilities]

3. AUTHENTICATION & AUTHORIZATION:
[Review access control implementation]

4. DATA PROTECTION:
[Assess data handling security]

5. INJECTION VULNERABILITIES:
[Look for injection attack vectors]

6. BUSINESS LOGIC FLAWS:
[Identify logic-based security issues]
</thinking>

**SECURITY VULNERABILITIES IDENTIFIED:**
Based on my threat analysis, here are the critical security issues (up to 5, ordered by risk level).

**IMPORTANT**: Keep explanations brief and to the point (max 1-2 sentences). Focus on the core security problem and solution.

**STRICT JSON FORMAT REQUIREMENT:**
You MUST use EXACTLY this JSON format with EXACTLY these field names. Do NOT create your own format.
Do NOT use fields like "file", "title", "description", "suggestion", "line_start", "line_end".

**CRITICAL REQUIREMENT: EVERY VULNERABILITY MUST HAVE A SOLUTION**
- The "new_content" field is MANDATORY and must contain actual secure code
- Do NOT leave "new_content" empty - provide concrete security fixes
- If you identify a vulnerability, you MUST provide a working secure solution
- If no fix is possible, do NOT report the vulnerability

**JSON FORMAT:**
{{"issue_description":"Security vulnerability description","line_number":"X","old_content":"vulnerable code","new_content":"secure code","explanation":"Brief security reason (1-2 sentences max)","impact":["security benefit1","benefit2"],"severity":"critical|high|medium","category":"security"}}

Each issue must be a separate JSON object on its own line.

```json"""
        
        return self.ai_client.analyze_code(prompt, "security")
    
    def _performance_review(self, diff_content: str, context_info: str) -> str:
        """Perform performance-focused code review with algorithmic analysis."""
        prompt = f"""You are a performance optimization expert analyzing code changes for efficiency issues. Use systematic performance analysis techniques.

**PERFORMANCE ANALYSIS FRAMEWORK:**

1. **ALGORITHMIC COMPLEXITY**: Analyze each function for:
   - Time complexity (Big O notation)
   - Space complexity and memory usage
   - Nested loop efficiency
   - Recursive call depth and memoization opportunities
   - Search and sort algorithm choices

2. **DATABASE PERFORMANCE**: Examine:
   - Query efficiency and index usage
   - N+1 query problems
   - Batch operation opportunities
   - Connection pooling and management
   - Transaction scope and duration
   - JOIN complexity and query optimization

3. **MEMORY MANAGEMENT**: Check for:
   - Memory leaks and proper cleanup
   - Unnecessary object creation
   - Large object retention
   - Garbage collection pressure
   - Memory pooling opportunities

4. **I/O OPERATIONS**: Evaluate:
   - File system operation efficiency
   - Network call optimization
   - Async/await usage for I/O bound operations
   - Batching of network requests
   - Streaming vs loading entire datasets

5. **CACHING STRATEGIES**: Assess:
   - Redundant computation elimination
   - Appropriate caching levels (memory, disk, distributed)
   - Cache invalidation strategies
   - Cache hit ratio optimization
   - Precomputation opportunities

6. **CONCURRENCY PATTERNS**: Review:
   - Thread safety and synchronization overhead
   - Lock contention and deadlock potential
   - Parallel processing opportunities
   - Async pattern usage
   - Resource sharing efficiency

**PERFORMANCE MEASUREMENT APPROACH:**
For each potential issue:
- Estimate performance impact (latency, throughput, resource usage)
- Consider scalability implications
- Identify bottlenecks and critical paths
- Evaluate optimization effort vs benefit
- Think about measurement and monitoring needs

{context_info}

**CODE CHANGES:**
```diff
{diff_content}
```

**PERFORMANCE ANALYSIS:**

<thinking>
Let me systematically analyze performance implications:

1. ALGORITHMIC COMPLEXITY:
[Analyze time/space complexity of changed code]

2. DATABASE PERFORMANCE:
[Review database operation efficiency]

3. MEMORY MANAGEMENT:
[Assess memory usage patterns]

4. I/O OPERATIONS:
[Evaluate I/O efficiency]

5. CACHING STRATEGIES:
[Review caching opportunities]

6. CONCURRENCY PATTERNS:
[Analyze concurrent execution efficiency]
</thinking>

**PERFORMANCE ISSUES IDENTIFIED:**
Based on my performance analysis, here are the critical efficiency issues (up to 5, prioritized by impact).

**IMPORTANT**: Keep explanations brief and to the point (max 1-2 sentences). Focus on the core performance problem and solution.

**STRICT JSON FORMAT REQUIREMENT:**
You MUST use EXACTLY this JSON format with EXACTLY these field names. Do NOT create your own format.
Do NOT use fields like "file", "title", "description", "suggestion", "line_start", "line_end".

**CRITICAL REQUIREMENT: EVERY PERFORMANCE ISSUE MUST HAVE A SOLUTION**
- The "new_content" field is MANDATORY and must contain actual optimized code
- Do NOT leave "new_content" empty - provide concrete performance optimizations
- If you identify a performance issue, you MUST provide a working optimized solution
- If no optimization is possible, do NOT report the issue

**JSON FORMAT:**
{{"issue_description":"Performance issue description","line_number":"X","old_content":"slow code","new_content":"optimized code","explanation":"Brief performance reason (1-2 sentences max)","impact":["performance benefit1","benefit2"],"severity":"high|medium|low","category":"performance"}}

Each issue must be a separate JSON object on its own line.

```json"""
        
        return self.ai_client.analyze_code(prompt, "performance")
    
    def _parse_review_response(self, ai_response: Dict[str, Any], review_type: str) -> Dict[str, Any]:
        """
        Parse AI review response into structured format.
        
        Args:
            ai_response: Response from the AI model
            review_type: Type of review performed
            
        Returns:
            Dictionary containing structured review results
        """
        logger.debug(f"Raw AI response to parse:\n{ai_response}")
        result = {
            "review_type": review_type,
            "issues": [],
            "suggested_changes": [],
            "explanation": "",
            "severity": "info"
        }

        try:
            # Handle case where ai_response is already a dictionary
            if isinstance(ai_response, dict):
                if ai_response.get("status") == "error":
                    return {
                        "status": "error",
                        "error": ai_response.get("error", "Unknown error in AI response"),
                        "review_type": review_type,
                        "issues": [],
                        "suggested_changes": [],
                        "severity": "error"
                    }
                
                # Extract issues from the analysis section
                analysis = ai_response.get("analysis", {})
                if isinstance(analysis, dict) and "issues" in analysis:
                    for issue in analysis["issues"]:
                        if not isinstance(issue, dict):
                            continue
                            
                        # Add to issues list
                        issue_desc = issue.get("issue_description", "")
                        explanation = issue.get("explanation", "")
                        if explanation:
                            issue_desc += f" (Reason: {explanation})"
                        result["issues"].append(issue_desc)
                        
                        # Add to suggested changes
                        result["suggested_changes"].append({
                            "line_number": issue.get("line_number"),
                            "old_content": issue.get("old_content", ""),
                            "new_content": issue.get("new_content", ""),
                            "description": issue.get("issue_description", ""),
                            "explanation": issue.get("explanation", ""),
                            "severity": issue.get("severity", "medium"),
                            "category": issue.get("category", "best_practice")
                        })
                        
                        # Update overall severity
                        if issue.get("severity") == "critical":
                            result["severity"] = "critical"
                        elif issue.get("severity") == "high" and result["severity"] not in ["critical"]:
                            result["severity"] = "high"
                        elif issue.get("severity") == "medium" and result["severity"] not in ["critical", "high"]:
                            result["severity"] = "medium"
                
                return result

            # If ai_response is a string (legacy format), try to parse it
            if isinstance(ai_response, str):
                return self._parse_legacy_response(ai_response, review_type)
            
            raise ValueError(f"Unexpected AI response type: {type(ai_response)}")
            
        except Exception as e:
            logger.error(f"Error parsing review response: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to parse AI response: {str(e)}",
                "review_type": review_type,
                "issues": [],
                "suggested_changes": [],
                "severity": "error"
            }

    def _parse_legacy_response(self, response_text: str, review_type: str) -> Dict[str, Any]:
        """Parse legacy string format response."""
        result = {
            "review_type": review_type,
            "issues": [],
            "suggested_changes": [],
            "explanation": "",
            "severity": "info"
        }

        if response_text.strip().startswith("NO_ISSUES:"):
            result["explanation"] = response_text.strip().split(':', 1)[1].strip()
            logger.info("AI reported no issues.")
            return result

        # Split into blocks and parse each one
        blocks = response_text.strip().split('\n\n')
        for block in blocks:
            if not block.strip().startswith("ISSUE:"):
                continue

            try:
                issue_data = self._parse_issue_block(block.strip())
                if issue_data:
                    desc = issue_data['description']
                    if issue_data.get('why'):
                        desc += f" (Reason: {issue_data['why']})"
                    result["issues"].append(desc)
                    
                    result["suggested_changes"].append({
                        "line_number": issue_data.get('line_number'),
                        "old_content": issue_data.get('old_content', ''),
                        "new_content": issue_data.get('new_content', ''),
                        "description": issue_data['description'],
                        "explanation": issue_data.get('why', ''),
                        "severity": "medium",  # Default severity for legacy format
                        "category": "best_practice"  # Default category for legacy format
                    })
            except Exception as e:
                logger.warning(f"Failed to parse issue block: {e}")

        if result["issues"]:
            result["severity"] = self._determine_severity(response_text)

        return result

    def _parse_issue_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse a single issue block from legacy format."""
        lines = block.split('\n')
        issue_data = {}
        
        for i, line in enumerate(lines):
            if line.startswith("ISSUE:"):
                issue_data['description'] = line.split(':', 1)[1].strip()
            elif line.startswith("LINE:"):
                try:
                    issue_data['line_number'] = int(line.split(':', 1)[1].strip())
                except ValueError:
                    issue_data['line_number'] = None
            elif line.startswith("OLD:"):
                issue_data['old_content'] = line.split(':', 1)[1].strip()
            elif line.startswith("NEW:"):
                new_content_lines = [line.split(':', 1)[1].strip()]
                for j in range(i + 1, len(lines)):
                    if not any(lines[j].startswith(k) for k in ["ISSUE:", "LINE:", "OLD:", "WHY:"]):
                        new_content_lines.append(lines[j])
                    else:
                        break
                issue_data['new_content'] = "\n".join(new_content_lines)
            elif line.startswith("WHY:"):
                issue_data['why'] = line.split(':', 1)[1].strip()
        
        if issue_data.get('description') and issue_data.get('new_content') is not None:
            return issue_data
        return None
    
    def _add_section_content(self, result: Dict, section: str, content: List[str]):
        """Add content to appropriate section of result."""
        content_text = '\n'.join(content).strip()
        
        if section == 'summary':
            result['summary'] = content_text
        elif section == 'issues':
            # Split into individual issues
            issues = [issue.strip() for issue in content_text.split('\n') if issue.strip()]
            result['issues'].extend(issues)
        elif section == 'recommendations':
            recommendations = [rec.strip() for rec in content_text.split('\n') if rec.strip()]
            result['recommendations'].extend(recommendations)
        elif section == 'positive_aspects':
            positives = [pos.strip() for pos in content_text.split('\n') if pos.strip()]
            result['positive_aspects'].extend(positives)
    
    def _determine_severity(self, response: str) -> str:
        """Determine overall severity based on AI response."""
        response_lower = response.lower()
        
        if any(keyword in response_lower for keyword in ['critical', 'severe', 'major security']):
            return "critical"
        elif any(keyword in response_lower for keyword in ['high', 'important', 'significant']):
            return "high"
        elif any(keyword in response_lower for keyword in ['medium', 'moderate', 'minor']):
            return "medium"
        elif any(keyword in response_lower for keyword in ['low', 'trivial', 'cosmetic']):
            return "low"
        else:
            return "info"
    
    def review_files(
        self,
        file_paths: List[str],
        review_type: str = "comprehensive"
    ) -> List[Dict[str, Any]]:
        """
        Review multiple files.
        
        Args:
            file_paths: List of file paths to review
            review_type: Type of review to perform
            
        Returns:
            List of review results for each file
        """
        results = []
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create a pseudo-diff for the entire file
                diff_content = f"--- /dev/null\n+++ {file_path}\n"
                for i, line in enumerate(content.split('\n'), 1):
                    diff_content += f"+{line}\n"
                
                context = {
                    "file_path": file_path,
                    "review_mode": "full_file"
                }
                
                review_result = self.review_code_diff(diff_content, review_type, context)
                review_result["file_path"] = file_path
                results.append(review_result)
                
            except Exception as e:
                logger.error(f"Error reviewing file {file_path}: {str(e)}")
                results.append({
                    "file_path": file_path,
                    "status": "error",
                    "error": str(e)
                })
        
        return results
    
    def generate_review_report(
        self,
        review_results: List[Dict[str, Any]],
        output_format: str = "markdown"
    ) -> str:
        """
        Generate a formatted review report.
        
        Args:
            review_results: List of review results
            output_format: Output format ('markdown', 'html', 'text')
            
        Returns:
            Formatted report as string
        """
        if output_format == "markdown":
            return self._generate_markdown_report(review_results)
        elif output_format == "html":
            return self._generate_html_report(review_results)
        else:
            return self._generate_text_report(review_results)
    
    def _generate_markdown_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate markdown report."""
        report = "# 🤖 AI Code Review Report\n\n"
        report += f"**Generated by CI Code Companion**\n\n"
        
        # Summary
        total_files = len(results)
        total_issues = sum(len(r.get('issues', [])) for r in results)
        total_recommendations = sum(len(r.get('recommendations', [])) for r in results)
        
        report += f"## 📊 Summary\n\n"
        report += f"- **Files Reviewed:** {total_files}\n"
        report += f"- **Total Issues Found:** {total_issues}\n"
        report += f"- **Total Recommendations:** {total_recommendations}\n\n"
        
        # Individual file results
        for result in results:
            if result.get('status') == 'error':
                report += f"## ❌ {result.get('file_path', 'Unknown File')}\n\n"
                report += f"**Error:** {result.get('error', 'Unknown error')}\n\n"
                continue
            
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠', 
                'medium': '🟡',
                'low': '🔵',
                'info': '⚪'
            }.get(result.get('severity', 'info'), '⚪')
            
            report += f"## {severity_emoji} {result.get('file_path', 'Unknown File')}\n\n"
            
            if result.get('summary'):
                report += f"**Summary:** {result['summary']}\n\n"
            
            if result.get('issues'):
                report += f"### ⚠️ Issues Found\n\n"
                for issue in result['issues']:
                    report += f"- {issue}\n"
                report += "\n"
            
            if result.get('recommendations'):
                report += f"### 💡 Recommendations\n\n"
                for rec in result['recommendations']:
                    report += f"- {rec}\n"
                report += "\n"
            
            if result.get('positive_aspects'):
                report += f"### ✅ Positive Aspects\n\n"
                for pos in result['positive_aspects']:
                    report += f"- {pos}\n"
                report += "\n"
        
        return report
    
    def _generate_html_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate HTML report."""
        # Basic HTML implementation
        html = "<h1>🤖 AI Code Review Report</h1>"
        html += "<p><strong>Generated by CI Code Companion</strong></p>"
        
        for result in results:
            html += f"<h2>{result.get('file_path', 'Unknown File')}</h2>"
            if result.get('summary'):
                html += f"<p><strong>Summary:</strong> {result['summary']}</p>"
            # Add more HTML formatting as needed
        
        return html
    
    def _generate_text_report(self, results: List[Dict[str, Any]]) -> str:
        """Generate plain text report."""
        report = "AI Code Review Report\n"
        report += "=" * 50 + "\n\n"
        
        for result in results:
            report += f"File: {result.get('file_path', 'Unknown File')}\n"
            report += "-" * 40 + "\n"
            
            if result.get('summary'):
                report += f"Summary: {result['summary']}\n\n"
            
            # Add more text formatting as needed
        
        return report
    
    def review_code_content(
        self,
        code_content: str,
        file_path: str,
        review_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Review a string of code content.

        Args:
            code_content: The code content as a string.
            file_path: The original path of the file for context.
            review_type: Type of review to perform ('comprehensive', 'security', 'performance').

        Returns:
            Dictionary containing review results for the content.
        """
        try:
            # Create a pseudo-diff for the entire content
            # This allows reusing the diff-based review logic
            diff_lines = []
            for i, line in enumerate(code_content.splitlines(), 1):
                diff_lines.append(f"+{line}") # Treat all lines as added
            
            # Ensure there's a newline at the end of each line for diff format
            pseudo_diff_content = f"--- a/{file_path}\n+++ b/{file_path}\n" + "\n".join(diff_lines) + "\n"

            context = {
                "file_path": file_path,
                "review_mode": "full_content"
            }
            
            # Call the existing review_code_diff method
            review_result = self.review_code_diff(pseudo_diff_content, review_type, context)
            review_result["file_path"] = file_path # Ensure file_path is in the final result
            return review_result
            
        except Exception as e:
            logger.error(f"Error reviewing code content for {file_path}: {str(e)}")
            return {
                "file_path": file_path,
                "status": "error",
                "error": str(e),
                "recommendations": [],
                "severity": "unknown"
            } 