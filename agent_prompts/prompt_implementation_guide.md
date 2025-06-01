# Agent Prompt Implementation Guide

This guide explains how to integrate the Cursor-style agent prompts into your existing CI Code Companion system and leverage them for maximum effectiveness.

## Overview

The prompt system follows Cursor's principles of:
- **Structured system prompts** for each specialist agent
- **Tool-use mechanisms** with function calling
- **Shared code index** for context retrieval  
- **Context window management** with condensation
- **Plan-and-act prompting** for complex tasks
- **Unified conversation experience** through orchestration

## Integration Architecture

### 1. Prompt Loading System

```python
# prompt_loader.py
import os
from pathlib import Path

class PromptLoader:
    def __init__(self, prompts_dir="agent_prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts = {}
        self.load_all_prompts()
    
    def load_all_prompts(self):
        """Load all agent prompts from markdown files"""
        prompt_files = {
            'react_code': 'react_code_agent_prompt.md',
            'python_code': 'python_code_agent_prompt.md', 
            'security_scanner': 'security_scanner_agent_prompt.md',
            'react_test': 'react_test_agent_prompt.md',
            'master_orchestrator': 'master_orchestrator_prompt.md'
        }
        
        for agent_name, filename in prompt_files.items():
            prompt_path = self.prompts_dir / filename
            if prompt_path.exists():
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    self.prompts[agent_name] = f.read()
            else:
                print(f"Warning: Prompt file not found: {prompt_path}")
    
    def get_prompt(self, agent_name):
        """Get system prompt for specific agent"""
        return self.prompts.get(agent_name, "")
    
    def get_enhanced_prompt(self, agent_name, context=None):
        """Get prompt with dynamic context injection"""
        base_prompt = self.get_prompt(agent_name)
        
        if context:
            context_injection = self._build_context_injection(context)
            return f"{base_prompt}\n\n{context_injection}"
        
        return base_prompt
    
    def _build_context_injection(self, context):
        """Build context-specific prompt additions"""
        context_parts = []
        
        if context.get('project_files'):
            context_parts.append(f"## Project Context\n\nCurrent project files: {', '.join(context['project_files'])}")
        
        if context.get('selected_file'):
            context_parts.append(f"## Current File\n\nYou are currently analyzing: {context['selected_file']['path']}")
        
        if context.get('conversation_history'):
            recent_messages = context['conversation_history'][-3:]  # Last 3 messages for context
            context_parts.append(f"## Recent Conversation\n\n{self._format_conversation(recent_messages)}")
        
        return "\n\n".join(context_parts)
    
    def _format_conversation(self, messages):
        """Format recent conversation for context"""
        formatted = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')[:200] + "..." if len(msg.get('content', '')) > 200 else msg.get('content', '')
            formatted.append(f"{role.upper()}: {content}")
        return "\n".join(formatted)
```

### 2. Enhanced Specialized Engine

