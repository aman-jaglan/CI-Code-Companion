from typing import Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "model": {
        "name": "gemini-pro",
        "temperature": 0.2,
        "top_p": 0.8,
        "top_k": 40,
        "max_tokens": 1024
    },
    "review": {
        "max_lines_per_review": 500,
        "min_confidence_score": 0.7,
        "severity_thresholds": {
            "critical": 0.9,
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        },
        "review_aspects": [
            "security",
            "performance",
            "reliability",
            "maintainability",
            "best_practices"
        ]
    },
    "prompts": {
        "code_review": """You are an expert Python code reviewer. Review the following code and provide detailed, actionable feedback.
Focus on identifying actual issues that affect code execution, security, and reliability.

For each issue found, provide a response in the following JSON format:
{
    "issue_description": "Brief description of the issue",
    "line_number": "Line number where the issue occurs",
    "old_content": "The problematic code",
    "new_content": "The suggested fix",
    "explanation": "Detailed explanation of why this is an issue",
    "impact": ["List", "of", "specific", "impacts"],
    "severity": "critical|high|medium|low",
    "category": "security|performance|reliability|maintainability|best_practice|bug"
}

Code to review:
```{file_type}
{code}
```
""",
        "security_review": """Analyze the following Python code for security vulnerabilities.
Focus on:
- Input validation
- Authentication/authorization
- Data exposure
- Injection vulnerabilities
- Secure coding practices

Provide findings in the standard JSON format.

Code to analyze:
```python
{code}
```
""",
        "performance_review": """Analyze the following Python code for performance issues.
Focus on:
- Algorithmic complexity
- Memory usage
- Resource management
- Optimization opportunities
- Performance best practices

Provide findings in the standard JSON format.

Code to analyze:
```python
{code}
```
"""
    },
    "ui": {
        "diff_colors": {
            "inserted": {
                "background": "#51cf6633",
                "line_background": "#51cf6619",
                "gutter": "#51cf66"
            },
            "deleted": {
                "background": "#ff6b6b33",
                "line_background": "#ff6b6b19",
                "gutter": "#ff6b6b"
            }
        },
        "editor": {
            "theme": "vs-dark",
            "font_size": 14,
            "line_height": 21,
            "word_wrap": True,
            "show_whitespace": "boundary",
            "minimap_enabled": False
        }
    }
}

class ReviewConfig:
    """Manages configuration for the code review system."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize review configuration.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or str(Path.home() / ".ci_code_companion" / "config.json")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file) as f:
                    user_config = json.load(f)
                    # Deep merge with defaults
                    return self._deep_merge(DEFAULT_CONFIG, user_config)
            else:
                # Create default config
                config_file.parent.mkdir(parents=True, exist_ok=True)
                with open(config_file, 'w') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4)
                return DEFAULT_CONFIG
                
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return DEFAULT_CONFIG
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        merged = base.copy()
        
        for key, value in update.items():
            if (
                key in merged and
                isinstance(merged[key], dict) and
                isinstance(value, dict)
            ):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
                
        return merged
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model-specific configuration."""
        return self.config["model"]
    
    def get_review_config(self) -> Dict[str, Any]:
        """Get review-specific configuration."""
        return self.config["review"]
    
    def get_prompt(self, prompt_type: str) -> str:
        """Get prompt template by type."""
        return self.config["prompts"].get(prompt_type, "")
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI-specific configuration."""
        return self.config["ui"]
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self.config = self._deep_merge(self.config, updates)
        self.save() 