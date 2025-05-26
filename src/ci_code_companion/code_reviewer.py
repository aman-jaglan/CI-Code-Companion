"""
Code Reviewer for CI Code Companion

This module handles AI-powered code review and analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from .vertex_ai_client import VertexAIClient
import json

logger = logging.getLogger(__name__)


class CodeReviewer:
    """Provides AI-powered code review capabilities."""
    
    def __init__(self, vertex_ai_client: VertexAIClient):
        """
        Initialize the code reviewer.
        
        Args:
            vertex_ai_client: Initialized Vertex AI client
        """
        self.ai_client = vertex_ai_client
        
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
        """Perform comprehensive code review."""
        # Include context info in the prompt
        prompt = self._get_review_prompt(diff_content, f"diff_content{context_info}")
        
        return self.ai_client.analyze_code(prompt, "review")
    
    def _security_review(self, diff_content: str, context_info: str) -> str:
        """Perform security-focused code review."""
        prompt = f"""
Please perform a security-focused review of the following git diff.

{context_info}

Git Diff:
```diff
{diff_content}
```

Focus specifically on security vulnerabilities and risks:

1. **Input Validation**:
   - Are user inputs properly validated and sanitized?
   - SQL injection vulnerabilities
   - XSS vulnerabilities
   - Command injection risks

2. **Authentication & Authorization**:
   - Proper access controls
   - Session management
   - Permission checks

3. **Data Protection**:
   - Sensitive data exposure
   - Encryption of sensitive data
   - Proper handling of credentials

4. **Configuration Security**:
   - Hardcoded secrets or passwords
   - Insecure default configurations
   - Environment variable usage

5. **Dependencies**:
   - Known vulnerable dependencies
   - Insecure library usage

Please format your response as:

## Security Assessment
[Overall security posture of the changes]

## Vulnerabilities Found
[List specific security issues with CRITICAL/HIGH/MEDIUM/LOW severity]

## Security Recommendations
[Specific security improvements]

## Compliance Notes
[Any regulatory or compliance considerations]
"""
        
        return self.ai_client.analyze_code(diff_content, "security")
    
    def _performance_review(self, diff_content: str, context_info: str) -> str:
        """Perform performance-focused code review."""
        prompt = f"""
Please perform a performance-focused review of the following git diff.

{context_info}

Git Diff:
```diff
{diff_content}
```

Focus specifically on performance implications:

1. **Algorithmic Complexity**:
   - Time complexity analysis
   - Space complexity considerations
   - Algorithm efficiency

2. **Resource Usage**:
   - Memory leaks
   - Resource cleanup
   - Connection management

3. **Database Performance**:
   - Query optimization
   - Index usage
   - N+1 query problems

4. **Caching**:
   - Caching opportunities
   - Cache invalidation
   - Memory caching strategies

5. **Scalability**:
   - Bottleneck identification
   - Concurrent access handling
   - Load handling capabilities

Please format your response as:

## Performance Assessment
[Overall performance impact of the changes]

## Performance Issues
[List specific performance concerns with HIGH/MEDIUM/LOW impact]

## Optimization Recommendations
[Specific performance improvements]

