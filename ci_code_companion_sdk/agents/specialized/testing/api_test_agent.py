"""
API Test Agent - Specialized for API Testing

This agent focuses exclusively on API testing, including REST APIs, GraphQL,
authentication, performance testing, contract testing, and API validation.
It provides expert guidance for API test automation and quality assurance.
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class ApiTestAgent(BaseAgent):
    """
    Specialized agent for API testing and validation.
    Focuses on REST APIs, GraphQL, authentication, and performance testing.
    """
    
    def _initialize(self):
        """Initialize API Test Agent with specialized configuration"""
        super()._initialize()
        self.name = "api_test"
        self.version = "2.0.0"
        
        # API testing patterns
        self.api_patterns = {
            'http_methods': r'(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)',
            'rest_endpoint': r'/api/[^\s\'"]+',
            'graphql_query': r'query\s+\w+|mutation\s+\w+',
            'json_schema': r'{\s*["\']?\$schema["\']?:',
            'status_codes': r'(?:200|201|204|400|401|403|404|422|500)\b',
            'auth_header': r'Authorization:\s*(?:Bearer|Basic)',
            'content_type': r'Content-Type:\s*application/json',
            'response_time': r'response.time|response_time',
            'assertion_patterns': r'assert|expect|should',
            'test_data': r'test_data|test_user|fixture'
        }
        
        # Testing framework patterns
        self.test_frameworks = {
            'postman': {
                'collection': r'pm\.test\s*\(',
                'variables': r'pm\.environment\.get|pm\.globals\.get',
                'assertions': r'pm\.expect\s*\(',
                'scripts': r'pm\.request|pm\.response'
            },
            'newman': {
                'command': r'newman\s+run',
                'reporter': r'--reporter\s+\w+',
                'environment': r'--environment',
                'data': r'--iteration-data'
            },
            'rest_assured': {
                'given': r'given\s*\(\s*\)',
                'when': r'\.when\s*\(\s*\)',
                'then': r'\.then\s*\(\s*\)',
                'status_code': r'\.statusCode\s*\(',
                'body': r'\.body\s*\('
            },
            'supertest': {
                'request': r'request\s*\(\s*app\s*\)',
                'expect': r'\.expect\s*\(',
                'end': r'\.end\s*\(',
                'send': r'\.send\s*\('
            },
            'pytest_requests': {
                'requests': r'import\s+requests',
                'response': r'response\s*=\s*requests\.',
                'json': r'response\.json\s*\(\s*\)',
                'status': r'response\.status_code'
            }
        }
        
        # API quality checks
        self.quality_checks = {
            'missing_auth_tests': r'(?:login|auth|token)',
            'missing_error_tests': r'(?:error|fail|invalid)',
            'missing_validation': r'(?:validate|schema|format)',
            'hardcoded_urls': r'https?://[^\s\'"]+',
            'hardcoded_credentials': r'(?:password|secret|key)\s*[:=]\s*["\'][^"\']+["\']',
            'no_cleanup': r'(?:cleanup|teardown|after)',
            'performance_testing': r'(?:load|stress|performance)',
            'contract_testing': r'(?:contract|pact|schema)'
        }
        
        # Security testing patterns
        self.security_patterns = {
            'sql_injection': r'(?:\'|"|\||;|--)',
            'xss_payloads': r'<script|javascript:|onload=',
            'auth_bypass': r'(?:admin|root|system)',
            'rate_limiting': r'rate.?limit|throttle',
            'cors_testing': r'cors|origin|preflight',
            'csrf_testing': r'csrf|xsrf|token'
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get API Test Agent capabilities"""
        return [
            AgentCapability.TEST_GENERATION,
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported API test file types"""
        return ['.js', '.py', '.json', '.yaml', '.postman_collection', '.http']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported API testing frameworks"""
        return ['postman', 'newman', 'rest-assured', 'supertest', 'pytest', 'jest', 'mocha', 'pact']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze API test files for completeness and best practices.
        
        Args:
            file_path: Path to API test file
            content: Test file content
            context: Analysis context
            
        Returns:
            Dictionary containing API test analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract API test metadata
        metadata = self.extract_metadata(file_path, content)
        metadata.update(await self._extract_api_test_metadata(content))
        
        # Analyze API test patterns
        issues.extend(await self._analyze_test_coverage(content))
        issues.extend(await self._analyze_authentication_tests(content))
        issues.extend(await self._analyze_error_handling_tests(content))
        issues.extend(await self._analyze_data_validation(content))
        issues.extend(await self._analyze_security_tests(content))
        issues.extend(await self._analyze_performance_tests(content))
        
        # Generate improvement suggestions
        suggestions.extend(await self._suggest_test_improvements(content))
        suggestions.extend(await self._suggest_security_enhancements(content))
        suggestions.extend(await self._suggest_automation_improvements(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_api_test_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_api_test_metadata(self, content: str) -> Dict[str, Any]:
        """Extract API test-specific metadata"""
        metadata = {
            'framework': 'unknown',
            'api_type': 'rest',
            'endpoints_tested': [],
            'http_methods': [],
            'auth_mechanisms': [],
            'test_types': [],
            'assertions_count': 0,
            'has_performance_tests': False,
            'has_security_tests': False,
            'has_contract_tests': False,
            'response_validation': False,
            'environment_variables': []
        }
        
        # Detect testing framework
        metadata['framework'] = self._detect_api_framework(content)
        
        # Detect API type
        if 'graphql' in content.lower() or 'query' in content or 'mutation' in content:
            metadata['api_type'] = 'graphql'
        elif 'grpc' in content.lower():
            metadata['api_type'] = 'grpc'
        elif 'soap' in content.lower():
            metadata['api_type'] = 'soap'
        
        # Extract endpoints
        endpoints = re.findall(self.api_patterns['rest_endpoint'], content)
        metadata['endpoints_tested'] = list(set(endpoints))
        
        # Extract HTTP methods
        methods = re.findall(self.api_patterns['http_methods'], content)
        metadata['http_methods'] = list(set(methods))
        
        # Extract auth mechanisms
        if re.search(r'bearer|jwt|token', content.lower()):
            metadata['auth_mechanisms'].append('bearer_token')
        if re.search(r'basic.?auth|username.*password', content.lower()):
            metadata['auth_mechanisms'].append('basic_auth')
        if re.search(r'oauth|client_id|client_secret', content.lower()):
            metadata['auth_mechanisms'].append('oauth')
        if re.search(r'api.?key|x-api-key', content.lower()):
            metadata['auth_mechanisms'].append('api_key')
        
        # Categorize test types
        metadata['test_types'] = self._categorize_api_tests(content)
        
        # Count assertions
        assertions = re.findall(self.api_patterns['assertion_patterns'], content)
        metadata['assertions_count'] = len(assertions)
        
        # Check for specialized testing
        metadata['has_performance_tests'] = bool(re.search(r'performance|load|stress|benchmark', content.lower()))
        metadata['has_security_tests'] = bool(re.search(r'security|injection|xss|auth.?bypass', content.lower()))
        metadata['has_contract_tests'] = bool(re.search(r'contract|pact|schema', content.lower()))
        metadata['response_validation'] = bool(re.search(r'schema|validate|json.?schema', content.lower()))
        
        # Extract environment variables
        env_vars = re.findall(r'(?:env\.|ENV\.|process\.env\.)(\w+)', content)
        metadata['environment_variables'] = list(set(env_vars))
        
        return metadata
    
    async def _analyze_test_coverage(self, content: str) -> List[Dict[str, Any]]:
        """Analyze API test coverage"""
        issues = []
        
        # Check for CRUD operations coverage
        http_methods = re.findall(self.api_patterns['http_methods'], content)
        crud_methods = {'GET', 'POST', 'PUT', 'DELETE'}
        missing_methods = crud_methods - set(http_methods)
        
        if missing_methods:
            issues.append(self.create_issue(
                'test_coverage',
                'medium',
                f'Missing HTTP method tests: {", ".join(missing_methods)}',
                'API tests should cover all CRUD operations',
                suggestion=f'Add tests for {", ".join(missing_methods)} operations'
            ))
        
        # Check for status code coverage
        status_codes = re.findall(self.api_patterns['status_codes'], content)
        important_codes = {'200', '201', '400', '401', '404', '500'}
        missing_codes = important_codes - set(status_codes)
        
        if missing_codes:
            issues.append(self.create_issue(
                'status_coverage',
                'medium',
                f'Missing status code tests: {", ".join(missing_codes)}',
                'Tests should verify both success and error status codes',
                suggestion=f'Add tests for HTTP status codes: {", ".join(missing_codes)}'
            ))
        
        # Check for edge case testing
        if not re.search(r'edge|boundary|limit|empty|null', content.lower()):
            issues.append(self.create_issue(
                'edge_cases',
                'high',
                'Missing edge case testing',
                'API tests should include edge cases and boundary conditions',
                suggestion='Add tests for empty payloads, null values, and boundary conditions'
            ))
        
        return issues
    
    async def _analyze_authentication_tests(self, content: str) -> List[Dict[str, Any]]:
        """Analyze authentication and authorization testing"""
        issues = []
        
        # Check if auth header is used but not tested
        has_auth_header = bool(re.search(self.api_patterns['auth_header'], content))
        has_auth_tests = bool(re.search(r'auth|login|unauthorized|401|403', content.lower()))
        
        if has_auth_header and not has_auth_tests:
            issues.append(self.create_issue(
                'missing_auth_tests',
                'high',
                'Authentication used but not tested',
                'Authentication mechanisms should be thoroughly tested',
                suggestion='Add tests for valid/invalid tokens, expired tokens, and unauthorized access'
            ))
        
        # Check for unauthorized access tests
        if not re.search(r'401|unauthorized|invalid.?token', content.lower()):
            issues.append(self.create_issue(
                'auth_negative_testing',
                'medium',
                'Missing unauthorized access tests',
                'Should test unauthorized access scenarios',
                suggestion='Add tests for 401 Unauthorized responses'
            ))
        
        # Check for role-based access tests
        if re.search(r'role|permission|admin|user', content.lower()) and not re.search(r'403|forbidden', content.lower()):
            issues.append(self.create_issue(
                'rbac_testing',
                'medium',
                'Missing role-based access control tests',
                'Role-based permissions should be tested',
                suggestion='Add tests for 403 Forbidden responses for insufficient permissions'
            ))
        
        return issues
    
    async def _analyze_error_handling_tests(self, content: str) -> List[Dict[str, Any]]:
        """Analyze error handling in API tests"""
        issues = []
        
        # Check for error response testing
        error_codes = ['400', '422', '500']
        tested_errors = [code for code in error_codes if code in content]
        
        if len(tested_errors) < 2:
            issues.append(self.create_issue(
                'error_testing',
                'medium',
                'Insufficient error response testing',
                'Should test various error scenarios and status codes',
                suggestion='Add tests for 400 Bad Request, 422 Validation Error, and 500 Server Error'
            ))
        
        # Check for validation error testing
        if not re.search(r'validation|invalid|malformed|bad.?request', content.lower()):
            issues.append(self.create_issue(
                'validation_testing',
                'medium',
                'Missing input validation tests',
                'Should test API input validation and error responses',
                suggestion='Add tests for invalid input data and validation errors'
            ))
        
        # Check for timeout testing
        if not re.search(r'timeout|slow|delay', content.lower()):
            issues.append(self.create_issue(
                'timeout_testing',
                'low',
                'Missing timeout tests',
                'Should test API timeout scenarios',
                suggestion='Add tests for request timeouts and slow responses'
            ))
        
        return issues
    
    async def _analyze_data_validation(self, content: str) -> List[Dict[str, Any]]:
        """Analyze data validation in API tests"""
        issues = []
        
        # Check for response schema validation
        if not re.search(r'schema|validate|json.?schema', content.lower()):
            issues.append(self.create_issue(
                'schema_validation',
                'high',
                'Missing response schema validation',
                'API responses should be validated against schemas',
                suggestion='Add JSON schema validation for API responses'
            ))
        
        # Check for data type validation
        if not re.search(r'type|instanceof|typeof', content.lower()):
            issues.append(self.create_issue(
                'data_type_validation',
                'medium',
                'Missing data type validation',
                'Should validate response data types',
                suggestion='Add assertions to verify data types in responses'
            ))
        
        # Check for required field validation
        if not re.search(r'required|mandatory|must.?have', content.lower()):
            issues.append(self.create_issue(
                'required_fields',
                'medium',
                'Missing required field validation',
                'Should validate presence of required fields',
                suggestion='Add tests to verify required fields are present in responses'
            ))
        
        return issues
    
    async def _analyze_security_tests(self, content: str) -> List[Dict[str, Any]]:
        """Analyze security testing patterns"""
        issues = []
        
        # Check for injection testing
        has_injection_tests = any(
            re.search(pattern, content.lower()) 
            for pattern in self.security_patterns.values()
        )
        
        if not has_injection_tests:
            issues.append(self.create_issue(
                'security_testing',
                'high',
                'Missing security injection tests',
                'Should test for SQL injection, XSS, and other injection attacks',
                suggestion='Add tests for SQL injection, XSS, and command injection vulnerabilities'
            ))
        
        # Check for rate limiting tests
        if not re.search(r'rate.?limit|throttle|429', content.lower()):
            issues.append(self.create_issue(
                'rate_limiting',
                'medium',
                'Missing rate limiting tests',
                'Should test API rate limiting and throttling',
                suggestion='Add tests for rate limiting (429 Too Many Requests)'
            ))
        
        # Check for CORS testing
        if not re.search(r'cors|origin|preflight|options', content.lower()):
            issues.append(self.create_issue(
                'cors_testing',
                'low',
                'Missing CORS tests',
                'Should test Cross-Origin Resource Sharing policies',
                suggestion='Add tests for CORS headers and preflight requests'
            ))
        
        return issues
    
    async def _analyze_performance_tests(self, content: str) -> List[Dict[str, Any]]:
        """Analyze performance testing coverage"""
        issues = []
        
        # Check for response time testing
        if not re.search(r'response.?time|duration|latency|performance', content.lower()):
            issues.append(self.create_issue(
                'performance_testing',
                'medium',
                'Missing response time validation',
                'Should validate API response times',
                suggestion='Add assertions for response time thresholds'
            ))
        
        # Check for load testing
        if not re.search(r'load|concurrent|stress|volume', content.lower()):
            issues.append(self.create_issue(
                'load_testing',
                'low',
                'Missing load testing',
                'Should include load and stress testing for critical APIs',
                suggestion='Add load tests to verify API performance under load'
            ))
        
        return issues
    
    async def _suggest_test_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest improvements for API testing"""
        suggestions = []
        
        # Suggest contract testing
        if not re.search(r'contract|pact|schema', content.lower()):
            suggestions.append(self.create_suggestion(
                'contract_testing',
                'Implement contract testing',
                'Use tools like Pact for consumer-driven contract testing',
                impact='high',
                effort='medium'
            ))
        
        # Suggest test data management
        if re.search(r'test.?data|fixture', content.lower()) and not re.search(r'factory|builder', content.lower()):
            suggestions.append(self.create_suggestion(
                'test_data',
                'Improve test data management',
                'Use test data factories or builders for consistent test data',
                impact='medium',
                effort='low'
            ))
        
        # Suggest environment management
        if re.search(r'localhost|127\.0\.0\.1|hardcoded.?url', content):
            suggestions.append(self.create_suggestion(
                'environment_config',
                'Use environment configuration',
                'Externalize API URLs and credentials to environment variables',
                impact='high',
                effort='low'
            ))
        
        return suggestions
    
    async def _suggest_security_enhancements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest security testing enhancements"""
        suggestions = []
        
        # Suggest security scanning integration
        suggestions.append(self.create_suggestion(
            'security_scanning',
            'Integrate security scanning',
            'Add OWASP ZAP or similar security scanning to test pipeline',
            impact='high',
            effort='medium'
        ))
        
        # Suggest input fuzzing
        if not re.search(r'fuzz|random|invalid', content.lower()):
            suggestions.append(self.create_suggestion(
                'input_fuzzing',
                'Add input fuzzing tests',
                'Use fuzzing techniques to test API robustness with invalid inputs',
                impact='medium',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_automation_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest test automation improvements"""
        suggestions = []
        
        # Suggest CI/CD integration
        if not re.search(r'ci|cd|pipeline|jenkins|github.?actions', content.lower()):
            suggestions.append(self.create_suggestion(
                'cicd_integration',
                'Integrate with CI/CD pipeline',
                'Run API tests automatically in CI/CD pipeline',
                impact='high',
                effort='medium'
            ))
        
        # Suggest parallel execution
        if not re.search(r'parallel|concurrent', content.lower()):
            suggestions.append(self.create_suggestion(
                'parallel_execution',
                'Enable parallel test execution',
                'Run API tests in parallel to reduce execution time',
                impact='medium',
                effort='low'
            ))
        
        # Suggest reporting improvements
        suggestions.append(self.create_suggestion(
            'test_reporting',
            'Enhance test reporting',
            'Add detailed test reports with response times and success rates',
            impact='medium',
            effort='low'
        ))
        
        return suggestions
    
    async def generate_tests(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive API test cases.
        
        Args:
            context: Context containing API specification or existing tests
            
        Returns:
            Dictionary containing generated API test code and metadata
        """
        api_spec = context.get('api_spec', {})
        file_path = context.get('file_path', '')
        content = context.get('content', '')
        
        if not api_spec and not content:
            return {
                'test_code': '# No API specification or existing tests provided',
                'test_file_path': 'api_tests.py',
                'coverage_areas': [],
                'explanation': 'Cannot generate tests without API specification',
                'confidence_score': 0.0
            }
        
        # Generate test code based on framework
        framework = self._detect_api_framework(content) if content else 'pytest'
        test_code = self._generate_api_test_code(api_spec, framework, file_path)
        
        # Define coverage areas
        coverage_areas = [
            'crud_operations', 'authentication', 'authorization', 'error_handling',
            'data_validation', 'performance', 'security', 'edge_cases'
        ]
        
        return {
            'test_code': test_code,
            'test_file_path': f'test_api_{framework}.py',
            'coverage_areas': coverage_areas,
            'explanation': f'Generated comprehensive API test suite using {framework}',
            'confidence_score': 0.8,
            'metadata': {
                'framework': framework,
                'test_types': ['functional', 'security', 'performance'],
                'endpoints_covered': len(api_spec.get('endpoints', [])) if api_spec else 0
            }
        }
    
    def _detect_api_framework(self, content: str) -> str:
        """Detect API testing framework"""
        for framework, patterns in self.test_frameworks.items():
            if any(re.search(pattern, content) for pattern in patterns.values()):
                return framework
        return 'pytest'  # Default framework
    
    def _categorize_api_tests(self, content: str) -> List[str]:
        """Categorize API tests by type"""
        test_types = []
        
        if re.search(r'functional|crud|endpoint', content.lower()):
            test_types.append('functional')
        
        if re.search(r'auth|login|token|permission', content.lower()):
            test_types.append('authentication')
        
        if re.search(r'performance|load|stress|benchmark', content.lower()):
            test_types.append('performance')
        
        if re.search(r'security|injection|xss|csrf', content.lower()):
            test_types.append('security')
        
        if re.search(r'contract|pact|schema', content.lower()):
            test_types.append('contract')
        
        if re.search(r'integration|e2e|end.?to.?end', content.lower()):
            test_types.append('integration')
        
        return test_types or ['functional']
    
    def _generate_api_test_code(self, api_spec: Dict, framework: str, file_path: str) -> str:
        """Generate API test code based on framework"""
        if framework == 'pytest':
            return self._generate_pytest_api_tests(api_spec, file_path)
        elif framework == 'postman':
            return self._generate_postman_tests(api_spec)
        elif framework == 'rest_assured':
            return self._generate_rest_assured_tests(api_spec)
        else:
            return self._generate_pytest_api_tests(api_spec, file_path)
    
    def _generate_pytest_api_tests(self, api_spec: Dict, file_path: str) -> str:
        """Generate pytest-based API tests"""
        return '''"""
Comprehensive API Test Suite

Generated test suite covering:
- CRUD operations for all endpoints
- Authentication and authorization
- Error handling and validation
- Performance and security testing
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "https://api.example.com"
API_KEY = "your-api-key"

@pytest.fixture
def api_client():
    """API client fixture with authentication"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    })
    return session

@pytest.fixture
def test_data():
    """Test data fixture"""
    return {
        "user": {
            "name": "Test User",
            "email": "test@example.com"
        },
        "invalid_data": {
            "name": "",
            "email": "invalid-email"
        }
    }

class TestUserAPI:
    """Tests for User API endpoints"""
    
    def test_create_user_success(self, api_client, test_data):
        """Test successful user creation"""
        response = api_client.post(f"{BASE_URL}/users", json=test_data["user"])
        
        assert response.status_code == 201
        assert response.json()["name"] == test_data["user"]["name"]
        assert "id" in response.json()
    
    def test_create_user_validation_error(self, api_client, test_data):
        """Test user creation with invalid data"""
        response = api_client.post(f"{BASE_URL}/users", json=test_data["invalid_data"])
        
        assert response.status_code == 400
        assert "errors" in response.json()
    
    def test_get_user_success(self, api_client):
        """Test successful user retrieval"""
        # Create user first
        create_response = api_client.post(f"{BASE_URL}/users", json={"name": "Test", "email": "test@example.com"})
        user_id = create_response.json()["id"]
        
        # Get user
        response = api_client.get(f"{BASE_URL}/users/{user_id}")
        
        assert response.status_code == 200
        assert response.json()["id"] == user_id
    
    def test_get_user_not_found(self, api_client):
        """Test user retrieval with invalid ID"""
        response = api_client.get(f"{BASE_URL}/users/999999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()
    
    def test_update_user_success(self, api_client):
        """Test successful user update"""
        # Create user first
        create_response = api_client.post(f"{BASE_URL}/users", json={"name": "Test", "email": "test@example.com"})
        user_id = create_response.json()["id"]
        
        # Update user
        update_data = {"name": "Updated Name"}
        response = api_client.put(f"{BASE_URL}/users/{user_id}", json=update_data)
        
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"
    
    def test_delete_user_success(self, api_client):
        """Test successful user deletion"""
        # Create user first
        create_response = api_client.post(f"{BASE_URL}/users", json={"name": "Test", "email": "test@example.com"})
        user_id = create_response.json()["id"]
        
        # Delete user
        response = api_client.delete(f"{BASE_URL}/users/{user_id}")
        
        assert response.status_code == 204

class TestAuthentication:
    """Tests for authentication and authorization"""
    
    def test_unauthorized_access(self):
        """Test access without authentication"""
        response = requests.get(f"{BASE_URL}/users")
        
        assert response.status_code == 401
        assert "unauthorized" in response.json()["message"].lower()
    
    def test_invalid_token(self):
        """Test access with invalid token"""
        headers = {"Authorization": "Bearer invalid-token"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        
        assert response.status_code == 401
    
    def test_expired_token(self):
        """Test access with expired token"""
        expired_token = "expired-jwt-token"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        
        assert response.status_code == 401

class TestPerformance:
    """Performance tests for API endpoints"""
    
    def test_response_time_within_limits(self, api_client):
        """Test API response time is within acceptable limits"""
        start_time = time.time()
        response = api_client.get(f"{BASE_URL}/users")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0  # Should respond within 2 seconds
        assert response.status_code == 200
    
    @pytest.mark.load_test
    def test_concurrent_requests(self, api_client):
        """Test API under concurrent load"""
        import concurrent.futures
        
        def make_request():
            return api_client.get(f"{BASE_URL}/users")
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200

class TestSecurity:
    """Security tests for API endpoints"""
    
    def test_sql_injection_protection(self, api_client):
        """Test SQL injection protection"""
        malicious_payload = {"name": "'; DROP TABLE users; --"}
        response = api_client.post(f"{BASE_URL}/users", json=malicious_payload)
        
        # Should either reject the payload or sanitize it
        assert response.status_code in [400, 422]
    
    def test_xss_protection(self, api_client):
        """Test XSS protection"""
        xss_payload = {"name": "<script>alert('xss')</script>"}
        response = api_client.post(f"{BASE_URL}/users", json=xss_payload)
        
        if response.status_code == 201:
            # If created, response should escape the script tag
            assert "<script>" not in response.json()["name"]
    
    def test_rate_limiting(self, api_client):
        """Test rate limiting protection"""
        # Make rapid requests to trigger rate limiting
        responses = []
        for _ in range(100):
            response = api_client.get(f"{BASE_URL}/users")
            responses.append(response)
            if response.status_code == 429:
                break
        
        # Should eventually get rate limited
        assert any(r.status_code == 429 for r in responses)

class TestDataValidation:
    """Tests for data validation and schema compliance"""
    
    def test_response_schema_validation(self, api_client):
        """Test response matches expected schema"""
        response = api_client.get(f"{BASE_URL}/users")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert isinstance(data, list)
        if data:
            user = data[0]
            assert "id" in user
            assert "name" in user
            assert "email" in user
            assert isinstance(user["id"], int)
            assert isinstance(user["name"], str)
    
    def test_input_validation(self, api_client):
        """Test input validation for various data types"""
        test_cases = [
            {"name": None, "email": "test@example.com"},  # Null name
            {"name": "Test", "email": None},  # Null email
            {"name": "", "email": "test@example.com"},  # Empty name
            {"name": "Test", "email": "invalid-email"},  # Invalid email
            {"name": "A" * 1000, "email": "test@example.com"},  # Too long name
        ]
        
        for invalid_data in test_cases:
            response = api_client.post(f"{BASE_URL}/users", json=invalid_data)
            assert response.status_code in [400, 422], f"Failed for: {invalid_data}"
'''
    
    def _generate_postman_tests(self, api_spec: Dict) -> str:
        """Generate Postman collection tests"""
        return '''
{
  "info": {
    "name": "API Test Collection",
    "description": "Comprehensive API test collection"
  },
  "item": [
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/users",
        "header": [
          {"key": "Content-Type", "value": "application/json"},
          {"key": "Authorization", "value": "Bearer {{auth_token}}"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\\"name\\": \\"Test User\\", \\"email\\": \\"test@example.com\\"}"
        }
      },
      "test": "pm.test('Create user success', function () { pm.response.to.have.status(201); pm.expect(pm.response.json()).to.have.property('id'); });"
    }
  ]
}
'''
    
    def _generate_rest_assured_tests(self, api_spec: Dict) -> str:
        """Generate REST Assured tests"""
        return '''
import io.restassured.RestAssured;
import org.junit.jupiter.api.Test;
import static io.restassured.RestAssured.*;
import static org.hamcrest.Matchers.*;

public class ApiTest {
    
    @Test
    public void testCreateUser() {
        given()
            .contentType("application/json")
            .header("Authorization", "Bearer " + API_TOKEN)
            .body("{\\"name\\": \\"Test User\\", \\"email\\": \\"test@example.com\\"}")
        .when()
            .post("/users")
        .then()
            .statusCode(201)
            .body("name", equalTo("Test User"))
            .body("id", notNullValue());
    }
}
'''
    
    def _calculate_api_test_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for API test analysis"""
        base_confidence = 0.7
        
        # Boost confidence for good API test practices
        if re.search(r'assert|expect|should', content.lower()):
            base_confidence += 0.1
        if re.search(r'auth|token|unauthorized', content.lower()):
            base_confidence += 0.1
        if re.search(r'400|401|404|500', content):
            base_confidence += 0.1
        
        # Reduce confidence for issues
        if len(issues) > 3:
            base_confidence -= 0.2
        
        return max(0.3, min(1.0, base_confidence))
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle chat interactions for API testing assistance"""
        message = context.get('message', '').lower()
        
        if 'rest' in message or 'api' in message:
            return "I'm your REST API testing expert! I can help with endpoint testing, authentication, status codes, response validation, error handling, and API test automation. What API testing challenge are you facing?"
        elif 'graphql' in message:
            return "GraphQL testing requires special approaches! I can help with query testing, mutation validation, schema verification, and GraphQL-specific test patterns. What GraphQL testing question do you have?"
        elif 'postman' in message:
            return "Postman is a powerful API testing tool! I can help with collection creation, environment management, test scripts, automation with Newman, and Postman best practices. What Postman feature do you need help with?"
        elif 'auth' in message or 'token' in message:
            return "API authentication testing is crucial! I can help with JWT tokens, OAuth flows, API keys, basic auth, session management, and security testing. What authentication scenario are you testing?"
        elif 'performance' in message or 'load' in message:
            return "API performance testing is essential! I can help with response time validation, load testing, stress testing, concurrent requests, and performance benchmarking. What performance aspect are you testing?"
        elif 'security' in message:
            return "API security testing is critical! I can help with injection testing, authentication bypass, rate limiting, CORS, input validation, and security scanning integration. What security vulnerability are you testing for?"
        else:
            return "I'm your API testing specialist! I can help with REST/GraphQL APIs, authentication testing, performance validation, security testing, test automation, and API quality assurance across multiple frameworks like Postman, pytest, REST Assured, and more. What API testing challenge can I solve for you?" 