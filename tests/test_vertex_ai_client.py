"""
Unit tests for VertexAIClient
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add the CI Code Companion to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ci_code_companion.vertex_ai_client import VertexAIClient


class TestVertexAIClient:
    """Test cases for VertexAIClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.project_id = "test-project"
        self.location = "us-central1"
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_client_initialization(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test client initialization."""
        # Mock the model instances
        mock_gen_instance = Mock()
        mock_chat_instance = Mock()
        mock_gen_model.from_pretrained.return_value = mock_gen_instance
        mock_chat_model.from_pretrained.return_value = mock_chat_instance
        
        # Initialize client
        client = VertexAIClient(self.project_id, self.location)
        
        # Verify initialization
        assert client.project_id == self.project_id
        assert client.location == self.location
        mock_aiplatform.init.assert_called_once_with(
            project=self.project_id, 
            location=self.location
        )
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_generate_code_success(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test successful code generation."""
        # Mock the model response
        mock_response = Mock()
        mock_response.text = "def hello():\n    return 'Hello, World!'"
        
        mock_gen_instance = Mock()
        mock_gen_instance.predict.return_value = mock_response
        mock_gen_model.from_pretrained.return_value = mock_gen_instance
        mock_chat_model.from_pretrained.return_value = Mock()
        
        # Initialize client and generate code
        client = VertexAIClient(self.project_id, self.location)
        result = client.generate_code("Generate a hello function")
        
        # Verify result
        assert result == "def hello():\n    return 'Hello, World!'"
        mock_gen_instance.predict.assert_called_once()
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_analyze_code_success(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test successful code analysis."""
        # Mock the chat model and session
        mock_response = Mock()
        mock_response.text = "The code looks good but could use better error handling."
        
        mock_session = Mock()
        mock_session.send_message.return_value = mock_response
        
        mock_chat_instance = Mock()
        mock_chat_instance.start_chat.return_value = mock_session
        mock_chat_model.from_pretrained.return_value = mock_chat_instance
        mock_gen_model.from_pretrained.return_value = Mock()
        
        # Initialize client and analyze code
        client = VertexAIClient(self.project_id, self.location)
        result = client.analyze_code("def test(): pass", "review")
        
        # Verify result
        assert "error handling" in result
        mock_chat_instance.start_chat.assert_called_once()
        mock_session.send_message.assert_called_once()
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_generate_unit_tests(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test unit test generation."""
        # Mock the model response
        mock_response = Mock()
        mock_response.text = "def test_add():\n    assert add(2, 3) == 5"
        
        mock_gen_instance = Mock()
        mock_gen_instance.predict.return_value = mock_response
        mock_gen_model.from_pretrained.return_value = mock_gen_instance
        mock_chat_model.from_pretrained.return_value = Mock()
        
        # Initialize client and generate tests
        client = VertexAIClient(self.project_id, self.location)
        result = client.generate_unit_tests("def add(a, b): return a + b")
        
        # Verify result
        assert "test_add" in result
        assert "assert" in result
        mock_gen_instance.predict.assert_called_once()
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_health_check_healthy(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test health check when service is healthy."""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "def hello(): return 'Hello'"
        
        mock_gen_instance = Mock()
        mock_gen_instance.predict.return_value = mock_response
        mock_gen_model.from_pretrained.return_value = mock_gen_instance
        mock_chat_model.from_pretrained.return_value = Mock()
        
        # Initialize client and check health
        client = VertexAIClient(self.project_id, self.location)
        health = client.health_check()
        
        # Verify health status
        assert health['status'] == 'healthy'
        assert health['project_id'] == self.project_id
        assert health['location'] == self.location
        assert 'test_response_length' in health
        assert health['models_available']['code_generation'] is True
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_health_check_unhealthy(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test health check when service is unhealthy."""
        # Mock exception during health check
        mock_gen_instance = Mock()
        mock_gen_instance.predict.side_effect = Exception("API Error")
        mock_gen_model.from_pretrained.return_value = mock_gen_instance
        mock_chat_model.from_pretrained.return_value = Mock()
        
        # Initialize client and check health
        client = VertexAIClient(self.project_id, self.location)
        health = client.health_check()
        
        # Verify unhealthy status
        assert health['status'] == 'unhealthy'
        assert 'error' in health
        assert health['project_id'] == self.project_id
    
    def test_initialization_without_project_id(self):
        """Test that initialization fails without project ID."""
        with pytest.raises(Exception):
            # This should fail because aiplatform.init will be called
            # In real usage, this would be caught by the aiplatform library
            pass
    
    @patch.dict(os.environ, {'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/creds.json'})
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_initialization_with_credentials_path(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test initialization with credentials path."""
        mock_gen_model.from_pretrained.return_value = Mock()
        mock_chat_model.from_pretrained.return_value = Mock()
        
        # Initialize with credentials path
        client = VertexAIClient(
            self.project_id, 
            self.location, 
            credentials_path="/path/to/service-account.json"
        )
        
        # Verify environment variable was set
        assert os.environ['GOOGLE_APPLICATION_CREDENTIALS'] == "/path/to/service-account.json"
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_generate_code_with_parameters(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test code generation with custom parameters."""
        mock_response = Mock()
        mock_response.text = "generated code"
        
        mock_gen_instance = Mock()
        mock_gen_instance.predict.return_value = mock_response
        mock_gen_model.from_pretrained.return_value = mock_gen_instance
        mock_chat_model.from_pretrained.return_value = Mock()
        
        # Initialize client
        client = VertexAIClient(self.project_id, self.location)
        
        # Generate code with custom parameters
        result = client.generate_code(
            prompt="test prompt",
            max_output_tokens=512,
            temperature=0.5,
            candidate_count=2
        )
        
        # Verify the predict method was called with correct parameters
        mock_gen_instance.predict.assert_called_once_with(
            prompt="test prompt",
            max_output_tokens=512,
            temperature=0.5,
            candidate_count=2
        )
        assert result == "generated code"
    
    @patch('src.ci_code_companion.vertex_ai_client.aiplatform')
    @patch('src.ci_code_companion.vertex_ai_client.CodeGenerationModel')
    @patch('src.ci_code_companion.vertex_ai_client.CodeChatModel')
    def test_analyze_code_different_types(self, mock_chat_model, mock_gen_model, mock_aiplatform):
        """Test different analysis types."""
        mock_response = Mock()
        mock_response.text = "Analysis result"
        
        mock_session = Mock()
        mock_session.send_message.return_value = mock_response
        
        mock_chat_instance = Mock()
        mock_chat_instance.start_chat.return_value = mock_session
        mock_chat_model.from_pretrained.return_value = mock_chat_instance
        mock_gen_model.from_pretrained.return_value = Mock()
        
        client = VertexAIClient(self.project_id, self.location)
        
        # Test different analysis types
        for analysis_type in ["review", "security", "performance"]:
            result = client.analyze_code("test code", analysis_type)
            assert result == "Analysis result"
            
        # Verify calls were made
        assert mock_session.send_message.call_count == 3 