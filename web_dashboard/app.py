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
    
    # Initialize SDK with streamlined configuration
    sdk_config = SDKConfig({
        'ai_provider': 'vertex_ai',
        'project_id': os.getenv('GCP_PROJECT_ID'),
        'region': os.getenv('GCP_REGION', 'us-central1'),
        'enable_caching': True,
        'max_workers': 3  # Reduced for better resource management
    })
    
    ci_sdk = CICodeCompanionSDK(config=sdk_config)
    logger.info(f"CI Code Companion SDK initialized successfully with model: {ci_sdk.ai_service.vertex_client.model_name}")
    
except ImportError as e:
    logger.error(f"Failed to import CI Code Companion SDK: {e}")
    ci_sdk = None
except ConfigurationError as e:
    logger.error(f"SDK configuration error: {e}")
    logger.error(f"Suggestions: {e.suggestions}")
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
    """Streamlined AI-powered file review using direct AI service"""
    logger.info("🌐 ENDPOINT HIT: /ai/review-file - File review request received")
    
    if not ci_sdk:
        logger.error("❌ SDK ERROR: CI Code Companion SDK not available")
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available. Check configuration and model setup."
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        logger.info(f"📋 REQUEST DATA: File: {file_path}, Analysis: {analysis_type}, Code length: {len(code)}")
        
        if not code:
            logger.warning("⚠️ VALIDATION: No code provided for review")
            return jsonify({
                "success": False,
                "error": "No code provided for review"
            }), 400
        
        logger.info("🚀 SDK CALL: Calling ci_sdk.analyze_file() → StreamlinedAIService")
        
        # Analyze file using streamlined SDK
        result = run_async(ci_sdk.analyze_file(file_path, code, analysis_type=analysis_type))
        
        logger.info(f"✅ SDK RESPONSE: Analysis completed successfully")
        logger.info(f"📊 RESULTS: Found {len(result.issues)} issues, {len(result.suggestions)} suggestions")
        
        # Convert result to expected format
        review_response = {
            "success": True,
            "analysis": {
                "operation_id": result.operation_id,
                "file_path": result.file_path,
                "confidence_score": result.confidence_score,
                "model_used": result.metadata.get('model_used', 'unknown'),
                "issues": [
                    {
                        "title": issue.title,
                        "description": issue.description,
                        "severity": issue.severity,
                        "line_number": issue.line_number,
                        "suggestion": issue.suggestion
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
        
        logger.info("🎉 RESPONSE: Sending successful analysis response to UI")
        return jsonify(review_response)
        
    except ConfigurationError as e:
        logger.error(f"⚙️ CONFIG ERROR: Configuration error in file review: {e}")
        return jsonify({
            "success": False,
            "error": f"Configuration error: {e.message}",
            "suggestions": e.suggestions
        }), 500
    except AnalysisError as e:
        logger.error(f"🔍 ANALYSIS ERROR: Analysis error in file review: {e}")
        return jsonify({
            "success": False,
            "error": f"AI analysis error: {e.message}"
        }), 500
    except Exception as e:
        logger.error(f"💥 UNEXPECTED ERROR: Unexpected error in file review: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/ai/generate-tests', methods=['POST'])
def generate_tests_ai():
    """Streamlined AI-powered test generation using direct AI service"""
    logger.info("🌐 ENDPOINT HIT: /ai/generate-tests - Test generation request received")
    
    if not ci_sdk:
        logger.error("❌ SDK ERROR: CI Code Companion SDK not available")
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available. Check configuration and model setup."
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        test_type = data.get('test_type', 'unit')
        
        logger.info(f"📋 REQUEST DATA: File: {file_path}, Test type: {test_type}, Code length: {len(code)}")
        
        if not code:
            logger.warning("⚠️ VALIDATION: No code provided for test generation")
            return jsonify({
                "success": False,
                "error": "No code provided for test generation"
            }), 400
        
        logger.info("🚀 SDK CALL: Calling ci_sdk.generate_tests() → StreamlinedAIService")
        
        # Generate tests using streamlined SDK
        result = run_async(ci_sdk.generate_tests(file_path, code, test_type=test_type))
        
        logger.info(f"✅ SDK RESPONSE: Test generation completed successfully")
        logger.info(f"📝 TEST CODE: Generated {len(result.test_code)} characters of test code")
        
        response_data = {
            "success": True,
            "tests": {
                "operation_id": result.operation_id,
                "test_code": result.test_code,
                "test_type": result.test_type,
                "coverage_estimate": result.coverage_estimate,
                "model_used": result.metadata.get('model_used', 'unknown')
            }
        }
        
        logger.info("🎉 RESPONSE: Sending successful test generation response to UI")
        return jsonify(response_data)
        
    except ConfigurationError as e:
        logger.error(f"⚙️ CONFIG ERROR: Configuration error in test generation: {e}")
        return jsonify({
            "success": False,
            "error": f"Configuration error: {e.message}",
            "suggestions": e.suggestions
        }), 500
    except AnalysisError as e:
        logger.error(f"🔍 ANALYSIS ERROR: Analysis error in test generation: {e}")
        return jsonify({
            "success": False,
            "error": f"AI analysis error: {e.message}"
        }), 500
    except Exception as e:
        logger.error(f"💥 UNEXPECTED ERROR: Unexpected error in test generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/ai/optimize-code', methods=['POST'])
def optimize_code_ai():
    """Streamlined AI-powered code optimization using direct AI service"""
    logger.info("🌐 ENDPOINT HIT: /ai/optimize-code - Code optimization request received")
    
    if not ci_sdk:
        logger.error("❌ SDK ERROR: CI Code Companion SDK not available")
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available. Check configuration and model setup."
        }), 500
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        file_path = data.get('file_path', 'unknown.py')
        optimization_type = data.get('optimization_type', 'performance')
        
        logger.info(f"📋 REQUEST DATA: File: {file_path}, Optimization: {optimization_type}, Code length: {len(code)}")
        
        if not code:
            logger.warning("⚠️ VALIDATION: No code provided for optimization")
            return jsonify({
                "success": False,
                "error": "No code provided for optimization"
            }), 400
        
        logger.info("🚀 SDK CALL: Calling ci_sdk.optimize_code() → StreamlinedAIService")
        
        # Optimize code using streamlined SDK
        result = run_async(ci_sdk.optimize_code(file_path, code, optimization_type=optimization_type))
        
        logger.info(f"✅ SDK RESPONSE: Code optimization completed successfully")
        logger.info(f"⚡ OPTIMIZED CODE: Generated {len(result.optimized_code)} characters of optimized code")
        
        response_data = {
            "success": True,
            "optimization": {
                "operation_id": result.operation_id,
                "optimized_code": result.optimized_code,
                "optimization_type": result.optimization_type,
                "performance_impact": result.performance_impact,
                "model_used": result.metadata.get('model_used', 'unknown')
            }
        }
        
        logger.info("🎉 RESPONSE: Sending successful optimization response to UI")
        return jsonify(response_data)
        
    except ConfigurationError as e:
        logger.error(f"⚙️ CONFIG ERROR: Configuration error in code optimization: {e}")
        return jsonify({
            "success": False,
            "error": f"Configuration error: {e.message}",
            "suggestions": e.suggestions
        }), 500
    except AnalysisError as e:
        logger.error(f"🔍 ANALYSIS ERROR: Analysis error in code optimization: {e}")
        return jsonify({
            "success": False,
            "error": f"AI analysis error: {e.message}"
        }), 500
    except Exception as e:
        logger.error(f"💥 UNEXPECTED ERROR: Unexpected error in code optimization: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/ai/chat', methods=['POST'])
def chat_ai():
    """Streamlined AI chat functionality using direct AI service"""
    logger.info("🌐 ENDPOINT HIT: /ai/chat - Chat request received")
    
    if not ci_sdk:
        logger.error("❌ SDK ERROR: CI Code Companion SDK not available")
        return jsonify({
            "success": False,
            "error": "CI Code Companion SDK not available. Check configuration and model setup."
        }), 500
    
    try:
        data = request.get_json()
        message = data.get('message', '')
        file_path = data.get('file_path')
        content = data.get('content')
        conversation_history = data.get('conversation_history', [])
        
        logger.info(f"💬 CHAT REQUEST: Message: '{message[:50]}{'...' if len(message) > 50 else ''}'")
        logger.info(f"📁 CHAT CONTEXT: File: {file_path if file_path else 'None'}")
        logger.info(f"📚 CHAT HISTORY: {len(conversation_history)} previous messages")
        
        if not message:
            logger.warning("⚠️ VALIDATION: No message provided")
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400
        
        logger.info("🚀 SDK CALL: Calling ci_sdk.chat() → StreamlinedAIService")
        
        # Chat using streamlined SDK
        response = run_async(ci_sdk.chat(
            message=message,
            file_path=file_path,
            content=content,
            conversation_history=conversation_history
        ))
        
        logger.info(f"✅ SDK RESPONSE: Chat completed successfully")
        logger.info(f"📝 CHAT RESPONSE: Response length: {len(response)} characters")
        
        chat_response = {
            "success": True,
            "response": response,
            "model_used": ci_sdk.ai_service.vertex_client.model_name if ci_sdk.ai_service else "unknown"
        }
        
        logger.info("🎉 RESPONSE: Sending successful chat response to UI")
        return jsonify(chat_response)
        
    except ConfigurationError as e:
        logger.error(f"⚙️ CONFIG ERROR: Configuration error in AI chat: {e}")
        return jsonify({
            "success": False,
            "error": f"Configuration error: {e.message}",
            "suggestions": e.suggestions
        }), 500
    except AnalysisError as e:
        logger.error(f"🔍 ANALYSIS ERROR: Analysis error in AI chat: {e}")
        return jsonify({
            "success": False,
            "error": f"AI analysis error: {e.message}"
        }), 500
    except Exception as e:
        logger.error(f"💥 UNEXPECTED ERROR: Unexpected error in AI chat: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
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
    """Check CI Code Companion SDK status with streamlined health check and agent integration"""
    if not ci_sdk:
        return jsonify({
            "available": False,
            "error": "SDK not initialized. Check configuration and model setup.",
            "suggestions": [
                "Verify GEMINI_MODEL environment variable is set",
                "Check Google Cloud credentials",
                "Ensure Vertex AI is enabled in your project"
            ]
        })
    
    try:
        # Get SDK health status
        health = run_async(ci_sdk.health_check())
        
        # Get detailed agent information
        agent_details = {}
        if hasattr(ci_sdk, 'ai_service') and ci_sdk.ai_service and hasattr(ci_sdk.ai_service, 'agents'):
            for agent_name, agent in ci_sdk.ai_service.agents.items():
                try:
                    capabilities = [cap.value for cap in agent.get_capabilities()]
                    agent_details[agent_name] = {
                        "status": "healthy",
                        "capabilities": capabilities,
                        "chat_support": "CHAT_SUPPORT" in [cap.value for cap in agent.get_capabilities()],
                        "supported_files": agent.get_supported_file_types(),
                        "version": getattr(agent, 'version', '1.0.0')
                    }
                except Exception as e:
                    agent_details[agent_name] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        return jsonify({
            "available": True,
            "health": health,
            "config": {
                "ai_provider": ci_sdk.config.ai_provider,
                "project_id": getattr(ci_sdk.config, 'project_id', None),
                "region": getattr(ci_sdk.config, 'region', None)
            },
            "model_info": {
                "model_name": ci_sdk.ai_service.vertex_client.model_name if ci_sdk.ai_service else "unknown",
                "direct_connection": True,
                "fallback_models": "disabled",  # No more fallback models
                "context_window": "1M+ tokens"
            },
            "agent_integration": {
                "enabled": True,
                "total_agents": len(agent_details),
                "agents": agent_details,
                "chat_enabled_agents": [name for name, info in agent_details.items() 
                                      if info.get("chat_support", False)],
                "flow": "Chatbot → StreamlinedAIService → Agents → VertexAI → Gemini Model"
            },
            "architecture": {
                "streamlined": True,
                "redundancy_removed": True,
                "single_model_focus": True,
                "agent_specialization": True
            }
        })
    except Exception as e:
        logger.error(f"SDK health check failed: {e}")
        return jsonify({
            "available": True,
            "error": str(e),
            "health": {"status": "unhealthy"},
            "agent_integration": {"enabled": True, "error": "Health check failed"}
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True) 