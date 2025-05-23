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
Please perform a comprehensive code review of the following git diff.

{context_info}

Git Diff:
```diff
{diff_content}
```

Please analyze the code changes and provide feedback on:

1. **Code Quality**:
   - Adherence to coding standards and best practices
   - Code readability and maintainability
   - Proper error handling
   - Code organization and structure

2. **Potential Issues**:
   - Logic errors or bugs
   - Edge cases not handled
   - Potential runtime errors
   - Inconsistencies with existing code

3. **Security Considerations**:
   - Input validation
   - Authentication/authorization issues
   - Data exposure risks
   - Injection vulnerabilities

4. **Performance**:
   - Algorithmic efficiency
   - Memory usage considerations
   - Database query optimization
   - Resource management

5. **Testing**:
   - Are tests needed for these changes?
   - Are existing tests affected?
   - Test coverage considerations

Please format your response as:

## Summary
[Brief overview of the changes and overall assessment]

## Issues Found
[List any problems, bugs, or concerns - use CRITICAL/HIGH/MEDIUM/LOW severity]

## Recommendations
[Specific suggestions for improvement]

## Positive Aspects
[What was done well in this code]

If no issues are found, please state that clearly.
"""
        
        return self.ai_client.analyze_code(diff_content, "review", prompt)
    
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
        
        return self.ai_client.analyze_code(diff_content, "security", prompt)
    
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
        
        return self.ai_client.analyze_code(diff_content, "performance", prompt)
    
    def _parse_review_response(self, ai_response: str, review_type: str) -> Dict[str, Any]:
        """
        Parse AI review response into structured format.
        
        Args:
            ai_response: Raw AI response
            review_type: Type of review performed
            
        Returns:
            Structured review results
        """
        try:
            # Basic parsing - in a real implementation, this would be more sophisticated
            lines = ai_response.split('\n')
            
            result = {
                "review_type": review_type,
                "summary": "",
                "issues": [],
                "recommendations": [],
                "positive_aspects": [],
                "severity": "info",
                "raw_response": ai_response
            }
            
            current_section = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                
                # Detect section headers
                if line.startswith('## Summary') or line.startswith('# Summary'):
                    current_section = 'summary'
                    current_content = []
                elif line.startswith('## Issues') or line.startswith('# Issues'):
                    current_section = 'issues'
                    current_content = []
                elif line.startswith('## Recommendations') or line.startswith('# Recommendations'):
                    current_section = 'recommendations'
                    current_content = []
                elif line.startswith('## Positive') or line.startswith('# Positive'):
                    current_section = 'positive_aspects'
                    current_content = []
                elif line.startswith('##') or line.startswith('#'):
                    # Other section, continue collecting
                    if current_content:
                        self._add_section_content(result, current_section, current_content)
                    current_section = 'other'
                    current_content = []
                else:
                    if line and current_section:
                        current_content.append(line)
            
            # Add final section
            if current_content and current_section:
                self._add_section_content(result, current_section, current_content)
            
            # Determine overall severity
            result["severity"] = self._determine_severity(ai_response)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing review response: {str(e)}")
            return {
                "review_type": review_type,
                "summary": "Error parsing review response",
                "issues": [],
                "recommendations": [],
                "positive_aspects": [],
                "severity": "error",
                "raw_response": ai_response,
                "parse_error": str(e)
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