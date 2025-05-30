"""
CI Code Companion API Routes
Provides endpoints for code analysis, metrics, and suggestions
"""

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import json

from ci_code_companion.models import (
    Repository, Commit, CodeFile, FileChange, 
    AIAnalysis, CodeIssue, PerformanceMetrics
)

# Create blueprint
api = Blueprint('api', __name__, url_prefix='/api/v2')

# Database setup
def init_database():
    """Initialize database connection and create tables if they don't exist"""
    engine = create_engine(current_app.config['DATABASE_URL'])
    Session = sessionmaker(bind=engine)
    return Session()

# Helper functions
def calculate_metrics(session):
    """Calculate overall metrics from the database"""
    try:
        # Get recent analyses
        recent_analyses = session.query(AIAnalysis)\
            .order_by(AIAnalysis.created_at.desc())\
            .limit(100)\
            .all()
        
        if not recent_analyses:
            return {
                'code_quality': 0,
                'security_score': 0,
                'test_coverage': 0,
                'active_issues': 0
            }
        
        # Calculate averages
        total_quality = sum(a.code_quality for a in recent_analyses if a.code_quality)
        total_security = sum(a.security_score for a in recent_analyses if a.security_score)
        total_coverage = sum(a.test_coverage for a in recent_analyses if a.test_coverage)
        
        # Count active issues
        active_issues = session.query(CodeIssue)\
            .filter(CodeIssue.status == 'open')\
            .count()
        
        count = len(recent_analyses)
        return {
            'code_quality': round(total_quality / count if count > 0 else 0, 1),
            'security_score': round(total_security / count if count > 0 else 0, 1),
            'test_coverage': round(total_coverage / count if count > 0 else 0, 1),
            'active_issues': active_issues
        }
    except Exception as e:
        current_app.logger.error(f"Error calculating metrics: {str(e)}")
        return None

def get_trend_data(session, days=30):
    """Get trend data for charts"""
    try:
        # Get metrics for the last N days
        start_date = datetime.utcnow() - timedelta(days=days)
        metrics = session.query(PerformanceMetrics)\
            .filter(PerformanceMetrics.recorded_at >= start_date)\
            .order_by(PerformanceMetrics.recorded_at)\
            .all()
        
        # Group by date
        daily_metrics = {}
        for metric in metrics:
            date_key = metric.recorded_at.strftime('%Y-%m-%d')
            if date_key not in daily_metrics:
                daily_metrics[date_key] = {
                    'quality': [],
                    'security': [],
                    'coverage': []
                }
            
            if metric.metric_name == 'code_quality':
                daily_metrics[date_key]['quality'].append(metric.metric_value)
            elif metric.metric_name == 'security_score':
                daily_metrics[date_key]['security'].append(metric.metric_value)
            elif metric.metric_name == 'test_coverage':
                daily_metrics[date_key]['coverage'].append(metric.metric_value)
        
        # Calculate daily averages
        trend_data = {
            'dates': [],
            'quality': [],
            'security': [],
            'coverage': []
        }
        
        for date, values in sorted(daily_metrics.items()):
            trend_data['dates'].append(date)
            trend_data['quality'].append(
                sum(values['quality']) / len(values['quality']) if values['quality'] else 0
            )
            trend_data['security'].append(
                sum(values['security']) / len(values['security']) if values['security'] else 0
            )
            trend_data['coverage'].append(
                sum(values['coverage']) / len(values['coverage']) if values['coverage'] else 0
            )
        
        return trend_data
    except Exception as e:
        current_app.logger.error(f"Error getting trend data: {str(e)}")
        return None

# API Routes

@api.route('/metrics')
def get_metrics():
    """Get current metrics and trends"""
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
        session.close()

