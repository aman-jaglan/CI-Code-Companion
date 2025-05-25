import logging
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add web_dashboard to Python path for imports
web_dashboard_path = os.path.join(os.path.dirname(__file__), 'web_dashboard')
sys.path.insert(0, web_dashboard_path)

# Import the app without changing working directory
from app import app

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting Flask server on http://localhost:5001")
    app.run(
        host='0.0.0.0',  # Allow connections from all interfaces
        port=5001,
        debug=True,
        use_reloader=True
    ) 