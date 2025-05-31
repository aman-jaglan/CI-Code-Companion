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

# Import AI agents
try:
    from ai_agents.multi_tech_agents import (
        analyze_react_file, analyze_python_file, analyze_node_file, analyze_database_file,
        analyze_devops_file, analyze_mobile_file, analyze_general_file,
        generate_react_tests, generate_python_tests, generate_node_tests, generate_database_tests,
        generate_devops_tests, generate_mobile_tests, generate_general_tests,
        optimize_react_code, optimize_python_code, optimize_node_code, optimize_database_code,
        optimize_devops_code, optimize_mobile_code, optimize_general_code,
        chat_react_expert, chat_python_expert, chat_node_expert, chat_database_expert,
        chat_devops_expert, chat_mobile_expert, chat_general_expert,
        get_complete_project_structure, analyze_project_structure
    )
except ImportError as e:
    print(f"Warning: AI agents not available: {e}")
    # Create fallback functions
    def fallback_function(*args, **kwargs):
        return []
    
    # Set all functions to fallback
    analyze_react_file = analyze_python_file = analyze_node_file = fallback_function
    analyze_database_file = analyze_devops_file = analyze_mobile_file = fallback_function
    analyze_general_file = fallback_function
    
    def fallback_test_function(*args, **kwargs):
        return {
            'code': '// AI agents not available',
            'explanation': 'AI functionality is currently unavailable',
            'coverage_areas': [],
            'framework': 'none'
        }
    
    generate_react_tests = generate_python_tests = generate_node_tests = fallback_test_function
    generate_database_tests = generate_devops_tests = generate_mobile_tests = fallback_test_function
    generate_general_tests = fallback_test_function
    
    optimize_react_code = optimize_python_code = optimize_node_code = fallback_function
    optimize_database_code = optimize_devops_code = optimize_mobile_code = fallback_function
    optimize_general_code = fallback_function
    
    def fallback_chat_function(*args, **kwargs):
        return "AI chat functionality is currently unavailable. Please check the AI agents configuration."
    
    chat_react_expert = chat_python_expert = chat_node_expert = fallback_chat_function
    chat_database_expert = chat_devops_expert = chat_mobile_expert = fallback_chat_function
    chat_general_expert = fallback_chat_function
    
    def fallback_structure_function(*args, **kwargs):
        return {'files': [], 'directories': [], 'total_files': 0}
    
    def fallback_analysis_function(*args, **kwargs):
        return {'organization_score': 0, 'suggestions': [], 'issues': []}
    
    get_complete_project_structure = fallback_structure_function
    analyze_project_structure = fallback_analysis_function

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
        # Use the gitlab_api blueprint to get projects
        from routes.gitlab_api import get_projects
        return get_projects()
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
        language = data.get('language', 'python')
        
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
        
        def extract_code_context(content, line_number, context_lines=3):
            """Extract code context around a specific line."""
            lines = content.split('\n')
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            return {
                'start_line': start + 1,
                'end_line': end,
                'code': '\n'.join(lines[start:end]),
                'focus_line': line_number
            }
        
        def analyze_issue_context(content, issue_description):
            """Analyze the context of an issue to find relevant code sections."""
            lines = content.split('\n')
            context = None
            
            # Look for code patterns mentioned in the issue
            for i, line in enumerate(lines, 1):
                # Extract potential code snippets or patterns from issue description
                if any(pattern in line for pattern in extract_code_patterns(issue_description)):
                    context = extract_code_context(content, i)
                    break
            
            return context
        
        def extract_code_patterns(description):
            """Extract potential code patterns from issue description."""
            # Extract quoted code, function names, variable names, etc.
            patterns = []
            
            # Look for quoted code
            import re
            quoted = re.findall(r'`([^`]+)`', description)
            patterns.extend(quoted)
            
            # Look for common code patterns
            code_patterns = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*\([^)]*\))', description)
            patterns.extend(code_patterns)
            
            return patterns
        
        def analyze_code_structure(code, lang='python'):
            """Analyze code structure to determine proper indentation and context."""
            lines = code.split('\n')
            structure = {
                'indent_map': {},
                'context_map': {},
                'block_starts': set(),
                'block_ends': set(),
                'indent_size': 4 if lang in ['python'] else 2
            }
            
            stack = []
            current_class = None
            current_function = None
            
            for i, line in enumerate(lines):
                line_num = i + 1
                trimmed = line.strip()
                
                # Skip empty lines but maintain context
                if not trimmed:
                    structure['indent_map'][line_num] = len(stack)
                    continue
                
                # Detect block starts
                if trimmed.endswith(':'):
                    structure['block_starts'].add(line_num)
                    stack.append(line_num)
                
                # Track class and function context
                if trimmed.startswith('class '):
                    current_class = trimmed.split('class ')[1].split('(')[0].split(':')[0].strip()
                    structure['context_map'][line_num] = {'class': current_class, 'function': None}
                elif trimmed.startswith('def '):
                    current_function = trimmed.split('def ')[1].split('(')[0].strip()
                    structure['context_map'][line_num] = {'class': current_class, 'function': current_function}
                
                # Detect block ends
                if stack and (trimmed.startswith('return') or trimmed.startswith('break') or 
                            trimmed.startswith('continue') or trimmed.startswith('raise')):
                    structure['block_ends'].add(line_num)
                    if stack:
                        stack.pop()
                
                # Store indentation level
                structure['indent_map'][line_num] = len(stack)
            
            return structure
        
        def apply_proper_indentation(code, structure):
            """Apply proper indentation based on code structure analysis."""
            lines = code.split('\n')
            result = []
            
            for i, line in enumerate(lines, 1):
                if not line.strip():
                    result.append('')
                    continue
                
                indent_level = structure['indent_map'].get(i, 0)
                indent = ' ' * (indent_level * structure['indent_size'])
                result.append(indent + line.strip())
            
            return '\n'.join(result)
        
        def complete_code_block(code, structure, language):
            """Complete code blocks by adding necessary closing statements."""
            lines = code.split('\n')
            completions = []
            
            # Add missing block endings
            for block_start in structure['block_starts']:
                if block_start not in structure['block_ends']:
                    indent_level = structure['indent_map'].get(block_start, 0)
                    indent = ' ' * (indent_level * structure['indent_size'])
                    
                    # Add appropriate closing statement based on language
                    if language == 'python':
                        if 'class' in structure['context_map'].get(block_start, {}):
                            completions.append(f"{indent}    pass")
                        elif 'function' in structure['context_map'].get(block_start, {}):
                            completions.append(f"{indent}    return None")
                        else:
                            completions.append(f"{indent}    pass")
            
            if completions:
                lines.extend(completions)
            
            return '\n'.join(lines)
        
        result = {}
        
        if action == 'review':
            reviewer = CodeReviewer(ai_client)
            review_result = reviewer.review_code_content(content, file_path)
            
            # Enhance issues with context
            if 'issues' in review_result:
                enhanced_issues = []
                for i, issue in enumerate(review_result['issues']):
                    issue_context = analyze_issue_context(content, issue)
                    enhanced_issues.append({
                        'id': i + 1,
                        'description': issue,
                        'context': issue_context,
                        'severity': determine_issue_severity(issue),
                        'category': categorize_issue(issue)
                    })
                review_result['issues'] = enhanced_issues
            
            # Enhance suggested changes
            if 'suggested_changes' in review_result:
                for i, change in enumerate(review_result['suggested_changes']):
                    if 'new_content' in change:
                        # Analyze structure of the new content
                        structure = analyze_code_structure(change['new_content'], language)
                        
                        # Complete any incomplete code blocks
                        completed_code = complete_code_block(change['new_content'], structure, language)
                        
                        # Apply proper indentation
                        indented_code = apply_proper_indentation(completed_code, structure)
                        
                        # Add context information
                        raw_line_num_context = change.get('line_number', '1') # Default to 1 if not present
                        line_for_context = -1
                        try:
                            if isinstance(raw_line_num_context, str) and '-' in raw_line_num_context:
                                start_str, _ = raw_line_num_context.split("-", 1)
                                line_for_context = int(start_str.strip())
                            else:
                                line_for_context = int(raw_line_num_context)
                        except ValueError:
                            logger.warning(f"Could not parse line_number '{raw_line_num_context}' for context, defaulting to 1.")
                            line_for_context = 1

                        change.update({
                            'issue_index': determine_related_issue(change, review_result['issues']),
                            'change_index': i,
                            'context': extract_code_context(content, line_for_context),
                            'new_content': indented_code,
                            'change_type': determine_change_type(change),
                            'impact': assess_change_impact(change)
                        })
            
            result = {
                'action': 'review',
                'file_path': file_path,
                'analysis': review_result,
                'timestamp': datetime.now().isoformat()
            }
            
        elif action == 'test-generation':
            test_generator = TestGenerator(ai_client)
            test_result = test_generator.generate_tests(content, file_path)
            
            if 'test_code' in test_result:
                structure = analyze_code_structure(test_result['test_code'], language)
                completed_code = complete_code_block(test_result['test_code'], structure, language)
                test_result['test_code'] = apply_proper_indentation(completed_code, structure)
            
            result = {
                'action': 'test-generation',
                'file_path': file_path,
                'tests': test_result,
                'timestamp': datetime.now().isoformat()
            }
            
        elif action == 'improve':
            reviewer = CodeReviewer(ai_client)
            improvement_result = reviewer.review_code_content(content, file_path, review_type="comprehensive")
            
            if 'suggested_changes' in improvement_result:
                for change in improvement_result['suggested_changes']:
                    if 'new_content' in change:
                        structure = analyze_code_structure(change['new_content'], language)
                        completed_code = complete_code_block(change['new_content'], structure, language)
                        change['new_content'] = apply_proper_indentation(completed_code, structure)
            
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

