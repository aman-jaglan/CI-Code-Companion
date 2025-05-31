# CI Code Companion SDK
*Production-Ready AI Development Assistant*

---

> 💡 **Navigation Tip**: Use the table of contents (type `/toc`) for sidebar navigation in Notion

---

# 🏠 Getting Started

## Overview & Architecture

The **CI Code Companion SDK** is a production-ready Python SDK that brings advanced AI capabilities to development workflows. Built with modern async architecture and intelligent agent routing.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CI Code Companion SDK                    │
├─────────────────────────────────────────────────────────────┤
│  🧠 Core Engine                                            │
│  ├── Orchestration & Configuration                         │
│  ├── Exception Handling & Utilities                        │
│  └── Async Task Management                                 │
├─────────────────────────────────────────────────────────────┤
│  🤖 Multi-Agent System                                     │
│  ├── React Agent     ├── Python Agent   ├── Node Agent    │
│  ├── Database Agent  ├── DevOps Agent   ├── Mobile Agent  │
│  └── Intelligent Routing & Load Balancing                  │
├─────────────────────────────────────────────────────────────┤
│  📊 Data Models & Services                                 │
│  ├── Analysis Results ├── File Service ├── Git Service    │
│  └── AI Provider Integration                               │
├─────────────────────────────────────────────────────────────┤
│  🌐 Integration Layer                                      │
│  ├── Web Dashboard   ├── GitLab CI/CD   ├── REST API      │
│  └── Docker & Cloud Run Deployment                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Features
- ⚡ **Async Performance** - Modern async/await architecture
- 🎯 **Intelligent Routing** - Automatic agent selection
- 🔍 **Comprehensive Analysis** - Security, performance, style
- 🧪 **Smart Test Generation** - Framework-specific tests
- 💬 **Interactive AI Chat** - Context-aware assistance
- 🚀 **Production Ready** - Error handling, monitoring, logging

---

## Quick Start Guide

### 1. Installation

```bash
# Install from source
git clone https://github.com/your-org/CI-Code-Companion.git
cd CI-Code-Companion
pip install -e .
```

### 2. Basic Usage

```python
import asyncio
from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig

async def main():
    # Initialize SDK
    config = SDKConfig(ai_provider='vertex_ai', project_id='your-project')
    sdk = CICodeCompanionSDK(config=config)
    
    # Analyze code
    with open('example.py', 'r') as f:
        code = f.read()
    
    analysis = await sdk.analyze_file('example.py', code)
    print(f"Issues found: {len(analysis.issues)}")
    
    # Generate tests
    tests = await sdk.generate_tests('example.py', code)
    print(f"Framework: {tests.get('framework')}")

asyncio.run(main())
```

### 3. Web Dashboard

```bash
python run_dashboard.py
# Visit http://localhost:5001
```

---

# 🧠 Core SDK

## Engine Architecture

The core engine (`ci_code_companion_sdk/core/engine.py`) orchestrates all SDK operations with async/await patterns.

### Main Components

```python
class CICodeCompanionSDK:
    """Main SDK interface providing unified access to all capabilities"""
    
    def __init__(self, config: SDKConfig):
        self.config = config
        self.agent_manager = AgentManager(config)
        self.file_service = FileService(config)
        
    async def analyze_file(self, file_path: str, content: str) -> AnalysisResult:
        """Analyze code with appropriate agent"""
        agent = self.agent_manager.get_agent_for_file(file_path)
        return await agent.analyze(file_path, content)
```

### Key Features
- **Singleton Pattern** - Single SDK instance per configuration
- **Async Operations** - All operations are non-blocking
- **Resource Management** - Automatic cleanup and timeout handling
- **Error Recovery** - Graceful handling of failures
- **Operation Tracking** - Monitor active operations and performance

---

## Configuration Management

The configuration system (`ci_code_companion_sdk/core/config.py`) provides flexible, hierarchical configuration management.

### Configuration Sources (Priority Order)

1. **Environment Variables** - Highest priority
2. **Configuration Files** - YAML/JSON support
3. **Default Values** - Fallback defaults

### Configuration Structure