## Scalability Notes
[Considerations for scale]
"""
        
        return self.ai_client.analyze_code(diff_content, "performance")
    
    def _parse_review_response(self, ai_response: str, review_type: str) -> Dict[str, Any]:
        """
        Parse AI review response into structured format.
        The AI is expected to return blocks of:
        ISSUE: [description]
        LINE: [line_number]
        OLD: [old_code_line_or_empty]
        NEW: [new_code_line_or_multiline_block]
        WHY: [explanation]
        Separated by blank lines if multiple issues.
        Or "NO_ISSUES: ..." if no issues.
        """
        logger.debug(f"Raw AI response to parse:\n{ai_response}")
        result = {
            "review_type": review_type,
            "issues": [],
            "suggested_changes": [],
            "explanation": "", # General explanation if any, specific WHYs go into issues
            "severity": "info"
        }

        if ai_response.strip().startswith("NO_ISSUES:"):
            result["explanation"] = ai_response.strip().split(':', 1)[1].strip()
            logger.info("AI reported no issues.")
            return result

        # Split the response into potential blocks of issues based on double newlines or "ISSUE:"
        # This handles cases where blank lines might be missing but "ISSUE:" starts a new block.
        blocks = ai_response.strip().split('\n\n') # Split by blank lines first
        
        issues_found = []
        current_issue_block = []
        
        # Re-process blocks to handle cases where ISSUE: might not be separated by double newline
        processed_blocks = []
        for block_text in blocks:
            parts = block_text.split("ISSUE:")
            if parts[0].strip() == "" and len(parts) > 1: # Starts with ISSUE:
                processed_blocks.append("ISSUE:" + parts[1])
            elif len(parts) > 1 : # ISSUE: is in the middle of a block
                if parts[0].strip() != "": processed_blocks.append(parts[0].strip())
                processed_blocks.append("ISSUE:" + parts[1])
            else:
                processed_blocks.append(block_text)

        for block_text in processed_blocks:
            if not block_text.strip().startswith("ISSUE:"):
                continue

            lines = block_text.strip().split('\n')
            issue_data = {}
            
            # Use a state machine or simply iterate and look for keywords
            # to make parsing robust to slight variations if AI doesn't strictly follow format.
            for i, line in enumerate(lines):
                if line.startswith("ISSUE:"):
                    issue_data['description'] = line.split(':', 1)[1].strip()
                elif line.startswith("LINE:"):
                    try:
                        issue_data['line_number'] = int(line.split(':', 1)[1].strip())
                    except ValueError:
                        logger.warning(f"Could not parse line number from: {line}")
                        issue_data['line_number'] = None 
                elif line.startswith("OLD:"):
                    issue_data['old_content'] = line.split(':', 1)[1].strip()
                elif line.startswith("NEW:"):
                    # Handle potential multi-line NEW content
                    new_content_lines = [line.split(':', 1)[1].strip()]
                    # Check subsequent lines if they are part of NEW block (not starting with another keyword)
                    for j in range(i + 1, len(lines)):
                        if not any(lines[j].startswith(k) for k in ["ISSUE:", "LINE:", "OLD:", "WHY:"]):
                            new_content_lines.append(lines[j])
                        else:
                            break
                    issue_data['new_content'] = "\n".join(new_content_lines)
                elif line.startswith("WHY:"):
                    issue_data['why'] = line.split(':', 1)[1].strip()
            
            if issue_data.get('description') and issue_data.get('new_content') is not None and issue_data.get('line_number') is not None:
                result["issues"].append(issue_data['description'] + (f" (Reason: {issue_data['why']}") if issue_data.get('why') else '')
                result["suggested_changes"].append({
                    "line_number": issue_data['line_number'],
                    "old_content": issue_data.get('old_content', ''), # Default to empty string if not present
                    "new_content": issue_data['new_content'],
                    "description": issue_data['description'],
                    "explanation": issue_data.get('why', '')
                })
            elif issue_data: # Log if we parsed something but it was incomplete for a change
                logger.warning(f"Parsed incomplete issue block: {issue_data} from block: \n{block_text}")

        if result["issues"]:
            result["severity"] = "medium" # Default severity if issues are found
            if any("critical" in issue.lower() or "severe" in issue.lower() or "error" in issue.lower() for issue in result["issues"]):
                result["severity"] = "high"
        
        logger.debug(f"Parsed AI response: {json.dumps(result, indent=2)}")
        return result
    
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
    
    def _get_review_prompt(self, code, file_path):
        """Generate a comprehensive code review prompt."""
        # Define the suggestion format template separately to avoid f-string issues
        suggestion_format = '''{
    "issue_description": "Clear description of the issue",
    "line_number": "Line number where the issue occurs",
    "old_content": "The exact problematic code with proper indentation",
    "new_content": "The suggested fix with proper indentation",
    "explanation": "Detailed explanation of why this is an issue and how the fix helps",
    "impact": ["List", "of", "impacts"],
    "severity": "critical|high|medium|low",
    "category": "security|performance|reliability|maintainability|style"
}'''

        return f"""Please perform a thorough code review of the following code from {file_path}. 
    
Code to review:
```
{code}
```

Analyze the code for the following aspects and provide specific, actionable feedback:

1. Code Quality and Best Practices:
   - Identify any violations of coding standards or best practices
   - Check for code readability and maintainability issues
   - Look for opportunities to improve code organization
   - Verify proper error handling and logging
   - Check for proper use of comments and documentation

2. Security Issues:
   - Identify potential security vulnerabilities
   - Check for proper input validation
   - Verify secure handling of sensitive data
   - Look for authentication/authorization issues
   - Check for proper use of security-related functions

3. Performance Optimization:
   - Identify performance bottlenecks
   - Look for inefficient algorithms or data structures
   - Check for unnecessary computations or operations
   - Identify potential memory leaks
   - Suggest performance improvements

4. Code Structure and Design:
   - Evaluate class and function organization
   - Check for proper separation of concerns
   - Identify violations of SOLID principles
   - Look for opportunities to improve design patterns
   - Check for code duplication

5. Bug Detection:
   - Identify potential runtime errors
   - Look for edge cases that aren't handled
   - Check for off-by-one errors
   - Verify proper null/undefined checks
   - Identify potential race conditions

For each issue found, please provide:
1. A clear description of the issue
2. The exact location (line numbers) where the issue occurs
3. The problematic code snippet
4. A detailed explanation of why it's an issue
5. A specific, properly indented code suggestion to fix the issue
6. The expected impact of the fix

Format each suggestion exactly as follows:
{suggestion_format}

Additional requirements:
1. Maintain the exact same indentation level as the surrounding code
2. Ensure all code blocks are complete (no partial blocks)
3. Include necessary imports or dependencies
4. Consider the context of the entire file
5. Preserve the existing coding style
6. Ensure backward compatibility
7. Follow language-specific best practices

Please be thorough and specific in your review.""" 