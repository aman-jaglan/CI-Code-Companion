"""
CI Code Companion API Routes
Provides endpoints for code analysis, metrics, and suggestions

Enhanced with PromptLoader integration for Cursor-style prompting and Gemini 2.5 Pro optimization.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import json
import random
from typing import Dict, Any, List

# Add SDK to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import enhanced SDK components
try:
    from ci_code_companion_sdk.core.prompt_loader import PromptLoader
    from ci_code_companion_sdk.core.config import SDKConfig
    from ci_code_companion_sdk.agents.specialized.code.react_code_agent import ReactCodeAgent
    from ci_code_companion_sdk.integrations.vertex_ai_client import VertexAIClient
    SDK_AVAILABLE = True
except ImportError as e:
    current_app.logger.warning(f"SDK import failed: {e}")
    SDK_AVAILABLE = False

# Temporarily commented out old imports that are causing module errors
# These will need to be updated to use the new SDK models
# from ci_code_companion.models import (
#     Repository, Commit, CodeFile, FileChange, 
#     AIAnalysis, CodeIssue, PerformanceMetrics,
#     AIContextCache, AILearning
# )
# from ci_code_companion.ai_context_manager import AIContextManager

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api/v2')

# Global instances for enhanced system
prompt_loader = None
enhanced_agents = {}
vertex_ai_client = None

def initialize_enhanced_system():
    """Initialize the enhanced prompt system with Vertex AI integration"""
    global prompt_loader, enhanced_agents, vertex_ai_client
    
    if not SDK_AVAILABLE:
        return False
        
    try:
        # Initialize SDK config
        config = SDKConfig()
        logger = logging.getLogger(__name__)
        
        # Initialize Vertex AI client
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            logger.warning("GCP_PROJECT_ID not set, using default project")
            project_id = "your-default-project"
        
        vertex_ai_client = VertexAIClient(
            project_id=project_id,
            location=os.getenv('GCP_LOCATION', 'us-central1'),
            model_name=os.getenv('GEMINI_MODEL', 'gemini-2.5-pro')
        )
        
        # Test Vertex AI connection
        health_status = vertex_ai_client.health_check()
        if health_status['status'] != 'healthy':
            logger.warning(f"Vertex AI health check failed: {health_status}")
        
        # Initialize prompt loader
        prompt_loader = PromptLoader(config, logger)
        
        # Initialize enhanced React agent with Vertex AI
        enhanced_agents['react_code'] = ReactCodeAgent(
            config.get_agent_config('react_code'), 
            logger, 
            prompt_loader
        )
        
        logger.info("Enhanced system with Vertex AI initialized successfully")
        return True
        
    except Exception as e:
        current_app.logger.error(f"Failed to initialize enhanced system: {e}")
        return False

# Database setup
def init_database():
    """Initialize database connection and create tables if they don't exist"""
    # Placeholder function since old models are commented out
    # TODO: Update to use new SDK database models
    return None
    
    # Original code commented out until models are updated
    # engine = create_engine(current_app.config['DATABASE_URL'])
    # Session = sessionmaker(bind=engine)
    # return Session()

# Helper functions
def calculate_metrics(session):
    """Calculate overall metrics from the database"""
    try:
        # Placeholder metrics since old models are commented out
        # TODO: Update to use new SDK models
        return {
            'code_quality': 85.5,
            'security_score': 92.3,
            'test_coverage': 78.2,
            'active_issues': 12
        }
        
        # Original code commented out until models are updated
        # # Get recent analyses
        # recent_analyses = session.query(AIAnalysis)\
        #     .order_by(AIAnalysis.created_at.desc())\
        #     .limit(100)\
        #     .all()
        # 
        # if not recent_analyses:
        #     return {
        #         'code_quality': 0,
        #         'security_score': 0,
        #         'test_coverage': 0,
        #         'active_issues': 0
        #     }
        # 
        # # Calculate averages
        # total_quality = sum(a.code_quality for a in recent_analyses if a.code_quality)
        # total_security = sum(a.security_score for a in recent_analyses if a.security_score)
        # total_coverage = sum(a.test_coverage for a in recent_analyses if a.test_coverage)
        # 
        # # Count active issues
        # active_issues = session.query(CodeIssue)\
        #     .filter(CodeIssue.status == 'open')\
        #     .count()
        # 
        # count = len(recent_analyses)
        # return {
        #     'code_quality': round(total_quality / count if count > 0 else 0, 1),
        #     'security_score': round(total_security / count if count > 0 else 0, 1),
        #     'test_coverage': round(total_coverage / count if count > 0 else 0, 1),
        #     'active_issues': active_issues
        # }
    except Exception as e:
        current_app.logger.error(f"Error calculating metrics: {str(e)}")
        return None

