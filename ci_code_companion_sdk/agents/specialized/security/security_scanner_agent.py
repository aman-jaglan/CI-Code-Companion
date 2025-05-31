"""
Security Scanner Agent - Specialized for Security Analysis

This agent focuses exclusively on security vulnerability detection, compliance checking,
and security best practices across different programming languages and frameworks.
It provides comprehensive security analysis and remediation guidance.
"""

import re
import hashlib
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class SecurityScannerAgent(BaseAgent):
    """
    Specialized agent for security analysis and vulnerability detection.
    Focuses on code security, dependency security, and compliance standards.
    """
    
    def _initialize(self):
        """Initialize Security Scanner Agent with specialized configuration"""
        super()._initialize()
        self.name = "security_scanner"
        self.version = "2.0.0"
        
        # Security vulnerability patterns
        self.vulnerability_patterns = {
            'sql_injection': [
                r'(?i)SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\+',
                r'(?i)INSERT\s+INTO\s+.*\s+VALUES\s*\([^)]*\+',
                r'(?i)UPDATE\s+.*\s+SET\s+.*\+',
                r'(?i)DELETE\s+FROM\s+.*\s+WHERE\s+.*\+',
                r'execute\s*\(\s*[\'"].*\+.*[\'"]',
                r'query\s*\(\s*[\'"].*\+.*[\'"]'
            ],
            'xss': [
                r'innerHTML\s*=\s*.*\+',
                r'document\.write\s*\([^)]*\+',
                r'eval\s*\([^)]*\+',
                r'outerHTML\s*=\s*.*\+',
                r'insertAdjacentHTML\s*\([^)]*,\s*[^)]*\+'
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'%2e%2e%2f',
                r'%2e%2e%5c',
                r'file\s*:\s*\/\/',
                r'readFile\s*\([^)]*\+.*[\'"]'
            ],
            'command_injection': [
                r'exec\s*\([^)]*\+',
                r'system\s*\([^)]*\+',
                r'shell_exec\s*\([^)]*\+',
                r'subprocess\.\w+\([^)]*\+',
                r'os\.system\s*\([^)]*\+',
                r'child_process\.\w+\s*\([^)]*\+'
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*[\'"][^\'"]{8,}[\'"]',
                r'api_key\s*=\s*[\'"][^\'"]{20,}[\'"]',
                r'secret\s*=\s*[\'"][^\'"]{16,}[\'"]',
                r'token\s*=\s*[\'"][^\'"]{20,}[\'"]',
                r'private_key\s*=\s*[\'"]-----BEGIN',
                r'BEGIN\s+RSA\s+PRIVATE\s+KEY'
            ],
            'crypto_weaknesses': [
                r'MD5\s*\(',
                r'SHA1\s*\(',
                r'DES\s*\(',
                r'RC4\s*\(',
                r'Math\.random\s*\(\)',
                r'rand\s*\(\)',
                r'srand\s*\('
            ],
            'insecure_random': [
                r'Math\.random\s*\(\)',
                r'Random\s*\(\)',
                r'rand\s*\(\)',
                r'random\.randint\s*\(',
                r'random\.choice\s*\('
            ],
            'file_inclusion': [
                r'include\s*\([^)]*\$',
                r'require\s*\([^)]*\$',
                r'include_once\s*\([^)]*\$',
                r'require_once\s*\([^)]*\$',
                r'file_get_contents\s*\([^)]*\$'
            ]
        }
        
        # Sensitive data patterns
        self.sensitive_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
            'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            'api_key': r'(?i)(?:api_key|apikey|api-key)\s*[:=]\s*[\'"]?[a-zA-Z0-9]{20,}[\'"]?',
            'jwt_token': r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'
        }
        
        # Framework-specific security patterns
        self.framework_security = {
            'react': {
                'dangerous_props': [r'dangerouslySetInnerHTML', r'__html'],
                'unsafe_refs': [r'findDOMNode\s*\(', r'ReactDOM\.findDOMNode'],
                'eval_usage': [r'eval\s*\(', r'Function\s*\(.*\)']
            },
            'express': {
                'csrf_missing': [r'app\.use\s*\(\s*cors\s*\(\s*\)\s*\)'],
                'helmet_missing': [r'app\.use\s*\(\s*helmet\s*\(\s*\)\s*\)'],
                'rate_limiting': [r'express-rate-limit', r'rate-limiter']
            },
            'django': {
                'debug_enabled': [r'DEBUG\s*=\s*True'],
                'secret_key': [r'SECRET_KEY\s*=\s*[\'"][^\'"]*[\'"]'],
                'csrf_disabled': [r'csrf_exempt', r'@csrf_exempt']
            }
        }
        
        # Compliance standards
        self.compliance_standards = {
            'gdpr': ['personal_data', 'consent', 'privacy_policy', 'data_protection'],
            'pci_dss': ['credit_card', 'payment', 'cardholder_data', 'encryption'],
            'hipaa': ['patient_data', 'health_information', 'medical_records', 'phi'],
            'owasp': ['authentication', 'authorization', 'input_validation', 'encryption']
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Security Scanner Agent capabilities"""
        return [
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.DEPENDENCY_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported file types for security analysis"""
        return ['.py', '.js', '.jsx', '.ts', '.tsx', '.php', '.java', '.cs', '.rb', '.go', '.rs', '.sql', '.yaml', '.yml', '.json', '.xml']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported frameworks for security analysis"""
        return ['react', 'express', 'django', 'flask', 'spring', 'asp.net', 'laravel', 'ruby-on-rails']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive security analysis on code files.
        
        Args:
            file_path: Path to file being analyzed
            content: File content to analyze
            context: Analysis context including project info
            
        Returns:
            Dictionary containing security analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract security metadata
        metadata = self.extract_metadata(file_path, content)
        metadata.update(await self._extract_security_metadata(content))
        
        # Perform security analysis
        issues.extend(await self._scan_vulnerabilities(content, file_path))
        issues.extend(await self._scan_sensitive_data(content))
        issues.extend(await self._scan_crypto_usage(content))
        issues.extend(await self._scan_framework_security(content, file_path))
        issues.extend(await self._scan_dependency_security(content))
        
        # Generate security suggestions
        suggestions.extend(await self._suggest_security_improvements(content, file_path))
        suggestions.extend(await self._suggest_compliance_measures(content, context))
        suggestions.extend(await self._suggest_security_tools(content, file_path))
        
        # Calculate security confidence score
        confidence_score = self._calculate_security_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_security_metadata(self, content: str) -> Dict[str, Any]:
        """Extract security-specific metadata"""
        metadata = {
            'vulnerabilities_found': [],
            'sensitive_data_types': [],
            'crypto_algorithms': [],
            'authentication_methods': [],
            'authorization_patterns': [],
            'input_validation': False,
            'output_encoding': False,
            'security_headers': [],
            'compliance_indicators': []
        }
        
        # Detect vulnerabilities
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    metadata['vulnerabilities_found'].append(vuln_type)
                    break
        
        # Detect sensitive data
        for data_type, pattern in self.sensitive_patterns.items():
            if re.search(pattern, content):
                metadata['sensitive_data_types'].append(data_type)
        
        # Detect crypto usage
        crypto_keywords = ['encrypt', 'decrypt', 'hash', 'crypto', 'cipher', 'AES', 'RSA', 'HMAC']
        for keyword in crypto_keywords:
            if keyword.lower() in content.lower():
                metadata['crypto_algorithms'].append(keyword)
        
        # Detect authentication patterns
        auth_patterns = ['login', 'authenticate', 'password', 'token', 'session', 'jwt', 'oauth']
        for pattern in auth_patterns:
            if pattern.lower() in content.lower():
                metadata['authentication_methods'].append(pattern)
        
        # Check for input validation
        validation_patterns = ['validate', 'sanitize', 'escape', 'filter', 'clean']
        metadata['input_validation'] = any(pattern in content.lower() for pattern in validation_patterns)
        
        # Check for output encoding
        encoding_patterns = ['encode', 'escape', 'htmlspecialchars', 'encodeURIComponent']
        metadata['output_encoding'] = any(pattern in content.lower() for pattern in encoding_patterns)
        
        return metadata
    
    async def _scan_vulnerabilities(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Scan for common security vulnerabilities"""
        issues = []
        lines = content.split('\n')
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        severity = self._get_vulnerability_severity(vuln_type)
                        issues.append(self.create_issue(
                            'security_vulnerability',
                            severity,
                            f'{vuln_type.replace("_", " ").title()} vulnerability detected',
                            f'Potential {vuln_type} vulnerability found in line {i}',
                            line_number=i,
                            suggestion=self._get_vulnerability_fix(vuln_type)
                        ))
        
        return issues
    
    async def _scan_sensitive_data(self, content: str) -> List[Dict[str, Any]]:
        """Scan for sensitive data exposure"""
        issues = []
        lines = content.split('\n')
        
        for data_type, pattern in self.sensitive_patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                
                # Skip if it's in a comment or string literal that looks like example data
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                if self._is_likely_example_data(match.group(), line_content):
                    continue
                
                issues.append(self.create_issue(
                    'data_exposure',
                    'high',
                    f'Sensitive {data_type} detected',
                    f'Potential {data_type} found in source code. This should not be hardcoded.',
                    line_number=line_num,
                    suggestion=f'Move {data_type} to environment variables or secure configuration'
                ))
        
        return issues
    
    async def _scan_crypto_usage(self, content: str) -> List[Dict[str, Any]]:
        """Scan for cryptographic weaknesses"""
        issues = []
        lines = content.split('\n')
        
        # Check for weak crypto algorithms
        weak_crypto_patterns = self.vulnerability_patterns['crypto_weaknesses']
        for pattern in weak_crypto_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(self.create_issue(
                        'crypto_weakness',
                        'high',
                        'Weak cryptographic algorithm',
                        'Use of weak or deprecated cryptographic algorithm detected',
                        line_number=i,
                        suggestion='Use strong algorithms like AES-256, SHA-256, or bcrypt'
                    ))
        
        # Check for insecure random number generation
        insecure_random_patterns = self.vulnerability_patterns['insecure_random']
        for pattern in insecure_random_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    issues.append(self.create_issue(
                        'insecure_random',
                        'medium',
                        'Insecure random number generation',
                        'Use of cryptographically insecure random number generator',
                        line_number=i,
                        suggestion='Use cryptographically secure random generators'
                    ))
        
        return issues
    
    async def _scan_framework_security(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Scan for framework-specific security issues"""
        issues = []
        
        # Detect framework
        framework = self._detect_framework(content, file_path)
        if not framework or framework not in self.framework_security:
            return issues
        
        framework_patterns = self.framework_security[framework]
        lines = content.split('\n')
        
        if framework == 'react':
            # Check for dangerouslySetInnerHTML
            for pattern in framework_patterns['dangerous_props']:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        issues.append(self.create_issue(
                            'react_security',
                            'high',
                            'Dangerous HTML injection',
                            'Use of dangerouslySetInnerHTML can lead to XSS attacks',
                            line_number=i,
                            suggestion='Sanitize HTML content or use safe alternatives'
                        ))
        
        elif framework == 'express':
            # Check for missing security middleware
            has_helmet = 'helmet' in content
            has_cors = 'cors' in content
            
            if not has_helmet:
                issues.append(self.create_issue(
                    'express_security',
                    'medium',
                    'Missing security middleware',
                    'Express app should use helmet for security headers',
                    suggestion='Add app.use(helmet()) to set security headers'
                ))
            
            if not has_cors:
                issues.append(self.create_issue(
                    'express_security',
                    'medium',
                    'Missing CORS configuration',
                    'Configure CORS properly to prevent cross-origin attacks',
                    suggestion='Add proper CORS configuration with app.use(cors())'
                ))
        
        elif framework == 'django':
            # Check for debug mode
            if re.search(r'DEBUG\s*=\s*True', content):
                issues.append(self.create_issue(
                    'django_security',
                    'high',
                    'Debug mode enabled',
                    'DEBUG=True should never be used in production',
                    suggestion='Set DEBUG=False in production settings'
                ))
        
        return issues
    
    async def _scan_dependency_security(self, content: str) -> List[Dict[str, Any]]:
        """Scan for dependency-related security issues"""
        issues = []
        
        # Check for known vulnerable packages (simplified)
        vulnerable_packages = {
            'lodash': ['4.17.15', '4.17.19'],  # Example vulnerable versions
            'moment': ['2.18.0', '2.19.3'],
            'axios': ['0.18.0', '0.19.0'],
            'jquery': ['1.12.4', '2.2.4', '3.0.0']
        }
        
        # Scan package.json-like dependencies
        import_patterns = [
            r'import\s+.*\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
        ]
        
        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                package_name = match.group(1)
                if package_name in vulnerable_packages:
                    line_num = content[:match.start()].count('\n') + 1
                    issues.append(self.create_issue(
                        'vulnerable_dependency',
                        'high',
                        f'Vulnerable dependency: {package_name}',
                        f'Package {package_name} has known security vulnerabilities',
                        line_number=line_num,
                        suggestion=f'Update {package_name} to the latest secure version'
                    ))
        
        return issues
    
    async def _suggest_security_improvements(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Suggest security improvements"""
        suggestions = []
        
        # Suggest input validation
        if not self._has_input_validation(content):
            suggestions.append(self.create_suggestion(
                'input_validation',
                'Implement input validation',
                'Add comprehensive input validation to prevent injection attacks',
                impact='high',
                effort='medium'
            ))
        
        # Suggest output encoding
        if not self._has_output_encoding(content):
            suggestions.append(self.create_suggestion(
                'output_encoding',
                'Implement output encoding',
                'Add output encoding to prevent XSS attacks',
                impact='high',
                effort='low'
            ))
        
        # Suggest authentication improvements
        if self._needs_authentication_improvement(content):
            suggestions.append(self.create_suggestion(
                'authentication',
                'Strengthen authentication',
                'Implement stronger authentication mechanisms like 2FA or OAuth',
                impact='high',
                effort='high'
            ))
        
        # Suggest encryption
        if self._should_use_encryption(content):
            suggestions.append(self.create_suggestion(
                'encryption',
                'Add data encryption',
                'Encrypt sensitive data at rest and in transit',
                impact='high',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_compliance_measures(self, content: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest compliance-related security measures"""
        suggestions = []
        
        # Check for GDPR compliance needs
        if self._handles_personal_data(content):
            suggestions.append(self.create_suggestion(
                'gdpr_compliance',
                'Implement GDPR compliance measures',
                'Add consent management, data anonymization, and right to deletion features',
                impact='high',
                effort='high'
            ))
        
        # Check for PCI DSS compliance needs
        if self._handles_payment_data(content):
            suggestions.append(self.create_suggestion(
                'pci_compliance',
                'Implement PCI DSS compliance',
                'Add secure payment processing, tokenization, and audit logging',
                impact='high',
                effort='high'
            ))
        
        # Check for audit logging
        if not self._has_audit_logging(content):
            suggestions.append(self.create_suggestion(
                'audit_logging',
                'Implement audit logging',
                'Add comprehensive logging for security events and user actions',
                impact='medium',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_security_tools(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Suggest security tools and practices"""
        suggestions = []
        
        # Suggest static analysis tools
        suggestions.append(self.create_suggestion(
            'static_analysis',
            'Use static analysis security testing (SAST)',
            'Integrate tools like ESLint security plugins, Bandit, or SonarQube',
            impact='medium',
            effort='low'
        ))
        
        # Suggest dependency scanning
        suggestions.append(self.create_suggestion(
            'dependency_scanning',
            'Implement dependency vulnerability scanning',
            'Use tools like npm audit, Snyk, or OWASP Dependency Check',
            impact='medium',
            effort='low'
        ))
        
        # Suggest security testing
        suggestions.append(self.create_suggestion(
            'security_testing',
            'Add security testing to CI/CD',
            'Include security tests in your automated testing pipeline',
            impact='high',
            effort='medium'
        ))
        
        return suggestions
    
    def _get_vulnerability_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type"""
        high_severity = ['sql_injection', 'command_injection', 'path_traversal', 'hardcoded_secrets']
        medium_severity = ['xss', 'crypto_weaknesses', 'insecure_random']
        
        if vuln_type in high_severity:
            return 'high'
        elif vuln_type in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    def _get_vulnerability_fix(self, vuln_type: str) -> str:
        """Get remediation suggestion for vulnerability type"""
        fixes = {
            'sql_injection': 'Use parameterized queries or prepared statements',
            'xss': 'Sanitize and encode user input before output',
            'path_traversal': 'Validate and sanitize file paths, use allowlists',
            'command_injection': 'Avoid dynamic command execution, use safe alternatives',
            'hardcoded_secrets': 'Move secrets to environment variables or vault',
            'crypto_weaknesses': 'Use strong cryptographic algorithms',
            'insecure_random': 'Use cryptographically secure random generators',
            'file_inclusion': 'Validate file paths and use allowlists'
        }
        return fixes.get(vuln_type, 'Review and fix the security issue')
    
    def _is_likely_example_data(self, data: str, line_content: str) -> bool:
        """Check if detected sensitive data is likely example/test data"""
        example_indicators = [
            'example', 'test', 'dummy', 'fake', 'sample', 'demo',
            'TODO', 'FIXME', 'placeholder', 'your_', 'user@example'
        ]
        
        line_lower = line_content.lower()
        data_lower = data.lower()
        
        return any(indicator in line_lower or indicator in data_lower for indicator in example_indicators)
    
    def _detect_framework(self, content: str, file_path: str) -> Optional[str]:
        """Detect the framework being used"""
        if 'react' in content.lower() or file_path.endswith(('.jsx', '.tsx')):
            return 'react'
        elif 'express' in content.lower() or 'app.use' in content:
            return 'express'
        elif 'django' in content.lower() or 'from django' in content:
            return 'django'
        elif 'flask' in content.lower() or 'from flask' in content:
            return 'flask'
        
        return None
    
    def _has_input_validation(self, content: str) -> bool:
        """Check if code has input validation"""
        validation_patterns = [
            r'validate\s*\(',
            r'sanitize\s*\(',
            r'escape\s*\(',
            r'filter\s*\(',
            r'clean\s*\(',
            r'validator\.',
            r'joi\.',
            r'yup\.'
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in validation_patterns)
    
    def _has_output_encoding(self, content: str) -> bool:
        """Check if code has output encoding"""
        encoding_patterns = [
            r'encode\s*\(',
            r'escape\s*\(',
            r'htmlspecialchars\s*\(',
            r'encodeURIComponent\s*\(',
            r'encodeHTML\s*\(',
            r'sanitize\s*\('
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in encoding_patterns)
    
    def _needs_authentication_improvement(self, content: str) -> bool:
        """Check if authentication needs improvement"""
        weak_auth_indicators = [
            'password' in content.lower() and 'hash' not in content.lower(),
            'login' in content.lower() and ('jwt' not in content.lower() and 'session' not in content.lower()),
            'auth' in content.lower() and '2fa' not in content.lower()
        ]
        return any(weak_auth_indicators)
    
    def _should_use_encryption(self, content: str) -> bool:
        """Check if data should be encrypted"""
        sensitive_data_indicators = [
            'password', 'credit_card', 'ssn', 'personal_data',
            'private_key', 'secret', 'token', 'api_key'
        ]
        
        has_sensitive_data = any(indicator in content.lower() for indicator in sensitive_data_indicators)
        has_encryption = any(crypto in content.lower() for crypto in ['encrypt', 'cipher', 'aes', 'rsa'])
        
        return has_sensitive_data and not has_encryption
    
    def _handles_personal_data(self, content: str) -> bool:
        """Check if code handles personal data"""
        personal_data_indicators = [
            'email', 'name', 'address', 'phone', 'personal_data',
            'user_data', 'profile', 'gdpr', 'consent'
        ]
        return any(indicator in content.lower() for indicator in personal_data_indicators)
    
    def _handles_payment_data(self, content: str) -> bool:
        """Check if code handles payment data"""
        payment_indicators = [
            'credit_card', 'payment', 'billing', 'card_number',
            'cvv', 'expiry', 'stripe', 'paypal', 'transaction'
        ]
        return any(indicator in content.lower() for indicator in payment_indicators)
    
    def _has_audit_logging(self, content: str) -> bool:
        """Check if code has audit logging"""
        logging_patterns = [
            r'log\s*\(',
            r'logger\.',
            r'audit\s*\(',
            r'console\.log\s*\(',
            r'print\s*\(',
            r'winston\.',
            r'bunyan\.'
        ]
        return any(re.search(pattern, content, re.IGNORECASE) for pattern in logging_patterns)
    
    def _calculate_security_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for security analysis"""
        base_confidence = 0.8
        
        # Reduce confidence for high number of issues
        high_severity_issues = [issue for issue in issues if issue.get('severity') == 'high']
        if len(high_severity_issues) > 3:
            base_confidence -= 0.3
        elif len(high_severity_issues) > 1:
            base_confidence -= 0.1
        
        # Adjust based on file size
        lines = len(content.split('\n'))
        if lines < 50:
            base_confidence += 0.1
        elif lines > 500:
            base_confidence -= 0.1
        
        # Boost confidence if security practices are detected
        if self._has_input_validation(content):
            base_confidence += 0.05
        if self._has_output_encoding(content):
            base_confidence += 0.05
        
        return max(0.4, min(1.0, base_confidence))
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle chat interactions for security assistance"""
        message = context.get('message', '').lower()
        
        if 'vulnerability' in message or 'security' in message:
            return "I'm your security specialist! I can help identify vulnerabilities like SQL injection, XSS, CSRF, and more. I also check for hardcoded secrets, weak crypto, and insecure configurations. What security concern do you have?"
        elif 'compliance' in message or 'gdpr' in message or 'pci' in message:
            return "I can help with compliance requirements! I analyze code for GDPR, PCI DSS, HIPAA, and OWASP compliance. I check data handling, consent management, encryption requirements, and audit logging. What compliance standard are you working with?"
        elif 'encrypt' in message or 'crypto' in message:
            return "Cryptography security is crucial! I can identify weak algorithms, insecure random generators, hardcoded keys, and improper key management. I'll suggest strong alternatives like AES-256, SHA-256, and proper key storage. What crypto issue are you facing?"
        elif 'authentication' in message or 'auth' in message:
            return "Authentication security is my expertise! I analyze login systems, password handling, session management, JWT tokens, and 2FA implementation. I can spot weak auth patterns and suggest improvements. What authentication challenge do you have?"
        elif 'dependency' in message or 'package' in message:
            return "Dependency security is important! I scan for vulnerable packages, outdated libraries, and insecure dependencies. I suggest secure alternatives and update strategies. Which dependencies are you concerned about?"
        else:
            return "I'm your comprehensive security analyst! I specialize in vulnerability detection, compliance checking, cryptography analysis, authentication security, and dependency scanning. I cover OWASP Top 10, GDPR, PCI DSS, and more. What security aspect can I help you with?" 