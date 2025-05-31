# CI Code Companion SDK

> 🤖 **Production-Ready AI-Powered Code Analysis, Test Generation, and Optimization SDK**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GitLab CI](https://img.shields.io/badge/GitLab%20CI-Enabled-orange.svg)](https://gitlab.com)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Vertex%20AI-blue.svg)](https://cloud.google.com/vertex-ai)

## 🎯 Overview

The **CI Code Companion SDK** is a comprehensive, production-ready Python SDK that brings advanced AI capabilities to your development workflow. Built with modern async architecture and intelligent agent routing, it provides seamless code analysis, automated test generation, performance optimization, and interactive AI assistance.

### ✨ Key Features

- 🧠 **Multi-Agent AI System** - Specialized agents for React, Python, Node.js, Database, DevOps, and Mobile
- ⚡ **Async Performance** - Modern async/await architecture with parallel processing
- 🎯 **Intelligent Routing** - Automatic agent selection based on file content and technology stack
- 🧪 **Smart Test Generation** - Automated unit test creation with coverage analysis
- 🔍 **Advanced Code Analysis** - Security scanning, performance optimization, and style checking
- 💬 **Interactive Chat** - Context-aware AI assistance for development questions
- 🚀 **Production Ready** - Comprehensive error handling, logging, and monitoring
- 🔌 **Easy Integration** - GitLab CI/CD, Cloud Run components, and standalone usage

### 🏗️ Architecture

```
CI Code Companion SDK
├── 🧠 Core Engine         # Orchestration, config, utilities
├── 🤖 Agent System        # Specialized AI agents with intelligent routing
├── 📊 Data Models         # Structured analysis results and metrics
├── 🔧 Services           # File operations and external integrations
├── 🌐 Web Dashboard      # Interactive web interface
└── 📦 Cloud Components   # GitLab CI/CD and Cloud Run deployments
```

## 🚀 Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/your-org/CI-Code-Companion.git
cd CI-Code-Companion
pip install -e .

# Or install from PyPI (when published)
pip install ci-code-companion-sdk
```

### Basic Usage

```python
import asyncio
from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig

async def main():
    # Initialize SDK
    config = SDKConfig(
        ai_provider='vertex_ai',
        project_id='your-gcp-project'
    )
    sdk = CICodeCompanionSDK(config=config)
    
    # Analyze code
    with open('example.py', 'r') as f:
        code = f.read()
    
    # Get comprehensive analysis
    analysis = await sdk.analyze_file('example.py', code)
    print(f"Issues found: {len(analysis.issues)}")
    print(f"Confidence: {analysis.confidence_score:.2f}")
    
    # Generate tests
    tests = await sdk.generate_tests('example.py', code)
    print(f"Generated test framework: {tests.get('framework')}")
    
    # Get optimization suggestions
    optimizations = await sdk.optimize_code('example.py', code)
    print(f"Optimizations: {len(optimizations.get('optimizations', []))}")
    
    # Interactive AI chat
    response = await sdk.chat("How can I improve this code?", 'example.py', code)
    print(f"AI Suggestion: {response[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())
```

### Web Dashboard

```bash
# Start the web dashboard
python run_dashboard.py

# Visit http://localhost:5001
# - Upload files for analysis
# - Generate tests interactively
# - Chat with specialized AI agents
# - View detailed reports and metrics
```

## 🤖 Specialized Agents

### Agent Capabilities

| Agent | File Types | Specializations |
|-------|------------|----------------|
| **React Agent** | `.jsx`, `.tsx` | Hooks validation, performance, component analysis |
| **Python Agent** | `.py` | PEP8, security, Django/Flask/FastAPI frameworks |
| **Node Agent** | `.js`, `.ts` | Express/NestJS, async patterns, performance |
| **Database Agent** | `.sql` | Query optimization, security, performance tuning |
| **DevOps Agent** | `.yml`, `.tf` | Docker, Kubernetes, Terraform best practices |
| **Mobile Agent** | `.dart`, `.kt` | React Native, Flutter, platform-specific optimizations |

### Intelligent Routing

The SDK automatically routes files to the most appropriate agent based on:

- **File Extensions** - Direct mapping for common file types
- **Content Analysis** - Framework and library detection within files
- **Project Context** - Understanding project structure and dependencies
- **Agent Capabilities** - Matching required analysis types with agent strengths

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GCP_PROJECT_ID="your-gcp-project"

# Optional
export CI_SDK_LOG_LEVEL="INFO"
export CI_SDK_MAX_FILE_SIZE="10485760"  # 10MB
export CI_SDK_MAX_CONCURRENT="5"
export CI_SDK_CACHE_ENABLED="true"
```

### Configuration File (`ci_config.yaml`)

```yaml
ai_provider: "vertex_ai"
project_id: "your-gcp-project" 
region: "us-central1"

# Agent configuration
agents:
  react_agent:
    enabled: true
    max_file_size: 1048576  # 1MB
  python_agent:
    enabled: true
    frameworks: ["django", "flask", "fastapi"]

# File handling
allowed_file_types:
  - ".py"
  - ".js"
  - ".jsx"
  - ".ts"
  - ".tsx"
  - ".sql"

# Performance
max_concurrent_operations: 5
enable_metrics: true
cache_enabled: true
```

## 🚀 GitLab CI/CD Integration

### Cloud Run Components

The SDK provides production-ready GitLab CI/CD components:

```yaml
# .gitlab-ci.yml
include:
  - component: $CI_SERVER_FQDN/your-group/ci-code-companion/ai-code-reviewer@main
    inputs:
      gcp_project_id: $GCP_PROJECT_ID
      review_type: "comprehensive"
      severity_threshold: "medium"
      post_comment: true

  - component: $CI_SERVER_FQDN/your-group/ci-code-companion/ai-test-generator@main
    inputs:
      gcp_project_id: $GCP_PROJECT_ID
      test_framework: "pytest"
      create_mr: true
```

### Custom Pipeline

```yaml
ai-analysis:
  stage: test
  image: python:3.11
  before_script:
    - pip install ci-code-companion-sdk
  script:
    - python -c "
        import asyncio;
        from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig;
        
        async def analyze():
            sdk = CICodeCompanionSDK(SDKConfig());
            # Your analysis logic here
            
        asyncio.run(analyze())
      "
```

## 🐳 Docker Deployment

### Development

```bash
# Build development image
docker build --target development -t ci-companion-dev .

# Run with hot reload
docker run -p 5000:5000 -v $(pwd):/app ci-companion-dev
```

### Production

```bash
# Build production image
docker build --target production -t ci-companion-prod .

# Run production server
docker run -p 8080:8080 -e PORT=8080 ci-companion-prod
```

### Cloud Run Deployment

```bash
# Deploy to Google Cloud Run
gcloud run deploy ci-code-companion \
    --image gcr.io/your-project/ci-companion-prod \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
```

## 📊 API Reference

### Core SDK Methods

#### `analyze_file(file_path: str, content: str) -> AnalysisResult`

Performs comprehensive code analysis including:
- Issue detection with severity levels
- Code suggestions and improvements
- Security vulnerability scanning
- Performance optimization opportunities
- Style and convention adherence

#### `generate_tests(file_path: str, content: str) -> TestGenerationResult`

Generates comprehensive test suites:
- Unit tests with high coverage
- Integration test templates
- Mock and fixture generation
- Framework-specific best practices

#### `optimize_code(file_path: str, content: str) -> OptimizationResult`

Provides optimization recommendations:
- Performance improvements
- Memory usage optimization
- Algorithm efficiency suggestions
- Best practice implementations

#### `chat(message: str, file_path: str = None, content: str = None) -> str`

Interactive AI assistance:
- Context-aware responses
- Code-specific guidance
- Architecture recommendations
- Debugging assistance

### Data Models

```python
from ci_code_companion_sdk.models import AnalysisResult, CodeIssue, CodeSuggestion

# Analysis result structure
class AnalysisResult:
    issues: List[CodeIssue]           # Detected issues
    suggestions: List[CodeSuggestion]  # Improvement suggestions
    confidence_score: float           # AI confidence (0-1)
    metadata: Dict[str, Any]          # Additional context
    
class CodeIssue:
    title: str                        # Issue title
    description: str                  # Detailed description
    severity: str                     # critical, high, medium, low, info
    line_number: Optional[int]        # Location in file
    suggestion: Optional[str]         # How to fix
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run unit tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=ci_code_companion_sdk --cov-report=html

# Run integration tests
pytest tests/integration/ -v --slow
```

### Test Generation

```bash
# Generate tests for SDK components
python examples/sdk_basic_usage.py

# Run generated tests
pytest generated_tests/ -v
```

## 🔍 Monitoring and Metrics

### Built-in Metrics

```python
# Get SDK statistics
stats = await sdk.get_stats()
print(f"Active agents: {stats['active_agents']}")
print(f"Success rate: {stats['success_rate']:.1%}")
print(f"Avg response time: {stats['avg_response_time']:.2f}s")
```

### Health Checks

```python
# Verify SDK health
health = await sdk.health_check()
if health['status'] == 'healthy':
    print("✅ SDK is operational")
```

## 🛠️ Development

### Project Structure

```
CI-Code-Companion/
├── ci_code_companion_sdk/     # Main SDK package
│   ├── core/                  # Engine, config, exceptions
│   ├── agents/                # Specialized AI agents
│   ├── models/                # Data models
│   └── services/              # File and external services
├── web_dashboard/             # Web interface
├── components/                # GitLab CI/CD components
├── examples/                  # Usage examples
├── tests/                     # Test suite
└── docs/                      # Documentation
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Test** your changes: `pytest tests/`
4. **Commit** changes: `git commit -m 'Add amazing feature'`
5. **Push** to branch: `git push origin feature/amazing-feature`
6. **Open** a Pull Request

### Code Quality

```bash
# Format code
black ci_code_companion_sdk/ tests/

# Lint code
flake8 ci_code_companion_sdk/ tests/

# Type checking
mypy ci_code_companion_sdk/
```

## 📖 Documentation

### Additional Resources

- [Migration Guide](MIGRATION_GUIDE.md) - Upgrading from legacy versions
- [Project Structure](PROJECT_STRUCTURE.md) - Detailed architecture overview
- [Examples](examples/) - Comprehensive usage examples
- [API Documentation](docs/api/) - Detailed API reference

### Community

- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/CI-Code-Companion/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-org/CI-Code-Companion/discussions)
- 📧 **Email**: support@cicompanion.ai

## 🔒 Security

### Security Features

- **Input Validation** - All inputs are sanitized and validated
- **File Size Limits** - Configurable limits prevent resource exhaustion
- **Secure AI Prompts** - Prompt injection protection and sanitization
- **Access Controls** - Token-based authentication for production deployments

### Reporting Security Issues

Please report security vulnerabilities to [security@cicompanion.ai](mailto:security@cicompanion.ai)

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Cloud Vertex AI** - Powering our AI capabilities
- **GitLab** - CI/CD platform integration
- **Python Community** - Amazing ecosystem and tools
- **Contributors** - Thank you for making this project better

---

**CI Code Companion SDK** - *Bringing AI-powered intelligence to every line of code* 🚀