def get_trend_data(session, days=30):
    """Get trend data for charts"""
    try:
        # Placeholder trend data since old models are commented out
        # TODO: Update to use new SDK models
        
        # Generate sample trend data for the last 30 days
        dates = []
        quality_scores = []
        security_scores = []
        coverage_scores = []
        
        base_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            current_date = base_date + timedelta(days=i)
            dates.append(current_date.strftime('%Y-%m-%d'))
            
            # Generate trending data with some randomness
            quality_scores.append(round(80 + random.uniform(-5, 10), 1))
            security_scores.append(round(90 + random.uniform(-8, 5), 1))
            coverage_scores.append(round(75 + random.uniform(-10, 15), 1))
        
        return {
            'dates': dates,
            'quality': quality_scores,
            'security': security_scores,
            'coverage': coverage_scores
        }
        
        # Original code commented out until models are updated
        # # Get metrics for the last N days
        # start_date = datetime.utcnow() - timedelta(days=days)
        # metrics = session.query(PerformanceMetrics)\
        #     .filter(PerformanceMetrics.recorded_at >= start_date)\
        #     .order_by(PerformanceMetrics.recorded_at)\
        #     .all()
        # 
        # # Group by date
        # daily_metrics = {}
        # for metric in metrics:
        #     date_key = metric.recorded_at.strftime('%Y-%m-%d')
        #     if date_key not in daily_metrics:
        #         daily_metrics[date_key] = {
        #             'quality': [],
        #             'security': [],
        #             'coverage': []
        #         }
        #     
        #     if metric.metric_name == 'code_quality':
        #         daily_metrics[date_key]['quality'].append(metric.metric_value)
        #     elif metric.metric_name == 'security_score':
        #         daily_metrics[date_key]['security'].append(metric.metric_value)
        #     elif metric.metric_name == 'test_coverage':
        #         daily_metrics[date_key]['coverage'].append(metric.metric_value)
        # 
        # # Calculate daily averages
        # trend_data = {
        #     'dates': [],
        #     'quality': [],
        #     'security': [],
        #     'coverage': []
        # }
        # 
        # for date, values in sorted(daily_metrics.items()):
        #     trend_data['dates'].append(date)
        #     trend_data['quality'].append(
        #         sum(values['quality']) / len(values['quality']) if values['quality'] else 0
        #     )
        #     trend_data['security'].append(
        #         sum(values['security']) / len(values['security']) if values['security'] else 0
        #     )
        #     trend_data['coverage'].append(
        #         sum(values['coverage']) / len(values['coverage']) if values['coverage'] else 0
        #     )
        # 
        # return trend_data
    except Exception as e:
        current_app.logger.error(f"Error getting trend data: {str(e)}")
        return None

# API Routes

