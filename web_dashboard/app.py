"""
CI Code Companion Web Dashboard
Visualizes AI-powered code analysis results
"""

from flask import Flask, render_template, jsonify, session, redirect, url_for, request
from flask_cors import CORS
import json
import os
import logging
import asyncio
from datetime import datetime
from routes.gitlab_api import gitlab_bp, init_gitlab
from config.gitlab_config import GitLabConfig
from dotenv import load_dotenv
import time

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

# Initialize GitLab connection
gitlab_config = GitLabConfig()
if gitlab_config.is_configured:
    init_success = init_gitlab(gitlab_config.url, gitlab_config.token)
    if init_success:
        logger.info("GitLab connection initialized successfully")
    else:
        logger.error("Failed to initialize GitLab connection")
else:
    logger.warning("GitLab configuration not found")

# Register GitLab blueprint with the correct URL prefix
app.register_blueprint(gitlab_bp, url_prefix='/gitlab')

# Import CI Code Companion SDK
try:
    import sys
    import os
    # Add the parent directory to the path to import the SDK
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig
    from ci_code_companion_sdk.core.exceptions import SDKError, AnalysisError, ConfigurationError
    
    # Initialize SDK
    sdk_config = SDKConfig(
        ai_provider=os.getenv('AI_PROVIDER', 'vertex_ai'),
        project_id=os.getenv('GCP_PROJECT_ID'),
        region=os.getenv('GCP_REGION', 'us-central1'),
        enable_caching=True,
        max_concurrent_operations=5
    )
    
    ci_sdk = CICodeCompanionSDK(config=sdk_config)
    logger.info("CI Code Companion SDK initialized successfully")
    
except ImportError as e:
    logger.error(f"Failed to import CI Code Companion SDK: {e}")
    ci_sdk = None
except Exception as e:
    logger.error(f"Failed to initialize CI Code Companion SDK: {e}")
    ci_sdk = None