```yaml
# ci_config.yaml
ai_provider: "vertex_ai"
project_id: "your-gcp-project"
region: "us-central1"

agents:
  react_agent:
    enabled: true
    max_file_size: 1048576
    timeout: 60
  python_agent:
    enabled: true
    frameworks: ["django", "flask", "fastapi"]

performance:
  max_concurrent_operations: 5
  enable_caching: true
  cache_ttl: 3600
```

---

## Exception Handling

Structured error handling with context and recovery suggestions.

### Exception Hierarchy

- **SDKError** - Base exception
  - **ConfigurationError** - Configuration issues
    - **MissingConfigError** - Required config missing
    - **InvalidConfigError** - Invalid config values
  - **AnalysisError** - Analysis failures
    - **UnsupportedFileError** - File type not supported
    - **FileTooLargeError** - File exceeds size limit
    - **AgentTimeoutError** - Agent operation timeout
  - **AIProviderError** - AI service issues

### Error Context & Recovery

```python
try:
    result = await sdk.analyze_file(file_path, content)
except FileTooLargeError as e:
    print(f"Error: {e.message}")
    print(f"File size: {e.file_size}, Max allowed: {e.max_size}")
    print(f"Suggestion: {e.suggestion}")
```

---

# 🤖 Agent System

## Agent Architecture

The agent system provides specialized AI capabilities for different technologies and file types.

### Base Agent Interface

```python
class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, config: AgentConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.capabilities = self.get_capabilities()
    
    @abstractmethod
    async def analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze file content and return results"""
        
    @abstractmethod
    async def generate_tests(self, file_path: str, content: str) -> Dict[str, Any]:
        """Generate tests for the given code"""
```

---

## React Agent

Specialized for React, Next.js, and modern frontend development.

### Capabilities

- **JSX/TSX Pattern Analysis** - Component lifecycle issues, Props validation, State management patterns
- **React Hooks Validation** - Rules of Hooks compliance, Dependency array issues, Hook optimization opportunities
- **Performance Analysis** - Unnecessary re-renders, Bundle size optimization, Lazy loading opportunities
- **Component Structure** - Component composition, Prop drilling detection, Accessibility improvements

### Analysis Features

```python
class ReactAgent(BaseAgent):
    """React/Frontend specialist agent"""
    
    SUPPORTED_EXTENSIONS = ['.jsx', '.tsx', '.js', '.ts']
    FRAMEWORKS = ['react', 'next.js', 'gatsby', 'vue']
    
    async def analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """React-specific analysis"""
        
        issues = []
        suggestions = []
        
        # JSX/TSX analysis
        jsx_issues = await self._analyze_jsx_patterns(content)
        issues.extend(jsx_issues)
        
        # React Hooks validation
        hooks_issues = await self._validate_react_hooks(content)
        issues.extend(hooks_issues)
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'confidence_score': self._calculate_confidence(content),
            'metadata': {
                'framework': self._detect_framework(content),
                'component_type': self._detect_component_type(content),
                'hooks_used': self._extract_hooks(content)
            }
        }
```

---

## Python Agent

Specialized for Python backend development, frameworks, and best practices.

### Analysis Features

1. **Syntax & Style** - PEP 8 compliance, Code formatting issues, Import organization
2. **Security Scanning** - SQL injection vulnerabilities, XSS prevention, Insecure dependencies
3. **Framework Analysis** - Django best practices, Flask security patterns, FastAPI optimization
4. **Performance Optimization** - Database query optimization, Async/await usage, Memory efficiency

---

## Database Agent

Specialized for SQL optimization, schema validation, and database performance.

### Analysis Features

1. **Query Optimization** - Performance bottlenecks, Index usage analysis, Join optimization
2. **Security Analysis** - SQL injection prevention, Access control validation, Data exposure risks
3. **Schema Validation** - Foreign key constraints, Data type optimization, Normalization suggestions

---

# 📊 Data Models

## Analysis Results

Structured data models for all analysis operations.

### AnalysisResult Structure

