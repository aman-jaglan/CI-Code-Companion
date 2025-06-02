"""
Node.js Code Agent - Specialized for Node.js Development

This agent focuses exclusively on Node.js backend development, API design, and optimization.
It provides expert guidance for Express.js, async patterns, middleware, database integration,
and Node.js performance optimization.
"""

import re
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...base_agent import BaseAgent, AgentCapability


class NodeCodeAgent(BaseAgent):
    """
    Specialized agent for Node.js backend development and analysis.
    Focuses on Express.js, APIs, middleware, async patterns, and performance.
    """
    
    def __init__(self, config: Dict[str, Any], logger, prompt_loader=None):
        """Initialize NodeCodeAgent with optional PromptLoader"""
        super().__init__(config, logger)
        self.prompt_loader = prompt_loader
    
    def _initialize(self):
        """Initialize Node Code Agent with specialized configuration"""
        super()._initialize()
        self.name = "node_code"
        self.version = "2.0.0"
        
        # Node.js-specific patterns and rules
        self.node_patterns = {
            'express_app': r'(?:const|let|var)\s+app\s*=\s*express\s*\(\s*\)',
            'route_definition': r'app\.(?:get|post|put|delete|patch|use)\s*\(',
            'middleware_usage': r'app\.use\s*\(',
            'async_function': r'async\s+(?:function\s+\w+|\([^)]*\)\s*=>|\w+\s*=>)',
            'await_usage': r'await\s+[\w.]+(?:\([^)]*\))?',
            'promise_usage': r'\.then\s*\(|\.catch\s*\(|new\s+Promise\s*\(',
            'callback_pattern': r'function\s*\([^)]*,\s*callback\s*\)|callback\s*\(',
            'require_statement': r'(?:const|let|var)\s+[\w{},\s]+\s*=\s*require\s*\([\'"][^\'"]+[\'"]\)',
            'import_statement': r'import\s+[\w{},\s]*\s+from\s+[\'"][^\'"]+[\'"]',
            'module_exports': r'module\.exports\s*=|exports\.\w+\s*=',
            'process_env': r'process\.env\.\w+',
            'error_handling': r'try\s*{|catch\s*\([^)]*\)',
            'json_parse': r'JSON\.parse\s*\(',
            'file_operations': r'fs\.(?:readFile|writeFile|stat|access)',
            'database_query': r'\.(?:find|findOne|save|update|delete|query|execute)\s*\('
        }
        
        self.performance_checks = {
            'sync_file_operations': r'fs\.(?:readFileSync|writeFileSync|statSync)',
            'blocking_operations': r'\.(?:forEach|map|filter)\s*\([^)]*\)\s*{[^}]*(?:await|\.then)',
            'memory_leaks': r'setInterval\s*\(|setTimeout\s*\(',
            'inefficient_loops': r'for\s*\([^)]*in\s+',
            'unhandled_promises': r'\.then\s*\([^)]*\)(?!\s*\.catch)',
            'global_variables': r'(?:global\.|GLOBAL\.)',
            'console_logs': r'console\.(?:log|debug|info)\s*\(',
            'large_payloads': r'JSON\.stringify\s*\([^)]*\)',
            'dense_operations': r'(?:crypto\.pbkdf2|bcrypt\.hash|scrypt)',
            'nested_callbacks': r'function\s*\([^)]*\)\s*{\s*[^}]*function\s*\([^)]*\)'
        }
        
        # Framework-specific patterns
        self.framework_patterns = {
            'express': {
                'security_middleware': r'app\.use\s*\(\s*(?:helmet|cors|rateLimit)',
                'body_parser': r'app\.use\s*\(\s*(?:express\.json|bodyParser)',
                'static_files': r'app\.use\s*\(\s*express\.static',
                'error_middleware': r'app\.use\s*\(\s*function\s*\([^)]*err[^)]*\)',
                'route_params': r'req\.params\.\w+',
                'query_params': r'req\.query\.\w+',
                'request_body': r'req\.body\.\w+',
                'response_methods': r'res\.(?:json|send|status|redirect)'
            },
            'fastify': {
                'route_registration': r'fastify\.(?:get|post|put|delete)',
                'hooks': r'fastify\.addHook\s*\(',
                'plugins': r'fastify\.register\s*\(',
                'schema_validation': r'schema\s*:\s*{',
                'reply_methods': r'reply\.(?:send|code|type)'
            },
            'koa': {
                'middleware': r'app\.use\s*\(\s*async\s*\(',
                'context_usage': r'ctx\.(?:request|response|state)',
                'next_function': r'await\s+next\s*\(\s*\)',
                'throw_errors': r'ctx\.throw\s*\('
            }
        }
        
        # Security patterns
        self.security_patterns = {
            'sql_injection': r'(?:query|execute)\s*\([^)]*\+[^)]*\)',
            'xss_vulnerability': r'res\.send\s*\([^)]*\+[^)]*\)',
            'path_traversal': r'\.\./',
            'eval_usage': r'eval\s*\(',
            'command_injection': r'(?:exec|spawn|fork)\s*\([^)]*\+',
            'hardcoded_secrets': r'(?:password|secret|key)\s*[:=]\s*[\'"][^\'"]{8,}[\'"]',
            'insecure_random': r'Math\.random\s*\(\s*\)',
            'weak_crypto': r'crypto\.createHash\s*\(\s*[\'"]md5[\'"]'
        }
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get Node Code Agent capabilities"""
        return [
            AgentCapability.CODE_ANALYSIS,
            AgentCapability.CODE_OPTIMIZATION,
            AgentCapability.PERFORMANCE_ANALYSIS,
            AgentCapability.REFACTORING,
            AgentCapability.CHAT_SUPPORT
        ]
    
    def get_supported_file_types(self) -> List[str]:
        """Get supported file types for Node.js code analysis"""
        return ['.js', '.mjs', '.ts', '.json']
    
    def get_supported_frameworks(self) -> List[str]:
        """Get supported Node.js frameworks"""
        return ['express', 'fastify', 'koa', 'hapi', 'nest', 'adonis']
    
    async def analyze_file(self, file_path: str, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Node.js code for backend development best practices and optimization.
        
        Args:
            file_path: Path to Node.js file
            content: File content to analyze
            context: Analysis context including project info
            
        Returns:
            Dictionary containing comprehensive code analysis results
        """
        if not await self.validate_input(file_path, content):
            return self.format_result([], [], {}, 0.0)
        
        issues = []
        suggestions = []
        
        # Extract file metadata
        metadata = self.extract_metadata(file_path, content)
        metadata.update(await self._extract_node_metadata(content))
        
        # Perform Node.js-specific code analysis
        issues.extend(await self._analyze_api_design(content))
        issues.extend(await self._analyze_async_patterns(content))
        issues.extend(await self._analyze_middleware_usage(content))
        issues.extend(await self._analyze_error_handling(content))
        issues.extend(await self._analyze_security_patterns(content))
        issues.extend(await self._analyze_performance_issues(content))
        
        # Generate optimization suggestions
        suggestions.extend(await self._suggest_performance_optimizations(content))
        suggestions.extend(await self._suggest_security_improvements(content))
        suggestions.extend(await self._suggest_modern_patterns(content))
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(content, issues, suggestions)
        
        return self.format_result(issues, suggestions, metadata, confidence_score)
    
    async def _extract_node_metadata(self, content: str) -> Dict[str, Any]:
        """Extract Node.js-specific metadata from file content"""
        metadata = {
            'node_version': 'unknown',
            'framework': None,
            'dependencies': [],
            'routes': [],
            'middleware': [],
            'async_functions': 0,
            'promise_usage': 0,
            'callback_usage': 0,
            'security_middleware': [],
            'database_usage': False,
            'api_type': 'unknown',
            'complexity_score': 0
        }
        
        # Detect framework
        metadata['framework'] = self._detect_framework(content)
        
        # Extract dependencies
        require_matches = re.findall(self.node_patterns['require_statement'], content)
        import_matches = re.findall(self.node_patterns['import_statement'], content)
        metadata['dependencies'] = require_matches + import_matches
        
        # Extract routes
        route_matches = re.findall(self.node_patterns['route_definition'], content)
        metadata['routes'] = route_matches
        
        # Extract middleware
        middleware_matches = re.findall(self.node_patterns['middleware_usage'], content)
        metadata['middleware'] = middleware_matches
        
        # Count async patterns
        metadata['async_functions'] = len(re.findall(self.node_patterns['async_function'], content))
        metadata['promise_usage'] = len(re.findall(self.node_patterns['promise_usage'], content))
        metadata['callback_usage'] = len(re.findall(self.node_patterns['callback_pattern'], content))
        
        # Check for database usage
        metadata['database_usage'] = bool(re.search(self.node_patterns['database_query'], content))
        
        # Determine API type
        metadata['api_type'] = self._determine_api_type(content)
        
        # Calculate complexity
        metadata['complexity_score'] = self._calculate_complexity(content)
        
        return metadata
    
    async def _analyze_api_design(self, content: str) -> List[Dict[str, Any]]:
        """Analyze API design patterns and best practices"""
        issues = []
        lines = content.split('\n')
        
        # Check for RESTful patterns
        for i, line in enumerate(lines, 1):
            # Check for proper HTTP status codes
            if 'res.send(' in line and 'res.status(' not in line:
                issues.append(self.create_issue(
                    'api_design',
                    'medium',
                    'Missing HTTP status code',
                    'API responses should include appropriate HTTP status codes',
                    line_number=i,
                    suggestion='Use res.status(200).send() or res.status(404).json()'
                ))
            
            # Check for proper error responses
            if 'throw' in line and 'Error(' in line and 'status' not in line.lower():
                issues.append(self.create_issue(
                    'api_design',
                    'medium',
                    'Missing error status information',
                    'Error objects should include HTTP status information',
                    line_number=i,
                    suggestion='Include status code in error objects'
                ))
            
            # Check for input validation
            if ('req.body' in line or 'req.params' in line or 'req.query' in line) and 'validate' not in content.lower():
                issues.append(self.create_issue(
                    'api_security',
                    'high',
                    'Missing input validation',
                    'User input should be validated before processing',
                    line_number=i,
                    suggestion='Add input validation using joi, express-validator, or similar'
                ))
        
        return issues
    
    async def _analyze_async_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze asynchronous programming patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for promise handling
        for i, line in enumerate(lines, 1):
            # Unhandled promises
            if re.search(self.performance_checks['unhandled_promises'], line):
                issues.append(self.create_issue(
                    'async_patterns',
                    'high',
                    'Unhandled promise rejection',
                    'Promises should have proper error handling with .catch()',
                    line_number=i,
                    suggestion='Add .catch() to handle promise rejections'
                ))
            
            # Mixed async patterns
            if 'await' in line and '.then(' in line:
                issues.append(self.create_issue(
                    'async_patterns',
                    'medium',
                    'Mixed async patterns',
                    'Avoid mixing async/await with .then() patterns',
                    line_number=i,
                    suggestion='Use consistent async/await pattern'
                ))
            
            # Callback hell detection
            callback_nesting = line.count('function(') + line.count('=>')
            if callback_nesting > 2:
                issues.append(self.create_issue(
                    'async_patterns',
                    'high',
                    'Callback hell detected',
                    'Deep nesting of callbacks makes code hard to maintain',
                    line_number=i,
                    suggestion='Refactor to use async/await or promises'
                ))
        
        return issues
    
    async def _analyze_middleware_usage(self, content: str) -> List[Dict[str, Any]]:
        """Analyze middleware usage and patterns"""
        issues = []
        
        framework = self._detect_framework(content)
        if framework != 'express':
            return issues
        
        # Check for security middleware
        security_middleware = ['helmet', 'cors', 'rate-limit', 'express-rate-limit']
        has_security = any(middleware in content for middleware in security_middleware)
        
        if 'app.listen(' in content and not has_security:
            issues.append(self.create_issue(
                'security',
                'high',
                'Missing security middleware',
                'Express app should use security middleware like helmet, cors, rate limiting',
                suggestion='Add app.use(helmet()), app.use(cors()), and rate limiting'
            ))
        
        # Check for body parsing
        if ('req.body' in content and 
            'express.json()' not in content and 
            'bodyParser' not in content):
            issues.append(self.create_issue(
                'middleware',
                'high',
                'Missing body parser middleware',
                'Request body parsing middleware is required for POST/PUT requests',
                suggestion='Add app.use(express.json()) middleware'
            ))
        
        # Check for error handling middleware
        lines = content.split('\n')
        has_error_middleware = any(
            'function' in line and 'err' in line and len(line.split(',')) >= 4
            for line in lines
        )
        
        if 'app.listen(' in content and not has_error_middleware:
            issues.append(self.create_issue(
                'error_handling',
                'medium',
                'Missing error handling middleware',
                'Express app should have error handling middleware',
                suggestion='Add error handling middleware: app.use((err, req, res, next) => {...})'
            ))
        
        return issues
    
    async def _analyze_error_handling(self, content: str) -> List[Dict[str, Any]]:
        """Analyze error handling patterns"""
        issues = []
        lines = content.split('\n')
        
        # Check for try-catch around async operations
        async_lines = [i for i, line in enumerate(lines, 1) if 'await' in line]
        
        for line_num in async_lines:
            # Look for try-catch around async operations
            try_found = False
            for check_line in range(max(0, line_num - 5), min(len(lines), line_num + 2)):
                if 'try' in lines[check_line]:
                    try_found = True
                    break
            
            if not try_found:
                issues.append(self.create_issue(
                    'error_handling',
                    'high',
                    'Unhandled async operation',
                    'Async operations should be wrapped in try-catch blocks',
                    line_number=line_num,
                    suggestion='Wrap await calls in try-catch blocks'
                ))
        
        # Check for process error handlers
        if 'process.' in content:
            has_uncaught_exception = 'uncaughtException' in content
            has_unhandled_rejection = 'unhandledRejection' in content
            
            if not has_uncaught_exception:
                issues.append(self.create_issue(
                    'process_handling',
                    'medium',
                    'Missing uncaught exception handler',
                    'Node.js apps should handle uncaught exceptions',
                    suggestion="Add process.on('uncaughtException', handler)"
                ))
            
            if not has_unhandled_rejection:
                issues.append(self.create_issue(
                    'process_handling',
                    'medium',
                    'Missing unhandled rejection handler',
                    'Node.js apps should handle unhandled promise rejections',
                    suggestion="Add process.on('unhandledRejection', handler)"
                ))
        
        return issues
    
    async def _analyze_security_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Analyze security vulnerabilities and patterns"""
        issues = []
        lines = content.split('\n')
        
        for pattern_name, pattern in self.security_patterns.items():
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    severity, title, description, suggestion = self._get_security_issue_info(pattern_name)
                    issues.append(self.create_issue(
                        'security_vulnerability',
                        severity,
                        title,
                        description,
                        line_number=i,
                        suggestion=suggestion
                    ))
        
        return issues
    
    def _get_security_issue_info(self, pattern_name: str) -> tuple:
        """Get security issue information"""
        info = {
            'sql_injection': (
                'high',
                'SQL injection vulnerability',
                'Dynamic query construction can lead to SQL injection',
                'Use parameterized queries or ORM methods'
            ),
            'xss_vulnerability': (
                'high',
                'XSS vulnerability',
                'Unsanitized user input in response can lead to XSS',
                'Sanitize user input before including in responses'
            ),
            'path_traversal': (
                'high',
                'Path traversal vulnerability',
                'Path traversal sequences can access unauthorized files',
                'Validate and sanitize file paths'
            ),
            'eval_usage': (
                'high',
                'Code injection vulnerability',
                'eval() can execute arbitrary code and is dangerous',
                'Avoid eval() and use JSON.parse() for data parsing'
            ),
            'command_injection': (
                'high',
                'Command injection vulnerability',
                'Unsanitized input in system commands can lead to injection',
                'Validate input and use safe alternatives'
            ),
            'hardcoded_secrets': (
                'high',
                'Hardcoded secrets',
                'Secrets in source code can be exposed',
                'Use environment variables for sensitive data'
            ),
            'insecure_random': (
                'medium',
                'Insecure random number generation',
                'Math.random() is not cryptographically secure',
                'Use crypto.randomBytes() for security-sensitive operations'
            ),
            'weak_crypto': (
                'medium',
                'Weak cryptographic algorithm',
                'MD5 is cryptographically broken',
                'Use SHA-256 or stronger algorithms'
            )
        }
        return info.get(pattern_name, ('low', 'Security issue', 'Potential security concern', 'Review for security implications'))
    
    async def _analyze_performance_issues(self, content: str) -> List[Dict[str, Any]]:
        """Analyze performance-related issues"""
        issues = []
        lines = content.split('\n')
        
        for pattern_name, pattern in self.performance_checks.items():
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    severity, title, description, suggestion = self._get_performance_issue_info(pattern_name)
                    issues.append(self.create_issue(
                        'performance',
                        severity,
                        title,
                        description,
                        line_number=i,
                        suggestion=suggestion
                    ))
        
        return issues
    
    def _get_performance_issue_info(self, pattern_name: str) -> tuple:
        """Get performance issue information"""
        info = {
            'sync_file_operations': (
                'high',
                'Synchronous file operation',
                'Synchronous file operations block the event loop',
                'Use asynchronous file operations with fs.promises or callbacks'
            ),
            'blocking_operations': (
                'high',
                'Blocking operation in array method',
                'Async operations in array methods can block execution',
                'Use for...of loop with await or Promise.all() for parallel execution'
            ),
            'memory_leaks': (
                'medium',
                'Potential memory leak',
                'Timers without proper cleanup can cause memory leaks',
                'Clear timers and intervals when no longer needed'
            ),
            'inefficient_loops': (
                'low',
                'Inefficient for...in loop',
                'for...in loops are slower than for...of or traditional for loops',
                'Use for...of for arrays or Object.keys() for objects'
            ),
            'unhandled_promises': (
                'high',
                'Unhandled promise',
                'Promises without error handling can cause crashes',
                'Add .catch() or wrap in try-catch'
            ),
            'console_logs': (
                'low',
                'Console logging in production',
                'Console logs can impact performance in production',
                'Use proper logging library and remove debug logs'
            )
        }
        return info.get(pattern_name, ('low', 'Performance issue', 'Potential performance concern', 'Review for optimization'))
    
    async def _suggest_performance_optimizations(self, content: str) -> List[Dict[str, Any]]:
        """Suggest performance optimizations"""
        suggestions = []
        
        # Suggest clustering for CPU-intensive apps
        if 'app.listen(' in content and 'cluster' not in content:
            suggestions.append(self.create_suggestion(
                'scalability',
                'Consider Node.js clustering',
                'Use cluster module to utilize multiple CPU cores',
                impact='high',
                effort='medium'
            ))
        
        # Suggest compression middleware
        if 'express()' in content and 'compression' not in content:
            suggestions.append(self.create_suggestion(
                'performance',
                'Add compression middleware',
                'Compress responses to reduce bandwidth and improve load times',
                impact='medium',
                effort='low'
            ))
        
        # Suggest caching
        if 'database' in content.lower() or 'query' in content.lower():
            suggestions.append(self.create_suggestion(
                'performance',
                'Implement caching strategy',
                'Cache frequently accessed data to reduce database load',
                impact='high',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_security_improvements(self, content: str) -> List[Dict[str, Any]]:
        """Suggest security improvements"""
        suggestions = []
        
        # Suggest HTTPS
        if 'app.listen(' in content and 'https' not in content.lower():
            suggestions.append(self.create_suggestion(
                'security',
                'Implement HTTPS',
                'Use HTTPS in production for secure communication',
                impact='high',
                effort='medium'
            ))
        
        # Suggest environment variables
        if re.search(r'[\'"][a-zA-Z0-9]{20,}[\'"]', content):
            suggestions.append(self.create_suggestion(
                'security',
                'Use environment variables',
                'Move configuration and secrets to environment variables',
                impact='high',
                effort='low'
            ))
        
        # Suggest input validation
        if 'req.' in content and 'validate' not in content.lower():
            suggestions.append(self.create_suggestion(
                'security',
                'Add input validation',
                'Validate all user inputs to prevent injection attacks',
                impact='high',
                effort='medium'
            ))
        
        return suggestions
    
    async def _suggest_modern_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Suggest modern Node.js patterns"""
        suggestions = []
        
        # Suggest ES6 modules over CommonJS
        if 'require(' in content and 'import' not in content:
            suggestions.append(self.create_suggestion(
                'modernization',
                'Consider ES6 modules',
                'Use ES6 import/export syntax for better tree shaking and static analysis',
                impact='low',
                effort='medium'
            ))
        
        # Suggest async/await over callbacks
        if re.search(self.node_patterns['callback_pattern'], content) and 'async' not in content:
            suggestions.append(self.create_suggestion(
                'modernization',
                'Use async/await instead of callbacks',
                'async/await provides cleaner, more readable asynchronous code',
                impact='medium',
                effort='high'
            ))
        
        # Suggest destructuring
        if 'req.body.' in content or 'req.params.' in content:
            suggestions.append(self.create_suggestion(
                'code_quality',
                'Use destructuring assignment',
                'Destructure request objects for cleaner code',
                impact='low',
                effort='low'
            ))
        
        return suggestions
    
    def _detect_framework(self, content: str) -> Optional[str]:
        """Detect Node.js framework being used"""
        if 'express' in content.lower() or 'app.use(' in content:
            return 'express'
        elif 'fastify' in content.lower():
            return 'fastify'
        elif 'koa' in content.lower() or 'ctx.' in content:
            return 'koa'
        elif 'hapi' in content.lower():
            return 'hapi'
        elif '@nestjs' in content.lower():
            return 'nest'
        elif 'adonis' in content.lower():
            return 'adonis'
        
        return None
    
    def _determine_api_type(self, content: str) -> str:
        """Determine the type of API being built"""
        if 'graphql' in content.lower():
            return 'graphql'
        elif re.search(r'app\.(?:get|post|put|delete)', content):
            return 'rest'
        elif 'socket' in content.lower() or 'websocket' in content.lower():
            return 'websocket'
        elif 'rpc' in content.lower():
            return 'rpc'
        else:
            return 'unknown'
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate code complexity score"""
        complexity_factors = {
            'routes': len(re.findall(self.node_patterns['route_definition'], content)),
            'middleware': len(re.findall(self.node_patterns['middleware_usage'], content)),
            'async_functions': len(re.findall(self.node_patterns['async_function'], content)),
            'conditionals': len(re.findall(r'if\s*\(|switch\s*\(', content)),
            'loops': len(re.findall(r'for\s*\(|while\s*\(', content)),
            'try_catch': len(re.findall(r'try\s*{|catch\s*\(', content))
        }
        
        # Weighted complexity calculation
        score = (
            complexity_factors['routes'] * 2 +
            complexity_factors['middleware'] * 1.5 +
            complexity_factors['async_functions'] * 2 +
            complexity_factors['conditionals'] * 1 +
            complexity_factors['loops'] * 1.5 +
            complexity_factors['try_catch'] * 0.5
        )
        
        return min(score / 10, 10.0)  # Normalize to 0-10 scale
    
    def _calculate_confidence(self, content: str, issues: List, suggestions: List) -> float:
        """Calculate confidence score based on analysis completeness"""
        base_confidence = 0.8
        
        # Boost confidence for recognizable patterns
        if re.search(self.node_patterns['express_app'], content):
            base_confidence += 0.1
        
        # Adjust based on code complexity
        complexity = self._calculate_complexity(content)
        if complexity < 3:
            base_confidence += 0.1
        elif complexity > 8:
            base_confidence -= 0.1
        
        # Adjust based on issues found
        if len(issues) == 0:
            base_confidence += 0.1
        elif len(issues) > 10:
            base_confidence -= 0.1
        
        return max(0.5, min(1.0, base_confidence))
    
    async def _chat_impl(self, context: Dict[str, Any]) -> str:
        """
        Node.js agent chat implementation using PromptLoader.
        
        Args:
            context: Chat context including message, file info, and conversation history
            
        Returns:
            Helpful Node.js-specific response from PromptLoader
        """
        user_message = context.get('user_message', context.get('message', ''))
        file_path = context.get('file_path', '')
        file_content = context.get('file_content', context.get('content', ''))
        conversation_history = context.get('conversation_history', [])
        
        self.logger.info(f"🟢 NODE CHAT: Processing message: '{user_message[:100]}{'...' if len(user_message) > 100 else ''}'")
        
        # Use PromptLoader if available (should be injected via constructor)
        if hasattr(self, 'prompt_loader') and self.prompt_loader:
            self.logger.info(f"📚 NODE CHAT: Using PromptLoader for enhanced response")
            
            # Build enhanced context for PromptLoader
            enhanced_context = {
                'user_message': user_message,
                'selected_file': {
                    'path': file_path,
                    'content': file_content,
                    'language': 'javascript'
                } if file_content else None,
                'conversation_history': conversation_history,
                'chat_mode': True,
                'agent_type': 'node_code'
            }
            
            # Get enhanced prompt with context
            enhanced_prompt = self.prompt_loader.get_enhanced_prompt('node_code', enhanced_context)
            
            # Use the enhanced prompt to provide contextual guidance
            response = await self._generate_response_with_prompt_loader(
                user_message, enhanced_context, enhanced_prompt
            )
            
            self.logger.info(f"✅ NODE CHAT: Generated enhanced response ({len(response)} characters)")
            return response
        else:
            # Fallback to basic response if no PromptLoader
            self.logger.warning(f"⚠️ NODE CHAT: No PromptLoader available, using basic response")
            return await self._generate_basic_chat_response(user_message, file_path, file_content)
    
    async def _generate_response_with_prompt_loader(
        self, 
        user_message: str, 
        context: Dict[str, Any], 
        enhanced_prompt: str
    ) -> str:
        """Generate response using PromptLoader and enhanced context via Vertex AI."""
        
        try:
            # Import here to avoid circular imports
            from ....integrations.vertex_ai_client import VertexAIClient
            
            # Initialize Vertex AI client (reuse from service if available)
            # Use config.get() method to properly read from environment variables
            project_id = self.config.get('project_id') if hasattr(self.config, 'get') else os.getenv('GCP_PROJECT_ID')
            region = self.config.get('region', 'us-central1') if hasattr(self.config, 'get') else 'us-central1'
            
            vertex_client = VertexAIClient(
                project_id=project_id,
                location=region,
                model_name=None,  # Will read from GEMINI_MODEL env var
            )
            
            self.logger.info(f"🤖 NODE CHAT: Using Vertex AI with model: {vertex_client.model_name}")
            self.logger.info(f"📏 NODE CHAT: Enhanced prompt length: {len(enhanced_prompt)} characters")
            
            # Use the enhanced prompt with Vertex AI
            response = await vertex_client.chat_with_context(
                message=user_message,
                enhanced_prompt=enhanced_prompt,
                conversation_history=context.get('conversation_history', [])
            )
            
            self.logger.info(f"✅ NODE CHAT: Vertex AI response received")
            
            # Extract text from response
            if isinstance(response, dict):
                text_response = response.get('text') or response.get('response') or response.get('content')
                if text_response:
                    self.logger.info(f"📝 NODE CHAT: Returning AI-generated response ({len(text_response)} characters)")
                    return text_response
                else:
                    error_msg = response.get('error', 'Unknown error')
                    self.logger.error(f"❌ NODE CHAT: No text in AI response - Error: {error_msg}")
                    return await self._generate_basic_chat_response(user_message, context.get('selected_file', {}).get('path', ''), context.get('selected_file', {}).get('content', ''))
            else:
                self.logger.error(f"❌ NODE CHAT: Unexpected response format: {type(response)}")
                return await self._generate_basic_chat_response(user_message, context.get('selected_file', {}).get('path', ''), context.get('selected_file', {}).get('content', ''))
                
        except Exception as e:
            self.logger.error(f"❌ NODE CHAT: Error using PromptLoader with Vertex AI: {e}")
            # Fall back to basic response
            return await self._generate_basic_chat_response(
                user_message, 
                context.get('selected_file', {}).get('path', ''), 
                context.get('selected_file', {}).get('content', '')
            )
    
    async def _generate_basic_chat_response(
        self, 
        user_message: str, 
        file_path: str, 
        file_content: str
    ) -> str:
        """Basic fallback response when PromptLoader is not available."""
        
        return f"""## Node.js Development Assistant

I'm your Node.js backend specialist. I can help with:

- Express.js and API development
- Async programming and performance
- Database integration and optimization
- Security and authentication
- Modern JavaScript patterns

{f"Currently analyzing: `{file_path}`" if file_path else ""}

What Node.js challenge can I help you solve?""" 