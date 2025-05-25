"""
CI Code Companion Web Dashboard
Visualizes AI-powered code analysis results
"""

from flask import Flask, render_template, jsonify, session, redirect, url_for, request
from flask_cors import CORS
import json
import os
import logging
from datetime import datetime
from routes.gitlab_routes import gitlab_bp
from config.gitlab_config import GitLabConfig
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
            template_folder=os.path.join(basedir, 'templates'),
            static_folder=os.path.join(basedir, 'static'))

# Configure CORS to allow localhost and GitLab access
CORS(app, 
     resources={r"/*": {
         "origins": [
             "http://localhost:5001",
             "https://gitlab.com",
             "http://127.0.0.1:5001"
         ],
         "supports_credentials": True,
         "allow_headers": ["Content-Type", "Authorization"],
         "methods": ["GET", "POST", "OPTIONS"],
         "expose_headers": ["Content-Type", "X-CSRFToken"]
     }},
     supports_credentials=True
)

# Configure app security settings
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', 'dev-secret-key'),
    SESSION_COOKIE_SECURE=False,  # Set to True in production
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    # Ensure the server is accessible on localhost
    SERVER_NAME=None,
    APPLICATION_ROOT='/',
)

# Register GitLab blueprint with the correct URL prefix
app.register_blueprint(gitlab_bp, url_prefix='/gitlab')

@app.route('/app-test-route')
def app_test_route():
    return "App test route is working!", 200

@app.route('/')
def dashboard():
    """Main dashboard showing recent AI analysis results."""
    logger.debug("Dashboard accessed. Current session data: %s", dict(session))
    
    # Clear any stale session data if GitLab token exists but is invalid
    if 'gitlab_token' in session:
        try:
            import gitlab
            gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
            gl.auth()
            # Get current user info
            current_user = gl.user
            logger.debug(f"GitLab token is valid for user: {current_user.username}")
        except Exception as e:
            logger.warning(f"Found invalid GitLab token in session, clearing it: {str(e)}")
            session.pop('gitlab_token', None)
    
    gitlab_config = GitLabConfig()
    gitlab_connected = 'gitlab_token' in session
    logger.info(f"GitLab connection status: {'Connected' if gitlab_connected else 'Not connected'}")
    
    return render_template(
        'dashboard.html',
        gitlab_configured=gitlab_config.is_configured,
        gitlab_connected=gitlab_connected
    )

@app.route('/api/recent-analyses')
def recent_analyses():
    """API endpoint for recent AI analyses."""
    # This would normally fetch from database
    sample_data = [
        {
            "id": 1,
            "project": "user-auth-service",
            "commit": "a1b2c3d",
            "timestamp": "2024-01-20 14:30:00",
            "code_quality": 8.5,
            "security_score": 7.2,
            "tests_generated": 12,
            "issues_found": 3,
            "status": "completed"
        },
        {
            "id": 2,
            "project": "payment-processor",
            "commit": "e4f5g6h",
            "timestamp": "2024-01-20 13:15:00",
            "code_quality": 9.1,
            "security_score": 9.5,
            "tests_generated": 8,
            "issues_found": 1,
            "status": "completed"
        }
    ]
    return jsonify(sample_data)

@app.route('/analysis/<int:analysis_id>')
def analysis_detail(analysis_id):
    """Detailed view of a specific analysis."""
    return render_template('analysis_detail.html', analysis_id=analysis_id)

