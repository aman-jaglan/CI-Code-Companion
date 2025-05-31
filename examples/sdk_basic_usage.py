#!/usr/bin/env python3
"""
Basic SDK Usage Example

This example demonstrates how to use the CI Code Companion SDK
for basic code analysis, test generation, and optimization.
"""

import asyncio
import logging
from pathlib import Path

# Import the SDK
from ci_code_companion_sdk import CICodeCompanionSDK, SDKConfig
from ci_code_companion_sdk.core.exceptions import SDKError

async def main():
    """Main example function"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 CI Code Companion SDK - Basic Usage Example")
    print("=" * 50)
    
    # 1. Initialize SDK with default configuration
    try:
        config = SDKConfig()
        sdk = CICodeCompanionSDK(config=config)
        print("✅ SDK initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize SDK: {e}")
        return
    
    # 2. Sample code files for analysis
    sample_files = {
        "sample.py": '''
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
''',
        "sample.jsx": '''
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
    const [user, setUser] = useState(null);
    
    useEffect(() => {
        fetchUser(userId).then(setUser);
    });
    
    return (
        <div style={{padding: '10px'}}>
            {user && <h1>{user.name}</h1>}
        </div>
    );
}

export default UserProfile;
''',
        "sample.ts": '''
interface User {
    id: number;
    name: string;
    email: string;
}

class UserService {
    async getUser(id: number): Promise<User> {
        const response = await fetch('/api/users/' + id);
        return response.json();
    }
    
    async updateUser(user: User): Promise<void> {
        await fetch('/api/users/' + user.id, {
            method: 'PUT',
            body: JSON.stringify(user)
        });
    }
}
'''
    }
    
    # 3. Analyze each file
    print("\n📊 Code Analysis Results:")
    print("-" * 30)
    
    for file_path, content in sample_files.items():
        print(f"\n🔍 Analyzing: {file_path}")
        
        try:
            # Analyze the file
            result = await sdk.analyze_file(file_path, content)
            
            print(f"  📈 Confidence Score: {result.confidence_score:.2f}")
            print(f"  🐛 Issues Found: {len(result.issues)}")
            print(f"  💡 Suggestions: {len(result.suggestions)}")
            
            # Show top issues
            if result.issues:
                print("  🔴 Top Issues:")
                for issue in result.issues[:2]:  # Show first 2
                    print(f"    - {issue.get('title', 'Unknown')} (Severity: {issue.get('severity', 'unknown')})")
            
            # Show top suggestions
            if result.suggestions:
                print("  💫 Top Suggestions:")
                for suggestion in result.suggestions[:2]:  # Show first 2
                    print(f"    - {suggestion.get('title', 'Unknown')}")
            
        except SDKError as e:
            print(f"  ❌ Analysis failed: {e}")
    
    # 4. Test Generation Example
    print("\n🧪 Test Generation Example:")
    print("-" * 30)
    
    try:
        test_result = await sdk.generate_tests("sample.py", sample_files["sample.py"])
        print(f"✅ Tests generated for sample.py")
        print(f"  📝 Framework: {test_result.get('framework', 'unknown')}")
        print(f"  🎯 Coverage Areas: {', '.join(test_result.get('coverage_areas', []))}")
        print(f"  🔧 Test File: {test_result.get('test_file_path', 'N/A')}")
        
        # Show a snippet of generated test
        if 'test_code' in test_result:
            print("  📄 Generated Test Preview:")
            lines = test_result['test_code'].split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"    {line}")
            if len(test_result['test_code'].split('\n')) > 10:
                print("    ...")
        
    except SDKError as e:
        print(f"❌ Test generation failed: {e}")
    
    # 5. Code Optimization Example
    print("\n⚡ Code Optimization Example:")
    print("-" * 30)
    
    try:
        optimization_result = await sdk.optimize_code("sample.py", sample_files["sample.py"])
        print(f"✅ Optimization suggestions generated")
        
        if 'optimizations' in optimization_result:
            optimizations = optimization_result['optimizations']
            print(f"  🎯 Optimizations Found: {len(optimizations)}")
            
            for opt in optimizations[:2]:  # Show first 2
                print(f"    - {opt.get('title', 'Unknown')}")
                print(f"      Impact: {opt.get('impact', 'unknown')}")
                print(f"      Effort: {opt.get('effort', 'unknown')}")
        
    except SDKError as e:
        print(f"❌ Optimization failed: {e}")
    
    # 6. Interactive Chat Example
    print("\n💬 Interactive Chat Example:")
    print("-" * 30)
    
    chat_questions = [
        "How can I improve the performance of this Python code?",
        "What are the best practices for this React component?",
        "Are there any security issues in this code?"
    ]
    
    for question in chat_questions[:1]:  # Just show one example
        try:
            response = await sdk.chat(question, "sample.py", sample_files["sample.py"])
            print(f"❓ Question: {question}")
            print(f"🤖 Response: {response[:200]}{'...' if len(response) > 200 else ''}")
            break
        except SDKError as e:
            print(f"❌ Chat failed: {e}")
    
    # 7. SDK Statistics
    print("\n📊 SDK Statistics:")
    print("-" * 30)
    
    try:
        stats = await sdk.get_stats()
        print(f"  🔧 Active Agents: {stats.get('active_agents', 0)}")
        print(f"  📈 Total Operations: {stats.get('total_operations', 0)}")
        print(f"  ⏱️  Average Response Time: {stats.get('avg_response_time', 0):.2f}s")
        print(f"  ✅ Success Rate: {stats.get('success_rate', 0):.1%}")
    except Exception as e:
        print(f"❌ Failed to get stats: {e}")
    
    print("\n🎉 Example completed successfully!")
    print("💡 Try running with different file types to see specialized agent behavior")

if __name__ == "__main__":
    # Run the example
    asyncio.run(main()) 