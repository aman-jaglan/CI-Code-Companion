"""Test script for AI code generation and analysis features."""

import os
from dotenv import load_dotenv
from src.ci_code_companion.vertex_ai_client import VertexAIClient

def main():
    # Load environment variables
    load_dotenv()

    # Explicitly set GOOGLE_APPLICATION_CREDENTIALS if the path is found
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if credentials_path:
        if not os.path.isabs(credentials_path):
            # Attempt to make it absolute if it's relative to the project root
            script_dir = os.path.dirname(os.path.abspath(__file__))
            potential_path = os.path.join(script_dir, credentials_path)
            if os.path.exists(potential_path):
                credentials_path = potential_path
            else: # Or assume it's relative to where the script is run from (project root)
                credentials_path = os.path.abspath(credentials_path)
        
        if os.path.exists(credentials_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
            print(f"Using credentials from: {credentials_path}")
        else:
            print(f"WARNING: GOOGLE_APPLICATION_CREDENTIALS path not found: {credentials_path}")
            print("Proceeding with default credentials if available.")
    else:
        print("GOOGLE_APPLICATION_CREDENTIALS not set in .env. Using default credentials.")

    # Initialize client
    client = VertexAIClient(
        project_id=os.getenv('GOOGLE_CLOUD_PROJECT')
        # credentials_path can be passed here too, but VertexAIClient already handles it
    )
    
    # Test code generation
    print("\n=== Testing Code Generation ===")
    prompt = """Write a Python function that:
    1. Takes a list of numbers as input
    2. Returns the sum of all even numbers in the list
    Include docstring and type hints."""
    
    generated_code = client.generate_code(prompt)
    print("\nGenerated Code:")
    print(generated_code)
    
    # Test code analysis
    print("\n=== Testing Code Analysis ===")
    code_to_analyze = """
def process_data(data):
    result = []
    for i in range(len(data)):
        if data[i] > 0:
            result.append(data[i] * 2)
    return result
    """
    
    analysis = client.analyze_code(code_to_analyze)
    print("\nCode Analysis:")
    print(analysis)

if __name__ == "__main__":
    main() 