@app.route('/api/analysis/<int:analysis_id>')
def analysis_data(analysis_id):
    """API endpoint for detailed analysis data."""
    # Sample detailed analysis data
    sample_detail = {
        "id": analysis_id,
        "project": "user-auth-service",
        "commit": "a1b2c3d",
        "branch": "feature/user-validation",
        "author": "john.doe@company.com",
        "timestamp": "2024-01-20 14:30:00",
        "files_analyzed": ["auth.py", "validators.py", "models.py"],
        "code_review": {
            "overall_score": 8.5,
            "suggestions": [
                {
                    "file": "auth.py",
                    "line": 45,
                    "type": "improvement",
                    "message": "Consider adding type hints for better code clarity",
                    "code": "def validate_user(username, password):"
                },
                {
                    "file": "validators.py", 
                    "line": 23,
                    "type": "security",
                    "message": "Potential SQL injection vulnerability",
                    "code": "query = f'SELECT * FROM users WHERE name = {username}'"
                }
            ]
        },
        "generated_tests": [
            {
                "file": "test_auth.py",
                "function": "test_user_validation_success",
                "coverage": "Happy path for user validation"
            },
            {
                "file": "test_auth.py", 
                "function": "test_user_validation_failure",
                "coverage": "Invalid credentials handling"
            }
        ],
        "security_analysis": {
            "score": 7.2,
            "vulnerabilities": [
                {
                    "severity": "high",
                    "type": "SQL Injection",
                    "file": "validators.py",
                    "line": 23,
                    "description": "User input directly concatenated into SQL query"
                }
            ]
        }
    }
    return jsonify(sample_detail)

@app.route('/api/connected-projects')
def connected_projects():
    """API endpoint for listing connected GitLab projects."""
    if 'gitlab_token' not in session:
        return jsonify([])
        
    try:
        # Use the gitlab_routes blueprint to get projects
        from routes.gitlab_routes import list_projects
        return list_projects()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gitlab/status')
def gitlab_status():
    """Check GitLab connection status."""
    if 'gitlab_token' not in session:
        return jsonify({
            'connected': False,
            'message': 'No GitLab token found'
        })
    
    try:
        import gitlab
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        user = gl.user
        return jsonify({
            'connected': True,
            'user': user.username,
            'email': user.email
        })
    except Exception as e:
        logger.error(f"GitLab status check failed: {str(e)}")
        # Clear invalid token
        session.pop('gitlab_token', None)
        return jsonify({
            'connected': False,
            'message': str(e)
        })

@app.route('/repository')
def repository_browser():
    """Repository browser interface."""
    if 'gitlab_token' not in session:
        return redirect(url_for('dashboard'))
    
    return render_template('repository_browser.html')

@app.route('/api/ai-analyze', methods=['POST'])
def ai_analyze():
    """AI analysis endpoint for repository browser."""
    if 'gitlab_token' not in session:
        return jsonify({'error': 'Not authenticated with GitLab'}), 401
    
    try:
        data = request.json
        action = data.get('action')
        file_path = data.get('file_path')
        content = data.get('content')
        project_id = data.get('project_id')
        branch = data.get('branch')
        
        if not all([action, file_path, content]):
            return jsonify({'error': 'Missing required parameters'}), 400
        
        # Import AI components
        from src.ci_code_companion.vertex_ai_client import VertexAIClient
        from src.ci_code_companion.code_reviewer import CodeReviewer
        from src.ci_code_companion.test_generator import TestGenerator
        
        # Initialize AI components
        gcp_project_id = os.getenv('GCP_PROJECT_ID')
        if not gcp_project_id:
            logger.error("GCP_PROJECT_ID environment variable not set.")
            return jsonify({'error': 'AI service not configured (missing GCP_PROJECT_ID)'}), 500
        ai_client = VertexAIClient(project_id=gcp_project_id)
        
        result = {}
        
        if action == 'review':
            reviewer = CodeReviewer(ai_client)
            review_result = reviewer.review_code_content(content, file_path)
            result = {
                'action': 'review',
                'file_path': file_path,
                'analysis': review_result,
                'timestamp': datetime.now().isoformat()
            }
            
        elif action == 'test-generation':
            test_generator = TestGenerator(ai_client)
            test_result = test_generator.generate_tests(content, file_path)
            result = {
                'action': 'test-generation',
                'file_path': file_path,
                'tests': test_result,
                'timestamp': datetime.now().isoformat()
            }
            
        elif action == 'improve':
            reviewer = CodeReviewer(ai_client)
            # Get code improvement suggestions
            improvement_result = reviewer.review_code_content(content, file_path, review_type="comprehensive")
            result = {
                'action': 'improve',
                'file_path': file_path,
                'improvements': improvement_result,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 