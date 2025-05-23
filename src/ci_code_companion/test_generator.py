"""
Test Generator for CI Code Companion

This module handles automated generation of unit tests for code files.
"""

import os
import logging
import ast
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from .vertex_ai_client import VertexAIClient

logger = logging.getLogger(__name__)


class TestGenerator:
    """Generates unit tests for source code using AI."""
    
    def __init__(self, vertex_ai_client: VertexAIClient):
        """
        Initialize the test generator.
        
        Args:
            vertex_ai_client: Initialized Vertex AI client
        """
        self.ai_client = vertex_ai_client
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        
    def analyze_python_file(self, file_path: str) -> List[Dict]:
        """
        Analyze a Python file to extract functions and classes.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of dictionaries containing function/class information
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            functions_and_classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function information
                    func_info = {
                        'type': 'function',
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', node.lineno),
                        'code': ast.get_source_segment(content, node),
                        'args': [arg.arg for arg in node.args.args],
                        'is_method': False
                    }
                    functions_and_classes.append(func_info)
                    
                elif isinstance(node, ast.ClassDef):
                    # Extract class methods
                    class_info = {
                        'type': 'class',
                        'name': node.name,
                        'line_start': node.lineno,
                        'line_end': getattr(node, 'end_lineno', node.lineno),
                        'code': ast.get_source_segment(content, node),
                        'methods': []
                    }
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                'type': 'method',
                                'name': item.name,
                                'line_start': item.lineno,
                                'line_end': getattr(item, 'end_lineno', item.lineno),
                                'code': ast.get_source_segment(content, item),
                                'args': [arg.arg for arg in item.args.args],
                                'is_method': True,
                                'class_name': node.name
                            }
                            class_info['methods'].append(method_info)
                    
                    functions_and_classes.append(class_info)
            
            return functions_and_classes
            
        except Exception as e:
            logger.error(f"Error analyzing Python file {file_path}: {str(e)}")
            return []
    
    def extract_imports(self, file_path: str) -> List[str]:
        """
        Extract import statements from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of import statements
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"from {module} import {alias.name}")
            
            return imports
            
        except Exception as e:
            logger.error(f"Error extracting imports from {file_path}: {str(e)}")
            return []
    
    def generate_test_for_function(
        self,
        function_info: Dict,
        original_file_imports: List[str],
        language: str = "python",
        test_framework: str = "pytest"
    ) -> str:
        """
        Generate tests for a specific function.
        
        Args:
            function_info: Dictionary containing function information
            original_file_imports: Import statements from the original file
            language: Programming language
            test_framework: Testing framework to use
            
        Returns:
            Generated test code
        """
        # Prepare context for the AI
        imports_context = "\n".join(original_file_imports) if original_file_imports else ""
        
        # Create enhanced prompt with context
        context_prompt = f"""
Generate comprehensive unit tests for the following {language} function using {test_framework}.

Original file imports:
{imports_context}

Function to test:
```{language}
{function_info['code']}
```

Function details:
- Name: {function_info['name']}
- Parameters: {function_info.get('args', [])}
- Type: {function_info['type']}

Requirements:
1. Import the function being tested (adjust import path as needed)
2. Test normal/typical use cases with various input combinations
3. Test edge cases (empty inputs, None values, boundary conditions)
4. Test error handling and invalid inputs (if applicable)
5. Use proper {test_framework} assertions and fixtures
6. Include descriptive docstrings for each test method
7. Follow {test_framework} naming conventions (test_*)
8. Mock external dependencies if needed

Generate complete, runnable test code with proper imports:
"""

        try:
            return self.ai_client.generate_unit_tests(
                function_code=context_prompt,
                language=language,
                test_framework=test_framework,
                include_edge_cases=True
            )
        except Exception as e:
            logger.error(f"Error generating tests for function {function_info['name']}: {str(e)}")
            return f"# Error generating tests for {function_info['name']}: {str(e)}"
    
    def generate_tests_for_file(
        self,
        file_path: str,
        output_dir: Optional[str] = None,
        test_framework: str = "pytest"
    ) -> Dict[str, str]:
        """
        Generate tests for an entire file.
        
        Args:
            file_path: Path to the source file
            output_dir: Directory to save test files (optional)
            test_framework: Testing framework to use
            
        Returns:
            Dictionary mapping test file names to test content
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension not in self.supported_languages:
            logger.warning(f"Unsupported file type: {extension}")
            return {}
        
        language = self.supported_languages[extension]
        
        # Currently only supports Python analysis
        if language != 'python':
            logger.warning(f"Language {language} analysis not yet implemented")
            return {}
        
        # Analyze the file
        functions_and_classes = self.analyze_python_file(str(file_path))
        imports = self.extract_imports(str(file_path))
        
        if not functions_and_classes:
            logger.info(f"No functions or classes found in {file_path}")
            return {}
        
        generated_tests = {}
        
        # Generate test file name
        test_file_name = f"test_{file_path.stem}.py"
        
        # Collect all tests for the file
        all_tests = []
        
        # Add common test file header
        test_header = f'''"""
Generated unit tests for {file_path.name}

Auto-generated by CI Code Companion
"""

import pytest
{chr(10).join(imports)}
from {file_path.stem} import *

'''
        
        all_tests.append(test_header)
        
        for item in functions_and_classes:
            if item['type'] == 'function':
                # Generate tests for standalone functions
                test_code = self.generate_test_for_function(
                    item, imports, language, test_framework
                )
                all_tests.append(f"\n\n# Tests for {item['name']}\n{test_code}")
                
            elif item['type'] == 'class':
                # Generate tests for class methods
                for method in item.get('methods', []):
                    if not method['name'].startswith('_'):  # Skip private methods
                        test_code = self.generate_test_for_function(
                            method, imports, language, test_framework
                        )
                        all_tests.append(f"\n\n# Tests for {item['name']}.{method['name']}\n{test_code}")
        
        # Combine all tests
        full_test_content = "".join(all_tests)
        generated_tests[test_file_name] = full_test_content
        
        # Save to output directory if specified
        if output_dir:
            output_path = Path(output_dir) / test_file_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_test_content)
            
            logger.info(f"Generated test file: {output_path}")
        
        return generated_tests
    
    def batch_generate_tests(
        self,
        source_dir: str,
        output_dir: str,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate tests for multiple files in a directory.
        
        Args:
            source_dir: Directory containing source files
            output_dir: Directory to save test files
            file_patterns: Patterns to match files (e.g., ['*.py'])
            exclude_patterns: Patterns to exclude (e.g., ['*test*'])
            
        Returns:
            Dictionary mapping source files to their generated tests
        """
        source_path = Path(source_dir)
        file_patterns = file_patterns or ['*.py']
        exclude_patterns = exclude_patterns or ['*test*', '*__pycache__*']
        
        all_results = {}
        
        for pattern in file_patterns:
            for file_path in source_path.rglob(pattern):
                # Check exclusions
                should_exclude = any(
                    file_path.match(exclude_pattern) 
                    for exclude_pattern in exclude_patterns
                )
                
                if should_exclude:
                    continue
                
                logger.info(f"Generating tests for {file_path}")
                
                try:
                    results = self.generate_tests_for_file(
                        str(file_path),
                        output_dir
                    )
                    
                    if results:
                        all_results[str(file_path)] = results
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    continue
        
        logger.info(f"Generated tests for {len(all_results)} files")
        return all_results 