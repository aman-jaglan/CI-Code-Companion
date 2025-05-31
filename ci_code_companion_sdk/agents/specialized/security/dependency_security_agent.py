"""
Dependency Security Agent - Specialized for Dependency Security

This agent focuses exclusively on analyzing dependencies for security vulnerabilities,
license compliance, outdated packages, and supply chain security risks.
It provides expert guidance for dependency management and security assessment.
"""

import re
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class DependencySecurityAgent(BaseAgent):
    """
    Specialized agent for dependency security analysis.
    Focuses on vulnerability scanning, license compliance, and supply chain security.
    """
    
    def _initialize(self):
        """Initialize Dependency Security Agent with specialized configuration"""
        super()._initialize()
        self.name = "dependency_security"
        self.version = "2.0.0"
        
        # Dependency file patterns
        self.dependency_files = {
            'package.json': r'package\.json$',
            'package-lock.json': r'package-lock\.json$',
            'yarn.lock': r'yarn\.lock$',
            'requirements.txt': r'requirements\.txt$',
            'Pipfile': r'Pipfile$',
            'Pipfile.lock': r'Pipfile\.lock$',
            'pyproject.toml': r'pyproject\.toml$',
            'poetry.lock': r'poetry\.lock$',
            'Gemfile': r'Gemfile$',
            'Gemfile.lock': r'Gemfile\.lock$',
            'pom.xml': r'pom\.xml$',
            'build.gradle': r'build\.gradle$',
            'composer.json': r'composer\.json$',
            'composer.lock': r'composer\.lock$',
            'go.mod': r'go\.mod$',
            'go.sum': r'go\.sum$',
            'Cargo.toml': r'Cargo\.toml$',
            'Cargo.lock': r'Cargo\.lock$'
        }
        
        # Security vulnerability patterns
        self.vulnerability_patterns = {
            'known_vulnerable_packages': {
                'node': [
                    r'lodash@[0-3]\.',
                    r'axios@0\.[0-9]\.',
                    r'express@[0-3]\.',
                    r'moment@.*',  # Deprecated
                    r'request@.*'  # Deprecated
                ],
                'python': [
                    r'django@[12]\.',
                    r'flask@0\.',
                    r'pillow@[0-6]\.',
                    r'pyyaml@[0-4]\.'
                ],
                'java': [
                    r'log4j@[01]\.',
                    r'spring-core@[0-4]\.',
                    r'jackson-databind@2\.[0-9]\.'
                ]
            },
            'security_tools': {
                'npm_audit': r'npm\s+audit',
                'snyk': r'snyk\s+test',
                'safety': r'safety\s+check',
                'bandit': r'bandit',
                'semgrep': r'semgrep',
                'dependabot': r'dependabot',
                'renovate': r'renovate'
            }
        }
        
        # License compliance patterns
        self.license_patterns = {
            'restrictive': [
                r'GPL-[23]\.0',
                r'AGPL-3\.0',
                r'SSPL-1\.0',
                r'BUSL-1\.1'
            ],
            'permissive': [
                r'MIT',
                r'Apache-2\.0',
                r'BSD-[23]-Clause',
                r'ISC'
            ],
            'copyleft': [
                r'GPL-.*',
                r'LGPL-.*',
                r'MPL-2\.0'
            ]
        }
        
        # Supply chain security indicators
        self.supply_chain_risks = {
            'suspicious_patterns': [
                r'eval\s*\(',
                r'Function\s*\(',
                r'crypto\.randomBytes\(\d+\)\.toString\([\'"]hex[\'"]\)',
                r'process\.env\..*PASSWORD',
                r'fs\.unlinkSync',
                r'child_process\.exec'
            ],
            'typosquatting': [
                r'reqests',  # requests
                r'beautifulsup',  # beautifulsoup
                r'piloww',  # pillow
                r'numpyy',  # numpy
                r'pandass'  # pandas
            ],
            'malicious_indicators': [
                r'bitcoin',
                r'cryptocurrency',
                r'mining',
                r'wallet',
                r'keylogger',
                r'backdoor'
            ]
        }
        
        # Dependency management best practices
        self.best_practices = {
            'version_pinning': r'[~^]?\d+\.\d+\.\d+',
            'lock_files': ['package-lock.json', 'yarn.lock', 'Pipfile.lock', 'poetry.lock'],
            'dev_dependencies': r'"devDependencies"|dev-dependencies',
            'peer_dependencies': r'"peerDependencies"',
            'private_registry': r'registry\.npmjs\.org|pypi\.org'
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Dependency Security Agent capabilities"""
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.SECURITY_ANALYSIS,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported dependency file types"""
        return ['.json', '.txt', '.toml', '.lock', '.xml', '.gradle', '.mod']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported dependency management systems"""
        return ['npm', 'yarn', 'pip', 'pipenv', 'poetry', 'maven', 'gradle', 'composer', 'go-modules', 'cargo']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze dependency files for security vulnerabilities and compliance.
        
        Args:
            file_path: Path to dependency file
            content: File content to analyze
            context: Analysis context
            
        Returns:
            Dictionary containing dependency security analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract dependency metadata
        metadata = self.extract_metadata(file_path, content)
        metadata.update(await self._extract_dependency_metadata(file_path, content))
        
        # Perform security analysis
        issues.extend(await self._analyze_vulnerability_risks(content, file_path))
        issues.extend(await self._analyze_license_compliance(content, file_path))
        issues.extend(await self._analyze_dependency_management(content, file_path))
        issues.extend(await self._analyze_supply_chain_risks(content))
        issues.extend(await self._analyze_outdated_dependencies(content, file_path))
        
        # Generate security improvement suggestions
        suggestions.extend(await self._suggest_security_tools(content, file_path))
        suggestions.extend(await self._suggest_dependency_policies(content))
        suggestions.extend(await self._suggest_automation_improvements(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_dependency_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_dependency_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extract dependency-specific metadata"""
        metadata = {
            'dependency_manager': 'unknown',
            'total_dependencies': 0,
            'dev_dependencies': 0,
            'production_dependencies': 0,
            'direct_dependencies': [],
            'transitive_dependencies': [],
            'licenses': [],
            'security_tools_configured': [],
            'has_lock_file': False,
            'version_constraints': {},
            'private_registries': [],
            'deprecated_packages': []
        }
        
        # Detect dependency manager
        metadata['dependency_manager'] = self._detect_dependency_manager(file_path)
        
        # Parse dependencies based on file type
        if 'package.json' in file_path:
            metadata.update(self._parse_npm_dependencies(content))
        elif 'requirements.txt' in file_path:
            metadata.update(self._parse_pip_dependencies(content))
        elif 'Pipfile' in file_path:
            metadata.update(self._parse_pipfile_dependencies(content))
        elif 'pyproject.toml' in file_path:
            metadata.update(self._parse_poetry_dependencies(content))
        elif 'pom.xml' in file_path:
            metadata.update(self._parse_maven_dependencies(content))
        elif 'build.gradle' in file_path:
            metadata.update(self._parse_gradle_dependencies(content))
        elif 'composer.json' in file_path:
            metadata.update(self._parse_composer_dependencies(content))
        elif 'go.mod' in file_path:
            metadata.update(self._parse_go_dependencies(content))
        elif 'Cargo.toml' in file_path:
            metadata.update(self._parse_cargo_dependencies(content))
        
        # Check for security tools
        metadata['security_tools_configured'] = self._detect_security_tools(content)
        
        return metadata
    
    async def _analyze_vulnerability_risks(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze for known vulnerable dependencies"""
        issues = []
        
        # Get language-specific vulnerable packages
        lang = self._get_language_from_file(file_path)
        vulnerable_patterns = self.vulnerability_patterns['known_vulnerable_packages'].get(lang, [])
        
        for pattern in vulnerable_patterns:
            if re.search(pattern, content):
                package_name = pattern.split('@')[0].split(r'\b')[-1]
                issues.append(self.create_issue(
                    'vulnerable_dependency',
                    'high',
                    f'Known vulnerable package: {package_name}',
                    'This package has known security vulnerabilities',
                    suggestion=f'Update {package_name} to latest secure version or find alternative'
                ))
        
        # Check for lack of security scanning
        has_security_tools = any(
            re.search(pattern, content) 
            for pattern in self.vulnerability_patterns['security_tools'].values()
        )
        
        if not has_security_tools:
            issues.append(self.create_issue(
                'missing_security_scanning',
                'high',
                'No security scanning tools configured',
                'Dependencies should be regularly scanned for vulnerabilities',
                suggestion='Add npm audit, Snyk, Safety, or similar security scanning tools'
            ))
        
        return issues
    
    async def _analyze_license_compliance(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze license compliance issues"""
        issues = []
        
        # Check for restrictive licenses
        for license_pattern in self.license_patterns['restrictive']:
            if re.search(license_pattern, content):
                issues.append(self.create_issue(
                    'restrictive_license',
                    'medium',
                    f'Restrictive license detected: {license_pattern}',
                    'Package uses a restrictive license that may impact commercial use',
                    suggestion='Review license compatibility with your project requirements'
                ))
        
        # Check for license scanning
        if not re.search(r'license|licens', content.lower()):
            issues.append(self.create_issue(
                'missing_license_info',
                'low',
                'Missing license information',
                'Dependencies should have clear license information',
                suggestion='Add license scanning and tracking to your dependency management'
            ))
        
        return issues
    
    async def _analyze_dependency_management(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze dependency management practices"""
        issues = []
        
        # Check for unpinned versions
        if re.search(r'[~^]\d+\.\d+\.\d+|latest|\*', content):
            issues.append(self.create_issue(
                'unpinned_versions',
                'medium',
                'Dependencies with unpinned versions detected',
                'Unpinned versions can lead to unexpected behavior and security issues',
                suggestion='Pin dependency versions to specific versions or use lock files'
            ))
        
        # Check for missing lock file (for package.json)
        if 'package.json' in file_path and 'lock' not in content:
            issues.append(self.create_issue(
                'missing_lock_file',
                'medium',
                'Missing lock file',
                'Lock files ensure consistent dependency versions across environments',
                suggestion='Commit package-lock.json or yarn.lock to version control'
            ))
        
        # Check for excessive dependencies
        dep_count = self._count_dependencies(content, file_path)
        if dep_count > 100:
            issues.append(self.create_issue(
                'excessive_dependencies',
                'low',
                f'Large number of dependencies ({dep_count})',
                'Too many dependencies increase attack surface and maintenance burden',
                suggestion='Review and remove unnecessary dependencies'
            ))
        
        return issues
    
    async def _analyze_supply_chain_risks(self, content: str) -> List[Dict[str, Any]]:
        """Analyze supply chain security risks"""
        issues = []
        
        # Check for typosquatting
        for typo_pattern in self.supply_chain_risks['typosquatting']:
            if re.search(typo_pattern, content):
                issues.append(self.create_issue(
                    'typosquatting_risk',
                    'high',
                    f'Potential typosquatting package: {typo_pattern}',
                    'Package name resembles a popular package and may be malicious',
                    suggestion='Verify package name and use official packages only'
                ))
        
        # Check for suspicious patterns
        for suspicious_pattern in self.supply_chain_risks['suspicious_patterns']:
            if re.search(suspicious_pattern, content):
                issues.append(self.create_issue(
                    'suspicious_dependency',
                    'high',
                    'Dependency contains suspicious code patterns',
                    'Package may contain malicious code or security risks',
                    suggestion='Review package source code and consider alternatives'
                ))
        
        # Check for malicious indicators
        for malicious_pattern in self.supply_chain_risks['malicious_indicators']:
            if re.search(malicious_pattern, content.lower()):
                issues.append(self.create_issue(
                    'malicious_indicator',
                    'high',
                    f'Potential malicious package indicator: {malicious_pattern}',
                    'Package contains keywords associated with malicious software',
                    suggestion='Investigate package thoroughly before use'
                ))
        
        return issues
    
    async def _analyze_outdated_dependencies(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Analyze for outdated dependencies"""
        issues = []
        
        # Check for deprecated packages (example patterns)
        deprecated_patterns = {
            'node': ['moment', 'request', 'babel-preset-es2015'],
            'python': ['imp', 'optparse', 'distutils'],
            'java': ['commons-logging']
        }
        
        lang = self._get_language_from_file(file_path)
        deprecated_packages = deprecated_patterns.get(lang, [])
        
        for package in deprecated_packages:
            if re.search(rf'\b{package}\b', content):
                issues.append(self.create_issue(
                    'deprecated_dependency',
                    'medium',
                    f'Deprecated package: {package}',
                    'Package is deprecated and may have security or maintenance issues',
                    suggestion=f'Replace {package} with modern alternative'
                ))
        
        return issues
    
    async def _suggest_security_tools(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Suggest security tools and practices"""
        suggestions = []
        
        lang = self._get_language_from_file(file_path)
        
        # Suggest language-specific security tools
        if lang == 'node':
            suggestions.append(self.create_suggestion(
                'npm_audit',
                'Enable npm audit',
                'Use npm audit to automatically check for vulnerabilities',
                impact='high',
                effort='low'
            ))
            suggestions.append(self.create_suggestion(
                'snyk_integration',
                'Integrate Snyk security scanning',
                'Use Snyk for continuous vulnerability monitoring',
                impact='high',
                effort='medium'
            ))
        elif lang == 'python':
            suggestions.append(self.create_suggestion(
                'safety_check',
                'Use Safety for vulnerability scanning',
                'Add Safety to check Python dependencies for vulnerabilities',
                impact='high',
                effort='low'
            ))
            suggestions.append(self.create_suggestion(
                'bandit_analysis',
                'Add Bandit for security analysis',
                'Use Bandit to identify security issues in Python code',
                impact='medium',
                effort='low'
            ))
        
        # General suggestions
        suggestions.append(self.create_suggestion(
            'dependabot',
            'Enable Dependabot alerts',
            'Use GitHub Dependabot for automated vulnerability alerts',
            impact='high',
            effort='low'
        ))
        
        return suggestions
    
    async def _suggest_dependency_policies(self, content: str) -> List[Dict[str, Any]]:
        """Suggest dependency management policies"""
        suggestions = []
        
        suggestions.append(self.create_suggestion(
            'dependency_policy',
            'Establish dependency security policy',
            'Create guidelines for dependency selection and security requirements',
            impact='high',
            effort='medium'
        ))
        
        suggestions.append(self.create_suggestion(
            'license_compliance',
            'Implement license compliance checking',
            'Use tools to automatically check license compatibility',
            impact='medium',
            effort='medium'
        ))
        
        suggestions.append(self.create_suggestion(
            'supply_chain_verification',
            'Implement supply chain verification',
            'Verify package integrity and provenance before use',
            impact='high',
            effort='high'
        ))
        
        return suggestions
    
    async def _suggest_automation_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest automation improvements"""
        suggestions = []
        
        suggestions.append(self.create_suggestion(
            'automated_updates',
            'Automate dependency updates',
            'Use automated tools to keep dependencies updated with security patches',
            impact='high',
            effort='medium'
        ))
        
        suggestions.append(self.create_suggestion(
            'ci_cd_scanning',
            'Integrate security scanning in CI/CD',
            'Add dependency scanning to your CI/CD pipeline',
            impact='high',
            effort='medium'
        ))
        
        suggestions.append(self.create_suggestion(
            'sbom_generation',
            'Generate Software Bill of Materials (SBOM)',
            'Create SBOM for better dependency visibility and compliance',
            impact='medium',
            effort='medium'
        ))
        
        return suggestions
    
    def _detect_dependency_manager(self, file_path: str) -> str:
        """Detect dependency manager from file path"""
        if 'package.json' in file_path:
            return 'npm'
        elif 'yarn.lock' in file_path:
            return 'yarn'
        elif 'requirements.txt' in file_path:
            return 'pip'
        elif 'Pipfile' in file_path:
            return 'pipenv'
        elif 'pyproject.toml' in file_path:
            return 'poetry'
        elif 'pom.xml' in file_path:
            return 'maven'
        elif 'build.gradle' in file_path:
            return 'gradle'
        elif 'composer.json' in file_path:
            return 'composer'
        elif 'go.mod' in file_path:
            return 'go-modules'
        elif 'Cargo.toml' in file_path:
            return 'cargo'
        else:
            return 'unknown'
    
    def _get_language_from_file(self, file_path: str) -> str:
        """Get programming language from dependency file"""
        if any(pattern in file_path for pattern in ['package.json', 'yarn.lock']):
            return 'node'
        elif any(pattern in file_path for pattern in ['requirements.txt', 'Pipfile', 'pyproject.toml']):
            return 'python'
        elif any(pattern in file_path for pattern in ['pom.xml', 'build.gradle']):
            return 'java'
        elif 'composer.json' in file_path:
            return 'php'
        elif 'go.mod' in file_path:
            return 'go'
        elif 'Cargo.toml' in file_path:
            return 'rust'
        else:
            return 'unknown'
    
    def _parse_npm_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse npm package.json dependencies"""
        try:
            data = json.loads(content)
            dependencies = data.get('dependencies', {})
            dev_dependencies = data.get('devDependencies', {})
            
            return {
                'total_dependencies': len(dependencies) + len(dev_dependencies),
                'production_dependencies': len(dependencies),
                'dev_dependencies': len(dev_dependencies),
                'direct_dependencies': list(dependencies.keys()) + list(dev_dependencies.keys())
            }
        except json.JSONDecodeError:
            return {'total_dependencies': 0}
    
    def _parse_pip_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse pip requirements.txt dependencies"""
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        dependencies = [line.split('==')[0].split('>=')[0].split('~=')[0] for line in lines]
        
        return {
            'total_dependencies': len(dependencies),
            'direct_dependencies': dependencies
        }
    
    def _parse_pipfile_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse Pipfile dependencies"""
        # Basic parsing - would need proper TOML parser for production
        lines = content.split('\n')
        in_packages = False
        in_dev_packages = False
        dependencies = []
        dev_dependencies = []
        
        for line in lines:
            if '[packages]' in line:
                in_packages = True
                in_dev_packages = False
            elif '[dev-packages]' in line:
                in_packages = False
                in_dev_packages = True
            elif line.startswith('['):
                in_packages = False
                in_dev_packages = False
            elif '=' in line and (in_packages or in_dev_packages):
                dep_name = line.split('=')[0].strip().strip('"')
                if in_packages:
                    dependencies.append(dep_name)
                else:
                    dev_dependencies.append(dep_name)
        
        return {
            'total_dependencies': len(dependencies) + len(dev_dependencies),
            'production_dependencies': len(dependencies),
            'dev_dependencies': len(dev_dependencies),
            'direct_dependencies': dependencies + dev_dependencies
        }
    
    def _parse_poetry_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse pyproject.toml poetry dependencies"""
        # Basic parsing - would need proper TOML parser for production
        lines = content.split('\n')
        in_dependencies = False
        in_dev_dependencies = False
        dependencies = []
        dev_dependencies = []
        
        for line in lines:
            if '[tool.poetry.dependencies]' in line:
                in_dependencies = True
                in_dev_dependencies = False
            elif '[tool.poetry.dev-dependencies]' in line or '[tool.poetry.group.dev.dependencies]' in line:
                in_dependencies = False
                in_dev_dependencies = True
            elif line.startswith('['):
                in_dependencies = False
                in_dev_dependencies = False
            elif '=' in line and (in_dependencies or in_dev_dependencies):
                dep_name = line.split('=')[0].strip()
                if dep_name != 'python':  # Skip python version
                    if in_dependencies:
                        dependencies.append(dep_name)
                    else:
                        dev_dependencies.append(dep_name)
        
        return {
            'total_dependencies': len(dependencies) + len(dev_dependencies),
            'production_dependencies': len(dependencies),
            'dev_dependencies': len(dev_dependencies),
            'direct_dependencies': dependencies + dev_dependencies
        }
    
    def _parse_maven_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse Maven pom.xml dependencies"""
        dependencies = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
        return {
            'total_dependencies': len(dependencies),
            'direct_dependencies': dependencies
        }
    
    def _parse_gradle_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse Gradle build.gradle dependencies"""
        # Extract dependencies from implementation, api, testImplementation, etc.
        dependency_patterns = [
            r'implementation\s+[\'"]([^:\'"]+):([^:\'"]+)',
            r'api\s+[\'"]([^:\'"]+):([^:\'"]+)',
            r'testImplementation\s+[\'"]([^:\'"]+):([^:\'"]+)'
        ]
        
        dependencies = []
        for pattern in dependency_patterns:
            matches = re.findall(pattern, content)
            dependencies.extend([f"{group}:{artifact}" for group, artifact in matches])
        
        return {
            'total_dependencies': len(dependencies),
            'direct_dependencies': dependencies
        }
    
    def _parse_composer_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse PHP composer.json dependencies"""
        try:
            data = json.loads(content)
            dependencies = data.get('require', {})
            dev_dependencies = data.get('require-dev', {})
            
            return {
                'total_dependencies': len(dependencies) + len(dev_dependencies),
                'production_dependencies': len(dependencies),
                'dev_dependencies': len(dev_dependencies),
                'direct_dependencies': list(dependencies.keys()) + list(dev_dependencies.keys())
            }
        except json.JSONDecodeError:
            return {'total_dependencies': 0}
    
    def _parse_go_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse Go go.mod dependencies"""
        dependencies = re.findall(r'require\s+([^\s]+)', content)
        return {
            'total_dependencies': len(dependencies),
            'direct_dependencies': dependencies
        }
    
    def _parse_cargo_dependencies(self, content: str) -> Dict[str, Any]:
        """Parse Rust Cargo.toml dependencies"""
        lines = content.split('\n')
        in_dependencies = False
        in_dev_dependencies = False
        dependencies = []
        dev_dependencies = []
        
        for line in lines:
            if '[dependencies]' in line:
                in_dependencies = True
                in_dev_dependencies = False
            elif '[dev-dependencies]' in line:
                in_dependencies = False
                in_dev_dependencies = True
            elif line.startswith('['):
                in_dependencies = False
                in_dev_dependencies = False
            elif '=' in line and (in_dependencies or in_dev_dependencies):
                dep_name = line.split('=')[0].strip()
                if in_dependencies:
                    dependencies.append(dep_name)
                else:
                    dev_dependencies.append(dep_name)
        
        return {
            'total_dependencies': len(dependencies) + len(dev_dependencies),
            'production_dependencies': len(dependencies),
            'dev_dependencies': len(dev_dependencies),
            'direct_dependencies': dependencies + dev_dependencies
        }
    
    def _detect_security_tools(self, content: str) -> List[str]:
        """Detect configured security tools"""
        tools = []
        
        for tool_name, pattern in self.vulnerability_patterns['security_tools'].items():
            if re.search(pattern, content):
                tools.append(tool_name)
        
        return tools
    
    def _count_dependencies(self, content: str, file_path: str) -> int:
        """Count total dependencies in file"""
        if 'package.json' in file_path:
            return self._parse_npm_dependencies(content).get('total_dependencies', 0)
        elif 'requirements.txt' in file_path:
            return self._parse_pip_dependencies(content).get('total_dependencies', 0)
        elif 'Pipfile' in file_path:
            return self._parse_pipfile_dependencies(content).get('total_dependencies', 0)
        elif 'pyproject.toml' in file_path:
            return self._parse_poetry_dependencies(content).get('total_dependencies', 0)
        else:
            # Generic count based on lines with dependency patterns
            lines = [line for line in content.split('\n') if line.strip() and not line.startswith('#')]
            return len(lines)
    
    def _calculate_dependency_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score for dependency analysis"""
        base_confidence = 0.8
        
        # Adjust based on file type recognition
        if any(re.search(pattern, content) for pattern in ['dependencies', 'require', 'import']):
            base_confidence += 0.1
        
        # Reduce confidence for too many high-severity issues
        high_severity_issues = [issue for issue in issues if issue.get('severity') == 'high']
        if len(high_severity_issues) > 5:
            base_confidence -= 0.2
        
        return max(0.3, min(1.0, base_confidence))
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """Handle chat interactions for dependency security assistance"""
        message = context.get('message', '').lower()
        
        if 'vulnerability' in message or 'cve' in message:
            return "I'm an expert in dependency vulnerabilities! I can help identify vulnerable packages, set up security scanning with tools like npm audit, Snyk, or Safety, and create policies for managing security updates. What vulnerability concern do you have?"
        elif 'license' in message:
            return "License compliance is crucial! I can help identify restrictive licenses, check license compatibility, set up automated license scanning, and create license policies for your project. What license issue are you facing?"
        elif 'supply chain' in message:
            return "Supply chain security is critical! I can help detect typosquatting, identify suspicious packages, implement package verification, and secure your software supply chain. What supply chain risk are you concerned about?"
        elif 'outdated' in message or 'update' in message:
            return "Keeping dependencies updated is essential! I can help identify outdated packages, set up automated updates with Dependabot or Renovate, and create update policies. What dependency update challenge do you have?"
        elif 'npm' in message or 'node' in message:
            return "Node.js dependency security is my specialty! I can help with npm audit, package-lock.json security, Snyk integration, and Node.js-specific vulnerability management. What Node.js dependency issue do you have?"
        elif 'python' in message or 'pip' in message:
            return "Python dependency security is important! I can help with Safety checks, pip-audit, Poetry security features, and Python package vulnerability management. What Python dependency concern do you have?"
        elif 'java' in message or 'maven' in message:
            return "Java dependency security requires attention! I can help with Maven dependency scanning, Gradle security plugins, and Java-specific vulnerability management. What Java dependency issue are you facing?"
        else:
            return "I'm your dependency security specialist! I can help with vulnerability scanning, license compliance, supply chain security, dependency management policies, and security automation across all major package managers (npm, pip, Maven, Gradle, Composer, etc.). What dependency security challenge can I help you solve?" 