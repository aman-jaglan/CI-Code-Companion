## GitLab Integration Setup Guide

### 1. Required Environment Variables

Set up the following environment variables in your GitLab project (Settings > CI/CD > Variables):

- `GITLAB_ACCESS_TOKEN`: Your GitLab Personal Access Token (with API access)
- `CI_PROJECT_ID`: Your GitLab project ID (found in project settings)
- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `GCP_SERVICE_ACCOUNT_KEY`: Your GCP service account key JSON (for Vertex AI)
- `SLACK_WEBHOOK_URL` (optional): For Slack notifications

### 2. Personal Access Token Creation

1. Go to GitLab > User Settings > Access Tokens
2. Create a new token with the following scopes:
   - `api` (Full API access)
   - `read_repository`
   - `write_repository`
3. Copy the token and set it as `GITLAB_ACCESS_TOKEN` in your project variables

### 3. Project Configuration

1. Project ID can be found in:
   - Project Settings > General > Project ID
   - Or from your project URL: `gitlab.com/group/project` where the number in the URL is your project ID

### 4. Update .gitlab-ci.yml

The repository already includes a `.gitlab-ci.yml` file with the necessary configuration. Make sure to:

1. Update the `GCP_PROJECT_ID` in the integration_test job if needed
2. Update the dashboard URL in the deploy-dashboard job
3. Customize notification settings in ai-analysis-notification job

### 5. Testing the Integration

1. Create a new branch
2. Make some changes to Python files
3. Create a merge request
4. The CI pipeline will automatically:
   - Run AI code analysis
   - Generate test suggestions
   - Post review comments
   - Send notifications (if configured)

### 6. Troubleshooting

If you encounter issues:

1. Check the CI/CD pipeline logs
2. Verify environment variables are set correctly
3. Ensure the GitLab token has sufficient permissions
4. Check the project's Runner is active and available

### 7. Security Notes

- Store sensitive tokens as masked variables in GitLab
- Never commit tokens or credentials to the repository
- Use environment-specific variables for different stages
- Regularly rotate access tokens

### 8. Additional Features

The integration supports:
- Automated code review
- Test generation
- Security analysis
- Quality scoring
- MR comments
- Slack notifications
- Dashboard deployment

For more details, refer to the `DEVELOPER_WORKFLOW_GUIDE.md`. 