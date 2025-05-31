# CI Code Companion SDK - Complete Documentation

---

## 📋 **Table of Contents**

### 🏠 **Getting Started**
- [Overview & Architecture](#overview--architecture)
- [Quick Start Guide](#quick-start-guide)
- [Installation](#installation)
- [Configuration](#configuration)

### 🧠 **Core SDK**
- [Engine Architecture](#engine-architecture)
- [Configuration Management](#configuration-management)
- [Exception Handling](#exception-handling)
- [Utility Functions](#utility-functions)

### 🤖 **Agent System**
- [Agent Architecture](#agent-architecture)
- [React Agent](#react-agent)
- [Python Agent](#python-agent)
- [Node.js Agent](#nodejs-agent)
- [Database Agent](#database-agent)
- [DevOps Agent](#devops-agent)
- [Mobile Agent](#mobile-agent)

### 📊 **Data Models**
- [Analysis Results](#analysis-results)
- [Code Issues](#code-issues)
- [Test Generation](#test-generation)
- [Optimization Results](#optimization-results)

### 🔧 **Services**
- [File Service](#file-service)
- [Git Integration](#git-integration)
- [AI Provider Integration](#ai-provider-integration)

### 🌐 **Web Dashboard**
- [Dashboard Architecture](#dashboard-architecture)
- [File Upload & Analysis](#file-upload--analysis)
- [Interactive Chat](#interactive-chat)
- [Report Generation](#report-generation)

### 📦 **GitLab CI/CD Components**
- [AI Code Reviewer Component](#ai-code-reviewer-component)
- [AI Test Generator Component](#ai-test-generator-component)
- [Custom Pipeline Integration](#custom-pipeline-integration)

### 🚀 **Deployment**
- [Docker Deployment](#docker-deployment)
- [Cloud Run Deployment](#cloud-run-deployment)
- [Local Development](#local-development)

### 📚 **API Reference**
- [SDK Methods](#sdk-methods)
- [REST API Endpoints](#rest-api-endpoints)
- [Configuration Options](#configuration-options)

### 💡 **Examples & Tutorials**
- [Basic Usage Examples](#basic-usage-examples)
- [Advanced Integrations](#advanced-integrations)
- [Custom Agent Development](#custom-agent-development)

---

## 🏠 Getting Started

### Overview & Architecture

The **CI Code Companion SDK** is a production-ready Python SDK that brings advanced AI capabilities to development workflows. Built with modern async architecture and intelligent agent routing.

#### **System Architecture**

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

#### **Key Features**
- ⚡ **Async Performance** - Modern async/await architecture
- 🎯 **Intelligent Routing** - Automatic agent selection
- 🔍 **Comprehensive Analysis** - Security, performance, style
- 🧪 **Smart Test Generation** - Framework-specific tests
- 💬 **Interactive AI Chat** - Context-aware assistance
- 🚀 **Production Ready** - Error handling, monitoring, logging

---

### Quick Start Guide

#### **1. Installation**

```bash
# Install from source
git clone https://github.com/your-org/CI-Code-Companion.git
cd CI-Code-Companion
pip install -e .
```

#### **2. Basic Usage**

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

#### **3. Web Dashboard**

```bash
python run_dashboard.py
# Visit http://localhost:5001
```

---

## 🧠 Core SDK

### Engine Architecture

The core engine (`ci_code_companion_sdk/core/engine.py`) orchestrates all SDK operations with async/await patterns.

#### **Main Components**

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

#### **Key Features**
- **Singleton Pattern** - Single SDK instance per configuration
- **Async Operations** - All operations are non-blocking
- **Resource Management** - Automatic cleanup and timeout handling
- **Error Recovery** - Graceful handling of failures
- **Operation Tracking** - Monitor active operations and performance

#### **Configuration Integration**

```python
# Environment-based configuration
config = SDKConfig(
    ai_provider='vertex_ai',
    project_id=os.getenv('GCP_PROJECT_ID'),
    max_concurrent=5,
    enable_caching=True
)

# File-based configuration
config = SDKConfig.from_file('ci_config.yaml')
```

---

### Configuration Management

The configuration system (`ci_code_companion_sdk/core/config.py`) provides flexible, hierarchical configuration management.

#### **Configuration Sources (Priority Order)**

1. **Environment Variables** - Highest priority
2. **Configuration Files** - YAML/JSON support
3. **Default Values** - Fallback defaults

#### **Configuration Structure**

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

security:
  allowed_file_types: [".py", ".js", ".jsx", ".ts", ".tsx"]
  max_file_size: 10485760  # 10MB
  blocked_patterns: ["**/node_modules/**", "**/.git/**"]
```

#### **Dynamic Configuration**

```python
# Runtime configuration updates
sdk.config.update_agent_config('python_agent', {
    'frameworks': ['fastapi', 'starlette'],
    'enable_security_scan': True
})

# Feature flag management
if sdk.config.is_feature_enabled('advanced_analysis'):
    result = await sdk.analyze_file_advanced(file_path, content)
```

---

### Exception Handling

The exception system (`ci_code_companion_sdk/core/exceptions.py`) provides structured error handling with context and recovery suggestions.

#### **Exception Hierarchy**

```python
SDKError                          # Base exception
├── ConfigurationError            # Configuration issues
│   ├── MissingConfigError       # Required config missing
│   └── InvalidConfigError       # Invalid config values
├── AnalysisError                # Analysis failures
│   ├── UnsupportedFileError     # File type not supported
│   ├── FileTooLargeError        # File exceeds size limit
│   └── AgentTimeoutError        # Agent operation timeout
├── AIProviderError              # AI service issues
│   ├── AuthenticationError      # Auth failures
│   ├── QuotaExceededError       # Rate limits
│   └── ServiceUnavailableError  # Service down
└── ValidationError              # Input validation failures
```

#### **Error Context & Recovery**

```python
try:
    result = await sdk.analyze_file(file_path, content)
except FileTooLargeError as e:
    print(f"Error: {e.message}")
    print(f"File size: {e.file_size}, Max allowed: {e.max_size}")
    print(f"Suggestion: {e.suggestion}")
    # e.suggestion: "Consider splitting large files or increasing max_file_size"
except AgentTimeoutError as e:
    print(f"Agent {e.agent_name} timed out after {e.timeout}s")
    print(f"Recovery: {e.recovery_suggestions}")
```

#### **Error Aggregation**

```python
# Multiple file analysis with error collection
results = await sdk.analyze_files_batch(file_paths)
if results.has_errors():
    for error in results.errors:
        logger.error(f"Failed to analyze {error.file_path}: {error.message}")
```

---

## 🤖 Agent System

### Agent Architecture

The agent system provides specialized AI capabilities for different technologies and file types.

#### **Base Agent Interface**

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
        
    @abstractmethod
    async def optimize_code(self, file_path: str, content: str) -> Dict[str, Any]:
        """Provide optimization suggestions"""
```

#### **Agent Manager**

```python
class AgentManager:
    """Manages agent lifecycle and routing"""
    
    def get_agent_for_file(self, file_path: str) -> BaseAgent:
        """Intelligent agent selection based on file analysis"""
        
        # File extension mapping
        if file_path.endswith(('.jsx', '.tsx')):
            return self.react_agent
        elif file_path.endswith('.py'):
            return self.python_agent
            
        # Content-based detection
        content_hints = self.analyze_file_content(file_path)
        return self.select_agent_by_content(content_hints)
```

---

### React Agent

Specialized for React, Next.js, and modern frontend development.

#### **Capabilities**

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
        
        # Performance analysis
        perf_suggestions = await self._analyze_performance(content)
        suggestions.extend(perf_suggestions)
        
        # Component structure analysis
        structure_suggestions = await self._analyze_component_structure(content)
        suggestions.extend(structure_suggestions)
        
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

#### **Analysis Features**

1. **JSX/TSX Pattern Analysis**
   - Component lifecycle issues
   - Props validation
   - State management patterns

2. **React Hooks Validation**
   - Rules of Hooks compliance
   - Dependency array issues
   - Hook optimization opportunities

3. **Performance Analysis**
   - Unnecessary re-renders
   - Bundle size optimization
   - Lazy loading opportunities

4. **Component Structure**
   - Component composition
   - Prop drilling detection
   - Accessibility improvements

#### **Test Generation**

```python
async def generate_tests(self, file_path: str, content: str) -> Dict[str, Any]:
    """Generate React component tests"""
    
    # Extract component info
    component_info = self._parse_component(content)
    
    # Generate test cases
    test_cases = []
    test_cases.extend(self._generate_rendering_tests(component_info))
    test_cases.extend(self._generate_props_tests(component_info))
    test_cases.extend(self._generate_interaction_tests(component_info))
    test_cases.extend(self._generate_hook_tests(component_info))
    
    return {
        'test_code': self._generate_test_file(test_cases),
        'framework': 'jest',
        'coverage_areas': ['rendering', 'props', 'interactions', 'hooks'],
        'test_file_path': f"__tests__/{component_info['name']}.test.jsx"
    }
```

---

### Python Agent

Specialized for Python backend development, frameworks, and best practices.

#### **Capabilities**

```python
class PythonAgent(BaseAgent):
    """Python backend specialist agent"""
    
    SUPPORTED_EXTENSIONS = ['.py', '.pyx', '.pyi']
    FRAMEWORKS = ['django', 'flask', 'fastapi', 'starlette', 'pytest']
    
    async def analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Python-specific analysis"""
        
        issues = []
        suggestions = []
        
        # Syntax and style checking
        syntax_issues = await self._check_syntax(content)
        issues.extend(syntax_issues)
        
        # PEP 8 validation
        style_issues = await self._validate_pep8(content)
        issues.extend(style_issues)
        
        # Security scanning
        security_issues = await self._scan_security(content)
        issues.extend(security_issues)
        
        # Framework-specific analysis
        framework = self._detect_framework(content)
        if framework:
            framework_suggestions = await self._analyze_framework_patterns(content, framework)
            suggestions.extend(framework_suggestions)
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'confidence_score': self._calculate_confidence(content),
            'metadata': {
                'framework': framework,
                'python_version': self._detect_python_version(content),
                'complexity_score': self._calculate_complexity(content)
            }
        }
```

#### **Analysis Features**

1. **Syntax & Style**
   - PEP 8 compliance
   - Code formatting issues
   - Import organization

2. **Security Scanning**
   - SQL injection vulnerabilities
   - XSS prevention
   - Insecure dependencies

3. **Framework Analysis**
   - Django best practices
   - Flask security patterns
   - FastAPI optimization

4. **Performance Optimization**
   - Database query optimization
   - Async/await usage
   - Memory efficiency

---

### Database Agent

Specialized for SQL optimization, schema validation, and database performance.

#### **Capabilities**

```python
class DatabaseAgent(BaseAgent):
    """Database specialist agent"""
    
    SUPPORTED_EXTENSIONS = ['.sql', '.py', '.js', '.ts']
    DATABASES = ['postgresql', 'mysql', 'sqlite', 'mongodb']
    
    async def analyze_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Database-specific analysis"""
        
        if file_path.endswith('.sql'):
            return await self._analyze_sql_file(content)
        else:
            return await self._analyze_database_code(content)
    
    async def _analyze_sql_file(self, content: str) -> Dict[str, Any]:
        """Analyze SQL queries and schema"""
        
        issues = []
        suggestions = []
        
        # Query optimization
        queries = self._extract_queries(content)
        for query in queries:
            optimization_suggestions = await self._optimize_query(query)
            suggestions.extend(optimization_suggestions)
        
        # Security analysis
        security_issues = await self._scan_sql_security(content)
        issues.extend(security_issues)
        
        # Index recommendations
        index_suggestions = await self._recommend_indexes(content)
        suggestions.extend(index_suggestions)
        
        return {
            'issues': issues,
            'suggestions': suggestions,
            'metadata': {
                'query_count': len(queries),
                'complexity_level': self._assess_complexity(queries),
                'database_type': self._detect_database_type(content)
            }
        }
```

#### **Analysis Features**

1. **Query Optimization**
   - Performance bottlenecks
   - Index usage analysis
   - Join optimization

2. **Security Analysis**
   - SQL injection prevention
   - Access control validation
   - Data exposure risks

3. **Schema Validation**
   - Foreign key constraints
   - Data type optimization
   - Normalization suggestions

---

## 📊 Data Models

### Analysis Results

Structured data models for all analysis operations.

#### **AnalysisResult Structure**

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

#### **CodeIssue Structure**

```python
@dataclass
class CodeIssue:
    """Individual code issue"""
    
    id: str                             # Unique issue identifier
    title: str                          # Short issue description
    description: str                    # Detailed explanation
    severity: IssueSeverity            # critical, high, medium, low, info
    category: IssueCategory            # security, performance, style, logic
    line_number: Optional[int]         # Line location in file
    column_number: Optional[int]       # Column location
    suggestion: Optional[str]          # How to fix the issue
    fix_code: Optional[str]            # Suggested code replacement
    confidence_score: float            # AI confidence in this issue
    documentation_url: Optional[str]   # Reference documentation
    
    def is_auto_fixable(self) -> bool:
        """Check if issue can be automatically fixed"""
        return self.fix_code is not None and self.confidence_score > 0.8
```

---

## 🌐 Web Dashboard

### Dashboard Architecture

Interactive web interface built with Flask and modern frontend technologies.

#### **Backend Structure**

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
        
        @self.app.route('/api/generate-tests', methods=['POST'])
        async def generate_tests():
            data = request.json
            result = await self.sdk.generate_tests(data['path'], data['content'])
            return jsonify(result)
        
        @self.app.route('/api/chat', methods=['POST'])
        async def chat():
            data = request.json
            response = await self.sdk.chat(
                data['message'], 
                data.get('file_path'), 
                data.get('content')
            )
            return jsonify({'response': response})
```

#### **Frontend Features**

1. **File Upload & Analysis**
   - Drag & drop file upload
   - Real-time analysis progress
   - Interactive results display

2. **Code Editor Integration**
   - Monaco Editor with syntax highlighting
   - Inline issue annotations
   - Quick fix suggestions

3. **Interactive Chat**
   - Context-aware AI assistant
   - Code-specific questions
   - Multi-turn conversations

4. **Report Generation**
   - Exportable analysis reports
   - PDF and HTML formats
   - Custom report templates

---

## 📦 GitLab CI/CD Components

### AI Code Reviewer Component

Production-ready GitLab CI/CD component for automated code review.

#### **Component Configuration**

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

ai_code_reviewer:
  stage: test
  image: python:3.11
  variables:
    GCP_PROJECT_ID: $[[ inputs.gcp_project_id ]]
    REVIEW_TYPE: $[[ inputs.review_type ]]
    SEVERITY_THRESHOLD: $[[ inputs.severity_threshold ]]
    POST_COMMENT: $[[ inputs.post_comment ]]
  before_script:
    - pip install -e .
  script:
    - python -c "import asyncio; from ci_code_companion_sdk import CICodeCompanionSDK; # Analysis logic"
```

#### **Usage in Projects**

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

#### **Features**

- **Automated Analysis** - Triggers on merge requests
- **Intelligent Filtering** - Configurable severity thresholds
- **GitLab Integration** - Posts results as MR comments
- **Multi-language Support** - Supports all agent capabilities
- **Artifact Generation** - Exportable reports and JSON data

---

## 🚀 Deployment

### Docker Deployment

Multi-stage Dockerfile optimized for development and production.

#### **Development Deployment**

```bash
# Build development image
docker build --target development -t ci-companion-dev .

# Run with volume mounting for hot reload
docker run -p 5000:5000 \
  -v $(pwd):/app \
  -e GCP_PROJECT_ID=your-project \
  ci-companion-dev
```

#### **Production Deployment**

```bash
# Build production image
docker build --target production -t ci-companion-prod .

# Run production container
docker run -p 8080:8080 \
  -e PORT=8080 \
  -e GCP_PROJECT_ID=your-project \
  ci-companion-prod
```

#### **Docker Compose**

```yaml
# docker-compose.yml
version: '3.8'
services:
  ci-companion:
    build:
      context: .
      target: production
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - GCP_PROJECT_ID=${GCP_PROJECT_ID}
    volumes:
      - ./config:/app/config:ro
    restart: unless-stopped
```

### Cloud Run Deployment

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

## 📚 API Reference

### SDK Methods

#### **Core Analysis Methods**

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

# Code optimization
async def optimize_code(
    file_path: str,
    content: str,
    optimization_type: str = 'performance'
) -> OptimizationResult

# Interactive chat
async def chat(
    message: str,
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str
```

#### **Batch Operations**

```python
# Analyze multiple files
async def analyze_files_batch(
    file_paths: List[str],
    max_concurrent: int = 5
) -> BatchAnalysisResult

# Generate project report
async def generate_project_report(
    project_path: str,
    output_format: str = 'html'
) -> ProjectReport
```

#### **Management Methods**

```python
# Health check
async def health_check() -> Dict[str, Any]

# Get statistics
async def get_stats() -> Dict[str, Any]

# Get active operations
def get_active_operations() -> List[Dict[str, Any]]

# Cancel operation
def cancel_operation(operation_id: str) -> bool
```

### REST API Endpoints

#### **Analysis Endpoints**

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

#### **Interactive Endpoints**

```http
POST /api/chat
Content-Type: application/json

{
  "message": "How can I optimize this function?",
  "file_path": "src/helper.py",
  "content": "// code content",
  "conversation_id": "optional-uuid"
}
```

#### **Management Endpoints**

```http
GET /api/health
# Returns: {"status": "healthy", "version": "1.0.0"}

GET /api/stats
# Returns: {"active_operations": 3, "success_rate": 0.95}

GET /api/operations
# Returns: [{"id": "uuid", "status": "running", "progress": 0.75}]
```

---

## 💡 Examples & Tutorials

### Basic Usage Examples

#### **Simple File Analysis**

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

#### **Batch Project Analysis**

```python
async def analyze_project():
    """Analyze entire project directory"""
    
    sdk = CICodeCompanionSDK(SDKConfig())
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk('src/'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Analyze files in batches
    results = await sdk.analyze_files_batch(python_files, max_concurrent=3)
    
    # Generate summary
    total_issues = sum(len(r.issues) for r in results.results)
    avg_quality = sum(r.calculate_quality_score() for r in results.results) / len(results.results)
    
    print(f"Project Analysis Summary:")
    print(f"Files analyzed: {len(results.results)}")
    print(f"Total issues: {total_issues}")
    print(f"Average quality: {avg_quality:.1f}/10")
    
    # Generate HTML report
    report = await sdk.generate_project_report('src/', output_format='html')
    with open('project_report.html', 'w') as f:
        f.write(report.content)

asyncio.run(analyze_project())
```

#### **Interactive Development Assistant**

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

### Advanced Integrations

#### **Custom Agent Development**

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
        
        # Check for goroutine leaks
        if 'go func(' in content and 'defer' not in content:
            suggestions.append({
                'title': 'Potential goroutine leak',
                'description': 'Consider using context for goroutine cancellation',
                'impact': 'medium'
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
    
    async def generate_tests(self, file_path: str, content: str, context: Dict[str, Any]):
        """Generate Go tests"""
        
        # Extract functions from Go code
        functions = self._extract_functions(content)
        
        test_cases = []
        for func in functions:
            if func['is_exported']:  # Only test exported functions
                test_cases.extend(self._generate_test_cases_for_function(func))
        
        return {
            'test_code': self._generate_go_test_file(test_cases),
            'framework': 'testing',
            'test_file_path': file_path.replace('.go', '_test.go')
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

#### **GitLab CI Integration**

```python
# gitlab_integration.py
import os
import json
from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig

async def gitlab_ci_analysis():
    """GitLab CI integration for automated code review"""
    
    # Initialize SDK with GitLab environment
    config = SDKConfig(
        ai_provider='vertex_ai',
        project_id=os.getenv('GCP_PROJECT_ID'),
        gitlab_token=os.getenv('GITLAB_TOKEN'),
        gitlab_project_id=os.getenv('CI_PROJECT_ID')
    )
    sdk = CICodeCompanionSDK(config=config)
    
    # Get changed files in merge request
    changed_files = get_changed_files_from_git()
    
    results = []
    for file_path in changed_files:
        if is_analyzable_file(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                result = await sdk.analyze_file(file_path, content)
                results.append({
                    'file_path': file_path,
                    'analysis': result.to_dict()
                })
                
            except Exception as e:
                print(f"Failed to analyze {file_path}: {e}")
    
    # Generate reports
    os.makedirs('ai-reports', exist_ok=True)
    
    # JSON report for programmatic use
    with open('ai-reports/analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Markdown report for human review
    markdown_report = generate_markdown_report(results)
    with open('ai-reports/analysis.md', 'w') as f:
        f.write(markdown_report)
    
    # Post comment to merge request
    if os.getenv('CI_MERGE_REQUEST_IID'):
        await post_mr_comment(sdk, markdown_report)

def get_changed_files_from_git():
    """Get list of changed files in current branch"""
    import subprocess
    
    try:
        result = subprocess.run([
            'git', 'diff', '--name-only', 
            f'origin/{os.getenv("CI_MERGE_REQUEST_TARGET_BRANCH_NAME", "main")}...HEAD'
        ], capture_output=True, text=True, check=True)
        
        return [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except subprocess.CalledProcessError:
        return []

if __name__ == "__main__":
    import asyncio
    asyncio.run(gitlab_ci_analysis())
```

---

This comprehensive documentation provides a complete understanding of every component in the CI Code Companion SDK, from core architecture to advanced usage patterns. Each section includes practical examples and implementation details to help developers effectively use and extend the system. 