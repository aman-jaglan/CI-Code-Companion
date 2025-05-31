"""
GitLab Client

This module provides GitLab API integration functionality for the CI Code Companion SDK,
including project management, merge request operations, and CI/CD pipeline integration.
"""

import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
import time


class GitLabClient:
    """
    Client for GitLab API operations.
    Provides methods for interacting with GitLab projects, merge requests, and CI/CD pipelines.
    """
    
    def __init__(self, url: str, token: str, logger: Optional[logging.Logger] = None):
        """
        Initialize GitLab client.
        
        Args:
            url: GitLab instance URL
            token: GitLab access token
            logger: Logger instance for client operations
        """
        self.url = url.rstrip('/')
        self.token = token
        self.logger = logger or logging.getLogger(__name__)
        
        # API configuration
        self.api_base = f"{self.url}/api/v4"
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Rate limiting
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test GitLab connection and authentication."""
        try:
            response = self._make_request('GET', '/user')
            if response and response.get('id'):
                self.logger.info(f"Connected to GitLab as user: {response.get('username', 'unknown')}")
            else:
                self.logger.warning("GitLab connection test failed")
        except Exception as e:
            self.logger.error(f"GitLab connection error: {e}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make authenticated request to GitLab API with rate limiting.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            Response data or None if request failed
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        url = urljoin(self.api_base, endpoint.lstrip('/'))
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 204:
                return {}
            else:
                self.logger.error(f"GitLab API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"GitLab API request failed: {e}")
            return None
    
    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get project information.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            Project information dictionary
        """
        return self._make_request('GET', f'/projects/{project_id}')
    
    def get_project_by_path(self, project_path: str) -> Optional[Dict[str, Any]]:
        """
        Get project information by namespace/project path.
        
        Args:
            project_path: Project path (namespace/project-name)
            
        Returns:
            Project information dictionary
        """
        # URL encode the project path
        encoded_path = project_path.replace('/', '%2F')
        return self._make_request('GET', f'/projects/{encoded_path}')
    
    def get_merge_requests(
        self,
        project_id: int,
        state: str = 'opened',
        target_branch: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get merge requests for a project.
        
        Args:
            project_id: GitLab project ID
            state: MR state (opened, closed, merged)
            target_branch: Filter by target branch
            
        Returns:
            List of merge request dictionaries
        """
        params = {'state': state}
        if target_branch:
            params['target_branch'] = target_branch
        
        response = self._make_request('GET', f'/projects/{project_id}/merge_requests', params=params)
        return response if isinstance(response, list) else []
    
    def get_merge_request(self, project_id: int, mr_iid: int) -> Optional[Dict[str, Any]]:
        """
        Get specific merge request information.
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request internal ID
            
        Returns:
            Merge request information dictionary
        """
        return self._make_request('GET', f'/projects/{project_id}/merge_requests/{mr_iid}')
    
    def get_merge_request_changes(self, project_id: int, mr_iid: int) -> Optional[Dict[str, Any]]:
        """
        Get merge request file changes.
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request internal ID
            
        Returns:
            Merge request changes information
        """
        return self._make_request('GET', f'/projects/{project_id}/merge_requests/{mr_iid}/changes')
    
    def create_merge_request_note(
        self,
        project_id: int,
        mr_iid: int,
        body: str,
        position: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a note (comment) on a merge request.
        
        Args:
            project_id: GitLab project ID
            mr_iid: Merge request internal ID
            body: Comment body
            position: Position info for inline comments
            
        Returns:
            Created note information
        """
        data = {'body': body}
        if position:
            data['position'] = position
        
        return self._make_request('POST', f'/projects/{project_id}/merge_requests/{mr_iid}/notes', data=data)
    
    def get_file_content(
        self,
        project_id: int,
        file_path: str,
        ref: str = 'main'
    ) -> Optional[str]:
        """
        Get file content from repository.
        
        Args:
            project_id: GitLab project ID
            file_path: Path to the file
            ref: Branch or commit reference
            
        Returns:
            File content as string or None
        """
        # URL encode the file path
        encoded_path = file_path.replace('/', '%2F')
        params = {'ref': ref}
        
        response = self._make_request('GET', f'/projects/{project_id}/repository/files/{encoded_path}', params=params)
        
        if response and 'content' in response:
            import base64
            try:
                return base64.b64decode(response['content']).decode('utf-8')
            except Exception as e:
                self.logger.error(f"Failed to decode file content: {e}")
                return None
        
        return None
    
    def get_pipelines(self, project_id: int, status: str = None) -> List[Dict[str, Any]]:
        """
        Get CI/CD pipelines for a project.
        
        Args:
            project_id: GitLab project ID
            status: Filter by pipeline status
            
        Returns:
            List of pipeline dictionaries
        """
        params = {}
        if status:
            params['status'] = status
        
        response = self._make_request('GET', f'/projects/{project_id}/pipelines', params=params)
        return response if isinstance(response, list) else []
    
    def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> List[Dict[str, Any]]:
        """
        Get jobs for a specific pipeline.
        
        Args:
            project_id: GitLab project ID
            pipeline_id: Pipeline ID
            
        Returns:
            List of job dictionaries
        """
        response = self._make_request('GET', f'/projects/{project_id}/pipelines/{pipeline_id}/jobs')
        return response if isinstance(response, list) else []
    
    def get_job_artifacts(self, project_id: int, job_id: int) -> Optional[bytes]:
        """
        Download job artifacts.
        
        Args:
            project_id: GitLab project ID
            job_id: Job ID
            
        Returns:
            Artifacts as bytes or None
        """
        url = f"{self.api_base}/projects/{project_id}/jobs/{job_id}/artifacts"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.content
            else:
                self.logger.error(f"Failed to download artifacts: {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Artifacts download failed: {e}")
            return None
    
    def create_branch(
        self,
        project_id: int,
        branch_name: str,
        ref: str = 'main'
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new branch.
        
        Args:
            project_id: GitLab project ID
            branch_name: Name of the new branch
            ref: Reference to create branch from
            
        Returns:
            Created branch information
        """
        data = {
            'branch': branch_name,
            'ref': ref
        }
        
        return self._make_request('POST', f'/projects/{project_id}/repository/branches', data=data)
    
    def delete_branch(self, project_id: int, branch_name: str) -> bool:
        """
        Delete a branch.
        
        Args:
            project_id: GitLab project ID
            branch_name: Name of the branch to delete
            
        Returns:
            True if branch was deleted successfully
        """
        response = self._make_request('DELETE', f'/projects/{project_id}/repository/branches/{branch_name}')
        return response is not None
    
    def get_commits(
        self,
        project_id: int,
        ref_name: str = None,
        since: str = None,
        until: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get commit history.
        
        Args:
            project_id: GitLab project ID
            ref_name: Branch or tag name
            since: Start date (ISO format)
            until: End date (ISO format)
            
        Returns:
            List of commit dictionaries
        """
        params = {}
        if ref_name:
            params['ref_name'] = ref_name
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        response = self._make_request('GET', f'/projects/{project_id}/repository/commits', params=params)
        return response if isinstance(response, list) else []
    
    def get_commit_diff(self, project_id: int, sha: str) -> List[Dict[str, Any]]:
        """
        Get commit diff information.
        
        Args:
            project_id: GitLab project ID
            sha: Commit SHA
            
        Returns:
            List of diff dictionaries
        """
        response = self._make_request('GET', f'/projects/{project_id}/repository/commits/{sha}/diff')
        return response if isinstance(response, list) else []
    
    def trigger_pipeline(
        self,
        project_id: int,
        ref: str,
        variables: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Trigger a new pipeline.
        
        Args:
            project_id: GitLab project ID
            ref: Branch or tag to run pipeline on
            variables: Pipeline variables
            
        Returns:
            Pipeline information if successful
        """
        data = {'ref': ref}
        if variables:
            data['variables'] = [{'key': k, 'value': v} for k, v in variables.items()]
        
        return self._make_request('POST', f'/projects/{project_id}/pipeline', data=data)
    
    def get_project_members(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get project members.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            List of member dictionaries
        """
        response = self._make_request('GET', f'/projects/{project_id}/members')
        return response if isinstance(response, list) else []
    
    def search_projects(self, search: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for projects.
        
        Args:
            search: Search query
            limit: Maximum number of results
            
        Returns:
            List of project dictionaries
        """
        params = {
            'search': search,
            'per_page': limit
        }
        
        response = self._make_request('GET', '/projects', params=params)
        return response if isinstance(response, list) else []
    
    def get_project_variables(self, project_id: int) -> List[Dict[str, Any]]:
        """
        Get project CI/CD variables.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            List of variable dictionaries
        """
        response = self._make_request('GET', f'/projects/{project_id}/variables')
        return response if isinstance(response, list) else []
    
    def create_project_variable(
        self,
        project_id: int,
        key: str,
        value: str,
        protected: bool = False,
        masked: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Create a project CI/CD variable.
        
        Args:
            project_id: GitLab project ID
            key: Variable key
            value: Variable value
            protected: Whether variable is protected
            masked: Whether variable is masked
            
        Returns:
            Created variable information
        """
        data = {
            'key': key,
            'value': value,
            'protected': protected,
            'masked': masked
        }
        
        return self._make_request('POST', f'/projects/{project_id}/variables', data=data)
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get current user information.
        
        Returns:
            User information dictionary
        """
        return self._make_request('GET', '/user')
    
    def is_authenticated(self) -> bool:
        """
        Check if client is properly authenticated.
        
        Returns:
            True if authenticated
        """
        user_info = self.get_user_info()
        return user_info is not None and 'id' in user_info 