"""
Prompt Loader for CI Code Companion SDK

This module provides dynamic prompt loading and context injection for specialized agents,
following Cursor's approach to structured system prompts with context awareness.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import SDKConfig


class PromptLoader:
    """
    Dynamic prompt loader with context injection for specialized agents.
    Supports Cursor-style prompt enhancement with project context, conversation history,
    and file-specific information.
    """
    
    def __init__(self, config: SDKConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.prompts_dir = Path(config.get('prompts_dir', 'agent_prompts'))
        self.prompts: Dict[str, str] = {}
        self.context_templates: Dict[str, str] = {}
        
        # Initialize prompts
        self._load_all_prompts()
        self._load_context_templates()
    
    def _load_all_prompts(self) -> None:
        """Load all agent prompts from markdown files"""
        prompt_files = {
            'react_code': 'react_code_agent_prompt.md',
            'python_code': 'python_code_agent_prompt.md',
            'node_code': 'node_code_agent_prompt.md',
            'security_scanner': 'security_scanner_agent_prompt.md',
            'react_test': 'react_test_agent_prompt.md',
            'python_test': 'python_test_agent_prompt.md',
            'api_test': 'api_test_agent_prompt.md',
            'dependency_security': 'dependency_security_agent_prompt.md',
            'master_orchestrator': 'master_orchestrator_prompt.md'
        }
        
        for agent_name, filename in prompt_files.items():
            prompt_path = self.prompts_dir / filename
            if prompt_path.exists():
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        self.prompts[agent_name] = f.read()
                    self.logger.debug(f"Loaded prompt for {agent_name}")
                except Exception as e:
                    self.logger.error(f"Failed to load prompt {filename}: {e}")
            else:
                self.logger.warning(f"Prompt file not found: {prompt_path}")
    
    def _load_context_templates(self) -> None:
        """Load context injection templates"""
        self.context_templates = {
            'project_context': """
## Project Context

**Project Type**: {project_type}
**Main Technologies**: {technologies}
**File Structure**: {file_structure}
**Dependencies**: {dependencies}
""",
            'current_file': """
## Current File Analysis

**File**: `{file_path}`
**Language**: {language}
**Size**: {file_size} lines
**Last Modified**: {last_modified}

### File Content Summary:
{content_summary}
""",
            'conversation_history': """
## Recent Conversation Context

{conversation_summary}
""",
            'gemini_optimization': """
## Gemini 2.5 Pro Optimization Context

