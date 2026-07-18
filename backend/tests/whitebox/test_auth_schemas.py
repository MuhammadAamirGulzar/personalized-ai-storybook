"""
Unit tests for auth/schemas.py module
Tests Pydantic validation for user registration and login
"""

import pytest
from pydantic import ValidationError
from backend.auth.schemas import UserCreate, UserLogin, UserResponse


# ============================================================================
# TEST: UserCreate - Valid Data
# ============================================================================

@pytest.mark.unit
class TestUserCreateValid:
    """Test UserCreate with valid data"""
    
    def test_valid_user_creation(self):
        """Should accept valid user data"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "password123"
        }
        
        user = UserCreate(**user_data)
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password == "password123"
    
    def test_valid_long_username(self):
        """Should accept username at maximum length"""
        user_data = {
            "email": "test@example.com",
            "username": "a" * 50,  # Max 50 chars
            "password": "password123"
        }
        
        user = UserCreate(**user_data)
        assert len(user.username) == 50
    
    def test_valid_long_password(self):
        """Should accept password at maximum length"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "a" * 72  # Max 72 bytes
        }
        
        user = UserCreate(**user_data)
        assert len(user.password) == 72


# ============================================================================
# TEST: UserCreate - Password Validation
# ============================================================================

@pytest.mark.unit
class TestPasswordValidation:
    """Test password validation rules"""
    
    def test_password_too_short(self):
        """Should reject password less than 6 characters"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "pass1"  # Only 5 chars
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("at least 6 characters" in str(error) for error in errors)
    
    def test_password_minimum_valid(self):
        """Should accept password with exactly 6 characters"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "pass12"  # Exactly 6 chars
        }
        
        user = UserCreate(**user_data)
        assert len(user.password) == 6
    
    def test_password_too_long(self):
        """Should reject password longer than 72 bytes"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "a" * 73  # 73 bytes
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("too long" in str(error).lower() for error in errors)
    
    def test_password_with_special_characters(self):
        """Should accept password with special characters"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "P@ssw0rd!#$"
        }
        
        user = UserCreate(**user_data)
        assert user.password == "P@ssw0rd!#$"


# ============================================================================
# TEST: UserCreate - Username Validation
# ============================================================================

