"""
Setup configuration for CI Code Companion SDK

This setup file configures the SDK for installation and distribution.
It includes all necessary dependencies, entry points, and metadata for
a production-ready Python package.
"""

from setuptools import setup, find_packages
from pathlib import Path
import re

# Read version from __init__.py
def get_version():
    init_file = Path(__file__).parent / "ci_code_companion_sdk" / "__init__.py"
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
        if version_match:
            return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

# Read README for long description
def get_long_description():
    readme_file = Path(__file__).parent / "README.md"
    if readme_file.exists():
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Define dependencies
REQUIRED_DEPENDENCIES = [
    # Core dependencies
    "asyncio-contextmanager>=1.0.0",
    "dataclasses-json>=0.5.7",
    "typing-extensions>=4.0.0",
    
    # Configuration and serialization
    "pyyaml>=6.0",
    "python-dotenv>=0.19.0",
    
    # HTTP and API clients
    "aiohttp>=3.8.0",
    "requests>=2.28.0",
    
    # Git integration
    "gitpython>=3.1.27",
    
    # File processing
    "chardet>=5.0.0",
    "python-magic>=0.4.27",
    
    # Utilities
    "click>=8.0.0",
    "rich>=12.0.0",
    "tqdm>=4.64.0",
]

# Optional dependencies for enhanced features
OPTIONAL_DEPENDENCIES = {
    "web": [
        "flask>=2.2.0",
        "flask-cors>=3.0.10",
        "gunicorn>=20.1.0",
    ],
    "database": [
        "sqlalchemy>=1.4.0",
        "alembic>=1.8.0",
        "psycopg2-binary>=2.9.0",
    ],
    "monitoring": [
        "prometheus-client>=0.14.0",
        "sentry-sdk>=1.9.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.19.0",
        "pytest-cov>=3.0.0",
        "black>=22.0.0",
        "isort>=5.10.0",
        "flake8>=5.0.0",
        "mypy>=0.971",
        "pre-commit>=2.20.0",
    ],
    "docs": [
        "sphinx>=5.0.0",
        "sphinx-rtd-theme>=1.0.0",
        "myst-parser>=0.18.0",
    ],
    "testing": [
        "factory-boy>=3.2.0",
        "faker>=15.0.0",
        "responses>=0.21.0",
        "pytest-benchmark>=3.4.0",
    ]
}

# Combine all optional dependencies for full installation
OPTIONAL_DEPENDENCIES["full"] = [
    dep for deps in OPTIONAL_DEPENDENCIES.values() for dep in deps
]

# Remove duplicates
OPTIONAL_DEPENDENCIES["full"] = list(set(OPTIONAL_DEPENDENCIES["full"]))

# Entry points for CLI tools
ENTRY_POINTS = {
    "console_scripts": [
        "ci-code-companion=ci_code_companion_sdk.cli.main:main",
        "ccc=ci_code_companion_sdk.cli.main:main",
    ],
    "ci_code_companion_sdk.specialized_agents.code": [
        "react_code=ci_code_companion_sdk.agents.specialized.code.react_code_agent:ReactCodeAgent",
        "python_code=ci_code_companion_sdk.agents.specialized.code.python_code_agent:PythonCodeAgent",
        "node_code=ci_code_companion_sdk.agents.specialized.code.node_code_agent:NodeCodeAgent",
    ],
    "ci_code_companion_sdk.specialized_agents.testing": [
        "react_test=ci_code_companion_sdk.agents.specialized.testing.react_test_agent:ReactTestAgent",
        "python_test=ci_code_companion_sdk.agents.specialized.testing.python_test_agent:PythonTestAgent",
        "api_test=ci_code_companion_sdk.agents.specialized.testing.api_test_agent:ApiTestAgent",
    ],
    "ci_code_companion_sdk.specialized_agents.security": [
        "security_scanner=ci_code_companion_sdk.agents.specialized.security.security_scanner_agent:SecurityScannerAgent",
        "dependency_security=ci_code_companion_sdk.agents.specialized.security.dependency_security_agent:DependencySecurityAgent",
    ]
}

# Classifiers for PyPI
CLASSIFIERS = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Quality Assurance",
    "Topic :: Software Development :: Testing",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
    "Typing :: Typed",
]

# Keywords for PyPI search
KEYWORDS = [
    "code-analysis", "ai", "code-review", "static-analysis",
    "testing", "optimization", "gitlab", "sdk", "agents",
    "multi-technology", "python", "javascript", "react",
    "nodejs", "database", "devops", "mobile"
]

setup(
    # Basic package information
    name="ci-code-companion-sdk",
    version=get_version(),
    author="CI Code Companion Team",
    author_email="support@codecompanion.dev",
    maintainer="CI Code Companion Team",
    maintainer_email="support@codecompanion.dev",
    
    # Package description
    description="A comprehensive SDK for intelligent code analysis, review, and repository management",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    
    # URLs
    url="https://github.com/your-org/ci-code-companion",
    project_urls={
        "Documentation": "https://docs.codecompanion.dev",
        "Source": "https://github.com/your-org/ci-code-companion",
        "Bug Reports": "https://github.com/your-org/ci-code-companion/issues",
        "Funding": "https://github.com/sponsors/ci-code-companion",
        "Say Thanks!": "https://saythanks.io/to/ci-code-companion-team",
    },
    
    # Package discovery
    packages=find_packages(include=["ci_code_companion_sdk", "ci_code_companion_sdk.*"]),
    package_data={
        "ci_code_companion_sdk": [
            "py.typed",
            "config/*.yaml",
            "config/*.json",
            "templates/*.html",
            "templates/*.md",
            "static/**/*",
        ]
    },
    include_package_data=True,
    
    # Dependencies
    python_requires=">=3.8",
    install_requires=REQUIRED_DEPENDENCIES,
    extras_require=OPTIONAL_DEPENDENCIES,
    
    # Entry points
    entry_points=ENTRY_POINTS,
    
    # Metadata
    license="MIT",
    classifiers=CLASSIFIERS,
    keywords=" ".join(KEYWORDS),
    
    # Options
    zip_safe=False,
    platforms=["any"],
    
    # Testing
    test_suite="tests",
    tests_require=OPTIONAL_DEPENDENCIES["testing"],
    
    # Configuration files
    options={
        "bdist_wheel": {
            "universal": False,
        },
        "build": {
            "build_base": "build",
        },
        "egg_info": {
            "tag_build": "",
            "tag_date": False,
        },
    },
) 