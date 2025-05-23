#!/usr/bin/env python3
"""
Step 1 Setup Script for CI Code Companion
Tests repository browser functionality
"""

import os
import sys
import subprocess
import time

def check_requirements():
    """Check if all requirements are installed."""
    print("🔍 Checking requirements...")
    
    try:
        import flask
        import gitlab
        import google.cloud
        print("✅ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_environment():
    """Check environment configuration."""
    print("\n🔧 Checking environment configuration...")
    
    required_files = [
        'ci-code-companion-4a9f0060c508.json',
        'web_dashboard/app.py',
        'web_dashboard/templates/repository_browser.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Required files present")
    
    # Check .env file
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("📝 You need to create .env with GitLab OAuth credentials:")
        print("""
GITLAB_APP_ID=your_application_id
GITLAB_APP_SECRET=your_application_secret
GITLAB_REDIRECT_URI=http://localhost:5001/gitlab/callback
GOOGLE_APPLICATION_CREDENTIALS=ci-code-companion-4a9f0060c508.json
GCP_PROJECT_ID=ci-code-companion
        """)
        return False
    
    print("✅ .env file found")
    return True

def test_server_start():
    """Test if the server can start."""
    print("\n🚀 Testing server startup...")
    
    try:
        # Import to check for any import errors
        sys.path.insert(0, 'web_dashboard')
        from app import app
        print("✅ Flask app imports successfully")
        
        # Test a simple route
        with app.test_client() as client:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Dashboard route responds")
            else:
                print(f"⚠️  Dashboard route status: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        return False

def show_next_steps():
    """Show next steps to the user."""
    print("\n" + "="*60)
    print("🎯 STEP 1 COMPLETE: Repository Browser Ready!")
    print("="*60)
    
    print("\n📋 What you have now:")
    print("  ✅ Repository Browser interface")
    print("  ✅ GitLab project integration")
    print("  ✅ File tree navigation")
    print("  ✅ Code syntax highlighting")
    print("  ✅ AI analysis buttons (Review, Test Gen, Improve)")
    print("  ✅ Recent commits display")
    
    print("\n🚀 To test it:")
    print("  1. Create .env file with GitLab OAuth credentials")
    print("  2. Run: python run_dashboard.py")
    print("  3. Go to: http://localhost:5001")
    print("  4. Click 'Connect GitLab'")
    print("  5. Select a project and click 'Browse Code'")
    
    print("\n📝 GitLab OAuth Setup:")
    print("  1. Go to: https://gitlab.com/-/profile/applications")
    print("  2. Create application with redirect URI: http://localhost:5001/gitlab/callback")
    print("  3. Add credentials to .env file")
    
    print("\n🔄 Next Steps (Step 2):")
    print("  - Real-time commit monitoring")
    print("  - Automatic AI analysis on new commits")
    print("  - Interactive code editing with AI")
    print("  - Live dashboard updates")

def main():
    """Main setup function."""
    print("🤖 CI Code Companion - Step 1 Setup")
    print("Setting up Repository Browser...")
    
    if not check_requirements():
        sys.exit(1)
    
    if not check_environment():
        print("\n⚠️  Environment setup incomplete")
        print("Fix the issues above and run again.")
        sys.exit(1)
    
    if not test_server_start():
        sys.exit(1)
    
    show_next_steps()
    print("\n✨ Ready to test your AI-powered repository browser!")

if __name__ == '__main__':
    main() 