@api.route('/metrics')
def get_metrics():
    """Get current metrics and trends"""
    session = None
    try:
        session = init_database()
        
        # Get current metrics
        metrics = calculate_metrics(session)
        if not metrics:
            return jsonify({'error': 'Failed to calculate metrics'}), 500
        
        # Get trend data
        trends = get_trend_data(session)
        if not trends:
            return jsonify({'error': 'Failed to get trend data'}), 500
        
        return jsonify({
            'current': metrics,
            'trends': trends
        })
    except Exception as e:
        current_app.logger.error(f"Error in /metrics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if session:
            session.close()

@api.route('/issues/summary')
def get_issues_summary():
    """Get summary of current issues"""
    # Return placeholder data since database models are commented out
    return jsonify({
        'by_severity': {
            'high': 5,
            'medium': 12,
            'low': 8
        },
        'by_category': {
            'security': 3,
            'performance': 7,
            'style': 10,
            'maintainability': 5
        }
    })

@api.route('/activity/recent')
def get_recent_activity():
    """Get recent activity across all repositories"""
    # Return placeholder activity data since database models are commented out
    activities = [
        {
            'type': 'commit',
            'message': 'Fix authentication bug in login service',
            'author': 'developer@example.com',
            'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
            'repository_id': 1
        },
        {
            'type': 'analysis',
            'message': 'Analyzed commit a1b2c3d',
            'quality_score': 85.2,
            'security_score': 92.1,
            'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
            'repository_id': 1
        },
        {
            'type': 'commit',
            'message': 'Update documentation for API endpoints',
            'author': 'docs@example.com',
            'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
            'repository_id': 2
        }
    ]
    
    return jsonify(activities)

@api.route('/insights')
def get_ai_insights():
    """Get AI-generated insights about the codebase"""
    # Return placeholder insights since database models are commented out
    insights = [
        {
            'id': 'insight-1',
            'title': 'High Code Complexity Detected',
            'description': 'Several functions have high cyclomatic complexity that may affect maintainability',
            'category': 'maintainability',
            'priority': 'high',
            'timestamp': (datetime.now() - timedelta(hours=4)).isoformat()
        },
        {
            'id': 'insight-2',
            'title': 'Security Best Practices',
            'description': 'Consider implementing input validation in user-facing endpoints',
            'category': 'security',
            'priority': 'medium',
            'timestamp': (datetime.now() - timedelta(hours=6)).isoformat()
        },
        {
            'id': 'insight-3',
            'title': 'Test Coverage Opportunity',
            'description': 'Recent changes lack corresponding test coverage',
            'category': 'testing',
            'priority': 'medium',
            'timestamp': (datetime.now() - timedelta(hours=8)).isoformat()
        }
    ]
    
    return jsonify(insights)

@api.route('/suggestions/<int:file_id>')
def get_file_suggestions(file_id):
    """Get AI suggestions for a specific file"""
    # Return placeholder suggestions since database models are commented out
    suggestions = [
        {
            'id': f'suggestion-{file_id}-1',
            'line_number': 25,
            'old_content': 'if (user == null)',
            'new_content': 'if (user === null)',
            'issue_description': 'Use strict equality comparison',
            'explanation': 'Using === instead of == prevents type coercion issues',
            'severity': 'medium',
            'category': 'style',
            'impact': ['code quality', 'maintainability']
        }
    ]
    
    return jsonify(suggestions)

@api.route('/suggestions/<int:suggestion_id>/apply', methods=['POST'])
def apply_suggestion(suggestion_id):
    """Apply a specific suggestion"""
    # Placeholder implementation
    return jsonify({
        'success': True,
        'message': 'Suggestion applied successfully'
    })

@api.route('/suggestions/<int:suggestion_id>/reject', methods=['POST'])
def reject_suggestion(suggestion_id):
    """Reject a specific suggestion"""
    # Placeholder implementation
    return jsonify({
        'success': True,
        'message': 'Suggestion rejected successfully'
    })

@api.route('/gitlab/status')
def gitlab_status():
    """Check GitLab connection status."""
    try:
        # Import session from Flask
        from flask import session
        
        if 'gitlab_token' not in session:
            return jsonify({
                'connected': False,
                'message': 'No GitLab token found'
            })
        
        # Try to verify the token with GitLab
        try:
            import gitlab
            gl = gitlab.Gitlab('https://gitlab.com', oauth_token=session['gitlab_token'])
            gl.auth()
            user = gl.user
            return jsonify({
                'connected': True,
                'user': user.username,
                'email': getattr(user, 'email', 'N/A')
            })
        except Exception as e:
            # Clear invalid token
            session.pop('gitlab_token', None)
            return jsonify({
                'connected': False,
                'message': f'GitLab authentication failed: {str(e)}'
            })
    except Exception as e:
        current_app.logger.error(f"Error checking GitLab status: {str(e)}")
        return jsonify({
            'connected': False,
            'message': 'Internal server error'
        })

@api.route('/gitlab/disconnect', methods=['POST'])
def gitlab_disconnect():
    """Disconnect GitLab account."""
    # This is a placeholder - in a real implementation, you'd clear session/auth
    return jsonify({
        'success': True,
        'message': 'GitLab disconnected successfully'
    })

@api.route('/repository/<int:repo_id>/context', methods=['GET'])
def get_repository_context(repo_id):
    """Get comprehensive repository context including file relationships"""
    # Placeholder implementation
    return jsonify({
        'success': True,
        'context': {
            'repository_id': repo_id,
            'file_relationships': {},
            'architecture_context': {},
            'historical_patterns': {},
            'security_context': {},
            'performance_context': {}
        }
    })

@api.route('/repository/<int:repo_id>/file-relationships', methods=['GET'])
def get_file_relationships(repo_id):
    """Get detailed file relationships and dependencies"""
    # Placeholder implementation
    return jsonify({
        'success': True,
        'relationships': {
            'dependencies': {},
            'imports': {},
            'exports': {}
        },
        'visualization': {
            'nodes': [],
            'edges': [],
            'clusters': []
        }
    })

@api.route('/repository/<int:repo_id>/cache/build', methods=['POST'])
def build_repository_cache(repo_id):
    """Build or rebuild repository cache"""
    # Placeholder implementation
    return jsonify({
        'success': True,
        'message': 'Repository cache rebuilt successfully',
        'cache_stats': {
            'architecture_context': True,
            'historical_patterns': True,
            'file_relationships': True,
            'security_context': True,
            'performance_context': True
        }
    })

@api.route('/repository/<int:repo_id>/test-impact', methods=['POST'])
def analyze_test_impact(repo_id):
    """Analyze impact of changes on tests and suggest new test cases"""
    # Placeholder implementation
    return jsonify({
        'success': True,
        'test_impact': {
            'affected_tests': [],
            'suggested_tests': [],
            'coverage_impact': {},
            'risk_assessment': {}
        }
    })

@api.route('/v2/ai/chat', methods=['POST'])
def ai_chat_v2():
    """
    Enhanced AI chat endpoint that routes to specialized agents based on context.
    
    This endpoint provides intelligent routing to the appropriate enhanced agent
    based on the request mode and file types, with full Vertex AI integration.
    """
    try:
        # Initialize enhanced system if needed
        if not prompt_loader or not enhanced_agents or not vertex_ai_client:
            if not initialize_enhanced_system():
                return jsonify({'error': 'Enhanced AI system not available'}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '')
        mode = data.get('mode', 'general')
        model = data.get('model', 'gemini-2.5-pro')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Route based on mode and file context
        if mode == 'code' and context.get('selectedFile'):
            return handle_code_analysis_chat(message, context, model)
        elif mode == 'test':
            return handle_test_generation_chat(message, context, model)
        elif mode == 'security':
            return handle_security_analysis_chat(message, context, model)
        else:
            return handle_general_chat(message, context, model)
        
    except Exception as e:
        current_app.logger.error(f"Error in AI chat v2: {str(e)}")
        return jsonify({
            'error': 'AI chat failed',
            'details': str(e)
        }), 500

def handle_code_analysis_chat(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Handle code analysis chat requests with enhanced React agent"""
    
    selected_file = context.get('selectedFile', {})
    file_path = selected_file.get('path', '')
    file_content = selected_file.get('content', '')
    
    # Detect if this is a React file
    is_react_file = (
        file_path.endswith(('.tsx', '.jsx')) or
        'react' in file_content.lower() or
        'jsx' in file_content.lower() or
        'component' in file_content.lower()
    )
    
    if is_react_file and 'react_code' in enhanced_agents:
        # Use enhanced React agent
        try:
            # Build comprehensive context for React analysis
            enhanced_context = {
                'user_message': message,
                'selected_file': {
                    'path': file_path,
                    'content': file_content,
                    'language': detect_language(file_path)
                },
                'project_info': {
                    'type': 'react',
                    'technologies': ['react', 'typescript', 'javascript'],
                    'project_id': context.get('projectId'),
                    'branch': context.get('branch', 'main')
                },
                'conversation_history': [],
                'user_intent': classify_user_intent(message),
                'chat_mode': True,
                'vertex_ai_enabled': True
            }
            
            # Get enhanced prompt
            enhanced_prompt = prompt_loader.get_enhanced_prompt('react_code', enhanced_context)
            
            # Generate response using Vertex AI
            chat_result = asyncio.run(
                vertex_ai_client.chat_with_context(
                    message, enhanced_prompt, enhanced_context.get('conversation_history', [])
                )
            )
            
            # Format response for frontend
            response = {
                'response': chat_result.get('response', 'No response generated'),
                'success': chat_result.get('success', False),
                'metadata': {
                    'agent': 'enhanced_react_code',
                    'model': model,
                    'vertex_ai_powered': True,
                    'file_analyzed': file_path,
                    'context_used': True,
                    'gemini_optimized': True
                },
                'suggestions': chat_result.get('suggestions', []),
                'actions': generate_react_action_buttons(chat_result, enhanced_context),
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"Enhanced React analysis failed: {e}")
            # Fallback to general response
            pass
    
    # Fallback for non-React files or if enhanced agent fails
    return handle_general_code_analysis(message, context, model)

def handle_test_generation_chat(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Handle test generation requests"""
    
    selected_files = context.get('selectedFiles', [])
    test_config = context.get('testConfig', {})
    
    # Check if any React files are selected
    react_files = [f for f in selected_files if f.endswith(('.tsx', '.jsx'))]
    
    if react_files and 'react_test' in enhanced_agents:
        # Use React test agent if available
        try:
            test_context = {
                'user_message': message,
                'selected_files': react_files,
                'test_config': test_config,
                'project_info': {
                    'type': 'react',
                    'project_id': context.get('projectId'),
                    'branch': context.get('branch', 'main')
                },
                'chat_mode': True
            }
            
            # Generate test response
            response = {
                'response': f"I'll help you generate tests for your React components: {', '.join(react_files)}",
                'success': True,
                'metadata': {
                    'agent': 'react_test',
                    'model': model,
                    'files_count': len(react_files),
                    'test_type': test_config.get('type', 'unit')
                },
                'suggestions': [
                    {
                        'type': 'test_generation',
                        'title': 'Generate Unit Tests',
                        'description': 'Create comprehensive unit tests for React components',
                        'action': 'generate_unit_tests'
                    },
                    {
                        'type': 'test_generation',
                        'title': 'Generate Integration Tests',
                        'description': 'Create integration tests for component interactions',
                        'action': 'generate_integration_tests'
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"React test generation failed: {e}")
    
    # Fallback for general test generation
    return handle_general_test_generation(message, context, model)

def handle_security_analysis_chat(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Handle security analysis requests"""
    
    selected_files = context.get('selectedFiles', [])
    security_config = context.get('securityConfig', {})
    
    if 'security_scanner' in enhanced_agents:
        try:
            security_context = {
                'user_message': message,
                'selected_files': selected_files,
                'security_config': security_config,
                'project_info': {
                    'project_id': context.get('projectId'),
                    'branch': context.get('branch', 'main')
                },
                'chat_mode': True
            }
            
            response = {
                'response': f"I'll perform a security analysis on the selected files: {', '.join(selected_files)}",
                'success': True,
                'metadata': {
                    'agent': 'security_scanner',
                    'model': model,
                    'files_count': len(selected_files),
                    'scan_type': 'comprehensive'
                },
                'suggestions': [
                    {
                        'type': 'security',
                        'title': 'Vulnerability Scan',
                        'description': 'Scan for common security vulnerabilities',
                        'action': 'scan_vulnerabilities'
                    },
                    {
                        'type': 'security',
                        'title': 'Dependency Check',
                        'description': 'Check dependencies for known vulnerabilities',
                        'action': 'check_dependencies'
                    }
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"Security analysis failed: {e}")
    
    return handle_general_security_analysis(message, context, model)

def handle_general_chat(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Handle general chat requests"""
    
    if vertex_ai_client:
        try:
            # Use Vertex AI for general chat
            chat_result = asyncio.run(
                vertex_ai_client.chat_with_context(
                    message, 
                    "You are a helpful AI coding assistant. Provide clear, concise, and helpful responses.",
                    []
                )
            )
            
            response = {
                'response': chat_result.get('response', 'I can help you with code analysis, testing, and security. What would you like to work on?'),
                'success': chat_result.get('success', True),
                'metadata': {
                    'agent': 'general_ai',
                    'model': model,
                    'vertex_ai_powered': True
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response)
            
        except Exception as e:
            current_app.logger.error(f"General chat failed: {e}")
    
    # Fallback response
    response = {
        'response': f"I understand you want to: {message}\n\nI can help you with:\n- Code analysis and review\n- Test generation\n- Security scanning\n- Performance optimization\n\nPlease select a file and choose a specific mode for more detailed assistance.",
        'success': True,
        'metadata': {
            'agent': 'fallback',
            'model': 'local'
        },
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(response)

# Helper functions for chat handling

def handle_general_code_analysis(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Fallback code analysis for non-React files"""
    
    selected_file = context.get('selectedFile', {})
    file_path = selected_file.get('path', '')
    
    response = {
        'response': f"I'll analyze the code in {file_path}. This appears to be a {detect_language(file_path)} file.\n\n{message}",
        'success': True,
        'metadata': {
            'agent': 'general_code',
            'model': model,
            'file_type': detect_language(file_path)
        },
        'suggestions': [
            {
                'type': 'analysis',
                'title': 'Code Review',
                'description': 'Perform a comprehensive code review',
                'action': 'review_code'
            }
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(response)

def handle_general_test_generation(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Fallback test generation"""
    
    response = {
        'response': f"I'll help you generate tests. {message}",
        'success': True,
        'metadata': {
            'agent': 'general_test',
            'model': model
        },
        'suggestions': [
            {
                'type': 'test',
                'title': 'Generate Tests',
                'description': 'Create test cases for the selected files',
                'action': 'generate_tests'
            }
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(response)

def handle_general_security_analysis(message: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
    """Fallback security analysis"""
    
    response = {
        'response': f"I'll perform a security analysis. {message}",
        'success': True,
        'metadata': {
            'agent': 'general_security',
            'model': model
        },
        'suggestions': [
            {
                'type': 'security',
                'title': 'Security Scan',
                'description': 'Scan for security issues',
                'action': 'security_scan'
            }
        ],
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(response)

def generate_react_action_buttons(chat_result: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate action buttons for React analysis responses"""
    
    actions = [
        {
            'id': 'optimize_component',
            'title': 'Optimize Component',
            'description': 'Suggest performance optimizations',
            'type': 'optimization',
            'icon': 'fas fa-rocket'
        },
        {
            'id': 'generate_tests',
            'title': 'Generate Tests',
            'description': 'Create test cases for this component',
            'type': 'testing',
            'icon': 'fas fa-vial'
        },
        {
            'id': 'check_accessibility',
            'title': 'Check Accessibility',
            'description': 'Review accessibility compliance',
            'type': 'accessibility',
            'icon': 'fas fa-universal-access'
        },
        {
            'id': 'refactor_suggestions',
            'title': 'Refactor Suggestions',
            'description': 'Get refactoring recommendations',
            'type': 'refactoring',
            'icon': 'fas fa-code'
        }
    ]
    
    return actions

def detect_language(file_path):
    """Detect programming language from file extension"""
    if not file_path:
        return 'unknown'
    
    ext = file_path.split('.')[-1].lower()
    return {
        'tsx': 'typescript',
        'ts': 'typescript',
        'jsx': 'javascript',
        'js': 'javascript',
        'py': 'python'
    }.get(ext, 'unknown')

def classify_user_intent(message):
    """Classify user intent from message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['analyze', 'review', 'check']):
        return 'analysis'
    elif any(word in message_lower for word in ['optimize', 'improve', 'performance']):
        return 'optimization'
    elif any(word in message_lower for word in ['fix', 'error', 'bug', 'issue']):
        return 'debugging'
    elif any(word in message_lower for word in ['refactor', 'clean', 'restructure']):
        return 'refactoring'
    elif any(word in message_lower for word in ['test', 'testing', 'spec']):
        return 'testing'
    else:
        return 'general'

# Enhanced API Endpoints

@api.route('/react/analyze', methods=['POST'])
def analyze_react_enhanced():
    """
    Enhanced React code analysis with Cursor-style prompting and Gemini optimization.
    
    This endpoint provides comprehensive React analysis using the enhanced prompt system
    with full context awareness and Vertex AI integration.
    """
    try:
        # Initialize system if not already done
        if not prompt_loader or 'react_code' not in enhanced_agents or not vertex_ai_client:
            if not initialize_enhanced_system():
                return jsonify({'error': 'Enhanced system not available'}), 503
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract required fields
        file_content = data.get('content', '')
        file_path = data.get('filePath', 'unknown.tsx')
        user_message = data.get('message', 'Analyze this React component')
        
        if not file_content:
            return jsonify({'error': 'File content is required'}), 400
        
        # Build comprehensive context
        context = build_comprehensive_context(data, user_message)
        
        # Get enhanced prompt from prompt loader
        enhanced_prompt = prompt_loader.get_enhanced_prompt('react_code', context)
        
        # Perform enhanced analysis using Vertex AI
        vertex_result = asyncio.run(
            vertex_ai_client.analyze_with_enhanced_prompt(enhanced_prompt, context)
        )
        
        # Perform agent analysis for additional insights
        agent_result = asyncio.run(
            enhanced_agents['react_code'].analyze_with_enhanced_prompts(
                file_path, file_content, context
            )
        )
        
        # Combine results
        combined_result = combine_analysis_results(vertex_result, agent_result)
        
        # Format response for frontend
        formatted_response = format_enhanced_response(combined_result, context)
        
        return jsonify(formatted_response)
        
    except Exception as e:
        current_app.logger.error(f"Error in enhanced React analysis: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'details': str(e)
        }), 500

@api.route('/react/chat', methods=['POST'])
def chat_with_react_agent():
    """
    Interactive chat with the enhanced React agent using Vertex AI and Cursor-style conversation.
    """
    try:
        if not prompt_loader or 'react_code' not in enhanced_agents or not vertex_ai_client:
            if not initialize_enhanced_system():
                return jsonify({'error': 'Enhanced system not available'}), 503
        
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Build chat context
        chat_context = build_chat_context(data, message)
        
        # Get enhanced prompt for conversational response
        enhanced_prompt = prompt_loader.get_enhanced_prompt('react_code', chat_context)
        
        # Generate conversational response using Vertex AI
        chat_result = asyncio.run(
            vertex_ai_client.chat_with_context(
                message, enhanced_prompt, chat_context.get('conversation_history', [])
            )
        )
        
        return jsonify({
            'response': chat_result.get('response', 'No response generated'),
            'success': chat_result.get('success', False),
            'metadata': chat_result.get('metadata', {}),
            'context_used': True,
            'agent': 'enhanced_react_code',
            'vertex_ai_powered': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in React chat: {str(e)}")
        return jsonify({
            'error': 'Chat failed',
            'details': str(e)
        }), 500

@api.route('/react/suggestions', methods=['POST'])
def get_react_suggestions():
    """
    Get intelligent React code suggestions with Vertex AI and context awareness.
    """
    try:
        if not prompt_loader or 'react_code' not in enhanced_agents or not vertex_ai_client:
            if not initialize_enhanced_system():
                return jsonify({'error': 'Enhanced system not available'}), 503
        
        data = request.get_json()
        file_content = data.get('content', '')
        file_path = data.get('filePath', '')
        cursor_position = data.get('cursorPosition', {})
        
        # Build suggestion context
        suggestion_context = build_suggestion_context(data, cursor_position)
        
        # Get enhanced prompt for suggestions
        enhanced_prompt = prompt_loader.get_enhanced_prompt('react_code', suggestion_context)
        
        # Generate intelligent suggestions using Vertex AI
        suggestions = asyncio.run(
            vertex_ai_client.generate_suggestions(enhanced_prompt, suggestion_context)
        )
        
        return jsonify({
            'suggestions': suggestions,
            'context_aware': True,
            'vertex_ai_powered': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error generating suggestions: {str(e)}")
        return jsonify({
            'error': 'Suggestion generation failed',
            'details': str(e)
        }), 500

@api.route('/vertex-ai/health', methods=['GET'])
def check_vertex_ai_health():
    """
    Check Vertex AI connection and model availability.
    """
    try:
        if not vertex_ai_client:
            if not initialize_enhanced_system():
                return jsonify({
                    'status': 'unavailable',
                    'error': 'Vertex AI client not initialized'
                }), 503
        
        health_status = vertex_ai_client.health_check()
        
        return jsonify(health_status)
        
    except Exception as e:
        current_app.logger.error(f"Error checking Vertex AI health: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@api.route('/system/performance', methods=['GET'])
def get_enhanced_performance():
    """
    Get performance metrics for the enhanced prompt system with Vertex AI.
    """
    try:
        # Check Vertex AI health if available
        vertex_ai_status = None
        if vertex_ai_client:
            vertex_ai_status = vertex_ai_client.health_check()
        
        performance_metrics = {
            'prompt_system': {
                'status': 'active' if prompt_loader else 'inactive',
                'loaded_prompts': len(prompt_loader.get_available_agents()) if prompt_loader else 0,
                'context_window_usage': calculate_context_usage(),
                'optimization_level': 'gemini_2.5_pro'
            },
            'vertex_ai': {
                'status': vertex_ai_status.get('status', 'unknown') if vertex_ai_status else 'inactive',
                'model': vertex_ai_status.get('model', 'unknown') if vertex_ai_status else 'unknown',
                'project_id': vertex_ai_status.get('project_id', 'unknown') if vertex_ai_status else 'unknown',
                'gemini_2_5_pro_available': vertex_ai_status.get('gemini_2_5_pro_available', False) if vertex_ai_status else False
            },
            'agents': {
                'active_agents': len(enhanced_agents),
                'react_code_status': 'active' if 'react_code' in enhanced_agents else 'inactive'
            },
            'performance': {
                'average_response_time': get_average_response_time(),
                'context_efficiency': calculate_context_efficiency(),
                'gemini_optimization': 'enabled' if vertex_ai_client else 'disabled',
                'enhanced_prompting': 'enabled' if prompt_loader else 'disabled'
            }
        }
        
        return jsonify(performance_metrics)
        
    except Exception as e:
        current_app.logger.error(f"Error getting performance metrics: {str(e)}")
        return jsonify({
            'error': 'Performance metrics unavailable',
            'details': str(e)
        }), 500

# Helper Functions for Enhanced API with Vertex AI

def combine_analysis_results(vertex_result: Dict[str, Any], agent_result: Dict[str, Any]) -> Dict[str, Any]:
    """Combine Vertex AI and agent analysis results"""
    
    combined = agent_result.copy()
    
    # Integrate Vertex AI analysis
    if vertex_result.get('success'):
        combined.update({
            'vertex_ai_analysis': vertex_result.get('analysis', ''),
            'vertex_ai_metadata': vertex_result.get('metadata', {}),
            'vertex_ai_performance': vertex_result.get('performance_metrics', {}),
            'gemini_optimized': True
        })
        
        # Merge the analyses
        agent_analysis = combined.get('enhanced_analysis', combined.get('analysis', ''))
        vertex_analysis = vertex_result.get('analysis', '')
        
        if vertex_analysis and agent_analysis:
            combined['analysis'] = f"{vertex_analysis}\n\n---\n\n{agent_analysis}"
        elif vertex_analysis:
            combined['analysis'] = vertex_analysis
    
    return combined

def generate_conversational_response(message, context, agent_prompt):
    """Generate a conversational response using Vertex AI if available"""
    if vertex_ai_client:
        try:
            result = asyncio.run(
                vertex_ai_client.chat_with_context(
                    message, agent_prompt, context.get('conversation_history', [])
                )
            )
            return result.get('response', 'No response generated')
        except Exception as e:
            current_app.logger.error(f"Vertex AI chat failed: {e}")
    
    # Fallback response
    response_template = f"""
I'll help you with your React development question: "{message}"

Based on the enhanced context and my analysis, here's my response:

[Enhanced analysis would be provided here using Gemini 2.5 Pro]

Would you like me to:
- Provide more specific code examples?
- Analyze related files for better context?
- Suggest performance optimizations?
- Generate tests for this component?
"""
    
    return response_template

def generate_intelligent_suggestions(file_content, file_path, context):
    """Generate intelligent code suggestions using Vertex AI if available"""
    if vertex_ai_client and prompt_loader:
        try:
            enhanced_prompt = prompt_loader.get_enhanced_prompt('react_code', context)
            suggestions = asyncio.run(
                vertex_ai_client.generate_suggestions(enhanced_prompt, context)
            )
            return suggestions
        except Exception as e:
            current_app.logger.error(f"Vertex AI suggestions failed: {e}")
    
    # Fallback suggestions
    suggestions = []
    cursor_position = context.get('cursor_position', {})
    current_line = context.get('current_line', '')
    
    if 'useState' in current_line:
        suggestions.append({
            'type': 'completion',
            'text': 'const [state, setState] = useState()',
            'description': 'Complete useState hook declaration',
            'priority': 'high'
        })
    
    if 'useEffect' in current_line:
        suggestions.append({
            'type': 'completion',
            'text': 'useEffect(() => {\n  // effect logic\n  return () => {\n    // cleanup\n  };\n}, []);',
            'description': 'Complete useEffect with cleanup',
            'priority': 'high'
        })
    
    return suggestions

# Performance calculation helpers

def calculate_context_usage():
    """Calculate context window usage percentage"""
    return 0.15  # 15% usage estimate

def get_average_response_time():
    """Get average response time in milliseconds"""
    return 850  # 850ms estimate

def calculate_context_efficiency():
    """Calculate how efficiently context is being used"""
    return 0.92  # 92% efficiency

def extract_performance_recommendations(result):
    """Extract performance-specific recommendations"""
    suggestions = result.get('enhanced_suggestions', result.get('suggestions', []))
    return [s for s in suggestions if s.get('type') == 'performance']

def extract_accessibility_score(result):
    """Extract accessibility score from analysis"""
    metadata = result.get('metadata', {})
    return metadata.get('accessibility_score', 0)

def extract_type_safety_score(result):
    """Extract TypeScript type safety score"""
    metadata = result.get('metadata', {})
    return metadata.get('type_safety_score', 0)

def generate_action_buttons(result, context):
    """Generate contextual action buttons for the frontend"""
    actions = []
    
    # Always available actions
    actions.extend([
        {
            'id': 'optimize-performance',
            'type': 'primary',
            'icon': 'fas fa-rocket',
            'label': 'Optimize Performance'
        },
        {
            'id': 'generate-tests',
            'type': 'secondary',
            'icon': 'fas fa-vial',
            'label': 'Generate Tests'
        }
    ])
    
    # Conditional actions based on analysis
    if result.get('enhanced_suggestions', result.get('suggestions')):
        actions.append({
            'id': 'apply-suggestions',
            'type': 'success',
            'icon': 'fas fa-magic',
            'label': 'Apply Suggestions'
        })
    
    accessibility_score = extract_accessibility_score(result)
    if accessibility_score < 0.8:
        actions.append({
            'id': 'improve-accessibility',
            'type': 'warning',
            'icon': 'fas fa-universal-access',
            'label': 'Improve Accessibility'
        })
    
    return actions

def build_comprehensive_context(request_data, user_message):
    """Build comprehensive context for enhanced analysis"""
    return {
        'user_message': user_message,
        'selected_file': {
            'path': request_data.get('filePath', ''),
            'name': request_data.get('name', ''),
            'content': request_data.get('content', ''),
            'language': request_data.get('language', '')
        },
        'project_info': {
            'type': request_data.get('projectType', 'react'),
            'technologies': request_data.get('technologies', ['react', 'typescript']),
            'dependencies': request_data.get('dependencies', []),
            'structure': request_data.get('projectStructure', {})
        },
        'conversation_history': request_data.get('conversationHistory', []),
        'related_files': request_data.get('relatedFiles', []),
        'user_intent': classify_user_intent(user_message),
        'performance_context': {
            'gemini_model': 'gemini-2.5-pro',
            'context_window': '1M tokens',
            'optimization_enabled': True
        }
    }

def build_chat_context(request_data, message):
    """Build context for chat interactions"""
    return {
        'conversation_history': request_data.get('conversationHistory', []),
        'current_file': request_data.get('currentFile', {}),
        'project_context': request_data.get('projectContext', {}),
        'user_intent': classify_user_intent(message),
        'chat_mode': True
    }

def build_suggestion_context(request_data, cursor_position):
    """Build context for intelligent suggestions"""
    return {
        'cursor_position': cursor_position,
        'current_line': request_data.get('currentLine', ''),
        'surrounding_code': request_data.get('surroundingCode', ''),
        'project_patterns': request_data.get('projectPatterns', []),
        'recent_edits': request_data.get('recentEdits', [])
    }

def format_enhanced_response(result, context):
    """Format the enhanced analysis result for the frontend"""
    return {
        'success': result.get('success', False),
        'analysis': result.get('enhanced_analysis', result.get('analysis', '')),
        'metadata': {
            'file_metrics': result.get('metadata', {}),
            'confidence_score': result.get('enhanced_confidence_score', result.get('confidence_score', 0)),
            'processing_time': result.get('processing_time', ''),
            'tokens_used': result.get('tokens_used', 0),
            'context_used': result.get('context_used', False),
            'gemini_optimized': result.get('gemini_optimized', False)
        },
        'suggestions': result.get('enhanced_suggestions', result.get('suggestions', [])),
        'insights': {
            'cross_file_analysis': result.get('cross_file_insights', {}),
            'performance_recommendations': extract_performance_recommendations(result),
            'accessibility_score': extract_accessibility_score(result),
            'type_safety_score': extract_type_safety_score(result)
        },
        'actions': generate_action_buttons(result, context),
        'agent_info': {
            'agent': 'enhanced_react_code',
            'version': '3.0.0',
            'optimization': 'gemini_2.5_pro'
        }
    } 