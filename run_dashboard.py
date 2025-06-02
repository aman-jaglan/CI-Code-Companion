#!/usr/bin/env python3
"""
CI Code Companion Dashboard Server
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session

# Load environment variables
load_dotenv()

# Add web_dashboard to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'web_dashboard'))

# Import new SDK
from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig
from ci_code_companion_sdk.core.exceptions import CICodeCompanionError, ConfigurationError
from web_dashboard.routes.api import api, init_database
from web_dashboard.routes.gitlab_api import gitlab_bp, init_gitlab
from web_dashboard.routes.gitlab_routes import gitlab_bp as gitlab_oauth_bp

def create_app():
    """Create and configure the Flask application"""
    # Initialize Flask app with correct template and static folders
    app = Flask(__name__,
                template_folder='web_dashboard/templates',
                static_folder='web_dashboard/static')
    
    # Configure Flask
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///ci_code_companion.db')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get logger after configuring logging
    logger = logging.getLogger(__name__)
    
    # Initialize SDK
    try:
        sdk = CICodeCompanionSDK()
        logger.info("CI Code Companion SDK initialized successfully")
        app.sdk = sdk
    except Exception as e:
        logger.error(f"Failed to initialize SDK: {e}")
        app.sdk = None
    
    # Register blueprints
    from web_dashboard.routes.api import api
    
    app.register_blueprint(api)
    
    # Register GitLab API blueprint (for file operations)
    app.register_blueprint(gitlab_bp, url_prefix='/gitlab/api')
    
    # Register GitLab OAuth blueprint for authentication (for connect/auth operations)
    app.register_blueprint(gitlab_oauth_bp, url_prefix='/gitlab')
    
    # Initialize GitLab connection
    gitlab_url = os.getenv('GITLAB_URL', 'https://gitlab.com')
    gitlab_token = os.getenv('GITLAB_TOKEN')
    
    if gitlab_token:
        init_success = init_gitlab(gitlab_url, gitlab_token)
        if init_success:
            app.logger.info("GitLab connection initialized successfully")
        else:
            app.logger.error("Failed to initialize GitLab connection")
    else:
        app.logger.warning("GitLab token not found in environment variables")
    
    # Add route for dashboard
    @app.route('/')
    def dashboard():
        return render_template('dashboard.html')
    
    # Add project selector route
    @app.route('/projects')
    def project_selector():
        return render_template('project_selector.html')
    
    # Add repository browser route
    @app.route('/repository_browser')
    def repository_browser():
        try:
            return render_template('repository_browser.html')
        except Exception as e:
            app.logger.error(f"Error loading repository browser: {str(e)}")
            return f"Repository browser not available: {str(e)}", 404
    
    # Add AI analysis endpoint using new SDK
    @app.route('/api/ai-analyze', methods=['POST'])
    async def ai_analyze():
        """AI analysis endpoint using the new SDK."""
        app.logger.info(f"AI analysis request received for {request.path}")
        
        if not app.sdk:
            app.logger.error("SDK not initialized")
            return jsonify({'error': 'AI service not available'}), 500
        
        try:
            data = request.json
            if not data:
                app.logger.error("No JSON data received")
                return jsonify({'error': 'Request must be JSON'}), 400

            app.logger.info(f"Parsed JSON data keys: {list(data.keys())}")
            
            action = data.get('action')
            file_path = data.get('file_path')
            content = data.get('content')
            project_id = data.get('project_id')
            branch = data.get('branch')
            language = data.get('language', 'auto-detect')
            
            app.logger.info(f"Analysis params: action={action}, file_path={file_path}, project_id={project_id}, branch={branch}, language='{language}', content_length={len(content) if content else 0}")
            
            required_params = {'action': action, 'file_path': file_path, 'content': content}
            missing = [k for k, v in required_params.items() if v is None] 
            if missing:
                app.logger.error(f"Missing required parameters: {missing}")
                return jsonify({'error': f'Missing required parameters: {missing}'}), 400
            
            response_payload = {}
            
            try:
                if action == 'review':
                    app.logger.info(f"Starting SDK code analysis for: {file_path}")
                    result = await app.sdk.analyze_file(file_path, content)
                    response_payload = {
                        'action': action,
                        'file_path': file_path,
                        'analysis': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                elif action in ['test', 'test-generation']:
                    app.logger.info(f"Starting SDK test generation for: {file_path}")
                    result = await app.sdk.generate_tests(file_path, content)
                    response_payload = {
                        'action': action,
                        'file_path': file_path,
                        'tests': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                elif action == 'improve':
                    app.logger.info(f"Starting SDK code optimization for: {file_path}")
                    result = await app.sdk.optimize_code(file_path, content)
                    response_payload = {
                        'action': action,
                        'file_path': file_path,
                        'optimizations': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                elif action == 'chat':
                    app.logger.info(f"Starting SDK chat for: {file_path}")
                    message = data.get('message', '')
                    result = await app.sdk.chat(message, file_path, content)
                    response_payload = {
                        'action': action,
                        'file_path': file_path,
                        'response': result,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                else:
                    app.logger.error(f"Unknown action: {action}")
                    return jsonify({'error': f'Unknown action: {action}'}), 400
                
                app.logger.info(f"SDK operation '{action}' completed for {file_path}")
                return jsonify(response_payload)
                
            except CICodeCompanionError as e:
                app.logger.error(f"SDK error during '{action}' for {file_path}: {str(e)}")
                return jsonify({'error': f'SDK operation failed: {str(e)}'}), 500
            except Exception as e:
                app.logger.error(f"Unexpected error during '{action}' for {file_path}: {str(e)}", exc_info=True)
                return jsonify({'error': f'Operation failed: {str(e)}'}), 500
                
        except Exception as e:
            app.logger.error(f"Request processing error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Request processing failed: {str(e)}'}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    
    # Initialize database within application context
    with app.app_context():
        init_database()
    
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting CI Code Companion on port {port}")
    logger.info(f"Dashboard: http://localhost:{port}/")
    logger.info(f"Repository Browser: http://localhost:{port}/repository_browser")
    logger.info(f"API Endpoints: http://localhost:{port}/api/v2/")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=True
    ) 