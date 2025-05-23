# CI Code Companion - Project Structure

## Overview
CI Code Companion is an AI-powered code analysis tool that integrates with GitLab to provide automated code reviews, test generation, and security analysis.

## Directory Structure

```
CI-Code-Companion/
├── web_dashboard/                 # Flask web dashboard
│   ├── app.py                    # Main Flask application
│   ├── config/                   # Configuration files
│   │   ├── __init__.py
│   │   └── gitlab_config.py      # GitLab OAuth configuration
│   ├── routes/                   # Flask route blueprints
│   │   ├── __init__.py
│   │   └── gitlab_routes.py      # GitLab integration routes
│   ├── templates/                # HTML templates
│   │   ├── dashboard.html        # Main dashboard template
│   │   └── analysis_detail.html  # Analysis detail view
│   ├── static/                   # Static assets
│   │   ├── css/                  # CSS files
│   │   ├── js/                   # JavaScript files
│   │   └── images/               # Image assets
│   └── __init__.py
├── src/                          # Core AI analysis modules
├── components/                   # Reusable components
├── tests/                        # Test files
├── examples/                     # Example configurations
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── run_dashboard.py              # Dashboard startup script
├── requirements.txt              # Python dependencies
├── .gitlab-ci.yml               # GitLab CI/CD configuration
└── README.md                     # Project overview
```

## Key Files

### Web Dashboard
- **`run_dashboard.py`**: Entry point to start the Flask dashboard on port 5001
- **`web_dashboard/app.py`**: Main Flask application with dashboard routes
- **`web_dashboard/routes/gitlab_routes.py`**: GitLab OAuth integration and webhook handling
- **`web_dashboard/config/gitlab_config.py`**: GitLab OAuth configuration management

### Configuration
- **`.env`**: Environment variables (create this file with your GitLab OAuth credentials)
- **`requirements.txt`**: Python package dependencies

### Documentation
- **`GITLAB_SETUP.md`**: GitLab integration setup guide
- **`DEVELOPER_WORKFLOW_GUIDE.md`**: Complete developer workflow documentation

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure GitLab OAuth:**
   - Create GitLab OAuth application at https://gitlab.com/-/profile/applications
   - Create `.env` file with:
     ```
     GITLAB_APP_ID=your_application_id
     GITLAB_APP_SECRET=your_application_secret
     GITLAB_REDIRECT_URI=http://localhost:5001/gitlab/callback
     ```

3. **Start the dashboard:**
   ```bash
   python run_dashboard.py
   ```

4. **Access the dashboard:**
   Open http://localhost:5001 in your browser

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GITLAB_APP_ID` | GitLab OAuth Application ID | Yes |
| `GITLAB_APP_SECRET` | GitLab OAuth Application Secret | Yes |
| `GITLAB_REDIRECT_URI` | OAuth redirect URI | No (defaults to localhost:5001) |
| `FLASK_SECRET_KEY` | Flask session secret key | No (defaults to dev key) |

## Recent Changes

- ✅ Removed duplicate nested `web_dashboard/web_dashboard/` directory
- ✅ Fixed GitLab OAuth token authentication consistency
- ✅ Updated Flask app to run on port 5001
- ✅ Created organized static file directories
- ✅ Cleaned up import paths and directory structure

## Next Steps

1. Create `.env` file with your GitLab OAuth credentials
2. Test GitLab OAuth integration
3. Verify dashboard functionality
4. Configure webhook endpoints for automatic analysis 