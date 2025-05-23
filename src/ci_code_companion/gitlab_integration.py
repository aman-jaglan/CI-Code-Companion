"""
GitLab Integration for CI Code Companion

This module handles integration with GitLab API and CI/CD workflows.
"""

import os
import logging
import git
from typing import Dict, List, Optional, Any
from pathlib import Path
import gitlab
import requests

logger = logging.getLogger(__name__)


class GitLabIntegration:
    """Handles GitLab API interactions and CI/CD automation."""
    
    def __init__(
        self,
        gitlab_url: str = "https://gitlab.com",
        access_token: Optional[str] = None,
        project_id: Optional[int] = None
    ):
        """
        Initialize GitLab integration.
        
        Args:
            gitlab_url: GitLab instance URL
            access_token: GitLab access token (or use CI_JOB_TOKEN)
            project_id: GitLab project ID
        """
        self.gitlab_url = gitlab_url
        self.access_token = access_token or os.getenv('CI_JOB_TOKEN') or os.getenv('GITLAB_ACCESS_TOKEN')
        self.project_id = project_id or os.getenv('CI_PROJECT_ID')
        
        if not self.access_token:
            raise ValueError("GitLab access token is required")
        
        # Initialize GitLab client
        self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.access_token)
        
        if self.project_id:
            self.project = self.gl.projects.get(self.project_id)
        else:
            self.project = None
            
        logger.info(f"Initialized GitLab integration for {gitlab_url}")
    
    def get_merge_request_diff(self, merge_request_iid: int) -> Dict[str, Any]:
        """
        Get diff content for a merge request.
        
        Args:
            merge_request_iid: Merge request internal ID
            
        Returns:
            Dictionary containing diff information
        """
        try:
            if not self.project:
                raise ValueError("Project not initialized")
            
            mr = self.project.mergerequests.get(merge_request_iid)
            
            # Get changes (files changed)
            changes = mr.changes()
            
            # Get diff content
            diff_content = ""
            for change in changes.get('changes', []):
                diff_content += f"--- a/{change['old_path']}\n"
                diff_content += f"+++ b/{change['new_path']}\n"
                diff_content += change.get('diff', '') + "\n"
            
            return {
                "merge_request_id": merge_request_iid,
                "title": mr.title,
                "description": mr.description,
                "author": mr.author,
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "diff_content": diff_content,
                "changes": changes.get('changes', []),
                "files_changed": len(changes.get('changes', [])),
                "lines_added": sum(c.get('lines_added', 0) for c in changes.get('changes', [])),
                "lines_removed": sum(c.get('lines_removed', 0) for c in changes.get('changes', []))
            }
            
        except Exception as e:
            logger.error(f"Error getting MR diff {merge_request_iid}: {str(e)}")
            raise
    
    def create_merge_request(
        self,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str,
        remove_source_branch: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new merge request.
        
        Args:
            source_branch: Source branch name
            target_branch: Target branch name  
            title: MR title
            description: MR description
            remove_source_branch: Whether to remove source branch after merge
            
        Returns:
            Created merge request information
        """
        try:
            if not self.project:
                raise ValueError("Project not initialized")
            
            mr_data = {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'title': title,
                'description': description,
                'remove_source_branch': remove_source_branch
            }
            
            mr = self.project.mergerequests.create(mr_data)
            
            return {
                "merge_request_id": mr.iid,
                "web_url": mr.web_url,
                "title": mr.title,
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch
            }
            
        except Exception as e:
            logger.error(f"Error creating merge request: {str(e)}")
            raise
    
    def add_merge_request_note(
        self,
        merge_request_iid: int,
        note_body: str,
        resolvable: bool = False
    ) -> Dict[str, Any]:
        """
        Add a note/comment to a merge request.
        
        Args:
            merge_request_iid: Merge request internal ID
            note_body: Comment content
            resolvable: Whether the note is resolvable
            
        Returns:
            Created note information
        """
        try:
            if not self.project:
                raise ValueError("Project not initialized")
            
            mr = self.project.mergerequests.get(merge_request_iid)
            
            note_data = {
                'body': note_body,
                'resolvable': resolvable
            }
            
            note = mr.notes.create(note_data)
            
            return {
                "note_id": note.id,
                "body": note.body,
                "author": note.author,
                "created_at": note.created_at
            }
            
        except Exception as e:
            logger.error(f"Error adding MR note {merge_request_iid}: {str(e)}")
            raise
    
    def get_changed_files(self, base_branch: str = "main") -> List[str]:
        """
        Get list of changed files in current branch compared to base.
        
        Args:
            base_branch: Base branch to compare against
            
        Returns:
            List of changed file paths
        """
        try:
            # Use git to get changed files
            repo = git.Repo('.')
            
            # Get current branch
            current_branch = repo.active_branch.name
            
            if current_branch == base_branch:
                # If we're on the base branch, get staged changes
                changed_files = [item.a_path for item in repo.index.diff("HEAD")]
            else:
                # Compare current branch with base branch
                diff = repo.git.diff(f'{base_branch}...HEAD', name_only=True)
                changed_files = diff.split('\n') if diff else []
            
            # Filter out empty strings
            changed_files = [f for f in changed_files if f.strip()]
            
            logger.info(f"Found {len(changed_files)} changed files")
            return changed_files
            
        except Exception as e:
            logger.error(f"Error getting changed files: {str(e)}")
            return []
    
    def create_branch(self, branch_name: str, ref: str = "main") -> bool:
        """
        Create a new branch.
        
        Args:
            branch_name: Name of the new branch
            ref: Reference to create branch from
            
        Returns:
            True if successful
        """
        try:
            if not self.project:
                raise ValueError("Project not initialized")
            
            branch_data = {
                'branch': branch_name,
                'ref': ref
            }
            
            self.project.branches.create(branch_data)
            logger.info(f"Created branch: {branch_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating branch {branch_name}: {str(e)}")
            return False
    
    def commit_files(
        self,
        branch_name: str,
        files: Dict[str, str],
        commit_message: str,
        author_email: str = "ci-code-companion@example.com",
        author_name: str = "CI Code Companion Bot"
    ) -> bool:
        """
        Commit files to a branch.
        
        Args:
            branch_name: Branch to commit to
            files: Dictionary of file_path -> content
            commit_message: Commit message
            author_email: Author email
            author_name: Author name
            
        Returns:
            True if successful
        """
        try:
            if not self.project:
                raise ValueError("Project not initialized")
            
            # Prepare commit actions
            actions = []
            for file_path, content in files.items():
                actions.append({
                    'action': 'create',  # or 'update' if file exists
                    'file_path': file_path,
                    'content': content
                })
            
            commit_data = {
                'branch': branch_name,
                'commit_message': commit_message,
                'actions': actions,
                'author_email': author_email,
                'author_name': author_name
            }
            
            commit = self.project.commits.create(commit_data)
            logger.info(f"Committed {len(files)} files to {branch_name}: {commit.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error committing files to {branch_name}: {str(e)}")
            return False
    
    def create_issue(
        self,
        title: str,
        description: str,
        labels: List[str] = None,
        assignee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new issue.
        
        Args:
            title: Issue title
            description: Issue description
            labels: List of labels
            assignee_id: Assignee user ID
            
        Returns:
            Created issue information
        """
        try:
            if not self.project:
                raise ValueError("Project not initialized")
            
            issue_data = {
                'title': title,
                'description': description
            }
            
            if labels:
                issue_data['labels'] = labels
            
            if assignee_id:
                issue_data['assignee_id'] = assignee_id
            
            issue = self.project.issues.create(issue_data)
            
            return {
                "issue_id": issue.iid,
                "web_url": issue.web_url,
                "title": issue.title
            }
            
        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            raise
    
    def get_ci_variables(self) -> Dict[str, str]:
        """
        Get relevant CI environment variables.
        
        Returns:
            Dictionary of CI variables
        """
        ci_vars = {}
        
        # Common GitLab CI variables
        var_names = [
            'CI_COMMIT_SHA',
            'CI_COMMIT_REF_NAME',
            'CI_COMMIT_BRANCH',
            'CI_MERGE_REQUEST_ID',
            'CI_MERGE_REQUEST_IID',
            'CI_MERGE_REQUEST_SOURCE_BRANCH_NAME',
            'CI_MERGE_REQUEST_TARGET_BRANCH_NAME',
            'CI_PROJECT_ID',
            'CI_PROJECT_NAME',
            'CI_PROJECT_PATH',
            'CI_PIPELINE_ID',
            'CI_JOB_ID',
            'GITLAB_USER_EMAIL',
            'GITLAB_USER_NAME'
        ]
        
        for var_name in var_names:
            value = os.getenv(var_name)
            if value:
                ci_vars[var_name] = value
        
        return ci_vars
    
    def is_merge_request_pipeline(self) -> bool:
        """
        Check if current pipeline is for a merge request.
        
        Returns:
            True if this is a merge request pipeline
        """
        return bool(os.getenv('CI_MERGE_REQUEST_ID'))
    
    def upload_job_artifact(
        self,
        file_path: str,
        artifact_name: str = "ai_generated_report"
    ) -> bool:
        """
        Upload a file as a job artifact.
        
        Args:
            file_path: Path to file to upload
            artifact_name: Name for the artifact
            
        Returns:
            True if successful
        """
        try:
            # In GitLab CI, artifacts are typically handled via the .gitlab-ci.yml
            # This is a placeholder for artifact upload logic
            logger.info(f"Artifact {artifact_name} ready at {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading artifact: {str(e)}")
            return False
    
    def format_mr_comment_for_review(
        self,
        review_results: List[Dict[str, Any]],
        review_type: str = "comprehensive"
    ) -> str:
        """
        Format review results as a GitLab MR comment.
        
        Args:
            review_results: List of review results
            review_type: Type of review performed
            
        Returns:
            Formatted comment content
        """
        comment = "## 🤖 AI Code Review Results\n\n"
        comment += f"**Review Type:** {review_type.title()}\n"
        comment += f"**Generated by:** CI Code Companion\n\n"
        
        # Summary
        total_files = len(review_results)
        total_issues = sum(len(r.get('issues', [])) for r in review_results)
        
        if total_issues == 0:
            comment += "✅ **Great news!** No significant issues found in this merge request.\n\n"
        else:
            comment += f"⚠️ **Found {total_issues} issue(s) across {total_files} file(s)**\n\n"
        
        # File-by-file results
        for result in review_results:
            if result.get('status') == 'error':
                continue
                
            file_path = result.get('file_path', 'Unknown File')
            severity = result.get('severity', 'info')
            
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡', 
                'low': '🔵',
                'info': '⚪'
            }.get(severity, '⚪')
            
            comment += f"### {severity_emoji} `{file_path}`\n\n"
            
            if result.get('summary'):
                comment += f"**Summary:** {result['summary']}\n\n"
            
            if result.get('issues'):
                comment += "**Issues:**\n"
                for issue in result['issues'][:3]:  # Limit to first 3 issues
                    comment += f"- {issue}\n"
                if len(result['issues']) > 3:
                    comment += f"- ... and {len(result['issues']) - 3} more\n"
                comment += "\n"
            
            if result.get('recommendations'):
                comment += "**Recommendations:**\n"
                for rec in result['recommendations'][:2]:  # Limit to first 2 recommendations
                    comment += f"- {rec}\n"
                if len(result['recommendations']) > 2:
                    comment += f"- ... and {len(result['recommendations']) - 2} more\n"
                comment += "\n"
        
        comment += "---\n"
        comment += "*This review was automatically generated by CI Code Companion using Google Cloud Vertex AI.*\n"
        
        return comment
    
    def create_ai_generated_mr(
        self,
        generated_files: Dict[str, str],
        source_branch_prefix: str = "ai-generated",
        target_branch: str = "main",
        mr_title_prefix: str = "🤖 AI Generated:"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a merge request with AI-generated files.
        
        Args:
            generated_files: Dictionary of file_path -> content
            source_branch_prefix: Prefix for the generated branch name
            target_branch: Target branch for the MR
            mr_title_prefix: Prefix for MR title
            
        Returns:
            Merge request information if successful
        """
        try:
            if not generated_files:
                logger.warning("No files to create MR for")
                return None
            
            # Create unique branch name
            import time
            timestamp = int(time.time())
            branch_name = f"{source_branch_prefix}-{timestamp}"
            
            # Create branch
            if not self.create_branch(branch_name, target_branch):
                return None
            
            # Commit files
            commit_message = f"Add AI-generated files\n\nGenerated by CI Code Companion:\n"
            for file_path in generated_files.keys():
                commit_message += f"- {file_path}\n"
            
            if not self.commit_files(branch_name, generated_files, commit_message):
                return None
            
            # Create MR
            file_types = set()
            for file_path in generated_files.keys():
                if 'test' in file_path.lower():
                    file_types.add('tests')
                elif file_path.endswith('.md'):
                    file_types.add('documentation')
                else:
                    file_types.add('code')
            
            file_type_str = ', '.join(file_types)
            mr_title = f"{mr_title_prefix} {file_type_str.title()}"
            
            mr_description = f"""
## 🤖 AI-Generated Content

This merge request contains files automatically generated by CI Code Companion using Google Cloud Vertex AI.

### Generated Files:
{chr(10).join(f'- `{path}`' for path in generated_files.keys())}

### What to Review:
1. **Correctness**: Verify the generated code is logically correct
2. **Test Coverage**: Ensure tests cover the intended functionality  
3. **Code Style**: Check if the code follows project conventions
4. **Dependencies**: Verify any new imports or dependencies are appropriate

### How This Was Generated:
- **AI Model**: Google Cloud Vertex AI (Codey)
- **Trigger**: Automated CI/CD pipeline
- **Context**: Based on recent code changes in the target branch

Please review and merge if the generated content meets your standards. You can make additional commits to this branch if adjustments are needed.

---
*Generated by CI Code Companion*
            """
            
            mr_info = self.create_merge_request(
                source_branch=branch_name,
                target_branch=target_branch,
                title=mr_title,
                description=mr_description.strip()
            )
            
            logger.info(f"Created AI-generated MR: {mr_info['web_url']}")
            return mr_info
            
        except Exception as e:
            logger.error(f"Error creating AI-generated MR: {str(e)}")
            return None 