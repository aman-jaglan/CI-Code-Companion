#!/usr/bin/env python3
"""
Sample usage of CI Code Companion

This example demonstrates how to use the CI Code Companion components
in a standalone script or as part of a larger application.
"""

import os
import sys
import logging
from pathlib import Path

# Add the CI Code Companion to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ci_code_companion import VertexAIClient, TestGenerator, CodeReviewer, GitLabIntegration

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_test_generation():
    """Example 1: Basic test generation for a Python function."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Test Generation")
    print("="*60)
    
    # Sample function code
    function_code = '''
def calculate_fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n < 0:
        raise ValueError("n must be non-negative")
    elif n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
'''
    
    try:
        # Initialize AI client (requires GCP_PROJECT_ID environment variable)
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            print("⚠️  Skipping AI example - GCP_PROJECT_ID not set")
            return
        
        ai_client = VertexAIClient(project_id=project_id)
        
        # Generate tests
        print("🤖 Generating tests for Fibonacci function...")
        test_code = ai_client.generate_unit_tests(
            function_code=function_code,
            language="python",
            test_framework="pytest"
        )
        
        print("✅ Generated test code:")
        print("-" * 40)
        print(test_code)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_code_review():
    """Example 2: AI-powered code review."""
    print("\n" + "="*60)
    print("EXAMPLE 2: AI Code Review")
    print("="*60)
    
    # Sample code with potential issues
    problematic_code = '''
def process_user_data(user_input):
    # Potential security issue - using eval
    result = eval(user_input)
    
    # No error handling
    file_content = open("/tmp/data.txt").read()
    
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{result}'"
    
    return query
'''
    
    try:
        # Initialize AI client
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            print("⚠️  Skipping AI example - GCP_PROJECT_ID not set")
            return
        
        ai_client = VertexAIClient(project_id=project_id)
        reviewer = CodeReviewer(ai_client)
        
        # Review the code
        print("🤖 Reviewing code for security issues...")
        review_result = reviewer.review_code_diff(
            diff_content=f"```python\n{problematic_code}\n```",
            review_type="security"
        )
        
        print("✅ Review completed:")
        print(f"Severity: {review_result.get('severity', 'unknown')}")
        print(f"Issues found: {len(review_result.get('issues', []))}")
        
        for i, issue in enumerate(review_result.get('issues', [])[:3], 1):
            print(f"  {i}. {issue}")
        
        print("\nRecommendations:")
        for i, rec in enumerate(review_result.get('recommendations', [])[:3], 1):
            print(f"  {i}. {rec}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_file_analysis():
    """Example 3: Analyze a Python file and generate comprehensive tests."""
    print("\n" + "="*60)
    print("EXAMPLE 3: File Analysis and Test Generation")
    print("="*60)
    
    # Create a sample Python file
    sample_file_content = '''
"""
Sample e-commerce module for demonstration.
"""

class Product:
    def __init__(self, name, price, stock=0):
        self.name = name
        self.price = price
        self.stock = stock
    
    def update_stock(self, quantity):
        if quantity < 0 and abs(quantity) > self.stock:
            raise ValueError("Insufficient stock")
        self.stock += quantity
    
    def calculate_total(self, quantity):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self.stock:
            raise ValueError("Not enough stock available")
        return self.price * quantity

def apply_discount(price, discount_percent):
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)
'''
    
    try:
        # Create temporary file
        temp_file = Path("temp_example.py")
        with open(temp_file, 'w') as f:
            f.write(sample_file_content)
        
        print(f"📁 Created sample file: {temp_file}")
        
        # Initialize components
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            print("⚠️  Skipping AI example - GCP_PROJECT_ID not set")
            return
        
        ai_client = VertexAIClient(project_id=project_id)
        test_gen = TestGenerator(ai_client)
        
        # Analyze file
        print("🔍 Analyzing Python file...")
        functions_and_classes = test_gen.analyze_python_file(str(temp_file))
        
        print(f"Found {len(functions_and_classes)} functions/classes:")
        for item in functions_and_classes:
            if item['type'] == 'class':
                print(f"  📦 Class: {item['name']} ({len(item.get('methods', []))} methods)")
            else:
                print(f"  🔧 Function: {item['name']}")
        
        # Generate tests
        print("\n🤖 Generating comprehensive tests...")
        generated_tests = test_gen.generate_tests_for_file(str(temp_file))
        
        if generated_tests:
            for test_file_name, test_content in generated_tests.items():
                print(f"\n✅ Generated {test_file_name} ({len(test_content)} characters)")
                print("Preview (first 300 characters):")
                print("-" * 40)
                print(test_content[:300] + "..." if len(test_content) > 300 else test_content)
                print("-" * 40)
        
        # Cleanup
        temp_file.unlink()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        # Cleanup on error
        if temp_file.exists():
            temp_file.unlink()


def example_4_gitlab_integration():
    """Example 4: GitLab integration features."""
    print("\n" + "="*60)
    print("EXAMPLE 4: GitLab Integration")
    print("="*60)
    
    try:
        # Initialize GitLab integration
        gitlab_integration = GitLabIntegration()
        
        # Get CI environment info
        print("🔍 CI Environment Information:")
        ci_vars = gitlab_integration.get_ci_variables()
        
        if ci_vars:
            for key, value in ci_vars.items():
                print(f"  {key}: {value}")
        else:
            print("  No CI variables found (not running in GitLab CI)")
        
        # Check if this is a merge request pipeline
        is_mr = gitlab_integration.is_merge_request_pipeline()
        print(f"\n📋 Is Merge Request Pipeline: {is_mr}")
        
        # Demo comment formatting
        print("\n💬 Sample MR Comment Generation:")
        sample_review_results = [
            {
                "file_path": "product.py",
                "severity": "medium",
                "summary": "Code quality is good with minor improvements needed",
                "issues": [
                    "Missing type hints for function parameters",
                    "Exception messages could be more descriptive"
                ],
                "recommendations": [
                    "Add type hints to improve code documentation",
                    "Use f-strings for better string formatting",
                    "Consider adding logging for error conditions"
                ],
                "positive_aspects": [
                    "Good error handling with appropriate exceptions",
                    "Clear function and class names",
                    "Proper validation of input parameters"
                ]
            }
        ]
        
        comment = gitlab_integration.format_mr_comment_for_review(
            sample_review_results, "comprehensive"
        )
        
        print("Generated MR comment:")
        print("-" * 40)
        print(comment[:500] + "..." if len(comment) > 500 else comment)
        print("-" * 40)
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all examples."""
    print("🤖 CI Code Companion - Usage Examples")
    print("=" * 80)
    
    examples = [
        example_1_basic_test_generation,
        example_2_code_review,
        example_3_file_analysis,
        example_4_gitlab_integration
    ]
    
    for example_func in examples:
        try:
            example_func()
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Example failed: {e}")
            continue
    
    print("\n🎉 Examples completed!")
    print("\n📚 Next steps:")
    print("  1. Set up your Google Cloud project and credentials")
    print("  2. Configure GitLab CI/CD variables")
    print("  3. Include the CI components in your .gitlab-ci.yml")
    print("  4. Start generating tests and reviews automatically!")


if __name__ == "__main__":
    main() 