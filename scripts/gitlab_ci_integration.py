#!/usr/bin/env python3
"""
GitLab CI Integration Script
Runs AI code analysis and posts results to GitLab merge requests
"""

import os
import json
import argparse
from pathlib import Path
import subprocess
import sys
from datetime import datetime

# Add the parent directory to sys.path to import our modules
sys.path.append(str(Path(__file__).parent.parent))

from src.vertex_ai_client import VertexAIClient
from src.code_reviewer import CodeReviewer
from src.test_generator import TestGenerator

class GitLabCIIntegration:
    def __init__(self):
        self.vertex_client = VertexAIClient()
        self.code_reviewer = CodeReviewer(self.vertex_client)
        self.test_generator = TestGenerator(self.vertex_client)
        
        # GitLab environment variables
        self.project_id = os.getenv('CI_PROJECT_ID')
        self.merge_request_iid = os.getenv('CI_MERGE_REQUEST_IID')
        self.commit_sha = os.getenv('CI_COMMIT_SHA')
        self.project_url = os.getenv('CI_PROJECT_URL')
        self.gitlab_token = os.getenv('GITLAB_ACCESS_TOKEN')
        
    def get_changed_files(self):
        """Get list of changed files in the current merge request."""
        try:
            # Get changed files using git diff
            result = subprocess.run([
                'git', 'diff', '--name-only', 
                'origin/main...HEAD'
            ], capture_output=True, text=True, check=True)
            
            changed_files = result.stdout.strip().split('\n')
            # Filter for Python files only
            python_files = [f for f in changed_files if f.endswith('.py')]
            
            print(f"Found {len(python_files)} changed Python files:")
            for file in python_files:
                print(f"  - {file}")
                
            return python_files
        except subprocess.CalledProcessError as e:
            print(f"Error getting changed files: {e}")
            return []
    
    def read_file_content(self, file_path):
        """Read content of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def run_ai_analysis(self, files):
        """Run AI analysis on the given files."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'commit_sha': self.commit_sha,
            'files_analyzed': [],
            'code_reviews': [],
            'security_issues': [],
            'generated_tests': [],
            'overall_scores': {
                'code_quality': 0,
                'security': 0,
                'test_coverage': 0
            }
        }
        
        total_quality_score = 0
        total_security_score = 0
        analyzed_files = 0
        
        for file_path in files:
            if not os.path.exists(file_path):
                continue
                
            print(f"\n🔍 Analyzing {file_path}...")
            content = self.read_file_content(file_path)
            if not content:
                continue
                
            # Code review
            try:
                review_result = self.code_reviewer.review_code(content, file_path)
                results['code_reviews'].append({
                    'file': file_path,
                    'result': review_result
                })
                
                # Extract quality score (assume it's in the review result)
                quality_score = self.extract_quality_score(review_result)
                total_quality_score += quality_score
                
                # Security analysis
                security_result = self.code_reviewer.analyze_security(content, file_path)
                results['security_issues'].append({
                    'file': file_path,
                    'result': security_result
                })
                
                # Extract security score
                security_score = self.extract_security_score(security_result)
                total_security_score += security_score
                
                # Test generation
                test_result = self.test_generator.generate_tests(content, file_path)
                results['generated_tests'].append({
                    'file': file_path,
                    'result': test_result
                })
                
                results['files_analyzed'].append(file_path)
                analyzed_files += 1
                
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                continue
        
        # Calculate overall scores
        if analyzed_files > 0:
            results['overall_scores']['code_quality'] = round(total_quality_score / analyzed_files, 1)
            results['overall_scores']['security'] = round(total_security_score / analyzed_files, 1)
            results['overall_scores']['test_coverage'] = len(results['generated_tests'])
        
        return results
    
    def extract_quality_score(self, review_result):
        """Extract quality score from review result."""
        # This is a simplified implementation
        # In practice, you'd parse the AI response for actual scores
        if 'excellent' in review_result.lower():
            return 9.0
        elif 'good' in review_result.lower():
            return 8.0
        elif 'average' in review_result.lower():
            return 6.0
        else:
            return 7.0  # Default score
    
    def extract_security_score(self, security_result):
        """Extract security score from security analysis."""
        # Simplified implementation
        if 'critical' in security_result.lower():
            return 3.0
        elif 'high' in security_result.lower():
            return 5.0
        elif 'medium' in security_result.lower():
            return 7.0
        elif 'low' in security_result.lower():
            return 8.5
        else:
            return 9.0  # Default good score
    
    def format_mr_comment(self, results):
        """Format AI analysis results as GitLab MR comment."""
        comment = f"""
## 🤖 AI Code Companion Analysis

**Commit:** `{self.commit_sha[:8]}`  
**Analyzed:** {len(results['files_analyzed'])} files  
**Timestamp:** {results['timestamp']}

### 📊 Overall Scores
- **Code Quality:** {results['overall_scores']['code_quality']}/10
- **Security:** {results['overall_scores']['security']}/10  
- **Tests Generated:** {results['overall_scores']['test_coverage']}

### 📁 Files Analyzed
"""
        
        for file in results['files_analyzed']:
            comment += f"- `{file}`\n"
        
        # Add code review highlights
        comment += "\n### 🔍 Code Review Highlights\n"
        for review in results['code_reviews'][:3]:  # Show top 3
            comment += f"\n**{review['file']}:**\n"
            # Take first 200 chars of review
            review_text = review['result'][:200]
            if len(review['result']) > 200:
                review_text += "..."
            comment += f"```\n{review_text}\n```\n"
        
        # Add security issues
        security_count = len([s for s in results['security_issues'] if 'critical' in s['result'].lower() or 'high' in s['result'].lower()])
        if security_count > 0:
            comment += f"\n### 🔒 Security Issues Found: {security_count}\n"
            comment += "❗ **Please review security analysis in the detailed report.**\n"
        
        # Add generated tests info
        if results['generated_tests']:
            comment += f"\n### 🧪 Generated Tests: {len(results['generated_tests'])}\n"
            comment += "✅ **New test cases have been suggested to improve coverage.**\n"
        
        comment += f"\n---\n*💡 View detailed analysis at: {self.project_url}/-/jobs*"
        
        return comment
    
    def save_results(self, results):
        """Save analysis results to file."""
        os.makedirs('ai-reports', exist_ok=True)
        
        # Save JSON report
        with open('ai-reports/analysis-results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save HTML report
        html_report = self.generate_html_report(results)
        with open('ai-reports/analysis-report.html', 'w') as f:
            f.write(html_report)
        
        print("📊 Reports saved to ai-reports/ directory")
    
    def generate_html_report(self, results):
        """Generate HTML report from results."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Code Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; }}
        .score {{ display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 8px; }}
        .file-section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; background: #f8f9fa; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Code Analysis Report</h1>
        <p><strong>Commit:</strong> {results['commit_sha']}</p>
        <p><strong>Analyzed:</strong> {results['timestamp']}</p>
        <p><strong>Files:</strong> {len(results['files_analyzed'])}</p>
    </div>
    
    <h2>📊 Overall Scores</h2>
    <div class="score">Code Quality: {results['overall_scores']['code_quality']}/10</div>
    <div class="score">Security: {results['overall_scores']['security']}/10</div>
    <div class="score">Tests Generated: {results['overall_scores']['test_coverage']}</div>
    
    <h2>📁 Analyzed Files</h2>
"""
        
        for i, review in enumerate(results['code_reviews']):
            html += f"""
    <div class="file-section">
        <h3>{review['file']}</h3>
        <h4>Code Review:</h4>
        <pre>{review['result']}</pre>
        
        <h4>Security Analysis:</h4>
        <pre>{results['security_issues'][i]['result'] if i < len(results['security_issues']) else 'No security issues found'}</pre>
        
        <h4>Generated Tests:</h4>
        <pre>{results['generated_tests'][i]['result'] if i < len(results['generated_tests']) else 'No tests generated'}</pre>
    </div>
"""
        
        html += """
</body>
</html>
"""
        return html
    
    def post_mr_comment(self, comment):
        """Post comment to GitLab merge request."""
        if not self.merge_request_iid or not self.gitlab_token:
            print("⚠️  No merge request context or GitLab token - skipping MR comment")
            return
        
        print("💬 Posting AI analysis comment to merge request...")
        # In a real implementation, you'd use GitLab API here
        print("Comment preview:")
        print("=" * 50)
        print(comment)
        print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description='Run AI code analysis for GitLab CI')
    parser.add_argument('--files', nargs='*', help='Specific files to analyze')
    parser.add_argument('--skip-mr-comment', action='store_true', help='Skip posting MR comment')
    
    args = parser.parse_args()
    
    print("🚀 Starting AI Code Companion Analysis...")
    
    integration = GitLabCIIntegration()
    
    # Get files to analyze
    if args.files:
        files_to_analyze = args.files
    else:
        files_to_analyze = integration.get_changed_files()
    
    if not files_to_analyze:
        print("ℹ️  No Python files to analyze")
        return 0
    
    # Run AI analysis
    try:
        results = integration.run_ai_analysis(files_to_analyze)
        
        # Save results
        integration.save_results(results)
        
        # Post MR comment if requested
        if not args.skip_mr_comment:
            comment = integration.format_mr_comment(results)
            integration.post_mr_comment(comment)
        
        # Set exit code based on quality scores
        min_quality = results['overall_scores']['code_quality']
        min_security = results['overall_scores']['security']
        
        if min_quality < 6.0 or min_security < 6.0:
            print("❌ Code quality or security score below threshold")
            return 1
        
        print("✅ AI analysis completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Error during AI analysis: {e}")
        return 1

if __name__ == '__main__':
    exit(main()) 