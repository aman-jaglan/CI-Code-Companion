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

# Add src and web_dashboard to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root / 'web_dashboard'))

from web_dashboard.routes.api import api, init_database
from web_dashboard.routes.gitlab_api import gitlab_bp, init_gitlab

def create_app():
    # Initialize Flask app with correct template and static folders
    app = Flask(__name__,
                template_folder='web_dashboard/templates',
                static_folder='web_dashboard/static')
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///ci_code_companion.db')
    
    # Register API blueprint
    app.register_blueprint(api)
    
    # Register GitLab API blueprint
    app.register_blueprint(gitlab_bp, url_prefix='/gitlab')
    
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
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if app.debug else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
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
    
    # Add AI analysis endpoint
    @app.route('/api/ai-analyze', methods=['POST'])
    def ai_analyze():
        """AI analysis endpoint for repository browser."""
        app.logger.info(f"AI analysis request received for {request.path}")
        
        # if 'gitlab_token' not in session: # Keep commented for now to simplify debugging AI core
        #     app.logger.warning("No GitLab token for AI analysis.")
        #     return jsonify({'error': 'Not authenticated with GitLab'}), 401
        
        try:
            raw_data = request.data # Log raw data
            app.logger.info(f"Raw request data: {raw_data[:500]}..." if raw_data else "Raw request data: None")

            data = request.json
            if not data:
                app.logger.error("No JSON data received or could not parse JSON.")
                return jsonify({'error': 'Request must be JSON and parsable.'}), 400

            app.logger.info(f"Parsed JSON data keys: {list(data.keys())}")

            # === Explicitly test access to 'language' key ===
            language_via_get = data.get('language')
            app.logger.info(f"Attempting data.get('language'): '{language_via_get}' (Type: {type(language_via_get)})")
            
            language_via_direct_access = None
            has_language_key_direct = False
            try:
                language_via_direct_access = data['language']
                has_language_key_direct = True
                app.logger.info(f"Attempting data['language']: '{language_via_direct_access}' (Type: {type(language_via_direct_access)})")
            except KeyError:
                app.logger.warning("KeyError: 'language' key not found in parsed JSON data via direct access.")
            except Exception as e:
                app.logger.error(f"Error attempting data['language'] direct access: {str(e)}")
            app.logger.info(f"Does 'language' key exist (direct access check)?: {has_language_key_direct}")
            # === End explicit test ===
            
            action = data.get('action')
            file_path = data.get('file_path')
            content = data.get('content')
            project_id = data.get('project_id')
            branch = data.get('branch')
            # Use the value from .get() for consistency in the rest of the logic, but the logs above are key
            language_from_request = language_via_get 
            
            app.logger.info(f"Value of 'language' (derived from .get()) for further processing: '{language_from_request}' (Type: {type(language_from_request)})")

            app.logger.info(f"Analysis params: action={action}, file_path={file_path}, project_id={project_id}, branch={branch}, language='{language_from_request}', content_length={len(content) if content else 0}")
            
            required_params = {'action': action, 'file_path': file_path, 'content': content}
            missing = [k for k, v in required_params.items() if v is None] 
            if missing:
                app.logger.error(f"Missing required parameters (value is None): {missing}")
                return jsonify({'error': f'Missing required parameters (value is None): {missing}'}), 400
            
            # Handle language parameter separately with a default
            language_from_request = language_from_request or 'Python'  # Default to Python if not provided
            app.logger.info(f"Using language: {language_from_request}")

            try:
                app.logger.debug("Importing AI components...")
                from src.ci_code_companion.vertex_ai_client import VertexAIClient
                from src.ci_code_companion.code_reviewer import CodeReviewer
                from src.ci_code_companion.test_generator import TestGenerator
                app.logger.debug("AI components imported.")
            except ImportError as e:
                app.logger.error(f"Failed to import AI components: {str(e)}", exc_info=True)
                return jsonify({'error': f'AI components not available: {str(e)}'}), 500
            
            gcp_project_id = os.getenv('GCP_PROJECT_ID')
            if not gcp_project_id:
                app.logger.error("GCP_PROJECT_ID environment variable not set.")
                return jsonify({'error': 'AI service not configured (missing GCP_PROJECT_ID)'}), 500
            
            app.logger.debug(f"Initializing VertexAIClient with GCP project: {gcp_project_id}")
            try:
                ai_client = VertexAIClient(project_id=gcp_project_id)
                app.logger.debug("VertexAIClient initialized.")
            except Exception as e:
                app.logger.error(f"Failed to initialize VertexAIClient: {str(e)}", exc_info=True)
                return jsonify({'error': f'Failed to initialize AI client: {str(e)}'}), 500
            
            response_payload = {}
            action_to_perform = action
            if action == 'test': # Map frontend 'test' to backend 'test-generation'
                action_to_perform = 'test-generation'

            if action_to_perform == 'review':
                app.logger.info(f"Starting AI code review for: {file_path}")
                try:
                    reviewer = CodeReviewer(ai_client)
                    review_data = reviewer.review_code_content(content, file_path)
                    app.logger.info(f"AI code review for {file_path} completed.")
                    response_payload = {
                        'action': action, # Return original action
                        'file_path': file_path,
                        'analysis': review_data,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    app.logger.error(f"AI code review for {file_path} failed: {str(e)}", exc_info=True)
                    return jsonify({'error': f'Code review process failed: {str(e)}'}), 500
                
            elif action_to_perform == 'test-generation':
                app.logger.info(f"Starting AI test generation for: {file_path}")
                try:
                    test_generator = TestGenerator(ai_client)
                    test_data = test_generator.generate_tests(content, file_path)
                    app.logger.info(f"AI test generation for {file_path} completed.")
                    response_payload = {
                        'action': action, # Return original action
                        'file_path': file_path,
                        'tests': test_data,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    app.logger.error(f"AI test generation for {file_path} failed: {str(e)}", exc_info=True)
                    return jsonify({'error': f'Test generation process failed: {str(e)}'}), 500

            elif action_to_perform == 'improve':
                app.logger.info(f"Starting AI code improvement for: {file_path}")
                try:
                    reviewer = CodeReviewer(ai_client)
                    improvement_data = reviewer.review_code_content(content, file_path, review_type="comprehensive")
                    app.logger.info(f"AI code improvement for {file_path} completed.")
                    response_payload = {
                        'action': action, # Return original action
                        'file_path': file_path,
                        'improvements': improvement_data,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    app.logger.error(f"AI code improvement for {file_path} failed: {str(e)}", exc_info=True)
                    return jsonify({'error': f'Code improvement process failed: {str(e)}'}), 500
            else:
                app.logger.warning(f"Invalid action specified: {action}")
                return jsonify({'error': f'Invalid action: {action}'}), 400
            
            app.logger.info(f"AI analysis action '{action}' for {file_path} successful.")
            return jsonify(response_payload)
            
        except Exception as e:
            app.logger.error(f"Unhandled error in /api/ai-analyze: {str(e)}", exc_info=True)
            return jsonify({'error': f'An unexpected error occurred on the server: {str(e)}'}), 500
    
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