```python
@dataclass
class AnalysisResult:
    """Comprehensive analysis result"""
    
    operation_id: str                    # Unique operation identifier
    file_path: str                       # Analyzed file path
    agent_type: str                      # Agent that performed analysis
    issues: List[CodeIssue]              # Detected issues
    suggestions: List[CodeSuggestion]    # Improvement suggestions
    confidence_score: float              # AI confidence (0.0-1.0)
    execution_time: float                # Analysis time in seconds
    metadata: Dict[str, Any]             # Agent-specific metadata
    
    def get_critical_issues(self) -> List[CodeIssue]:
        """Filter critical severity issues"""
        return [issue for issue in self.issues if issue.severity == 'critical']
    
    def has_blocking_issues(self) -> bool:
        """Check if any critical/high issues exist"""
        return any(issue.severity in ['critical', 'high'] for issue in self.issues)
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score (0-10)"""
        if not self.issues:
            return 10.0
        
        severity_weights = {'critical': 5, 'high': 3, 'medium': 2, 'low': 1, 'info': 0.5}
        total_weight = sum(severity_weights.get(issue.severity, 1) for issue in self.issues)
        return max(0.0, 10.0 - (total_weight / len(self.issues)))
```

---

# 🌐 Web Dashboard

## Dashboard Architecture

Interactive web interface built with Flask and modern frontend technologies.

### Backend Structure

```python
# run_dashboard.py
class DashboardApp:
    """Main dashboard application"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.sdk = CICodeCompanionSDK(SDKConfig())
        self.setup_routes()
    
    def setup_routes(self):
        """Configure API routes"""
        
        @self.app.route('/api/analyze', methods=['POST'])
        async def analyze_file():
            data = request.json
            result = await self.sdk.analyze_file(data['path'], data['content'])
            return jsonify(result.to_dict())
```

### Frontend Features

1. **File Upload & Analysis** - Drag & drop file upload, Real-time analysis progress, Interactive results display
2. **Code Editor Integration** - Monaco Editor with syntax highlighting, Inline issue annotations, Quick fix suggestions
3. **Interactive Chat** - Context-aware AI assistant, Code-specific questions, Multi-turn conversations
4. **Report Generation** - Exportable analysis reports, PDF and HTML formats, Custom report templates

---

# 📦 GitLab CI/CD Components

## AI Code Reviewer Component

Production-ready GitLab CI/CD component for automated code review.

### Component Configuration

```yaml
# components/ai-code-reviewer/template.yml
spec:
  inputs:
    gcp_project_id:
      description: "Google Cloud Project ID"
      type: string
    review_type:
      description: "Type of review (comprehensive, security, performance)"
      type: string
      default: "comprehensive"
    severity_threshold:
      description: "Minimum severity to report"
      type: string
      default: "medium"
    post_comment:
      description: "Whether to post review as MR comment"
      type: boolean
      default: true
```

### Usage in Projects

```yaml
# Your project's .gitlab-ci.yml
include:
  - component: $CI_SERVER_FQDN/your-group/ci-code-companion/ai-code-reviewer@main
    inputs:
      gcp_project_id: $GCP_PROJECT_ID
      review_type: "security"
      severity_threshold: "high"
      post_comment: true
```

---

# 🚀 Deployment

## Docker Deployment

Multi-stage Dockerfile optimized for development and production.

### Development Deployment

```bash
# Build development image
docker build --target development -t ci-companion-dev .

# Run with volume mounting for hot reload
docker run -p 5000:5000 \
  -v $(pwd):/app \
  -e GCP_PROJECT_ID=your-project \
  ci-companion-dev
```

### Production Deployment

```bash
# Build production image
docker build --target production -t ci-companion-prod .

# Run production container
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e GCP_PROJECT_ID=your-project \
  ci-companion-prod
```

---

## Cloud Run Deployment

Optimized for Google Cloud Run with automatic scaling.

```bash
# Build and push to Container Registry
docker build -t gcr.io/your-project/ci-companion .
docker push gcr.io/your-project/ci-companion

# Deploy to Cloud Run
gcloud run deploy ci-code-companion \
  --image gcr.io/your-project/ci-companion \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=your-project \
  --memory 2Gi \
  --cpu 2 \
  --concurrency 80 \
  --max-instances 10
```

---

# 📚 API Reference

## SDK Methods

### Core Analysis Methods

