# CI Code Companion - Setup Guide

This guide will help you set up CI Code Companion in your GitLab project to start generating AI-powered tests and code reviews.

## 📋 Prerequisites

### 1. Google Cloud Platform Setup

1. **Create a Google Cloud Project**
   ```bash
   # Create a new project (optional)
   gcloud projects create your-project-id
   gcloud config set project your-project-id
   ```

2. **Enable Required APIs**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable secretmanager.googleapis.com
   ```

3. **Create a Service Account**
   ```bash
   # Create service account
   gcloud iam service-accounts create ci-code-companion \
     --description="Service account for CI Code Companion" \
     --display-name="CI Code Companion"

   # Grant necessary permissions
   gcloud projects add-iam-policy-binding your-project-id \
     --member="serviceAccount:ci-code-companion@your-project-id.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"

   # Create and download key
   gcloud iam service-accounts keys create ci-code-companion-key.json \
     --iam-account=ci-code-companion@your-project-id.iam.gserviceaccount.com
   ```

### 2. GitLab Project Setup

1. **Add CI/CD Variables**
   
   Go to your GitLab project → Settings → CI/CD → Variables and add:

   | Variable | Value | Masked | Protected |
   |----------|-------|---------|-----------|
   | `GCP_PROJECT_ID` | your-project-id | ❌ | ✅ |
   | `GCP_REGION` | us-central1 | ❌ | ❌ |
   | `GCP_SERVICE_ACCOUNT_KEY` | Contents of ci-code-companion-key.json | ✅ | ✅ |
   | `GITLAB_ACCESS_TOKEN` | Personal Access Token with API scope | ✅ | ✅ |

2. **Create Personal Access Token**
   
   Go to GitLab → User Settings → Access Tokens:
   - Name: `CI Code Companion`
   - Scopes: `api`, `read_repository`, `write_repository`
   - Save the token and add it as `GITLAB_ACCESS_TOKEN`

## 🚀 Quick Start

### Option 1: Include CI/CD Components (Recommended)

Add the following to your `.gitlab-ci.yml`:

```yaml
include:
  # Include the AI Test Generator component
  - component: gitlab.com/your-group/ci-code-companion/ai-test-generator@main
    inputs:
      gcp_project_id: $GCP_PROJECT_ID
      source_directory: "src"
      create_mr: true
  
  # Include the AI Code Reviewer component
  - component: gitlab.com/your-group/ci-code-companion/ai-code-reviewer@main
    inputs:
      gcp_project_id: $GCP_PROJECT_ID
      review_type: "comprehensive"
      post_comment: true

stages:
  - test
  - review

# Your existing jobs...
```

### Option 2: Direct Integration

Add jobs directly to your `.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

variables:
  PYTHON_VERSION: "3.11"

# AI Test Generation Job
ai_test_generation:
  stage: test
  image: python:$PYTHON_VERSION
  before_script:
    - pip install google-cloud-aiplatform python-gitlab
    - echo "$GCP_SERVICE_ACCOUNT_KEY" > /tmp/gcp-key.json
    - export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json
  script:
    - python -c "
      import sys, os
      sys.path.insert(0, '.')
      from src.ci_code_companion import VertexAIClient, TestGenerator, GitLabIntegration
      
      # Initialize components
      client = VertexAIClient('$GCP_PROJECT_ID')
      test_gen = TestGenerator(client)
      gitlab = GitLabIntegration()
      
      # Generate tests
      results = test_gen.batch_generate_tests('src', 'generated_tests')
      print(f'Generated tests for {len(results)} files')
      
      # Create MR with generated tests
      if results:
          files = {}
          for _, test_files in results.items():
              files.update(test_files)
          gitlab.create_ai_generated_mr(files)
      "
  artifacts:
    paths:
      - generated_tests/
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

# AI Code Review Job
ai_code_review:
  stage: review
  image: python:$PYTHON_VERSION
  before_script:
    - pip install google-cloud-aiplatform python-gitlab
    - echo "$GCP_SERVICE_ACCOUNT_KEY" > /tmp/gcp-key.json
    - export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcp-key.json
  script:
    - python -c "
      import sys, os
      sys.path.insert(0, '.')
      from src.ci_code_companion import VertexAIClient, CodeReviewer, GitLabIntegration
      
      # Initialize components
      client = VertexAIClient('$GCP_PROJECT_ID')
      reviewer = CodeReviewer(client)
      gitlab = GitLabIntegration()
      
      # Review merge request if applicable
      if gitlab.is_merge_request_pipeline():
          mr_info = gitlab.get_merge_request_diff(int('$CI_MERGE_REQUEST_IID'))
          review = reviewer.review_code_diff(mr_info['diff_content'])
          
          # Post review comment
          comment = gitlab.format_mr_comment_for_review([review])
          gitlab.add_merge_request_note(int('$CI_MERGE_REQUEST_IID'), comment)
      "
  artifacts:
    reports:
      junit: artifacts/review_report.xml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## 🔧 Configuration Options