```python
# specialized_engine.py (updated)
from prompt_loader import PromptLoader
import asyncio

class EnhancedSpecializedEngine:
    def __init__(self):
        self.prompt_loader = PromptLoader()
        self.agents = {
            'react_code': ReactCodeAgent(),
            'python_code': PythonCodeAgent(),
            'security_scanner': SecurityScannerAgent(),
            'react_test': ReactTestAgent(),
            'master_orchestrator': MasterOrchestratorAgent()
        }
        self.context_manager = ContextManager()
    
    async def process_request(self, message, mode, context):
        """Process request with enhanced prompting"""
        # Determine primary agent based on mode and context
        primary_agent = self._route_to_agent(message, mode, context)
        
        # Get enhanced prompt with context
        enhanced_prompt = self.prompt_loader.get_enhanced_prompt(
            primary_agent, 
            context
        )
        
        # Check if multi-agent workflow is needed
        if self._requires_multi_agent(message, context):
            return await self._execute_multi_agent_workflow(message, context, enhanced_prompt)
        else:
            return await self._execute_single_agent(primary_agent, message, context, enhanced_prompt)
    
    def _route_to_agent(self, message, mode, context):
        """Route request to appropriate agent based on Cursor-style analysis"""
        # File-based routing
        if context.get('selected_file'):
            file_ext = context['selected_file'].get('name', '').split('.')[-1]
            if file_ext in ['jsx', 'tsx']:
                return 'react_code'
            elif file_ext == 'py':
                return 'python_code'
        
        # Mode-based routing
        mode_routing = {
            'code': self._route_code_mode(message, context),
            'test': 'react_test' if 'react' in message.lower() else 'python_test',
            'security': 'security_scanner'
        }
        
        return mode_routing.get(mode, 'master_orchestrator')
    
    def _route_code_mode(self, message, context):
        """Route code mode requests to specific code agents"""
        keywords = message.lower()
        
        if any(word in keywords for word in ['react', 'component', 'jsx', 'frontend']):
            return 'react_code'
        elif any(word in keywords for word in ['python', 'django', 'flask', 'fastapi']):
            return 'python_code'
        else:
            # Default to file context or master orchestrator
            return self._route_by_file_context(context)
    
    def _requires_multi_agent(self, message, context):
        """Determine if request requires multiple agents (Cursor-style complexity assessment)"""
        complexity_indicators = [
            'full stack', 'end to end', 'complete implementation',
            'security audit', 'comprehensive test', 'deployment',
            'architecture', 'system design'
        ]
        
        return any(indicator in message.lower() for indicator in complexity_indicators)
    
    async def _execute_multi_agent_workflow(self, message, context, base_prompt):
        """Execute coordinated multi-agent workflow"""
        # Use master orchestrator to plan workflow
        orchestrator_prompt = self.prompt_loader.get_enhanced_prompt('master_orchestrator', context)
        
        workflow_plan = await self.agents['master_orchestrator'].plan_workflow(
            message, context, orchestrator_prompt
        )
        
        # Execute workflow phases
        results = {}
        for phase in workflow_plan['phases']:
            agent_name = phase['agent']
            agent_prompt = self.prompt_loader.get_enhanced_prompt(agent_name, {
                **context,
                'workflow_context': workflow_plan,
                'current_phase': phase
            })
            
            results[phase['name']] = await self.agents[agent_name].process(
                phase['task'], context, agent_prompt
            )
        
        # Coordinate final response through orchestrator
        return await self.agents['master_orchestrator'].coordinate_response(
            results, workflow_plan, context
        )
    
    async def _execute_single_agent(self, agent_name, message, context, enhanced_prompt):
        """Execute single agent with enhanced prompting"""
        agent = self.agents.get(agent_name)
        if not agent:
            # Fallback to master orchestrator
            agent = self.agents['master_orchestrator']
            enhanced_prompt = self.prompt_loader.get_enhanced_prompt('master_orchestrator', context)
        
        return await agent.process(message, context, enhanced_prompt)
```

### 3. Context Management System