**Context Window**: 1M tokens available
**Model Capabilities**: Advanced reasoning, code understanding, multimodal
**Processing Mode**: {processing_mode}
**Performance Level**: {performance_level}
"""
        }
    
    def get_prompt(self, agent_name: str) -> str:
        """Get base system prompt for specific agent"""
        return self.prompts.get(agent_name, "")
    
    def get_enhanced_prompt(
        self, 
        agent_name: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get prompt with dynamic context injection optimized for Gemini 2.5 Pro.
        
        Args:
            agent_name: Name of the agent to get prompt for
            context: Context data for injection
            
        Returns:
            Enhanced prompt with context
        """
        base_prompt = self.get_prompt(agent_name)
        if not base_prompt:
            self.logger.warning(f"No prompt found for agent: {agent_name}")
            return ""
        
        if not context:
            return base_prompt
        
        # Build context injection optimized for 1M context window
        context_injection = self._build_context_injection(context, agent_name)
        
        # Combine base prompt with context
        enhanced_prompt = f"{base_prompt}\n\n{context_injection}"
        
        # Add Gemini-specific optimizations
        enhanced_prompt = self._add_gemini_optimizations(enhanced_prompt, context, agent_name)
        
        return enhanced_prompt
    
    def _build_context_injection(self, context: Dict[str, Any], agent_name: str) -> str:
        """Build context-specific prompt additions"""
        context_parts = []
        
        # Project context
        if context.get('project_info'):
            project_context = self._format_project_context(context['project_info'])
            context_parts.append(project_context)
        
        # Current file context
        if context.get('selected_file'):
            file_context = self._format_file_context(context['selected_file'])
            context_parts.append(file_context)
        
        # Conversation history (optimized for large context window)
        if context.get('conversation_history'):
            conv_context = self._format_conversation_context(
                context['conversation_history'], 
                agent_name
            )
            context_parts.append(conv_context)
        
        # Related files context (leverage large context window)
        if context.get('related_files'):
            related_context = self._format_related_files_context(context['related_files'])
            context_parts.append(related_context)
        
        return "\n\n".join(context_parts)
    
    def _format_project_context(self, project_info: Dict[str, Any]) -> str:
        """Format project context for injection"""
        return self.context_templates['project_context'].format(
            project_type=project_info.get('type', 'Unknown'),
            technologies=', '.join(project_info.get('technologies', [])),
            file_structure=self._summarize_file_structure(project_info.get('structure', {})),
            dependencies=', '.join(project_info.get('dependencies', [])[:10])  # Limit for readability
        )
    
    def _format_file_context(self, file_info: Dict[str, Any]) -> str:
        """Format current file context for injection"""
        return self.context_templates['current_file'].format(
            file_path=file_info.get('path', 'Unknown'),
            language=file_info.get('language', 'Unknown'),
            file_size=len(file_info.get('content', '').split('\n')),
            last_modified=file_info.get('last_modified', 'Unknown'),
            content_summary=self._summarize_file_content(file_info.get('content', ''))
        )
    
    def _format_conversation_context(
        self, 
        conversation: List[Dict[str, Any]], 
        agent_name: str
    ) -> str:
        """Format conversation history with agent-specific focus"""
        if not conversation:
            return ""
        
        # Take more recent messages for large context window
        recent_messages = conversation[-10:] if len(conversation) > 10 else conversation
        
        # Filter messages relevant to current agent
        relevant_messages = self._filter_relevant_messages(recent_messages, agent_name)
        
        conversation_summary = self._summarize_conversation(relevant_messages)
        
        return self.context_templates['conversation_history'].format(
            conversation_summary=conversation_summary
        )
    
    def _format_related_files_context(self, related_files: List[Dict[str, Any]]) -> str:
        """Format related files context (leverage large context window)"""
        if not related_files:
            return ""
        
        context = "## Related Files Context\n\n"
        
        # Include more related files due to large context window
        for file_info in related_files[:20]:  # Up to 20 related files
            context += f"**{file_info.get('path', 'Unknown')}**\n"
            context += f"- Language: {file_info.get('language', 'Unknown')}\n"
            context += f"- Relationship: {file_info.get('relationship', 'Unknown')}\n"
            
            # Include code snippets for critical files
            if file_info.get('is_critical', False) and file_info.get('content'):
                snippet = file_info['content'][:500] + "..." if len(file_info['content']) > 500 else file_info['content']
                context += f"- Key Code:\n```{file_info.get('language', '')}\n{snippet}\n```\n"
            
            context += "\n"
        
        return context
    
    def _add_gemini_optimizations(
        self, 
        prompt: str, 
        context: Dict[str, Any], 
        agent_name: str
    ) -> str:
        """Add Gemini 2.5 Pro specific optimizations"""
        
        # Determine processing mode based on context complexity
        processing_mode = self._determine_processing_mode(context)
        performance_level = self._determine_performance_level(context, agent_name)
        
        gemini_context = self.context_templates['gemini_optimization'].format(
            processing_mode=processing_mode,
            performance_level=performance_level
        )
        
        # Add Gemini-specific instructions
        gemini_instructions = """
## Gemini 2.5 Pro Optimization Instructions

- **Leverage Full Context**: Use the entire 1M token context window for comprehensive analysis
- **Advanced Reasoning**: Apply multi-step reasoning for complex code problems
- **Code Understanding**: Utilize deep semantic understanding of code patterns
- **Multimodal Processing**: Consider code structure, documentation, and relationships
- **Response Quality**: Provide detailed, actionable insights with code examples
"""
        
        return f"{prompt}\n\n{gemini_context}\n\n{gemini_instructions}"
    
    def _determine_processing_mode(self, context: Dict[str, Any]) -> str:
        """Determine optimal processing mode for Gemini"""
        if context.get('related_files') and len(context['related_files']) > 10:
            return "Multi-file Analysis"
        elif context.get('conversation_history') and len(context['conversation_history']) > 5:
            return "Conversational Context"
        elif context.get('selected_file') and len(context.get('selected_file', {}).get('content', '')) > 10000:
            return "Deep Code Analysis"
        else:
            return "Standard Processing"
    
    def _determine_performance_level(self, context: Dict[str, Any], agent_name: str) -> str:
        """Determine performance level based on context complexity"""
        complexity_score = 0
        
        # Factor in various complexity indicators
        if context.get('selected_file'):
            file_size = len(context['selected_file'].get('content', ''))
            complexity_score += min(file_size / 1000, 5)  # Max 5 points for file size
        
        if context.get('related_files'):
            complexity_score += min(len(context['related_files']) / 5, 3)  # Max 3 points for related files
        
        if context.get('conversation_history'):
            complexity_score += min(len(context['conversation_history']) / 3, 2)  # Max 2 points for conversation
        
        if complexity_score > 7:
            return "Maximum Performance"
        elif complexity_score > 4:
            return "High Performance"
        else:
            return "Standard Performance"
    
    def _summarize_file_structure(self, structure: Dict[str, Any]) -> str:
        """Summarize project file structure"""
        if not structure:
            return "Structure not available"
        
        summary_parts = []
        for folder, files in structure.items():
            if isinstance(files, list):
                summary_parts.append(f"{folder}/ ({len(files)} files)")
            elif isinstance(files, dict):
                summary_parts.append(f"{folder}/ (nested)")
        
        return ", ".join(summary_parts[:10])  # Limit for readability
    
    def _summarize_file_content(self, content: str) -> str:
        """Summarize file content for context"""
        if not content:
            return "No content available"
        
        lines = content.split('\n')
        
        # Extract key information
        imports = [line.strip() for line in lines if line.strip().startswith(('import ', 'from ', 'const ', 'function '))][:5]
        classes = [line.strip() for line in lines if 'class ' in line or 'interface ' in line][:3]
        
        summary = f"File contains {len(lines)} lines"
        if imports:
            summary += f", Key imports: {', '.join(imports)}"
        if classes:
            summary += f", Classes/Interfaces: {', '.join(classes)}"
        
        return summary
    
    def _filter_relevant_messages(
        self, 
        messages: List[Dict[str, Any]], 
        agent_name: str
    ) -> List[Dict[str, Any]]:
        """Filter messages relevant to current agent"""
        agent_keywords = {
            'react_code': ['react', 'component', 'jsx', 'tsx', 'frontend', 'ui'],
            'python_code': ['python', 'django', 'flask', 'fastapi', 'backend', 'api'],
            'security_scanner': ['security', 'vulnerability', 'audit', 'secure'],
            'react_test': ['test', 'testing', 'jest', 'react testing library']
        }
        
        keywords = agent_keywords.get(agent_name, [])
        if not keywords:
            return messages  # Return all if no specific keywords
        
        relevant = []
        for message in messages:
            content = message.get('content', '').lower()
            if any(keyword in content for keyword in keywords):
                relevant.append(message)
        
        # If no relevant messages found, return recent ones
        return relevant if relevant else messages[-3:]
    
    def _summarize_conversation(self, messages: List[Dict[str, Any]]) -> str:
        """Summarize conversation for context"""
        if not messages:
            return "No previous conversation"
        
        summary_parts = []
        for msg in messages[-5:]:  # Last 5 messages
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."
            
            summary_parts.append(f"**{role.upper()}**: {content}")
        
        return "\n".join(summary_parts)
    
    def get_available_agents(self) -> List[str]:
        """Get list of available agent prompts"""
        return list(self.prompts.keys())
    
    def validate_prompt(self, agent_name: str) -> Dict[str, Any]:
        """Validate prompt completeness and structure"""
        prompt = self.get_prompt(agent_name)
        if not prompt:
            return {'valid': False, 'error': 'Prompt not found'}
        
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
            'valid': len(missing_sections) == 0,
            'missing_sections': missing_sections,
            'length': len(prompt),
            'estimated_tokens': len(prompt) // 4  # Rough token estimate
        } 