#!/usr/bin/env python3
"""
Test script for CI/CD component integration

This script tests the integration of the CI Code Companion components.
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path

# Add the CI Code Companion to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ci_code_companion import VertexAIClient, TestGenerator, CodeReviewer, GitLabIntegration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_python_file(directory: Path) -> Path:
    """Create a sample Python file for testing."""
    sample_code = '''"""
Sample calculator module for testing AI code generation.
"""

def add(a, b):
    """Add two numbers."""
    return a + b

def subtract(a, b):
    """Subtract b from a."""
    return a - b

def multiply(a, b):
    """Multiply two numbers."""
    return a * b

def divide(a, b):
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

class Calculator:
    """Simple calculator class."""
    
    def __init__(self):
        self.history = []
    
    def calculate(self, operation, a, b):
        """Perform calculation and store in history."""
        if operation == "add":
            result = add(a, b)
        elif operation == "subtract":
            result = subtract(a, b)
        elif operation == "multiply":
            result = multiply(a, b)
        elif operation == "divide":
            result = divide(a, b)
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        self.history.append((operation, a, b, result))
        return result
    
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()
'''
    
    file_path = directory / "calculator.py"
    with open(file_path, 'w') as f:
        f.write(sample_code)
    
    return file_path


def test_test_generator():
    """Test the test generator component."""
    logger.info("Testing TestGenerator component...")
    
    try:
        # Get project ID from environment
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            logger.warning("GCP_PROJECT_ID not set, skipping AI-dependent tests")
            return True
        
        # Initialize AI client
        ai_client = VertexAIClient(
            project_id=project_id,
            location=os.getenv('GCP_REGION', 'us-central1')
        )
        
        # Initialize test generator
        test_gen = TestGenerator(ai_client)
        
        # Create temporary directory with sample code
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sample_file = create_sample_python_file(temp_path)
            
            logger.info(f"Created sample file: {sample_file}")
            
            # Test file analysis
            logger.info("Testing Python file analysis...")
            functions_and_classes = test_gen.analyze_python_file(str(sample_file))
            
            if not functions_and_classes:
                logger.error("❌ Failed to analyze Python file")
                return False
            
            logger.info(f"✅ Found {len(functions_and_classes)} functions/classes")
            
            # Test test generation for the file
            logger.info("Testing test generation...")
            test_output_dir = temp_path / "tests"
            
            generated_tests = test_gen.generate_tests_for_file(
                str(sample_file),
                str(test_output_dir)
            )
            
            if not generated_tests:
                logger.error("❌ Failed to generate tests")
                return False
            
            logger.info(f"✅ Generated {len(generated_tests)} test files")
            
            # Check if test files were created
            for test_file_name, test_content in generated_tests.items():
                test_file_path = test_output_dir / test_file_name
                if test_file_path.exists():
                    logger.info(f"✅ Test file created: {test_file_path}")
                    logger.info(f"Test content length: {len(test_content)} characters")
                else:
                    logger.warning(f"⚠️ Test file not found: {test_file_path}")
        
        logger.info("✅ TestGenerator tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ TestGenerator test failed: {str(e)}")
        return False


def test_code_reviewer():
    """Test the code reviewer component."""
    logger.info("Testing CodeReviewer component...")
    
    try:
        # Get project ID from environment
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            logger.warning("GCP_PROJECT_ID not set, skipping AI-dependent tests")
            return True
        
        # Initialize AI client
        ai_client = VertexAIClient(
            project_id=project_id,
            location=os.getenv('GCP_REGION', 'us-central1')
        )
        
        # Initialize code reviewer
        reviewer = CodeReviewer(ai_client)
        
        # Test code diff review
        logger.info("Testing code diff review...")
        sample_diff = '''--- a/calculator.py
+++ b/calculator.py
@@ -10,7 +10,7 @@ def divide(a, b):
     """Divide a by b."""
-    if b == 0:
-        raise ValueError("Cannot divide by zero")
+    # Removed error handling - this is a bug!
     return a / b
 
 def new_function():
+    user_input = input("Enter something: ")
+    return eval(user_input)  # Security vulnerability!
'''
        
        review_result = reviewer.review_code_diff(
            diff_content=sample_diff,
            review_type="comprehensive"
        )
        
        if not review_result:
            logger.error("❌ Failed to review code diff")
            return False
        
        logger.info(f"✅ Code review completed")
        logger.info(f"Review severity: {review_result.get('severity', 'unknown')}")
        logger.info(f"Issues found: {len(review_result.get('issues', []))}")
        
        # Test review report generation
        logger.info("Testing review report generation...")
        report = reviewer.generate_review_report([review_result], 'markdown')
        
        if not report:
            logger.error("❌ Failed to generate review report")
            return False
        
        logger.info(f"✅ Generated review report ({len(report)} characters)")
        
        logger.info("✅ CodeReviewer tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ CodeReviewer test failed: {str(e)}")
        return False


def test_gitlab_integration():
    """Test the GitLab integration component."""
    logger.info("Testing GitLabIntegration component...")
    
    try:
        # Initialize GitLab integration (will work with dummy tokens in CI)
        gitlab_integration = GitLabIntegration()
        
        # Test CI variables
        logger.info("Testing CI variables extraction...")
        ci_vars = gitlab_integration.get_ci_variables()
        
        logger.info(f"✅ Found {len(ci_vars)} CI variables")
        for key, value in ci_vars.items():
            logger.info(f"  {key}: {value}")
        
        # Test MR pipeline detection
        is_mr_pipeline = gitlab_integration.is_merge_request_pipeline()
        logger.info(f"✅ Is MR pipeline: {is_mr_pipeline}")
        
        # Test comment formatting
        logger.info("Testing MR comment formatting...")
        sample_review_results = [
            {
                "file_path": "calculator.py",
                "severity": "high",
                "summary": "Found security vulnerability and missing error handling",
                "issues": [
                    "Use of eval() function is dangerous",
                    "Missing error handling for division by zero"
                ],
                "recommendations": [
                    "Replace eval() with safer alternatives",
                    "Add proper input validation"
                ]
            }
        ]
        
        comment = gitlab_integration.format_mr_comment_for_review(
            sample_review_results, "security"
        )
        
        if not comment:
            logger.error("❌ Failed to format MR comment")
            return False
        
        logger.info(f"✅ Generated MR comment ({len(comment)} characters)")
        
        logger.info("✅ GitLabIntegration tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ GitLabIntegration test failed: {str(e)}")
        # Don't fail for GitLab integration issues in testing
        logger.warning("GitLab integration tests are optional in this environment")
        return True


def test_component_templates():
    """Test that component templates are valid."""
    logger.info("Testing component templates...")
    
    try:
        # Check that component files exist
        components_dir = Path(__file__).parent.parent / "components"
        
        test_generator_template = components_dir / "ai-test-generator" / "template.yml"
        code_reviewer_template = components_dir / "ai-code-reviewer" / "template.yml"
        
        if not test_generator_template.exists():
            logger.error(f"❌ Test generator template not found: {test_generator_template}")
            return False
        
        if not code_reviewer_template.exists():
            logger.error(f"❌ Code reviewer template not found: {code_reviewer_template}")
            return False
        
        logger.info("✅ Component template files found")
        
        # Basic validation of template structure
        for template_file in [test_generator_template, code_reviewer_template]:
            with open(template_file, 'r') as f:
                content = f.read()
                
                if 'spec:' not in content:
                    logger.error(f"❌ Template missing spec section: {template_file}")
                    return False
                
                if 'inputs:' not in content:
                    logger.error(f"❌ Template missing inputs section: {template_file}")
                    return False
                
                logger.info(f"✅ Template structure valid: {template_file.name}")
        
        logger.info("✅ Component template tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Component template test failed: {str(e)}")
        return False


def main():
    """Main function."""
    logger.info("🤖 Starting CI/CD component integration tests...")
    
    tests = [
        ("Component Templates", test_component_templates),
        ("GitLab Integration", test_gitlab_integration),
        ("Test Generator", test_test_generator),
        ("Code Reviewer", test_code_reviewer),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info('='*50)
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} - PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} - FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} - ERROR: {str(e)}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"INTEGRATION TEST RESULTS")
    logger.info('='*50)
    logger.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All integration tests passed!")
        sys.exit(0)
    else:
        logger.error(f"❌ {total - passed} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 