@pytest.mark.unit
class TestUsernameValidation:
    """Test username validation rules"""
    
    def test_username_too_short(self):
        """Should reject username less than 3 characters"""
        user_data = {
            "email": "test@example.com",
            "username": "ab",  # Only 2 chars
            "password": "password123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("at least 3 characters" in str(error) for error in errors)
    
    def test_username_minimum_valid(self):
        """Should accept username with exactly 3 characters"""
        user_data = {
            "email": "test@example.com",
            "username": "abc",  # Exactly 3 chars
            "password": "password123"
        }
        
        user = UserCreate(**user_data)
        assert len(user.username) == 3
    
    def test_username_too_long(self):
        """Should reject username longer than 50 characters"""
        user_data = {
            "email": "test@example.com",
            "username": "a" * 51,  # 51 chars
            "password": "password123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("less than 50 characters" in str(error) for error in errors)
    
    def test_username_with_underscore(self):
        """Should accept username with underscores"""
        user_data = {
            "email": "test@example.com",
            "username": "test_user_123",
            "password": "password123"
        }
        
        user = UserCreate(**user_data)
        assert user.username == "test_user_123"


# ============================================================================
# TEST: UserCreate - Email Validation
# ============================================================================

@pytest.mark.unit
class TestEmailValidation:
    """Test email validation rules"""
    
    def test_valid_email(self):
        """Should accept valid email format"""
        valid_emails = [
            "user@example.com",
            "test.user@example.co.uk",
            "user+tag@example.com",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            user_data = {
                "email": email,
                "username": "testuser",
                "password": "password123"
            }
            user = UserCreate(**user_data)
            assert user.email == email
    
    def test_invalid_email_no_at(self):
        """Should reject email without @ symbol"""
        user_data = {
            "email": "userexample.com",
            "username": "testuser",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            UserCreate(**user_data)
        
        errors = exc_info.value.errors()
        assert any("email" in str(error).lower() for error in errors)
    
    def test_invalid_email_no_domain(self):
        """Should reject email without domain"""
        user_data = {
            "email": "user@",
            "username": "testuser",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_invalid_email_no_local_part(self):
        """Should reject email without local part"""
        user_data = {
            "email": "@example.com",
            "username": "testuser",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_empty_email(self):
        """Should reject empty email"""
        user_data = {
            "email": "",
            "username": "testuser",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)


# ============================================================================
# TEST: UserLogin Schema
# ============================================================================

@pytest.mark.unit
class TestUserLogin:
    """Test UserLogin schema"""
    
    def test_valid_login_data(self):
        """Should accept valid login credentials"""
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        
        user_login = UserLogin(**login_data)
        assert user_login.email == "test@example.com"
        assert user_login.password == "password123"
    
    def test_login_invalid_email(self):
        """Should reject invalid email in login"""
        login_data = {
            "email": "invalid-email",
            "password": "password123"
        }
        
        with pytest.raises(ValidationError):
            UserLogin(**login_data)
    
    def test_login_missing_password(self):
        """Should reject login without password"""
        login_data = {
            "email": "test@example.com"
        }
        
        with pytest.raises(ValidationError):
            UserLogin(**login_data)


# ============================================================================
# TEST: UserResponse Schema
# ============================================================================

@pytest.mark.unit
class TestUserResponse:
    """Test UserResponse schema"""
    
    def test_user_response_creation(self):
        """Should create UserResponse with valid data"""
        response_data = {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "is_active": True
        }
        
        user_response = UserResponse(**response_data)
        assert user_response.id == 1
        assert user_response.email == "test@example.com"
        assert user_response.username == "testuser"
        assert user_response.is_active == True


# ============================================================================
# TEST: Boundary Value Analysis
# ============================================================================

@pytest.mark.unit
class TestBoundaryValues:
    """Test boundary values for validation"""
    
    def test_username_boundary_below_min(self):
        """BVA: Username with 2 chars (below minimum)"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="ab",
                password="password123"
            )
    
    def test_username_boundary_at_min(self):
        """BVA: Username with 3 chars (at minimum)"""
        user = UserCreate(
            email="test@example.com",
            username="abc",
            password="password123"
        )
        assert len(user.username) == 3
    
    def test_username_boundary_above_min(self):
        """BVA: Username with 4 chars (above minimum)"""
        user = UserCreate(
            email="test@example.com",
            username="abcd",
            password="password123"
        )
        assert len(user.username) == 4
    
    def test_username_boundary_below_max(self):
        """BVA: Username with 49 chars (below maximum)"""
        user = UserCreate(
            email="test@example.com",
            username="a" * 49,
            password="password123"
        )
        assert len(user.username) == 49
    
    def test_username_boundary_at_max(self):
        """BVA: Username with 50 chars (at maximum)"""
        user = UserCreate(
            email="test@example.com",
            username="a" * 50,
            password="password123"
        )
        assert len(user.username) == 50
    
    def test_username_boundary_above_max(self):
        """BVA: Username with 51 chars (above maximum)"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="a" * 51,
                password="password123"
            )
    
    def test_password_boundary_below_min(self):
        """BVA: Password with 5 chars (below minimum)"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="pass1"
            )
    
    def test_password_boundary_at_min(self):
        """BVA: Password with 6 chars (at minimum)"""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="pass12"
        )
        assert len(user.password) == 6
    
    def test_password_boundary_above_min(self):
        """BVA: Password with 7 chars (above minimum)"""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="pass123"
        )
        assert len(user.password) == 7
    
    def test_password_boundary_at_max(self):
        """BVA: Password with 72 bytes (at maximum)"""
        user = UserCreate(
            email="test@example.com",
            username="testuser",
            password="a" * 72
        )
        assert len(user.password.encode('utf-8')) == 72
    
    def test_password_boundary_above_max(self):
        """BVA: Password with 73 bytes (above maximum)"""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                username="testuser",
                password="a" * 73
            )