```python
# context_manager.py
class ContextManager:
    def __init__(self):
        self.conversation_history = []
        self.project_context = {}
        self.user_preferences = {}
    
    def build_context(self, request_data):
        """Build comprehensive context for agent prompts"""
        context = {
            'conversation_history': self.conversation_history[-10:],  # Last 10 messages
            'project_context': self.project_context,
            'user_preferences': self.user_preferences,
            'selected_file': request_data.get('context', {}).get('selectedFile'),
            'selected_files': request_data.get('context', {}).get('selectedFiles', []),
            'project_files': self._get_relevant_files(request_data),
            'current_mode': request_data.get('mode'),
            'timestamp': datetime.now().isoformat()
        }
        
        return context
    
    def update_conversation(self, user_message, assistant_response):
        """Update conversation history"""
        self.conversation_history.extend([
            {'role': 'user', 'content': user_message, 'timestamp': datetime.now()},
            {'role': 'assistant', 'content': assistant_response, 'timestamp': datetime.now()}
        ])
        
        # Keep only last 50 messages to manage memory
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def update_project_context(self, project_data):
        """Update project-specific context"""
        self.project_context.update({
            'framework': self._detect_framework(project_data),
            'dependencies': project_data.get('dependencies', []),
            'structure': project_data.get('structure', {}),
            'last_updated': datetime.now().isoformat()
        })
    
    def _detect_framework(self, project_data):
        """Detect project framework from dependencies and structure"""
        dependencies = project_data.get('dependencies', [])
        
        if any('react' in dep.lower() for dep in dependencies):
            return 'react'
        elif any('django' in dep.lower() or 'flask' in dep.lower() for dep in dependencies):
            return 'python'
        elif 'package.json' in project_data.get('files', []):
            return 'node'
        
        return 'unknown'
```

### 4. Tool Integration (Cursor-style Function Calling)

```python
# tool_integration.py
class ToolIntegration:
    def __init__(self, agents):
        self.agents = agents
        self.available_tools = {
            'codebase_search': self.codebase_search,
            'read_file': self.read_file,
            'analyze_dependencies': self.analyze_dependencies,
            'check_requirements': self.check_requirements,
            'scan_configuration': self.scan_configuration
        }
    
    async def codebase_search(self, query, scope=None):
        """Search codebase for patterns (like Cursor's semantic search)"""
        # Implement semantic search across codebase
        # This would integrate with your existing file search functionality
        search_results = await self._perform_semantic_search(query, scope)
        return {
            'results': search_results,
            'context': f"Found {len(search_results)} relevant code patterns"
        }
    
    async def read_file(self, file_path, start_line=None, end_line=None):
        """Read specific file content (like Cursor's read_file)"""
        # Implement file reading with optional line range
        content = await self._read_file_content(file_path, start_line, end_line)
        return {
            'content': content,
            'context': f"File content from {file_path}"
        }
    
    async def analyze_dependencies(self, file_path):
        """Analyze file dependencies"""
        # Implement dependency analysis
        dependencies = await self._analyze_file_dependencies(file_path)
        return {
            'dependencies': dependencies,
            'context': f"Dependencies analysis for {file_path}"
        }
    
    def get_tools_for_agent(self, agent_name):
        """Get available tools for specific agent"""
        agent_tools = {
            'react_code': ['codebase_search', 'read_file', 'analyze_dependencies'],
            'python_code': ['codebase_search', 'read_file', 'analyze_dependencies', 'check_requirements'],
            'security_scanner': ['codebase_search', 'read_file', 'scan_configuration', 'check_requirements'],
            'react_test': ['codebase_search', 'read_file', 'analyze_dependencies']
        }
        
        return {tool: self.available_tools[tool] for tool in agent_tools.get(agent_name, [])}
```

### 5. Integration with Existing API Routes

```python
# Update your existing api.py to use enhanced prompting
async def handle_code_mode(engine, message, context):
    """Enhanced code mode handler with structured prompting"""
    
    # Build comprehensive context
    enhanced_context = engine.context_manager.build_context({
        'mode': 'code',
        'context': context
    })
    
    # Process with enhanced prompting
    try:
        response = await engine.process_request(message, 'code', enhanced_context)
        
        # Update conversation history
        engine.context_manager.update_conversation(message, response['content'])
        
        return {
            "content": response['content'],
            "actions": response.get('actions', []),
            "context_used": response.get('context_used', False)
        }
        
    except Exception as e:
        logger.error(f"Code mode processing error: {e}")
        # Fallback to general response with error context
        return {
            "content": f"I encountered an issue processing your request: {str(e)}. Let me provide general guidance instead.",
            "actions": [],
            "context_used": False
        }

# Similar updates for handle_test_mode and handle_security_mode
```

