import os
import sys
from pathlib import Path

# Add the project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.ci_code_companion import VertexAIClient

def test_connection():
    """Test the connection to Vertex AI."""
    try:
        # Get project ID from environment
        project_id = os.getenv('GCP_PROJECT_ID')
        if not project_id:
            print("❌ Error: GCP_PROJECT_ID environment variable not set")
            sys.exit(1)
            
        print(f"Testing connection to project: {project_id}")
        
        # Initialize client
        client = VertexAIClient(project_id=project_id)
        
        # Test health check
        health = client.health_check()
        
        if health['status'] == 'healthy':
            print("✅ Successfully connected to Vertex AI!")
            print(f"Models available: {health['models_available']}")
        else:
            print(f"❌ Connection failed: {health.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection() 