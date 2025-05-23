#!/usr/bin/env python3
"""
Test script for Vertex AI connection

This script tests the basic connectivity and functionality of the Vertex AI client.
"""

import os
import sys
import logging
from pathlib import Path

# Add the CI Code Companion to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ci_code_companion import VertexAIClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_vertex_ai_connection():
    """Test Vertex AI connection and basic functionality."""
    
    try:
        # Get project ID from environment
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            logger.error("GCP_PROJECT_ID environment variable is required")
            return False
        
        region = os.getenv('GCP_REGION', 'us-central1')
        
        logger.info(f"Testing Vertex AI connection to project: {project_id}")
        logger.info(f"Region: {region}")
        
        # Initialize client
        client = VertexAIClient(
            project_id=project_id,
            location=region
        )
        
        logger.info("✅ Vertex AI client initialized successfully")
        
        # Perform health check
        logger.info("Performing health check...")
        health_result = client.health_check()
        
        if health_result['status'] == 'healthy':
            logger.info("✅ Health check passed")
            logger.info(f"Test response length: {health_result['test_response_length']}")
            logger.info(f"Models available: {health_result['models_available']}")
        else:
            logger.error(f"❌ Health check failed: {health_result.get('error', 'Unknown error')}")
            return False
        
        # Test code generation
        logger.info("Testing code generation...")
        test_prompt = """
Generate a simple Python function that calculates the factorial of a number.
The function should handle edge cases and include proper error handling.
"""
        
        generated_code = client.generate_code(test_prompt, max_output_tokens=512)
        
        if generated_code:
            logger.info("✅ Code generation test passed")
            logger.info(f"Generated code (first 200 chars): {generated_code[:200]}...")
        else:
            logger.error("❌ Code generation test failed")
            return False
        
        # Test code analysis
        logger.info("Testing code analysis...")
        sample_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)
print(result)
"""
        
        analysis_result = client.analyze_code(sample_code, "review")
        
        if analysis_result:
            logger.info("✅ Code analysis test passed")
            logger.info(f"Analysis result (first 200 chars): {analysis_result[:200]}...")
        else:
            logger.error("❌ Code analysis test failed")
            return False
        
        # Test unit test generation
        logger.info("Testing unit test generation...")
        function_code = """
def calculate_area(length, width):
    if length <= 0 or width <= 0:
        raise ValueError("Length and width must be positive")
    return length * width
"""
        
        test_code = client.generate_unit_tests(function_code)
        
        if test_code:
            logger.info("✅ Unit test generation test passed")
            logger.info(f"Generated tests (first 200 chars): {test_code[:200]}...")
        else:
            logger.error("❌ Unit test generation test failed")
            return False
        
        logger.info("🎉 All Vertex AI tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        return False


def main():
    """Main function."""
    logger.info("🤖 Starting Vertex AI connection test...")
    
    success = test_vertex_ai_connection()
    
    if success:
        logger.info("✅ All tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 