## Configuration and Customization

### 1. Environment Configuration

```python
# config.py
class AgentConfig:
    # Prompt configuration
    PROMPTS_DIR = os.getenv('AGENT_PROMPTS_DIR', 'agent_prompts')
    CONTEXT_WINDOW_SIZE = int(os.getenv('CONTEXT_WINDOW_SIZE', '8000'))
    MAX_CONVERSATION_HISTORY = int(os.getenv('MAX_CONVERSATION_HISTORY', '50'))
    
    # Agent-specific configurations
    REACT_AGENT_CONFIG = {
        'preferred_styling': os.getenv('REACT_STYLING_PREFERENCE', 'styled-components'),
        'typescript_strict': os.getenv('TYPESCRIPT_STRICT', 'true').lower() == 'true'
    }
    
    PYTHON_AGENT_CONFIG = {
        'preferred_framework': os.getenv('PYTHON_FRAMEWORK_PREFERENCE', 'fastapi'),
        'type_checking': os.getenv('PYTHON_TYPE_CHECKING', 'strict')
    }
    
    SECURITY_AGENT_CONFIG = {
        'compliance_standards': os.getenv('SECURITY_COMPLIANCE', 'OWASP,NIST').split(','),
        'scan_depth': os.getenv('SECURITY_SCAN_DEPTH', 'comprehensive')
    }
```

### 2. Customization Hooks

```python
# customization.py
class PromptCustomizer:
    def __init__(self, prompt_loader):
        self.prompt_loader = prompt_loader
        self.customizations = {}
    
    def add_project_specific_rules(self, agent_name, rules):
        """Add project-specific rules to agent prompts"""
        if agent_name not in self.customizations:
            self.customizations[agent_name] = []
        
        self.customizations[agent_name].extend(rules)
    
    def get_customized_prompt(self, agent_name, base_context):
        """Get prompt with project-specific customizations"""
        base_prompt = self.prompt_loader.get_enhanced_prompt(agent_name, base_context)
        
        if agent_name in self.customizations:
            custom_rules = "\n\n## Project-Specific Rules\n\n"
            custom_rules += "\n".join(f"- {rule}" for rule in self.customizations[agent_name])
            base_prompt += custom_rules
        
        return base_prompt

# Usage example:
customizer = PromptCustomizer(prompt_loader)
customizer.add_project_specific_rules('react_code', [
    "Always use React Query for data fetching",
    "Prefer React Hook Form over Formik",
    "Use Chakra UI component library"
])
```

## Testing and Validation

### 1. Prompt Testing Framework

```python
# prompt_testing.py
class PromptTester:
    def __init__(self, prompt_loader):
        self.prompt_loader = prompt_loader
    
    def test_prompt_completeness(self, agent_name):
        """Test that prompt contains all required sections"""
        prompt = self.prompt_loader.get_prompt(agent_name)
        
        required_sections = [
            "Core Principles",
            "Domain Expertise", 
            "Tool Usage Guidelines",
            "Response Format"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in prompt:
                missing_sections.append(section)
        
        return {
            'complete': len(missing_sections) == 0,
            'missing_sections': missing_sections
        }
    
    def test_context_injection(self, agent_name, test_context):
        """Test context injection functionality"""
        enhanced_prompt = self.prompt_loader.get_enhanced_prompt(agent_name, test_context)
        
        # Verify context was properly injected
        context_indicators = [
            'Project Context' if test_context.get('project_files') else None,
            'Current File' if test_context.get('selected_file') else None,
            'Recent Conversation' if test_context.get('conversation_history') else None
        ]
        
        injected = [indicator for indicator in context_indicators if indicator and indicator in enhanced_prompt]
        
        return {
            'context_injected': len(injected) > 0,
            'injected_sections': injected
        }
```

### 2. Response Quality Validation