@api.route('/issues/summary')
def get_issues_summary():
    """Get summary of current issues"""
    try:
        session = init_database()
        
        # Get issue counts by severity
        severity_counts = session.query(
            CodeIssue.severity,
            text('COUNT(*) as count')
        ).group_by(CodeIssue.severity).all()
        
        # Get issue counts by category
        category_counts = session.query(
            CodeIssue.category,
            text('COUNT(*) as count')
        ).group_by(CodeIssue.category).all()
        
        return jsonify({
            'by_severity': dict(severity_counts),
            'by_category': dict(category_counts)
        })
    except Exception as e:
        current_app.logger.error(f"Error in /issues/summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()

@api.route('/activity/recent')
def get_recent_activity():
    """Get recent activity across all repositories"""
    try:
        session = init_database()
        
        # Get recent commits
        recent_commits = session.query(Commit)\
            .order_by(Commit.committed_at.desc())\
            .limit(10)\
            .all()
        
        # Get recent analyses
        recent_analyses = session.query(AIAnalysis)\
            .order_by(AIAnalysis.created_at.desc())\
            .limit(10)\
            .all()
        
        # Combine and sort activities
        activities = []
        
        for commit in recent_commits:
            activities.append({
                'type': 'commit',
                'message': commit.message,
                'author': commit.author,
                'timestamp': commit.committed_at.isoformat(),
                'repository_id': commit.repository_id
            })
        
        for analysis in recent_analyses:
            activities.append({
                'type': 'analysis',
                'message': f"Analyzed commit {analysis.commit_hash[:7]}",
                'quality_score': analysis.code_quality,
                'security_score': analysis.security_score,
                'timestamp': analysis.created_at.isoformat(),
                'repository_id': analysis.repository_id
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify(activities[:10])  # Return most recent 10
    except Exception as e:
        current_app.logger.error(f"Error in /activity/recent: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()

@api.route('/insights')
def get_ai_insights():
    """Get AI-generated insights about the codebase"""
    try:
        session = init_database()
        
        # Get recent analyses and their findings
        recent_analyses = session.query(AIAnalysis)\
            .order_by(AIAnalysis.created_at.desc())\
            .limit(5)\
            .all()
        
        insights = []
        for analysis in recent_analyses:
            # Parse stored insights
            if analysis.insights:
                analysis_insights = json.loads(analysis.insights)
                for insight in analysis_insights:
                    insights.append({
                        'id': f"{analysis.id}-{insight.get('id', 0)}",
                        'title': insight.get('title', 'Unnamed Insight'),
                        'description': insight.get('description', ''),
                        'category': insight.get('category', 'general'),
                        'priority': insight.get('priority', 'medium'),
                        'timestamp': analysis.created_at.isoformat()
                    })
        
        # Sort by priority (high -> medium -> low)
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        insights.sort(key=lambda x: priority_order.get(x['priority'], 99))
        
        return jsonify(insights[:5])  # Return top 5 insights
    except Exception as e:
        current_app.logger.error(f"Error in /insights: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()

@api.route('/suggestions/<int:file_id>')
def get_file_suggestions(file_id):
    """Get AI suggestions for a specific file"""
    try:
        session = init_database()
        
        # Get file and its latest analysis
        file = session.query(CodeFile).get(file_id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        latest_analysis = session.query(AIAnalysis)\
            .filter(AIAnalysis.repository_id == file.repository_id)\
            .order_by(AIAnalysis.created_at.desc())\
            .first()
        
        if not latest_analysis:
            return jsonify({'error': 'No analysis found'}), 404
        
        # Get suggestions for this file
        suggestions = []
        if latest_analysis.suggestions:
            all_suggestions = json.loads(latest_analysis.suggestions)
            for suggestion in all_suggestions:
                if suggestion.get('file_id') == file_id:
                    suggestions.append({
                        'id': suggestion.get('id'),
                        'line_number': suggestion.get('line_number'),
                        'old_content': suggestion.get('old_content'),
                        'new_content': suggestion.get('new_content'),
                        'issue_description': suggestion.get('description'),
                        'explanation': suggestion.get('explanation'),
                        'severity': suggestion.get('severity', 'medium'),
                        'category': suggestion.get('category', 'style'),
                        'impact': suggestion.get('impact', [])
                    })
        
        return jsonify(suggestions)
    except Exception as e:
        current_app.logger.error(f"Error in /suggestions/{file_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()

@api.route('/suggestions/<int:suggestion_id>/apply', methods=['POST'])
def apply_suggestion(suggestion_id):
    """Apply a specific suggestion"""
    try:
        session = init_database()
        
        # Get suggestion details from request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        file_id = data.get('file_id')
        if not file_id:
            return jsonify({'error': 'File ID required'}), 400
        
        # Get file
        file = session.query(CodeFile).get(file_id)
        if not file:
            return jsonify({'error': 'File not found'}), 404
        
        # Create file change record
        change = FileChange(
            file_id=file_id,
            change_type='suggestion_applied',
            old_content=data.get('old_content', ''),
            new_content=data.get('new_content', ''),
            metadata={
                'suggestion_id': suggestion_id,
                'applied_at': datetime.utcnow().isoformat(),
                'applied_by': data.get('user_id', 'system')
            }
        )
        session.add(change)
        
        # Update file content
        file.content = data.get('new_content', file.content)
        file.updated_at = datetime.utcnow()
        
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Suggestion applied successfully'
        })
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error applying suggestion {suggestion_id}: {str(e)}")
        return jsonify({'error': 'Failed to apply suggestion'}), 500
    finally:
        session.close()

@api.route('/suggestions/<int:suggestion_id>/reject', methods=['POST'])
def reject_suggestion(suggestion_id):
    """Reject a specific suggestion"""
    try:
        session = init_database()
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Record rejection
        rejection = {
            'suggestion_id': suggestion_id,
            'rejected_at': datetime.utcnow().isoformat(),
            'rejected_by': data.get('user_id', 'system'),
            'reason': data.get('reason', 'No reason provided')
        }
        
        # Store rejection data (you might want to create a proper model for this)
        metrics = PerformanceMetrics(
            metric_name='suggestion_rejection',
            metric_value=1,
            metric_unit='count',
            additional_data=rejection,
            recorded_at=datetime.utcnow()
        )
        session.add(metrics)
        session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Suggestion rejected successfully'
        })
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error rejecting suggestion {suggestion_id}: {str(e)}")
        return jsonify({'error': 'Failed to reject suggestion'}), 500
    finally:
        session.close()

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