# CI Code Companion

An AI-powered code review system that helps improve code quality by providing intelligent suggestions and automated fixes.

## Features

- Intelligent code review using Vertex AI (Gemini Pro)
- Python-specific code analysis and suggestions
- Beautiful diff viewer with syntax highlighting
- Configurable review settings and prompts
- Support for security and performance reviews
- Easy-to-use web interface

## Requirements

- Python 3.8+
- Node.js 16+
- Google Cloud Platform account with Vertex AI API enabled
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CI-Code-Companion.git
cd CI-Code-Companion
```

2. Set up a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install frontend dependencies:
```bash
cd frontend
npm install
```

5. Set up environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your Google Cloud credentials and other configuration.

## Configuration

The system can be configured through:

1. Environment variables in `.env`
2. Configuration file at `~/.ci_code_companion/config.json`
3. Command line arguments

See `config/review_config.py` for available configuration options.

## Usage

1. Start the backend server:
```bash
python -m ci_code_companion.app
```

2. Start the frontend development server:
```bash
cd frontend
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

## Code Review Process

1. Select a file or paste code for review
2. Choose review type (general, security, performance)
3. View and apply suggestions
4. Export review report (optional)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
black .
flake8 .
mypy .
```

### Building for Production
```bash
cd frontend
npm run build
python setup.py build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Cloud Vertex AI team for the powerful AI models
- Monaco Editor team for the excellent code editor
- All contributors and users of the project
