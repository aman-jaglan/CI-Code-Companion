# Specialized Agents Architecture

This directory contains the new specialized agent system for the CI Code Companion SDK. The agents are organized by their primary function rather than technology stack.

## Agent Categories

### 1. Code Agents (`code/`)
Focused exclusively on code writing, analysis, and optimization:
- `react_code_agent.py` - React component development and code analysis
- `python_code_agent.py` - Python code writing and analysis
- `node_code_agent.py` - Node.js backend code development
- `database_code_agent.py` - Database schema and query optimization

### 2. Test Agents (`testing/`)
Specialized in test generation, analysis, and quality assurance:
- `react_test_agent.py` - React component testing (Jest, RTL, Cypress)
- `python_test_agent.py` - Python testing (pytest, unittest, integration)
- `api_test_agent.py` - API endpoint testing and validation
- `e2e_test_agent.py` - End-to-end testing strategies

### 3. Security & Compliance Agents (`security/`)
Focused on security analysis, vulnerability detection, and compliance:
- `security_scanner_agent.py` - General security vulnerability scanning
- `dependency_security_agent.py` - Dependency vulnerability analysis
- `compliance_agent.py` - Code compliance and standards validation
- `data_privacy_agent.py` - Data privacy and GDPR compliance

## Agent Communication

Agents can work together through the AgentOrchestrator which:
- Routes requests to appropriate specialized agents
- Combines results from multiple agents
- Manages agent workflows for complex tasks
- Provides unified results to the interface

## Interface Integration

The new system supports separate chat interfaces:
- **Code Chat** - Interacts with code agents for development tasks
- **Analysis Chat** - Interacts with test and security agents for quality assurance

## Production Workflow

```
User Request → AgentOrchestrator → [Code Agent, Test Agent, Security Agent] → Combined Results
```

This ensures every code change is validated for:
1. Code quality and functionality
2. Test coverage and reliability  
3. Security and compliance standards 