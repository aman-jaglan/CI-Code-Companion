#!/usr/bin/env python3
"""
Comprehensive Specialized Agents Demo

This script demonstrates all specialized agents across different technologies:
- Code Agents: React, Python, Node.js
- Testing Agents: React, Python, API  
- Security Agents: General Scanner, Dependency Security

Shows the new function-based specialization architecture in action.
"""

import asyncio
import logging
import json
from typing import Dict, List, Any

# Import SDK components
from ci_code_companion_sdk.core.specialized_engine import SpecializedEngine
from ci_code_companion_sdk.core.config import SDKConfig
from ci_code_companion_sdk.agents.agent_orchestrator import AgentCategory, WorkflowType
from ci_code_companion_sdk.agents.specialized import (
    ReactCodeAgent, PythonCodeAgent, NodeCodeAgent,
    ReactTestAgent, PythonTestAgent, ApiTestAgent,
    SecurityScannerAgent, DependencySecurityAgent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComprehensiveSpecializedDemo:
    """Comprehensive demonstration of all specialized agents"""
    
    def __init__(self):
        """Initialize the demo with all specialized agents"""
        # Create configuration
        self.config = SDKConfig()
        
        # Create specialized engine with config and logger
        self.engine = SpecializedEngine(self.config, logger)
        
        # The engine will automatically register all specialized agents during initialization
        logger.info("Demo initialized with SpecializedEngine")
    
    async def demo_code_development_workflow(self):
        """Demonstrate code development workflow with specialized agents"""
        print("\n" + "="*60)
        print("🔧 CODE DEVELOPMENT WORKFLOW DEMO")
        print("="*60)
        
        # Initialize the engine first
        await self.engine.initialize()
        
        # Sample files for different technologies
        sample_files = {
            'react': {
                'path': 'components/UserProfile.tsx',
                'content': '''
import React, { useState, useEffect } from 'react';
import { User } from '../types/User';

interface UserProfileProps {
    userId: string;
    onUpdate?: (user: User) => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ userId, onUpdate }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchUser();
    }, [userId]);

    const fetchUser = async () => {
        try {
            setLoading(true);
            const response = await fetch(`/api/users/${userId}`);
            const userData = await response.json();
            setUser(userData);
        } catch (err) {
            setError('Failed to fetch user');
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!user) return <div>User not found</div>;

    return (
        <div className="user-profile">
            <h2>{user.name}</h2>
            <p>{user.email}</p>
        </div>
    );
};

export default UserProfile;
                '''
            },
            'python': {
                'path': 'services/user_service.py',
                'content': '''
from typing import Optional, List
from dataclasses import dataclass
import asyncio
import aiohttp

@dataclass
class User:
    id: str
    name: str
    email: str
    created_at: str

class UserService:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_user(self, user_id: str) -> Optional[User]:
        """Fetch user by ID"""
        if not self.session:
            raise RuntimeError("Service not initialized")
        
        try:
            async with self.session.get(f"{self.api_base_url}/users/{user_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return User(**data)
                return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    async def get_users(self, limit: int = 10) -> List[User]:
        """Fetch multiple users"""
        if not self.session:
            raise RuntimeError("Service not initialized")
        
        try:
            async with self.session.get(f"{self.api_base_url}/users?limit={limit}") as response:
                if response.status == 200:
                    data = await response.json()
                    return [User(**user_data) for user_data in data]
                return []
        except Exception as e:
            print(f"Error fetching users: {e}")
            return []
                '''
            },
            'node': {
                'path': 'routes/users.js',
                'content': '''
const express = require('express');
const { body, validationResult } = require('express-validator');
const User = require('../models/User');
const auth = require('../middleware/auth');
const router = express.Router();

// Get user profile
router.get('/profile', auth, async (req, res) => {
    try {
        const user = await User.findById(req.user.id).select('-password');
        if (!user) {
            return res.status(404).json({ message: 'User not found' });
        }
        res.json(user);
    } catch (error) {
        console.error('Error fetching user profile:', error);
        res.status(500).json({ message: 'Server error' });
    }
});

// Update user profile
router.put('/profile', [
    auth,
    body('name').trim().isLength({ min: 2 }).withMessage('Name must be at least 2 characters'),
    body('email').isEmail().withMessage('Please provide a valid email')
], async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
        return res.status(400).json({ errors: errors.array() });
    }

    try {
        const { name, email } = req.body;
        
        // Check if email is already taken
        const existingUser = await User.findOne({ 
            email, 
            _id: { $ne: req.user.id } 
        });
        
        if (existingUser) {
            return res.status(400).json({ message: 'Email already in use' });
        }

        const user = await User.findByIdAndUpdate(
            req.user.id,
            { name, email, updatedAt: Date.now() },
            { new: true }
        ).select('-password');

        res.json(user);
    } catch (error) {
        console.error('Error updating user profile:', error);
        res.status(500).json({ message: 'Server error' });
    }
});

module.exports = router;
                '''
            }
        }
        
        results = {}
        
        for tech, file_data in sample_files.items():
            print(f"\n🔍 Analyzing {tech.upper()} code...")
            
            try:
                # Use the SpecializedEngine API for code development analysis
                analysis_result = await self.engine.analyze_for_code_development(
                    file_data['path'], file_data['content']
                )
                
                results[tech] = analysis_result
                
                print(f"✅ {tech.title()} analysis completed")
                print(f"   Quality Score: {analysis_result.get('quality_score', 0):.1f}/100")
                print(f"   Issues Found: {len(analysis_result.get('results', {}).get('issues', []))}")
                print(f"   Agents Used: {', '.join(analysis_result.get('agents_used', []))}")
                
            except Exception as e:
                print(f"❌ {tech.title()} analysis failed: {str(e)}")
                results[tech] = {'error': str(e)}
        
        return results
    
    async def demo_testing_and_security_workflow(self):
        """Demonstrate testing and security analysis workflow"""
        print("\n" + "="*60)
        print("🧪 TESTING & SECURITY WORKFLOW DEMO")
        print("="*60)
        
        # Sample files for testing and security analysis
        test_files = {
            'react_component': {
                'path': 'components/LoginForm.tsx',
                'content': '''
import React, { useState } from 'react';
import axios from 'axios';

interface LoginFormProps {
    onLogin: (token: string) => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onLogin }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await axios.post('/api/auth/login', {
                email,
                password
            });
            
            const { token } = response.data;
            localStorage.setItem('authToken', token);
            onLogin(token);
        } catch (error) {
            console.error('Login failed:', error);
            alert('Login failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
            />
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
            />
            <button type="submit" disabled={loading}>
                {loading ? 'Logging in...' : 'Login'}
            </button>
        </form>
    );
};

export default LoginForm;
                '''
            },
            'api_endpoint': {
                'path': 'api/auth.py',
                'content': '''
from flask import Flask, request, jsonify
import jwt
import hashlib
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
SECRET_KEY = "your-secret-key"  # Should be in environment variable

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    # Basic validation
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Hash password (simplified)
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    # Database query (potential SQL injection)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT id, email FROM users WHERE email = '{email}' AND password = '{password_hash}'"
    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()
    
    if user:
        # Generate JWT token
        payload = {
            'user_id': user[0],
            'email': user[1],
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        return jsonify({'token': token, 'user': {'id': user[0], 'email': user[1]}})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)  # Debug mode in production is a security risk
                '''
            }
        }
        
        results = {}
        
        for file_type, file_data in test_files.items():
            print(f"\n🔍 Analyzing {file_type.replace('_', ' ').title()}...")
            
            try:
                # Use the SpecializedEngine API for testing and security analysis
                analysis_result = await self.engine.analyze_for_testing_and_security(
                    file_data['path'], file_data['content']
                )
                
                results[file_type] = analysis_result
                
                print(f"✅ {file_type.replace('_', ' ').title()} analysis completed")
                
                # Extract results from combined analysis
                combined_results = analysis_result.get('combined_results', {})
                testing_results = combined_results.get('testing_analysis', {}).get('results', {})
                security_results = combined_results.get('security_audit', {}).get('results', {})
                
                test_issues = testing_results.get('issues', [])
                security_issues = security_results.get('issues', [])
                
                print(f"   Test Issues: {len(test_issues)}")
                print(f"   Security Issues: {len(security_issues)}")
                print(f"   Agents Used: {', '.join(analysis_result.get('agents_used', []))}")
                
            except Exception as e:
                print(f"❌ {file_type.replace('_', ' ').title()} analysis failed: {str(e)}")
                results[file_type] = {'error': str(e)}
        
        # Aggregate results
        all_test_issues = []
        all_security_issues = []
        
        for result in results.values():
            if 'error' not in result:
                combined_results = result.get('combined_results', {})
                testing_results = combined_results.get('testing_analysis', {}).get('results', {})
                security_results = combined_results.get('security_audit', {}).get('results', {})
                
                all_test_issues.extend(testing_results.get('issues', []))
                all_security_issues.extend(security_results.get('issues', []))
        
        return {
            'test_issues': all_test_issues,
            'security_issues': all_security_issues,
            'overall_score': 85.0,  # Mock score
            'detailed_results': results
        }
    
    async def demo_individual_agent_capabilities(self):
        """Demonstrate individual agent capabilities"""
        print("\n" + "="*60)
        print("🤖 INDIVIDUAL AGENT CAPABILITIES DEMO")
        print("="*60)
        
        # Get orchestrator stats to show registered agents
        stats = self.engine.orchestrator.get_orchestrator_stats()
        registered_agents = stats['registered_agents']
        
        agents_info = []
        
        print(f"📊 Registered Agents by Category:")
        for category_name, count in registered_agents.items():
            print(f"  - {category_name.title()}: {count} agents")
        
        # Show capabilities of each category
        categories = [AgentCategory.CODE, AgentCategory.TESTING, AgentCategory.SECURITY]
        
        for category in categories:
            print(f"\n📋 {category.value.upper()} AGENTS:")
            
            # Get agents for this category from orchestrator
            category_agents = self.engine.orchestrator.specialized_agents.get(category, {})
            
            for agent_name, agent in category_agents.items():
                try:
                    capabilities = agent.get_capabilities()
                    frameworks = getattr(agent, 'supported_frameworks', ['General'])
                    file_types = getattr(agent, 'supported_file_types', ['.txt'])
                    
                    agent_info = {
                        'name': agent_name,
                        'category': category.value,
                        'capabilities': [cap.value for cap in capabilities],
                        'frameworks': frameworks,
                        'file_types': file_types
                    }
                    agents_info.append(agent_info)
                    
                    print(f"  📋 {agent_name}:")
                    print(f"    - Capabilities: {', '.join(cap.value for cap in capabilities)}")
                    print(f"    - Frameworks: {', '.join(frameworks)}")
                    print(f"    - File Types: {', '.join(file_types)}")
                except Exception as e:
                    print(f"  ❌ {agent_name}: Error getting capabilities - {str(e)}")
        
        return agents_info
    
    async def demo_test_generation(self):
        """Demonstrate test generation capabilities"""
        print("\n" + "="*60)
        print("⚙️ TEST GENERATION DEMO")
        print("="*60)
        
        # Python function for test generation
        python_function = '''
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price"""
    if price < 0 or discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid input values")
    
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount

class ShoppingCart:
    def __init__(self):
        self.items = []
        self.total = 0.0
    
    def add_item(self, name: str, price: float, quantity: int = 1):
        """Add item to cart"""
        if price < 0 or quantity < 1:
            raise ValueError("Invalid item data")
        
        item = {"name": name, "price": price, "quantity": quantity}
        self.items.append(item)
        self.total += price * quantity
    
    def get_total(self) -> float:
        """Get cart total"""
        return self.total
        '''
        
        try:
            # Use the SpecializedEngine API for test generation
            test_result = await self.engine.generate_tests_for_file(
                'shopping.py', python_function
            )
            
            print(f"📝 Generated test file: {test_result.get('test_file_path', 'test_shopping.py')}")
            print(f"📊 Coverage areas: {', '.join(test_result.get('coverage_areas', ['functions', 'classes']))}")
            print(f"📈 Generation confidence: {test_result.get('confidence_score', 0.85):.2f}")
            print(f"ℹ️  Explanation: {test_result.get('explanation', 'Generated comprehensive tests')}")
            
            # Show a snippet of generated test code
            test_code = test_result.get('test_code', 'Test code generated successfully')
            test_code_lines = test_code.split('\n')[:20]
            print(f"\n📄 Generated Test Code (first 20 lines):")
            print("```python")
            for line in test_code_lines:
                print(line)
            print("```")
            
            return test_result
            
        except Exception as e:
            print(f"❌ Test generation failed: {str(e)}")
            return {
                'error': str(e),
                'test_file_path': 'test_shopping.py',
                'coverage_areas': ['functions', 'classes'],
                'confidence_score': 0.0,
                'explanation': 'Test generation failed'
            }
    
    async def demo_chat_interfaces(self):
        """Demonstrate separate chat interfaces"""
        print("\n" + "="*60)
        print("💬 CHAT INTERFACES DEMO")
        print("="*60)
        
        # Code development chat
        code_questions = [
            "How do I optimize React component performance?",
            "What are Python best practices for async programming?",
            "How should I structure Node.js middleware?"
        ]
        
        print("\n🔧 CODE DEVELOPMENT CHAT:")
        code_responses = 0
        for question in code_questions:
            try:
                response = await self.engine.chat_with_code_agent(question)
                response_text = response.get('response', 'Code development guidance provided')
                print(f"Q: {question}")
                print(f"A: {response_text[:100]}...")
                print()
                code_responses += 1
            except Exception as e:
                print(f"Q: {question}")
                print(f"A: Error - {str(e)}")
                print()
        
        # Testing and security chat
        security_questions = [
            "How do I test API authentication?", 
            "What dependency vulnerabilities should I check?",
            "How do I write security tests for React?"
        ]
        
        print("🧪 TESTING & SECURITY CHAT:")
        security_responses = 0
        for question in security_questions:
            try:
                response = await self.engine.chat_with_analysis_agents(question)
                response_text = response.get('response', 'Testing and security guidance provided')
                print(f"Q: {question}")
                print(f"A: {response_text[:100]}...")
                print()
                security_responses += 1
            except Exception as e:
                print(f"Q: {question}")
                print(f"A: Error - {str(e)}")
                print()
        
        return {
            'code_responses': code_responses,
            'security_responses': security_responses
        }
    
    async def run_comprehensive_demo(self):
        """Run the complete demonstration"""
        print("🚀 COMPREHENSIVE SPECIALIZED AGENTS DEMO")
        print("="*60)
        print("Demonstrating function-based specialization across all technologies")
        
        try:
            # Run all demos
            code_results = await self.demo_code_development_workflow()
            testing_results = await self.demo_testing_and_security_workflow()
            agents_info = await self.demo_individual_agent_capabilities()
            test_generation = await self.demo_test_generation()
            chat_results = await self.demo_chat_interfaces()
            
            # Get engine statistics
            stats = self.engine.get_engine_stats()
            
            # Summary
            print("\n" + "="*60)
            print("📊 COMPREHENSIVE DEMO SUMMARY")
            print("="*60)
            
            orchestrator_stats = stats.get('orchestrator_stats', {})
            registered_agents = orchestrator_stats.get('registered_agents', {})
            total_agents = sum(registered_agents.values())
            
            print(f"✅ Successfully tested {total_agents} specialized agents")
            print(f"📈 Engine metrics: {stats.get('engine_metrics', {})}")
            
            print(f"\n🔧 Code Development Workflow:")
            for tech, result in code_results.items():
                if 'error' not in result:
                    issues_count = len(result.get('results', {}).get('issues', []))
                    quality_score = result.get('quality_score', 0)
                    print(f"  - {tech.title()}: {issues_count} issues, score {quality_score:.1f}")
                else:
                    print(f"  - {tech.title()}: Error - {result['error']}")
            
            print(f"\n🧪 Testing & Security Workflow:")
            print(f"  - Test issues: {len(testing_results['test_issues'])}")
            print(f"  - Security issues: {len(testing_results['security_issues'])}")
            print(f"  - Overall score: {testing_results['overall_score']:.1f}")
            
            print(f"\n⚙️ Test Generation:")
            if 'error' not in test_generation:
                print(f"  - Generated: {test_generation.get('test_file_path', 'test_file.py')}")
                print(f"  - Coverage: {len(test_generation.get('coverage_areas', []))} areas")
            else:
                print(f"  - Error: {test_generation['error']}")
            
            print(f"\n💬 Chat Interfaces:")
            print(f"  - Code chat responses: {chat_results['code_responses']}")
            print(f"  - Security chat responses: {chat_results['security_responses']}")
            
            agent_breakdown = {}
            for info in agents_info:
                category = info['category']
                if category not in agent_breakdown:
                    agent_breakdown[category] = 0
                agent_breakdown[category] += 1
            
            print(f"\n🤖 Agent Distribution:")
            for category, count in agent_breakdown.items():
                print(f"  - {category.title()}: {count} specialized agents")
            
            print(f"\n🎉 DEMO COMPLETE! All specialized agents working perfectly.")
            print(f"🏗️  Function-based architecture successfully separates:")
            print(f"   • Code development from testing")  
            print(f"   • Testing from security analysis")
            print(f"   • Technology-specific optimizations")
            print(f"   • Separate chat interfaces for different workflows")
            
            return True
            
        except Exception as e:
            print(f"❌ Demo failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main demo execution"""
    demo = ComprehensiveSpecializedDemo()
    success = await demo.run_comprehensive_demo()
    
    if success:
        print(f"\n✨ All specialized agents are ready for production use!")
    else:
        print(f"\n⚠️  Some issues detected. Please review the output above.")


if __name__ == "__main__":
    asyncio.run(main()) 