```python
# response_validation.py
class ResponseValidator:
    def __init__(self):
        self.quality_checks = [
            self.check_markdown_formatting,
            self.check_code_examples,
            self.check_actionable_recommendations,
            self.check_security_considerations
        ]
    
    def validate_response(self, response, agent_name):
        """Validate agent response quality"""
        results = {}
        
        for check in self.quality_checks:
            try:
                results[check.__name__] = check(response, agent_name)
            except Exception as e:
                results[check.__name__] = {'error': str(e)}
        
        return results
    
    def check_markdown_formatting(self, response, agent_name):
        """Check if response uses proper markdown formatting"""
        has_headers = '##' in response
        has_code_blocks = '```' in response
        has_lists = any(line.strip().startswith(('-', '*', '1.')) for line in response.split('\n'))
        
        return {
            'has_headers': has_headers,
            'has_code_blocks': has_code_blocks,
            'has_lists': has_lists,
            'score': sum([has_headers, has_code_blocks, has_lists]) / 3
        }
```

## Monitoring and Optimization

### 1. Usage Analytics

```python
# analytics.py
class PromptAnalytics:
    def __init__(self):
        self.usage_stats = defaultdict(int)
        self.response_times = defaultdict(list)
        self.user_satisfaction = defaultdict(list)
    
    def track_agent_usage(self, agent_name, response_time, user_rating=None):
        """Track agent usage and performance"""
        self.usage_stats[agent_name] += 1
        self.response_times[agent_name].append(response_time)
        
        if user_rating:
            self.user_satisfaction[agent_name].append(user_rating)
    
    def get_performance_report(self):
        """Generate performance report"""
        report = {}
        
        for agent in self.usage_stats:
            avg_response_time = sum(self.response_times[agent]) / len(self.response_times[agent])
            avg_satisfaction = sum(self.user_satisfaction[agent]) / len(self.user_satisfaction[agent]) if self.user_satisfaction[agent] else 0
            
            report[agent] = {
                'usage_count': self.usage_stats[agent],
                'avg_response_time': avg_response_time,
                'avg_satisfaction': avg_satisfaction
            }
        
        return report
```

### 2. Continuous Improvement

```python
# improvement.py
class PromptOptimizer:
    def __init__(self, analytics):
        self.analytics = analytics
    
    def suggest_improvements(self):
        """Suggest prompt improvements based on analytics"""
        report = self.analytics.get_performance_report()
        suggestions = []
        
        for agent, stats in report.items():
            if stats['avg_satisfaction'] < 3.5:  # Out of 5
                suggestions.append({
                    'agent': agent,
                    'issue': 'Low user satisfaction',
                    'suggestion': 'Review prompt clarity and accuracy'
                })
            
            if stats['avg_response_time'] > 10.0:  # Seconds
                suggestions.append({
                    'agent': agent,
                    'issue': 'Slow response time',
                    'suggestion': 'Optimize prompt length and complexity'
                })
        
        return suggestions
```

## Best Practices for Implementation

### 1. Gradual Rollout
- Start with one agent (e.g., ReactCodeAgent) to test the system
- Gradually add more agents once the first one is working well
- Monitor performance and user feedback closely

### 2. Context Management
- Implement efficient context caching to reduce redundant processing
- Use context window limits to prevent token overflow
- Prioritize most relevant context when limits are reached

### 3. Error Handling
- Always have fallback responses for when agents fail
- Log errors for debugging and improvement
- Provide graceful degradation to simpler responses

### 4. Performance Optimization
- Cache frequently used prompts and contexts
- Use async processing for multi-agent workflows
- Implement timeout handling for long-running requests

### 5. User Experience
- Maintain consistent response formatting across all agents
- Provide clear loading indicators for multi-agent workflows
- Allow users to interrupt or modify ongoing processes

This implementation guide provides a comprehensive framework for integrating Cursor-style prompting into your existing system while maintaining the flexibility to customize and optimize based on your specific needs. 