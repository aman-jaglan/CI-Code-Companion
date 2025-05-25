"""
Code Reviewer for CI Code Companion

This module handles AI-powered code review and analysis.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from .vertex_ai_client import VertexAIClient

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
        prompt = f"""
Review the following code and identify any missing functionality, potential issues, or improvements needed.
Focus on completeness, correctness, and best practices.

{context_info}

Code to review:
```python
{diff_content}
```

Format your response exactly as follows:

ISSUE: [Describe each issue/missing functionality, one at a time]

```diff
[Show exact changes needed using - for lines to remove and + for lines to add]
```

WHY: [Brief explanation of why these changes are needed]

[Repeat ISSUE/diff/WHY blocks for each separate issue]

If no issues are found, respond with "NO_ISSUES: Code looks good, no changes needed."

Requirements for your review:
1. Check for missing methods/functionality in classes
2. Verify error handling is complete
3. Look for missing type hints
4. Check for missing docstrings
5. Identify any missing edge cases
6. Verify class/function interfaces are complete

Example format:
ISSUE: Missing peek() method in Stack class

```diff
 def pop(self):
     if not self.is_empty():
         return self.items.pop()
     raise IndexError("pop from empty stack")
+
+def peek(self):
+    if not self.is_empty():
+        return self.items[-1]
+    raise IndexError("peek at empty stack")
```

WHY: Stack class should have peek() method to examine top item without removing it. This is a standard stack operation.

[Next issue block if there are more issues...]"""
        
        return self.ai_client.analyze_code(diff_content, "review")
    
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
        
        Args:
            ai_response: Raw AI response
            review_type: Type of review performed
            
        Returns:
            Structured review results with GitHub-like diff changes
        """
        try:
            # Initialize result structure
            result = {
                "review_type": review_type,
                "issues": [],
                "suggested_changes": [],
                "explanation": "",
                "severity": "info"
            }
            
            # Split response into sections
            sections = ai_response.split('\n\n')
            current_section = None
            current_content = []
            
            # Extract issues and code changes
            for section in sections:
                if '```diff' in section or '```python' in section:
                    # Found code block with changes
                    lines = section.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('```'):
                            if line.startswith('+'):
                                result["suggested_changes"].append({
                                    "type": "add",
                                    "line": line[1:].strip()
                                })
                            elif line.startswith('-'):
                                result["suggested_changes"].append({
                                    "type": "remove",
                                    "line": line[1:].strip()
                                })
                            else:
                                result["suggested_changes"].append({
                                    "type": "context",
                                    "line": line
                                })
                elif section.lower().startswith(('issue:', 'problem:', 'bug:')):
                    # Found issue
                    result["issues"].append(section.split(':', 1)[1].strip())
                elif section.lower().startswith(('why:', 'explanation:', 'reason:')):
                    # Found explanation
                    result["explanation"] = section.split(':', 1)[1].strip()
            
            # Determine severity based on issues
            if result["issues"]:
                if any('critical' in issue.lower() or 'severe' in issue.lower() for issue in result["issues"]):
                    result["severity"] = "critical"
                elif any('security' in issue.lower() or 'vulnerability' in issue.lower() for issue in result["issues"]):
                    result["severity"] = "high"
                else:
                    result["severity"] = "medium"
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing review response: {str(e)}")
            return {
                "review_type": review_type,
                "issues": ["Error parsing review response: " + str(e)],
                "suggested_changes": [],
                "explanation": "Failed to parse AI response",
                "severity": "error"
            }
    
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