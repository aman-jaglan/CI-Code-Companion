# Connecting Your GitLab Repository

## Overview

CI Code Companion can analyze your GitLab repositories by:
1. Monitoring commits and merge requests
2. Providing AI-powered code reviews
3. Generating test suggestions
4. Analyzing code quality and security

## Setup Steps

### 1. Connect Your GitLab Account

1. Go to the CI Code Companion dashboard
2. Click "Connect GitLab Account"
3. Authorize the application in GitLab
4. Select the repositories you want to analyze

### 2. Configure Repository Webhooks

The dashboard will automatically configure webhooks for:
- Push events
- Merge request events
- Pipeline events

### 3. Add CI Configuration

Add this to your `.gitlab-ci.yml`:

```yaml
include:
  - project: 'your-group/ci-code-companion'
    file: '/components/ai-code-reviewer/template.yml'
    ref: main
```

### 4. Environment Variables

Required variables in your GitLab project:
- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `GCP_SERVICE_ACCOUNT_KEY`: Your service account key (as JSON)

Optional variables:
- `SLACK_WEBHOOK_URL`: For Slack notifications
- `AI_QUALITY_THRESHOLD`: Minimum quality score (default: 7.0)
- `AI_SECURITY_THRESHOLD`: Minimum security score (default: 8.0)

## Features

### Automated Code Review
- Every commit is analyzed
- AI-powered suggestions
- Security vulnerability detection
- Code quality metrics

### Merge Request Integration
- Detailed MR comments
- Quality gates
- Test coverage analysis
- Security checks

### Dashboard Features
- Project overview
- Historical trends
- Quality metrics
- Security insights

## Customization

### Quality Gates
Configure in your `.gitlab-ci.yml`:
```yaml
variables:
  AI_QUALITY_THRESHOLD: "7.5"
  AI_SECURITY_THRESHOLD: "8.0"
  AI_TEST_COVERAGE_THRESHOLD: "80"
```

### Notification Settings
Configure in the dashboard:
- Email notifications
- Slack integration
- MS Teams webhooks
- Custom webhooks

## Support

For issues or questions:
- Open an issue on GitHub
- Contact support@cicode-companion.com
- Join our Discord community 