def determine_issue_severity(issue):
    """Determine the severity level of an issue."""
    keywords = {
        'critical': ['critical', 'severe', 'security', 'crash', 'memory leak'],
        'high': ['error', 'bug', 'incorrect', 'wrong', 'fail'],
        'medium': ['warning', 'potential', 'might', 'could', 'consider'],
        'low': ['style', 'formatting', 'documentation', 'suggestion']
    }
    
    issue_lower = issue.lower()
    for severity, words in keywords.items():
        if any(word in issue_lower for word in words):
            return severity
    return 'medium'

def categorize_issue(issue):
    """Categorize the type of issue."""
    categories = {
        'security': ['security', 'vulnerability', 'injection', 'xss', 'csrf'],
        'performance': ['performance', 'slow', 'optimization', 'memory', 'cpu'],
        'reliability': ['error', 'exception', 'crash', 'bug', 'incorrect'],
        'maintainability': ['duplicate', 'complex', 'readability', 'naming'],
        'style': ['style', 'formatting', 'whitespace', 'indentation']
    }
    
    issue_lower = issue.lower()
    for category, keywords in categories.items():
        if any(keyword in issue_lower for keyword in keywords):
            return category
    return 'general'

def determine_change_type(change):
    """Determine the type of code change."""
    old_content = change.get('old_content', '')
    new_content = change.get('new_content', '')
    
    if not old_content and new_content:
        return 'addition'
    elif old_content and not new_content:
        return 'deletion'
    else:
        return 'modification'

