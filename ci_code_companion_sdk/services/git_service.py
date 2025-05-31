"""
Git Service

This module provides Git integration functionality for the CI Code Companion SDK,
including repository management, branch operations, and GitLab integration.
"""

import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging


class GitService:
    """
    Service for Git operations and repository management.
    Provides methods for cloning, analyzing, and interacting with Git repositories.
    """
    
    def __init__(self, gitlab_client=None, logger: Optional[logging.Logger] = None):
        """
        Initialize Git service with optional GitLab integration.
        
        Args:
            gitlab_client: GitLab client for API operations
            logger: Logger instance for service operations
        """
        self.gitlab_client = gitlab_client
        self.logger = logger or logging.getLogger(__name__)
        
    def is_git_repository(self, path: str) -> bool:
        """
        Check if the given path is a Git repository.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a Git repository
        """
        try:
            git_dir = Path(path) / '.git'
            return git_dir.exists()
        except Exception:
            return False
    
    def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """
        Get comprehensive repository information.
        
        Args:
            repo_path: Path to the Git repository
            
        Returns:
            Dictionary containing repository information
        """
        if not self.is_git_repository(repo_path):
            raise ValueError(f"Path is not a Git repository: {repo_path}")
        
        info = {
            'path': repo_path,
            'is_git_repo': True,
            'remote_url': None,
            'current_branch': None,
            'current_commit': None,
            'commit_count': 0,
            'last_commit_date': None,
            'author': None,
            'status': {},
            'branches': [],
            'tags': []
        }
        
        try:
            # Get remote URL
            result = self._run_git_command(['remote', 'get-url', 'origin'], repo_path)
            if result['success']:
                info['remote_url'] = result['output'].strip()
            
            # Get current branch
            result = self._run_git_command(['branch', '--show-current'], repo_path)
            if result['success']:
                info['current_branch'] = result['output'].strip()
            
            # Get current commit
            result = self._run_git_command(['rev-parse', 'HEAD'], repo_path)
            if result['success']:
                info['current_commit'] = result['output'].strip()
            
            # Get commit count
            result = self._run_git_command(['rev-list', '--count', 'HEAD'], repo_path)
            if result['success']:
                info['commit_count'] = int(result['output'].strip())
            
            # Get last commit info
            result = self._run_git_command([
                'log', '-1', '--format=%ad|%an|%ae|%s', '--date=iso'
            ], repo_path)
            if result['success']:
                parts = result['output'].strip().split('|')
                if len(parts) >= 4:
                    info['last_commit_date'] = parts[0]
                    info['author'] = {
                        'name': parts[1],
                        'email': parts[2],
                        'message': parts[3]
                    }
            
            # Get repository status
            info['status'] = self.get_repository_status(repo_path)
            
            # Get branches
            result = self._run_git_command(['branch', '-a'], repo_path)
            if result['success']:
                branches = []
                for line in result['output'].split('\n'):
                    line = line.strip()
                    if line and not line.startswith('*'):
                        branches.append(line.replace('remotes/origin/', ''))
                info['branches'] = list(set(branches))  # Remove duplicates
            
            # Get tags
            result = self._run_git_command(['tag', '--list'], repo_path)
            if result['success']:
                info['tags'] = [tag.strip() for tag in result['output'].split('\n') if tag.strip()]
            
        except Exception as e:
            self.logger.warning(f"Error getting repository info: {e}")
        
        return info
    
    def get_repository_status(self, repo_path: str) -> Dict[str, Any]:
        """
        Get the status of the Git repository.
        
        Args:
            repo_path: Path to the Git repository
            
        Returns:
            Dictionary containing status information
        """
        status = {
            'clean': True,
            'staged_files': [],
            'modified_files': [],
            'untracked_files': [],
            'deleted_files': []
        }
        
        try:
            result = self._run_git_command(['status', '--porcelain'], repo_path)
            if result['success']:
                for line in result['output'].split('\n'):
                    if not line.strip():
                        continue
                    
                    status_code = line[:2]
                    file_path = line[3:].strip()
                    
                    if status_code[0] in ['A', 'M', 'D']:
                        status['staged_files'].append(file_path)
                        status['clean'] = False
                    
                    if status_code[1] == 'M':
                        status['modified_files'].append(file_path)
                        status['clean'] = False
                    
                    if status_code == '??':
                        status['untracked_files'].append(file_path)
                        status['clean'] = False
                    
                    if status_code[1] == 'D':
                        status['deleted_files'].append(file_path)
                        status['clean'] = False
        
        except Exception as e:
            self.logger.warning(f"Error getting repository status: {e}")
        
        return status
    
    def get_file_history(self, repo_path: str, file_path: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the commit history for a specific file.
        
        Args:
            repo_path: Path to the Git repository
            file_path: Path to the file within the repository
            limit: Maximum number of commits to retrieve
            
        Returns:
            List of commit information dictionaries
        """
        history = []
        
        try:
            result = self._run_git_command([
                'log', '--follow', f'-{limit}',
                '--format=%H|%ad|%an|%ae|%s', '--date=iso',
                '--', file_path
            ], repo_path)
            
            if result['success']:
                for line in result['output'].split('\n'):
                    if not line.strip():
                        continue
                    
                    parts = line.strip().split('|')
                    if len(parts) >= 5:
                        history.append({
                            'commit_hash': parts[0],
                            'date': parts[1],
                            'author_name': parts[2],
                            'author_email': parts[3],
                            'message': '|'.join(parts[4:])  # In case message contains |
                        })
        
        except Exception as e:
            self.logger.warning(f"Error getting file history: {e}")
        
        return history
    
    def get_file_diff(self, repo_path: str, file_path: str, commit1: str = None, commit2: str = None) -> str:
        """
        Get the diff for a file between commits.
        
        Args:
            repo_path: Path to the Git repository
            file_path: Path to the file within the repository
            commit1: First commit (defaults to HEAD~1)
            commit2: Second commit (defaults to HEAD)
            
        Returns:
            Diff output as string
        """
        try:
            if not commit1:
                commit1 = 'HEAD~1'
            if not commit2:
                commit2 = 'HEAD'
            
            result = self._run_git_command([
                'diff', f'{commit1}..{commit2}', '--', file_path
            ], repo_path)
            
            return result['output'] if result['success'] else ""
        
        except Exception as e:
            self.logger.warning(f"Error getting file diff: {e}")
            return ""
    
    def get_changed_files(self, repo_path: str, base_branch: str = None, target_branch: str = None) -> List[str]:
        """
        Get list of files changed between branches or commits.
        
        Args:
            repo_path: Path to the Git repository
            base_branch: Base branch for comparison (defaults to main/master)
            target_branch: Target branch for comparison (defaults to current branch)
            
        Returns:
            List of changed file paths
        """
        changed_files = []
        
        try:
            if not base_branch:
                # Try to find main or master branch
                branches_result = self._run_git_command(['branch', '-r'], repo_path)
                if branches_result['success']:
                    if 'origin/main' in branches_result['output']:
                        base_branch = 'origin/main'
                    elif 'origin/master' in branches_result['output']:
                        base_branch = 'origin/master'
                    else:
                        base_branch = 'HEAD~1'
            
            if not target_branch:
                target_branch = 'HEAD'
            
            result = self._run_git_command([
                'diff', '--name-only', f'{base_branch}...{target_branch}'
            ], repo_path)
            
            if result['success']:
                changed_files = [f.strip() for f in result['output'].split('\n') if f.strip()]
        
        except Exception as e:
            self.logger.warning(f"Error getting changed files: {e}")
        
        return changed_files
    
    def clone_repository(self, repo_url: str, destination: str = None, branch: str = None) -> Dict[str, Any]:
        """
        Clone a Git repository to a local destination.
        
        Args:
            repo_url: URL of the repository to clone
            destination: Local destination path (temporary if not provided)
            branch: Specific branch to clone
            
        Returns:
            Dictionary containing clone operation results
        """
        if not destination:
            destination = tempfile.mkdtemp(prefix='ci_companion_clone_')
        
        clone_info = {
            'success': False,
            'destination': destination,
            'branch': branch,
            'error': None
        }
        
        try:
            clone_cmd = ['clone']
            if branch:
                clone_cmd.extend(['-b', branch])
            clone_cmd.extend([repo_url, destination])
            
            result = self._run_git_command(clone_cmd, cwd=None)
            
            if result['success']:
                clone_info['success'] = True
                clone_info.update(self.get_repository_info(destination))
            else:
                clone_info['error'] = result['error']
        
        except Exception as e:
            clone_info['error'] = str(e)
            self.logger.error(f"Error cloning repository: {e}")
        
        return clone_info
    
    def create_branch(self, repo_path: str, branch_name: str, from_branch: str = None) -> bool:
        """
        Create a new branch in the repository.
        
        Args:
            repo_path: Path to the Git repository
            branch_name: Name of the new branch
            from_branch: Source branch (defaults to current)
            
        Returns:
            True if branch was created successfully
        """
        try:
            cmd = ['checkout', '-b', branch_name]
            if from_branch:
                cmd.append(from_branch)
            
            result = self._run_git_command(cmd, repo_path)
            return result['success']
        
        except Exception as e:
            self.logger.error(f"Error creating branch: {e}")
            return False
    
    def switch_branch(self, repo_path: str, branch_name: str) -> bool:
        """
        Switch to a different branch.
        
        Args:
            repo_path: Path to the Git repository
            branch_name: Name of the branch to switch to
            
        Returns:
            True if switch was successful
        """
        try:
            result = self._run_git_command(['checkout', branch_name], repo_path)
            return result['success']
        
        except Exception as e:
            self.logger.error(f"Error switching branch: {e}")
            return False
    
    def commit_changes(self, repo_path: str, message: str, files: List[str] = None) -> bool:
        """
        Commit changes to the repository.
        
        Args:
            repo_path: Path to the Git repository
            message: Commit message
            files: List of files to commit (all staged files if not provided)
            
        Returns:
            True if commit was successful
        """
        try:
            # Add files if specified
            if files:
                for file_path in files:
                    result = self._run_git_command(['add', file_path], repo_path)
                    if not result['success']:
                        return False
            
            # Commit
            result = self._run_git_command(['commit', '-m', message], repo_path)
            return result['success']
        
        except Exception as e:
            self.logger.error(f"Error committing changes: {e}")
            return False
    
    def push_changes(self, repo_path: str, remote: str = 'origin', branch: str = None) -> bool:
        """
        Push changes to remote repository.
        
        Args:
            repo_path: Path to the Git repository
            remote: Remote name (default: origin)
            branch: Branch name (current branch if not provided)
            
        Returns:
            True if push was successful
        """
        try:
            cmd = ['push', remote]
            if branch:
                cmd.append(branch)
            
            result = self._run_git_command(cmd, repo_path)
            return result['success']
        
        except Exception as e:
            self.logger.error(f"Error pushing changes: {e}")
            return False
    
    def _run_git_command(self, command: List[str], repo_path: str = None, cwd: str = None) -> Dict[str, Any]:
        """
        Run a Git command and return the result.
        
        Args:
            command: Git command as list of arguments
            repo_path: Repository path (used as working directory)
            cwd: Custom working directory
            
        Returns:
            Dictionary containing command results
        """
        full_command = ['git'] + command
        working_dir = cwd or repo_path
        
        result = {
            'success': False,
            'output': '',
            'error': '',
            'command': ' '.join(full_command)
        }
        
        try:
            process = subprocess.run(
                full_command,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            result['output'] = process.stdout
            result['error'] = process.stderr
            result['success'] = process.returncode == 0
            
            if not result['success']:
                self.logger.warning(f"Git command failed: {result['command']}, Error: {result['error']}")
        
        except subprocess.TimeoutExpired:
            result['error'] = 'Command timed out'
            self.logger.error(f"Git command timed out: {result['command']}")
        except subprocess.CalledProcessError as e:
            result['error'] = str(e)
            self.logger.error(f"Git command error: {result['command']}, Error: {e}")
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Unexpected error running git command: {e}")
        
        return result
    
    def cleanup_temporary_repo(self, repo_path: str) -> bool:
        """
        Clean up a temporary repository directory.
        
        Args:
            repo_path: Path to the repository directory
            
        Returns:
            True if cleanup was successful
        """
        try:
            import shutil
            if os.path.exists(repo_path) and '/tmp/' in repo_path:
                shutil.rmtree(repo_path)
                return True
        except Exception as e:
            self.logger.error(f"Error cleaning up repository: {e}")
        
        return False
    
    def get_gitlab_project_info(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        Get GitLab project information using the GitLab client.
        
        Args:
            project_id: GitLab project ID
            
        Returns:
            Project information dictionary or None
        """
        if not self.gitlab_client:
            self.logger.warning("GitLab client not available")
            return None
        
        try:
            return self.gitlab_client.get_project(project_id)
        except Exception as e:
            self.logger.error(f"Error getting GitLab project info: {e}")
            return None 