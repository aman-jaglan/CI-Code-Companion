"""
GitLab Integration Routes for CI Code Companion Dashboard
"""

from flask import Blueprint, request, redirect, url_for, jsonify, session, current_app
import gitlab
import requests
import logging
import os
from urllib.parse import quote
from config.gitlab_config import GitLabConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

gitlab_bp = Blueprint('gitlab', __name__)
gitlab_config = GitLabConfig()

@gitlab_bp.route('/gitlab/connect')
def connect_gitlab():
    """Start GitLab OAuth flow."""
    if not gitlab_config.is_configured:
        logger.error("GitLab integration not configured - missing credentials")
        return jsonify({'error': 'GitLab integration not configured'}), 500
    
    # Store state in session for security
    session['gitlab_state'] = os.urandom(16).hex()
    logger.debug("Current session data before OAuth: %s", dict(session))
    
    auth_url = gitlab_config.get_oauth_url()
    logger.info(f"Starting GitLab OAuth flow - redirecting to: {auth_url}")
    return redirect(auth_url)

@gitlab_bp.route('/gitlab/callback')
def gitlab_callback():
    """Handle GitLab OAuth callback."""
    logger.info("Received GitLab callback")
    logger.debug("Current session data at start of callback: %s", dict(session))
    logger.debug(f"Full callback URL: {request.url}")
    logger.debug(f"All request args: {request.args}")
    
    error = request.args.get('error')
    if error:
        logger.error(f"GitLab OAuth error: {error}")
        error_description = request.args.get('error_description', 'No description provided')
        return jsonify({'error': f'GitLab OAuth error: {error}', 'description': error_description}), 400
    
    code = request.args.get('code')
    if not code:
        logger.error("No authorization code received")
        return jsonify({'error': 'No authorization code received'}), 400
    
    # Exchange code for access token
    token_url = 'https://gitlab.com/oauth/token'
    
    # Ensure redirect URI is properly encoded
    redirect_uri = quote(gitlab_config.redirect_uri, safe='')
    
    data = {
        'client_id': gitlab_config.app_id,
        'client_secret': gitlab_config.app_secret,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': gitlab_config.redirect_uri
    }
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        logger.info("Exchanging authorization code for access token")
        response = requests.post(token_url, data=data, headers=headers)
        
        # Log detailed response information
        logger.debug(f"Token response status code: {response.status_code}")
        logger.debug(f"Token response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed. Status: {response.status_code}")
            logger.error(f"Error response: {response.text}")
            return jsonify({
                'error': 'Failed to get access token',
                'details': response.text,
                'status_code': response.status_code
            }), response.status_code
            
        token_data = response.json()
        if 'access_token' not in token_data:
            logger.error(f"No access token in response. Response data: {token_data}")
            return jsonify({'error': 'No access token in response'}), 400
            
        # Store the token in session
        session['gitlab_token'] = token_data['access_token']
        logger.info("Successfully obtained access token")
        
        # Verify the token works by getting user info
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=token_data['access_token'])
        try:
            gl.auth()
            # Get current user info
            current_user = gl.user
            logger.info(f"Successfully authenticated with GitLab API as user: {current_user.username}")
            return redirect(url_for('dashboard'))
        except gitlab.exceptions.GitlabAuthenticationError as e:
            logger.error(f"GitLab API authentication failed: {str(e)}")
            session.pop('gitlab_token', None)
            return jsonify({'error': 'GitLab API authentication failed', 'details': str(e)}), 401
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            session.pop('gitlab_token', None)
            return jsonify({'error': 'Failed to get user info', 'details': str(e)}), 500
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error during token exchange: {str(e)}")
        return jsonify({'error': 'Failed to exchange code for token', 'details': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@gitlab_bp.route('/gitlab/projects')
def list_projects():
    """List user's GitLab projects."""
    if 'gitlab_token' not in session:
        return jsonify({'error': 'Not authenticated with GitLab'}), 401
    
    try:
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        # Get current user's projects
        projects = gl.projects.list(owned=True, membership=True)
        return jsonify([{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'url': p.web_url,
            'default_branch': p.default_branch
        } for p in projects])
    except gitlab.exceptions.GitlabAuthenticationError as e:
        logger.error(f"GitLab API authentication failed: {str(e)}")
        session.pop('gitlab_token', None)
        return jsonify({'error': 'GitLab authentication failed', 'details': str(e)}), 401
    except Exception as e:
        logger.error(f"Error listing projects: {str(e)}")
        return jsonify({'error': str(e)}), 500

@gitlab_bp.route('/gitlab/webhook', methods=['POST'])
def gitlab_webhook():
    """Handle GitLab webhook events."""
    event = request.headers.get('X-Gitlab-Event')
    if not event:
        return jsonify({'error': 'No GitLab event header'}), 400
    
    data = request.json
    
    # Handle different event types
    if event == 'Push Hook':
        # Handle push event
        project_id = data['project']['id']
        commits = data['commits']
        branch = data['ref'].split('/')[-1]
        
        # Trigger analysis for each commit
        for commit in commits:
            analyze_commit(project_id, commit['id'], branch)
            
    elif event == 'Merge Request Hook':
        # Handle merge request event
        project_id = data['project']['id']
        mr_id = data['object_attributes']['iid']
        source_branch = data['object_attributes']['source_branch']
        
        # Analyze merge request changes
        analyze_merge_request(project_id, mr_id, source_branch)
    
    return jsonify({'status': 'success'})

def analyze_commit(project_id: int, commit_id: str, branch: str):
    """Analyze a specific commit."""
    # Import analysis modules
    from src.code_reviewer import CodeReviewer
    from src.test_generator import TestGenerator
    from src.vertex_ai_client import VertexAIClient
    
    # Initialize components
    ai_client = VertexAIClient()
    reviewer = CodeReviewer(ai_client)
    test_gen = TestGenerator(ai_client)
    
    # Perform analysis
    # This would be implemented based on your existing analysis logic
    pass

def analyze_merge_request(project_id: int, mr_id: int, source_branch: str):
    """Analyze a merge request."""
    # Similar to analyze_commit, but for merge requests
    pass

@gitlab_bp.route('/gitlab/repository/<int:project_id>/tree')
def get_repository_tree(project_id):
    """Get repository file tree structure."""
    if 'gitlab_token' not in session:
        return jsonify({'error': 'Not authenticated with GitLab'}), 401
    
    try:
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        
        project = gl.projects.get(project_id)
        branch = request.args.get('branch', project.default_branch)
        path = request.args.get('path', '')
        
        # Get repository tree
        items = project.repository_tree(ref=branch, path=path, get_all=True)
        
        tree_data = []
        for item in items:
            tree_data.append({
                'id': item['id'],
                'name': item['name'],
                'type': item['type'],  # 'tree' for directory, 'blob' for file
                'path': item['path'],
                'mode': item['mode']
            })
        
        return jsonify({
            'project_id': project_id,
            'branch': branch,
            'path': path,
            'items': tree_data
        })
        
    except gitlab.exceptions.GitlabAuthenticationError as e:
        logger.error(f"GitLab API authentication failed: {str(e)}")
        session.pop('gitlab_token', None)
        return jsonify({'error': 'GitLab authentication failed'}), 401
    except Exception as e:
        logger.error(f"Error getting repository tree: {str(e)}")
        return jsonify({'error': str(e)}), 500

@gitlab_bp.route('/gitlab/repository/<int:project_id>/file')
def get_file_content(project_id):
    """Get file content from repository."""
    if 'gitlab_token' not in session:
        return jsonify({'error': 'Not authenticated with GitLab'}), 401
    
    try:
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        
        project = gl.projects.get(project_id)
        file_path = request.args.get('path')
        branch = request.args.get('branch', project.default_branch)
        
        if not file_path:
            return jsonify({'error': 'File path is required'}), 400
        
        # Get file content
        file_info = project.files.get(file_path=file_path, ref=branch)
        
        return jsonify({
            'project_id': project_id,
            'file_path': file_path,
            'branch': branch,
            'content': file_info.decode().decode('utf-8'),
            'file_name': file_info.file_name,
            'size': file_info.size,
            'encoding': file_info.encoding,
            'content_sha256': file_info.content_sha256,
            'ref': file_info.ref,
            'blob_id': file_info.blob_id,
            'commit_id': file_info.commit_id,
            'last_commit_id': file_info.last_commit_id
        })
        
    except gitlab.exceptions.GitlabAuthenticationError as e:
        logger.error(f"GitLab API authentication failed: {str(e)}")
        session.pop('gitlab_token', None)
        return jsonify({'error': 'GitLab authentication failed'}), 401
    except Exception as e:
        logger.error(f"Error getting file content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@gitlab_bp.route('/gitlab/repository/<int:project_id>/commits')
def get_commits(project_id):
    """Get recent commits for a repository."""
    if 'gitlab_token' not in session:
        return jsonify({'error': 'Not authenticated with GitLab'}), 401
    
    try:
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        
        project = gl.projects.get(project_id)
        branch = request.args.get('branch', project.default_branch)
        per_page = min(int(request.args.get('per_page', 20)), 50)  # Limit to 50
        
        # Get recent commits
        commits = project.commits.list(ref_name=branch, per_page=per_page)
        
        commit_data = []
        for commit in commits:
            commit_data.append({
                'id': commit.id,
                'short_id': commit.short_id,
                'title': commit.title,
                'message': commit.message,
                'author_name': commit.author_name,
                'author_email': commit.author_email,
                'authored_date': commit.authored_date,
                'committer_name': commit.committer_name,
                'committer_email': commit.committer_email,
                'committed_date': commit.committed_date,
                'web_url': commit.web_url
            })
        
        return jsonify({
            'project_id': project_id,
            'branch': branch,
            'commits': commit_data
        })
        
    except gitlab.exceptions.GitlabAuthenticationError as e:
        logger.error(f"GitLab API authentication failed: {str(e)}")
        session.pop('gitlab_token', None)
        return jsonify({'error': 'GitLab authentication failed'}), 401
    except Exception as e:
        logger.error(f"Error getting commits: {str(e)}")
        return jsonify({'error': str(e)}), 500

@gitlab_bp.route('/gitlab/repository/<int:project_id>/branches')
def get_branches(project_id):
    """Get repository branches."""
    if 'gitlab_token' not in session:
        return jsonify({'error': 'Not authenticated with GitLab'}), 401
    
    try:
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        
        project = gl.projects.get(project_id)
        
        # Get branches
        branches = project.branches.list(get_all=True)
        
        branch_data = []
        for branch in branches:
            branch_data.append({
                'name': branch.name,
                'commit': {
                    'id': branch.commit['id'],
                    'short_id': branch.commit['short_id'],
                    'title': branch.commit['title'],
                    'author_name': branch.commit['author_name'],
                    'authored_date': branch.commit['authored_date']
                },
                'merged': branch.merged,
                'protected': branch.protected,
                'default': branch.name == project.default_branch,
                'can_push': branch.can_push,
                'web_url': branch.web_url
            })
        
        return jsonify({
            'project_id': project_id,
            'default_branch': project.default_branch,
            'branches': branch_data
        })
        
    except gitlab.exceptions.GitlabAuthenticationError as e:
        logger.error(f"GitLab API authentication failed: {str(e)}")
        session.pop('gitlab_token', None)
        return jsonify({'error': 'GitLab authentication failed'}), 401
    except Exception as e:
        logger.error(f"Error getting branches: {str(e)}")
        return jsonify({'error': str(e)}), 500 