```python
# File analysis
async def analyze_file(
    file_path: str,
    content: str,
    agent_type: Optional[str] = None,
    project_context: Optional[Dict[str, Any]] = None
) -> AnalysisResult

# Test generation
async def generate_tests(
    file_path: str,
    content: str,
    test_type: str = 'unit',
    framework: Optional[str] = None
) -> TestGenerationResult

# Interactive chat
async def chat(
    message: str,
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str
```

---

## REST API Endpoints

### Analysis Endpoints

```http
POST /api/analyze
Content-Type: application/json

{
  "file_path": "src/component.jsx",
  "content": "// code content",
  "options": {
    "agent_type": "react",
    "severity_threshold": "medium"
  }
}
```

```http
POST /api/generate-tests
Content-Type: application/json

{
  "file_path": "src/utils.py",
  "content": "// code content",
  "test_type": "unit",
  "framework": "pytest"
}
```

---

# 💡 Examples & Tutorials

## Basic Usage Examples

### Simple File Analysis

```python
import asyncio
from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig

async def analyze_python_file():
    """Basic Python file analysis"""
    
    # Initialize SDK
    config = SDKConfig(ai_provider='vertex_ai')
    sdk = CICodeCompanionSDK(config=config)
    
    # Read file
    with open('example.py', 'r') as f:
        content = f.read()
    
    # Analyze
    result = await sdk.analyze_file('example.py', content)
    
    # Process results
    print(f"Analysis complete!")
    print(f"Issues found: {len(result.issues)}")
    print(f"Quality score: {result.calculate_quality_score():.1f}/10")
    
    # Show critical issues
    for issue in result.get_critical_issues():
        print(f"🔴 {issue.title} (Line {issue.line_number})")
        print(f"   {issue.description}")
        if issue.suggestion:
            print(f"   💡 Suggestion: {issue.suggestion}")

asyncio.run(analyze_python_file())
```

### Interactive Development Assistant

```python
async def development_assistant():
    """Interactive AI assistant for development questions"""
    
    sdk = CICodeCompanionSDK(SDKConfig())
    conversation_history = []
    
    print("🤖 CI Code Companion Assistant")
    print("Ask questions about your code or type 'exit' to quit\n")
    
    while True:
        question = input("You: ")
        if question.lower() == 'exit':
            break
        
        # Get AI response
        response = await sdk.chat(
            message=question,
            conversation_history=conversation_history
        )
        
        print(f"Assistant: {response}\n")
        
        # Update conversation history
        conversation_history.extend([
            {"role": "user", "message": question},
            {"role": "assistant", "message": response}
        ])

asyncio.run(development_assistant())
```

---

## Advanced Integrations

### Custom Agent Development

```python
from ci_code_companion_sdk.agents.base_agent import BaseAgent
from ci_code_companion_sdk.agents.agent_manager import AgentCapability

class GoAgent(BaseAgent):
    """Custom agent for Go language analysis"""
    
    def __init__(self, config, logger):
        super().__init__(config, logger)
        self.name = "go"
        self.supported_extensions = ['.go']
        
    def get_capabilities(self):
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.TEST_GENERATION,
            AgentCapability.OPTIMIZATION
        ]
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]):
        """Go-specific analysis logic"""
        
        issues = []
        suggestions = []
        
        # Go-specific checks
        if 'panic(' in content:
            issues.append({
                'title': 'Use of panic() detected',
                'description': 'Consider using error handling instead of panic',
                'severity': 'medium',
                'line_number': self._find_line_number(content, 'panic('),
                'suggestion': 'Return an error instead of using panic()'
            })
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'confidence_score': 0.85,
            'metadata': {
                'language': 'go',
                'go_version': self._detect_go_version(content),
                'modules_used': self._extract_imports(content)
            }
        }

# Register custom agent
sdk.agent_manager.register_custom_agent(
    'go',
    GoAgent,
    detection_patterns={
        'extensions': ['.go'],
        'content_patterns': [r'package\s+\w+', r'func\s+\w+'],
        'framework_indicators': ['go.mod', 'go.sum']
    }
)
```

---

*This documentation provides a complete understanding of every component in the CI Code Companion SDK, from core architecture to advanced usage patterns.* 