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

# Note: AI system initialization is handled by ai_service.py
# This file contains only pure API request handlers

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

@api.route('/ai/chat', methods=['POST'])
def ai_chat():
    """
    Pure API handler - routes requests to AI service layer
    
    This endpoint only handles HTTP request/response and delegates to ai_service
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        message = data.get('message', '')
        mode = data.get('mode', 'general')
        model = data.get('model', 'gemini-2.5-pro')
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        current_app.logger.info(f"🌐 API HANDLER: Received {mode} request, delegating to AI service")
        
        # Import and use AI service
        try:
            from ci_code_companion_sdk.services.ai_service import StreamlinedAIService
            from ci_code_companion_sdk.core.config import SDKConfig
            
            # Initialize AI service
            config = SDKConfig()
            ai_service = StreamlinedAIService(config, current_app.logger)
            
            # Delegate to AI service based on mode
            if mode == 'code':
                result = asyncio.run(ai_service.handle_code_analysis(message, context, model))
            elif mode == 'test':
                result = asyncio.run(ai_service.handle_test_generation(message, context, model))
            elif mode == 'security':
                result = asyncio.run(ai_service.handle_security_analysis(message, context, model))
            else:
                result = asyncio.run(ai_service.handle_general_chat(message, context, model))
            
            current_app.logger.info(f"✅ API HANDLER: AI service completed, returning result")
            return jsonify(result)
            
        except ImportError as e:
            current_app.logger.error(f"❌ AI SERVICE IMPORT ERROR: {e}")
            return jsonify({
                'success': False,
                'error': 'AI service not available',
                'message': 'Please check AI service configuration'
            }), 503
        
    except Exception as e:
        current_app.logger.error(f"❌ API HANDLER ERROR: {str(e)}")
        return jsonify({
            'error': 'API request failed',
            'details': str(e)
        }), 500

# Helper functions for chat handling

# Utility functions for language detection and intent classification
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

# End of API routes 