def run_async(coro):
    """Helper function to run async functions in Flask routes"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

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
    
    gitlab_connected = 'gitlab_token' in session
    logger.info(f"GitLab connection status: {'Connected' if gitlab_connected else 'Not connected'}")
    
    # Check SDK status
    sdk_status = "Available" if ci_sdk else "Not Available"
    
    return render_template(
        'dashboard.html',
        gitlab_configured=gitlab_config.is_configured,
        gitlab_connected=gitlab_connected,
        sdk_status=sdk_status
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
        "timestamp": "2024-01-20 14:30:00",
        "overall_score": 8.5,
        "metrics": {
            "code_quality": 8.5,
            "security_score": 7.2,
            "performance_score": 8.0,
            "maintainability": 9.0
        },
        "issues": [
            {
                "id": 1,
                "type": "Security",
                "severity": "High",
                "description": "Potential SQL injection vulnerability in user query",
                "file": "auth/models.py",
                "line": 45,
                "suggestion": "Use parameterized queries instead of string concatenation"
            }
        ],
        "tests_generated": [
            {
                "file": "auth/test_models.py",
                "framework": "pytest",
                "test_cases": 8,
                "coverage_area": "User authentication logic"
            }
        ]
    }
    return jsonify(sample_detail)

@app.route('/api/connected-projects')
def connected_projects():
    """API endpoint for GitLab projects."""
    if 'gitlab_token' not in session:
        return jsonify([])
    
    try:
        import gitlab
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        projects = gl.projects.list(owned=True, all=True)
        
        project_list = []
        for project in projects[:10]:  # Limit to 10 projects for performance
            project_list.append({
                'id': project.id,
                'name': project.name,
                'web_url': project.web_url,
                'last_activity_at': project.last_activity_at
            })
        
        return jsonify(project_list)
    except Exception as e:
        logger.error(f"Error fetching GitLab projects: {str(e)}")
        return jsonify([])

@app.route('/api/gitlab/status')
def gitlab_status():
    """Check GitLab connection status."""
    if 'gitlab_token' not in session:
        return jsonify({
            'connected': False,
            'user': None,
            'error': 'No GitLab token found'
        })
    
    try:
        import gitlab
        gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
        gl.auth()
        current_user = gl.user
        
        return jsonify({
            'connected': True,
            'user': {
                'username': current_user.username,
                'name': current_user.name,
                'avatar_url': current_user.avatar_url
            },
            'error': None
        })
    except Exception as e:
        logger.error(f"GitLab status check failed: {str(e)}")
        # Clear invalid token
        session.pop('gitlab_token', None)
        return jsonify({
            'connected': False,
            'user': None,
            'error': str(e)
        })

@app.route('/repository')
def repository_browser():
    """Repository browser page."""
    return render_template('repository.html')

@app.route('/api/ai-analyze', methods=['POST'])
def ai_analyze():
    """Comprehensive AI analysis using CI Code Companion SDK"""
    if not ci_sdk:
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available"
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        language = data.get('language', 'python')
        
        if not code:
            return jsonify({
                "success": False,
                "error": "No code provided for analysis"
            }), 400
        
        # Run analysis using SDK
        result = run_async(ci_sdk.analyze_file(file_path, code))
        
        # Format response for frontend
        response = {
            "success": True,
            "analysis": {
                "operation_id": result.operation_id,
                "file_path": result.file_path,
                "agent_type": result.agent_type,
                "confidence_score": result.confidence_score,
                "execution_time": result.execution_time,
                "quality_score": result.calculate_quality_score(),
                "has_blocking_issues": result.has_blocking_issues(),
                "issues": [
                    {
                        "id": issue.id,
                        "title": issue.title,
                        "description": issue.description,
                        "severity": issue.severity,
                        "category": issue.category,
                        "line_number": issue.line_number,
                        "column_number": issue.column_number,
                        "suggestion": issue.suggestion,
                        "fix_code": issue.fix_code,
                        "confidence_score": issue.confidence_score,
                        "is_auto_fixable": issue.is_auto_fixable()
                    } for issue in result.issues
                ],
                "suggestions": [
                    {
                        "title": suggestion.title,
                        "description": suggestion.description,
                        "impact": suggestion.impact,
                        "effort": suggestion.effort,
                        "category": suggestion.category
                    } for suggestion in result.suggestions
                ],
                "metadata": result.metadata
            }
        }
        
        return jsonify(response)
        
    except AnalysisError as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error in AI analysis: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred during analysis"
        }), 500

@app.route('/project-selector')
def project_selector():
    """Project selector page."""
    return render_template('project_selector.html')

@app.route('/ai/review-file', methods=['POST'])
def review_file_ai():
    """AI-powered file review using CI Code Companion SDK"""
    if not ci_sdk:
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available"
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        
        if not code:
            return jsonify({
                "success": False,
                "error": "No code provided for review"
            }), 400
        
        # Analyze file using SDK
        result = run_async(ci_sdk.analyze_file(file_path, code))
        
        # Format for review response
        review_response = {
            "success": True,
            "review": {
                "overall_score": result.calculate_quality_score(),
                "agent_used": result.agent_type,
                "confidence": result.confidence_score,
                "critical_issues": len(result.get_critical_issues()),
                "total_issues": len(result.issues),
                "issues": [
                    {
                        "severity": issue.severity,
                        "category": issue.category,
                        "title": issue.title,
                        "description": issue.description,
                        "line": issue.line_number,
                        "suggestion": issue.suggestion,
                        "auto_fixable": issue.is_auto_fixable()
                    } for issue in result.issues
                ],
                "suggestions": [
                    {
                        "title": suggestion.title,
                        "description": suggestion.description,
                        "impact": suggestion.impact
                    } for suggestion in result.suggestions
                ]
            }
        }
        
        return jsonify(review_response)
        
    except Exception as e:
        logger.error(f"Error in file review: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/ai/generate-tests', methods=['POST'])
def generate_tests_ai():
    """AI-powered test generation using CI Code Companion SDK"""
    if not ci_sdk:
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available"
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        test_type = data.get('test_type', 'unit')
        
        if not code:
            return jsonify({
                "success": False,
                "error": "No code provided for test generation"
            }), 400
        
        # Generate tests using SDK
        result = run_async(ci_sdk.generate_tests(file_path, code, test_type=test_type))
        
        return jsonify({
            "success": True,
            "tests": result
        })
        
    except Exception as e:
        logger.error(f"Error in test generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/ai/optimize-code', methods=['POST'])
def optimize_code_ai():
    """AI-powered code optimization using CI Code Companion SDK"""
    if not ci_sdk:
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available"
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        optimization_type = data.get('optimization_type', 'performance')
        
        if not code:
            return jsonify({
                "success": False,
                "error": "No code provided for optimization"
            }), 400
        
        # Optimize code using SDK
        result = run_async(ci_sdk.optimize_code(file_path, code, optimization_type=optimization_type))
        
        return jsonify({
            "success": True,
            "optimization": result
        })
        
    except Exception as e:
        logger.error(f"Error in code optimization: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/ai/chat', methods=['POST'])
def chat_ai():
    """AI chat functionality using CI Code Companion SDK"""
    if not ci_sdk:
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available"
        }), 500
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        file_path = data.get('file_path')
        content = data.get('content')
        conversation_history = data.get('conversation_history', [])
        
        if not message:
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400
        
        # Chat using SDK
        response = run_async(ci_sdk.chat(
            message=message,
            file_path=file_path,
            content=content,
            conversation_history=conversation_history
        ))
        
        return jsonify({
            "success": True,
            "response": response
        })
        
    except Exception as e:
        logger.error(f"Error in AI chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/ai/analyze-directory', methods=['POST'])
def analyze_directory_ai():
    """AI-powered directory analysis using CI Code Companion SDK"""
    if not ci_sdk:
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available"
        }), 500
    
    try:
        data = request.get_json()
        directory_path = data.get('directory_path', '')
        
        if not directory_path:
            return jsonify({
                "success": False,
                "error": "No directory path provided"
            }), 400
        
        # This would need to be implemented in the SDK
        # For now, return a placeholder response
        return jsonify({
            "success": True,
            "analysis": {
                "directory": directory_path,
                "message": "Directory analysis functionality to be implemented in SDK"
            }
        })
        
    except Exception as e:
        logger.error(f"Error in directory analysis: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/sdk-status')
def sdk_status():
    """Check CI Code Companion SDK status"""
    if not ci_sdk:
        return jsonify({
            "available": False,
            "error": "SDK not initialized"
        })
    
    try:
        # Get SDK health status
        health = run_async(ci_sdk.health_check())
        return jsonify({
            "available": True,
            "health": health,
            "config": {
                "ai_provider": ci_sdk.config.ai_provider,
                "project_id": ci_sdk.config.project_id,
                "region": ci_sdk.config.region
            }
        })
    except Exception as e:
        return jsonify({
            "available": True,
            "error": str(e)
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 