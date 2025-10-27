"""
Unit tests for security module.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import os

from src.core.security import (
    InputValidator, 
    RateLimiter, 
    SecretsManager, 
    SecurityError,
    SecurityMiddleware
)


class TestInputValidator:
    """Test input validation."""
    
    def test_validate_file_path_valid(self):
        """Test valid file path validation."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'test content')
            tmp_path = tmp.name
        
        try:
            validator = InputValidator()
            result = validator.validate_file_path(tmp_path)
            assert isinstance(result, Path)
            assert result.exists()
        finally:
            os.unlink(tmp_path)
    
    def test_validate_file_path_nonexistent(self):
        """Test validation of non-existent file."""
        validator = InputValidator()
        with pytest.raises(SecurityError, match="File not found"):
            validator.validate_file_path("/nonexistent/file.pdf")
    
    def test_validate_file_path_too_large(self):
        """Test validation of oversized file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            # Create a large file (simulate)
            tmp.write(b'x' * (InputValidator.MAX_FILE_SIZE + 1))
            tmp_path = tmp.name
        
        try:
            validator = InputValidator()
            with pytest.raises(SecurityError, match="File too large"):
                validator.validate_file_path(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_file_path_invalid_extension(self):
        """Test validation of invalid file extension."""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as tmp:
            tmp.write(b'test content')
            tmp_path = tmp.name
        
        try:
            validator = InputValidator()
            with pytest.raises(SecurityError, match="Invalid file type"):
                validator.validate_file_path(tmp_path)
        finally:
            os.unlink(tmp_path)
    
    def test_validate_text_input_valid(self):
        """Test valid text input validation."""
        validator = InputValidator()
        result = validator.validate_text_input("Valid text input")
        assert result == "Valid text input"
    
    def test_validate_text_input_too_long(self):
        """Test validation of text that's too long."""
        validator = InputValidator()
        long_text = "x" * (InputValidator.MAX_TEXT_LENGTH + 1)
        with pytest.raises(SecurityError, match="too long"):
            validator.validate_text_input(long_text)
    
    def test_validate_text_input_sql_injection(self):
        """Test detection of SQL injection attempts."""
        validator = InputValidator()
        with pytest.raises(SecurityError, match="SQL injection"):
            validator.validate_text_input("'; DROP TABLE users; --")
    
    def test_validate_text_input_xss(self):
        """Test detection of XSS attempts."""
        validator = InputValidator()
        with pytest.raises(SecurityError, match="XSS"):
            validator.validate_text_input("<script>alert('xss')</script>")
    
    def test_validate_email_valid(self):
        """Test valid email validation."""
        validator = InputValidator()
        result = validator.validate_email("test@example.com")
        assert result == "test@example.com"
    
    def test_validate_email_invalid(self):
        """Test invalid email validation."""
        validator = InputValidator()
        with pytest.raises(SecurityError, match="Invalid email format"):
            validator.validate_email("invalid-email")
    
    def test_validate_nit_valid(self):
        """Test valid NIT validation."""
        validator = InputValidator()
        result = validator.validate_nit("12345678-9")
        assert result == "12345678-9"
    
    def test_validate_nit_invalid(self):
        """Test invalid NIT validation."""
        validator = InputValidator()
        with pytest.raises(SecurityError, match="Invalid NIT format"):
            validator.validate_nit("invalid-nit")


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @patch('redis.Redis')
    def test_rate_limiter_allowed(self, mock_redis):
        """Test rate limiter when request is allowed."""
        mock_redis_client = Mock()
        mock_redis_client.pipeline.return_value.__enter__.return_value.execute.return_value = [0, 5]
        mock_redis.return_value = mock_redis_client
        
        rate_limiter = RateLimiter(mock_redis_client, default_limit=100)
        is_allowed, rate_info = rate_limiter.is_allowed("test_key")
        
        assert is_allowed is True
        assert rate_info["limit"] == 100
        assert rate_info["remaining"] == 94  # 100 - 5 - 1
    
    @patch('redis.Redis')
    def test_rate_limiter_exceeded(self, mock_redis):
        """Test rate limiter when limit is exceeded."""
        mock_redis_client = Mock()
        mock_redis_client.pipeline.return_value.__enter__.return_value.execute.return_value = [0, 100]
        mock_redis.return_value = mock_redis_client
        
        rate_limiter = RateLimiter(mock_redis_client, default_limit=100)
        is_allowed, rate_info = rate_limiter.is_allowed("test_key")
        
        assert is_allowed is False
        assert rate_info["limit"] == 100
        assert rate_info["remaining"] == 0


class TestSecretsManager:
    """Test secrets management."""
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        secrets_manager = SecretsManager("test_master_key")
        
        original_data = "sensitive_data"
        encrypted = secrets_manager.encrypt(original_data)
        decrypted = secrets_manager.decrypt(encrypted)
        
        assert decrypted == original_data
        assert encrypted != original_data
    
    def test_hash_password(self):
        """Test password hashing."""
        secrets_manager = SecretsManager("test_master_key")
        
        password = "test_password"
        hashed = secrets_manager.hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        secrets_manager = SecretsManager("test_master_key")
        
        password = "test_password"
        hashed = secrets_manager.hash_password(password)
        
        assert secrets_manager.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        secrets_manager = SecretsManager("test_master_key")
        
        password = "test_password"
        wrong_password = "wrong_password"
        hashed = secrets_manager.hash_password(password)
        
        assert secrets_manager.verify_password(wrong_password, hashed) is False


class TestSecurityMiddleware:
    """Test security middleware."""
    
    @patch('src.core.security.RateLimiter')
    @patch('src.core.security.InputValidator')
    def test_validate_request_success(self, mock_validator, mock_rate_limiter):
        """Test successful request validation."""
        mock_validator_instance = Mock()
        mock_validator_instance.validate_file_path.return_value = Path("/valid/path.pdf")
        mock_validator.return_value = mock_validator_instance
        
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.is_allowed.return_value = (True, {"limit": 100, "remaining": 99})
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        middleware = SecurityMiddleware(mock_rate_limiter_instance, mock_validator_instance)
        result = middleware.validate_request("/valid/path.pdf", "user123")
        
        assert result["validated"] is True
        assert result["file_path"] == "/valid/path.pdf"
        assert "rate_info" in result
    
    @patch('src.core.security.RateLimiter')
    @patch('src.core.security.InputValidator')
    def test_validate_request_rate_limited(self, mock_validator, mock_rate_limiter):
        """Test request validation when rate limited."""
        mock_validator_instance = Mock()
        mock_validator.return_value = mock_validator_instance
        
        mock_rate_limiter_instance = Mock()
        mock_rate_limiter_instance.is_allowed.return_value = (False, {"limit": 100, "remaining": 0})
        mock_rate_limiter.return_value = mock_rate_limiter_instance
        
        middleware = SecurityMiddleware(mock_rate_limiter_instance, mock_validator_instance)
        
        with pytest.raises(SecurityError, match="Rate limit exceeded"):
            middleware.validate_request("/valid/path.pdf", "user123")