### AI Test Generator Configuration

```yaml
ai_test_generator:
  inputs:
    gcp_project_id: $GCP_PROJECT_ID      # Required: Your GCP Project ID
    gcp_region: "us-central1"            # Optional: GCP region
    source_directory: "src"              # Optional: Source code directory
    test_framework: "pytest"             # Optional: Testing framework
    language: "python"                   # Optional: Programming language
    create_mr: true                      # Optional: Create merge request
    target_branch: "main"                # Optional: Target branch for MR
    ai_model: "code-bison@001"          # Optional: AI model to use
```

### AI Code Reviewer Configuration

```yaml
ai_code_reviewer:
  inputs:
    gcp_project_id: $GCP_PROJECT_ID      # Required: Your GCP Project ID
    gcp_region: "us-central1"            # Optional: GCP region
    review_type: "comprehensive"         # Optional: comprehensive|security|performance
    post_comment: true                   # Optional: Post review as MR comment
    severity_threshold: "medium"         # Optional: info|low|medium|high|critical
    ai_model: "codechat-bison@001"      # Optional: AI model to use
```

## 📁 Project Structure

Ensure your project follows this structure for optimal results:

```
your-project/
├── src/                          # Source code directory
│   ├── __init__.py
│   ├── main.py
│   └── modules/
├── tests/                        # Existing tests
│   ├── __init__.py
│   └── test_main.py
├── generated_tests/              # AI-generated tests (created automatically)
├── .gitlab-ci.yml               # GitLab CI configuration
├── requirements.txt             # Python dependencies
└── README.md
```

## 🧪 Testing the Setup

### 1. Test Vertex AI Connection

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"

# Run connection test
python scripts/test_vertex_ai_connection.py
```

### 2. Test Component Integration

```bash
# Run integration tests
python scripts/test_component_integration.py
```

### 3. Run Example Usage

```bash
# Run usage examples
python examples/sample_usage.py
```

## 🔍 Troubleshooting

### Common Issues

1. **"Permission denied" errors**
   - Check that your service account has the correct IAM roles
   - Verify the `GCP_SERVICE_ACCOUNT_KEY` variable is correctly set

2. **"Project not found" errors**
   - Ensure `GCP_PROJECT_ID` matches your actual project ID
   - Verify the Vertex AI API is enabled

3. **"Model not found" errors**
   - Check that you're using the correct region (some models are region-specific)
   - Verify Vertex AI is available in your chosen region

4. **GitLab API errors**
   - Ensure `GITLAB_ACCESS_TOKEN` has the correct scopes
   - Check that the token hasn't expired

### Debug Mode

Enable debug logging by adding to your CI job:

```yaml
variables:
  PYTHONPATH: "."
  LOG_LEVEL: "DEBUG"
before_script:
  - export PYTHONPATH="."
  - python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### Manual Testing

Test individual components locally:

```python
from src.ci_code_companion import VertexAIClient

# Test basic connection
client = VertexAIClient("your-project-id")
health = client.health_check()
print(health)

# Test code generation
code = client.generate_code("Create a Python function to calculate factorial")
print(code)
```

## 📈 Best Practices

### 1. Cost Management

- Set up billing alerts in Google Cloud
- Use pipeline rules to limit when AI jobs run
- Consider using smaller models for development

### 2. Security

- Use masked variables for all credentials
- Regularly rotate access tokens
- Limit service account permissions

### 3. Performance

- Cache dependencies in CI jobs
- Use parallel jobs when possible
- Set appropriate timeouts

### 4. Quality

- Review AI-generated code before merging
- Set up code quality gates
- Monitor AI accuracy over time

## 🚀 Advanced Usage

### Custom Prompts

Modify prompts for your specific needs:

```python
from src.ci_code_companion import VertexAIClient

client = VertexAIClient("your-project-id")

# Custom test generation prompt
custom_prompt = """
Generate comprehensive unit tests for the following Python function.
Include tests for:
- Normal operation
- Edge cases
- Error conditions
- Performance considerations

Function:
{function_code}

Use pytest and follow our company's testing standards.
"""

tests = client.generate_code(custom_prompt.format(function_code=your_function))
```

### Integration with Other Tools

Combine with other CI/CD tools:

```yaml
# Example: Integration with SonarQube
sonarqube_analysis:
  stage: review
  script:
    - sonar-scanner
  dependencies:
    - ai_code_review

# Example: Integration with security scanning
security_scan:
  stage: security
  script:
    - bandit -r src/
  dependencies:
    - ai_code_review
```

## 📞 Support

If you encounter issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review the [examples](../examples/)
3. Run the test scripts to isolate issues
4. Check GitLab CI logs for detailed error messages

## 🎉 Next Steps

Once set up successfully:

1. **Customize for your team**: Adjust prompts and configurations
2. **Monitor usage**: Track costs and performance
3. **Expand integration**: Add more AI-powered features
4. **Share knowledge**: Document your team's best practices

Happy coding with AI assistance! 🤖✨ 