def assess_change_impact(change):
    """Assess the potential impact of a code change."""
    impacts = []
    
    # Check for function signature changes
    if 'def ' in change.get('old_content', '') and 'def ' in change.get('new_content', ''):
        impacts.append('function_signature')
    
    # Check for control flow changes
    if any(keyword in change.get('new_content', '') for keyword in ['if', 'for', 'while', 'try']):
        impacts.append('control_flow')
    
    # Check for error handling changes
    if any(keyword in change.get('new_content', '') for keyword in ['except', 'raise', 'try']):
        impacts.append('error_handling')
    
    return impacts

def determine_related_issue(change, issues):
    """Determine which issue this change is related to."""
    change_content = f"{change.get('old_content', '')} {change.get('new_content', '')}"
    
    for i, issue in enumerate(issues):
        # Look for keywords from the issue description in the change
        if any(keyword in change_content.lower() for keyword in issue['description'].lower().split()):
            return i
    
    return None

@app.route('/project-selector')
def project_selector():
    return render_template('project_selector.html')

# AI Assistant Multi-Technology System
@app.route('/ai/review-file', methods=['POST'])
def review_file_ai():
    """AI-powered file review with technology-specific analysis"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        file_content = data.get('file_content')
        language = data.get('language')
        agent = data.get('agent', 'general')
        project_context = data.get('project_context', {})
        
        # Route to appropriate agent
        if agent == 'frontend-react':
            issues = analyze_react_file(file_content, file_path, project_context)
        elif agent == 'backend-python':
            issues = analyze_python_file(file_content, file_path, project_context)
        elif agent == 'backend-node':
            issues = analyze_node_file(file_content, file_path, project_context)
        elif agent == 'database':
            issues = analyze_database_file(file_content, file_path, project_context)
        elif agent == 'devops':
            issues = analyze_devops_file(file_content, file_path, project_context)
        elif agent == 'mobile':
            issues = analyze_mobile_file(file_content, file_path, project_context)
        else:
            issues = analyze_general_file(file_content, file_path, language, project_context)
        
        return jsonify({
            'success': True,
            'agent': agent,
            'issues': issues,
            'analysis_time': time.time()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ai/generate-tests', methods=['POST'])
def generate_tests_ai():
    """AI-powered test generation with technology-specific strategies"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        file_content = data.get('file_content')
        language = data.get('language')
        agent = data.get('agent', 'general')
        test_config = data.get('test_config', {})
        project_context = data.get('project_context', {})
        
        # Route to appropriate test generator
        if agent == 'frontend-react':
            test_result = generate_react_tests(file_content, file_path, test_config, project_context)
        elif agent == 'backend-python':
            test_result = generate_python_tests(file_content, file_path, test_config, project_context)
        elif agent == 'backend-node':
            test_result = generate_node_tests(file_content, file_path, test_config, project_context)
        elif agent == 'database':
            test_result = generate_database_tests(file_content, file_path, test_config, project_context)
        elif agent == 'devops':
            test_result = generate_devops_tests(file_content, file_path, test_config, project_context)
        elif agent == 'mobile':
            test_result = generate_mobile_tests(file_content, file_path, test_config, project_context)
        else:
            test_result = generate_general_tests(file_content, file_path, language, test_config, project_context)
        
        return jsonify({
            'success': True,
            'agent': agent,
            'test_code': test_result['code'],
            'explanation': test_result['explanation'],
            'coverage_areas': test_result['coverage_areas'],
            'test_framework': test_result.get('framework', 'unknown')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ai/optimize-code', methods=['POST'])
def optimize_code_ai():
    """AI-powered code optimization with technology-specific improvements"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        file_content = data.get('file_content')
        language = data.get('language')
        agent = data.get('agent', 'general')
        project_context = data.get('project_context', {})
        
        # Route to appropriate optimizer
        if agent == 'frontend-react':
            optimizations = optimize_react_code(file_content, file_path, project_context)
        elif agent == 'backend-python':
            optimizations = optimize_python_code(file_content, file_path, project_context)
        elif agent == 'backend-node':
            optimizations = optimize_node_code(file_content, file_path, project_context)
        elif agent == 'database':
            optimizations = optimize_database_code(file_content, file_path, project_context)
        elif agent == 'devops':
            optimizations = optimize_devops_code(file_content, file_path, project_context)
        elif agent == 'mobile':
            optimizations = optimize_mobile_code(file_content, file_path, project_context)
        else:
            optimizations = optimize_general_code(file_content, file_path, language, project_context)
        
        return jsonify({
            'success': True,
            'agent': agent,
            'optimizations': optimizations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ai/chat', methods=['POST'])
def chat_ai():
    """AI-powered contextual chat about code with technology-specific knowledge"""
    try:
        data = request.get_json()
        message = data.get('message')
        file_path = data.get('file_path')
        file_content = data.get('file_content')
        language = data.get('language')
        agent = data.get('agent', 'general')
        chat_history = data.get('chat_history', [])
        project_context = data.get('project_context', {})
        
        # Route to appropriate chat agent
        if agent == 'frontend-react':
            response = chat_react_expert(message, file_content, file_path, chat_history, project_context)
        elif agent == 'backend-python':
            response = chat_python_expert(message, file_content, file_path, chat_history, project_context)
        elif agent == 'backend-node':
            response = chat_node_expert(message, file_content, file_path, chat_history, project_context)
        elif agent == 'database':
            response = chat_database_expert(message, file_content, file_path, chat_history, project_context)
        elif agent == 'devops':
            response = chat_devops_expert(message, file_content, file_path, chat_history, project_context)
        elif agent == 'mobile':
            response = chat_mobile_expert(message, file_content, file_path, chat_history, project_context)
        else:
            response = chat_general_expert(message, file_content, file_path, language, chat_history, project_context)
        
        return jsonify({
            'success': True,
            'agent': agent,
            'response': response,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/ai/analyze-directory', methods=['POST'])
def analyze_directory_ai():
    """AI-powered directory structure analysis and optimization suggestions"""
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        branch = data.get('branch', 'main')
        
        # Get complete project structure
        file_tree = get_complete_project_structure(project_id, branch)
        
        # Analyze directory structure
        analysis = analyze_project_structure(file_tree, project_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'suggestions': analysis.get('suggestions', []),
            'score': analysis.get('organization_score', 0),
            'issues': analysis.get('issues', [])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001) 