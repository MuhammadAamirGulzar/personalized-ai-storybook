"""
Unit tests for authentication API routes
Tests registration, login, and user info endpoints
"""

import pytest
from fastapi import status


# ============================================================================
# TEST: User Registration
# ============================================================================

@pytest.mark.unit
class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_success(self, client, db_session):
        """Should successfully register a new user"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"
        assert "hashed_password" not in data["user"]  # Password should not be exposed
    
    def test_register_duplicate_email(self, client, test_user):
        """Should reject registration with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "testuser@example.com",  # Already exists
                "username": "differentuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email already registered" in response.json()["detail"].lower()
    
    def test_register_duplicate_username(self, client, test_user):
        """Should reject registration with duplicate username"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",  # Already exists
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "username already taken" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Should reject registration with invalid email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "testuser",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_short_password(self, client):
        """Should reject registration with password < 6 chars"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "pass1"  # Only 5 chars
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_register_short_username(self, client):
        """Should reject registration with username < 3 chars"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@example.com",
                "username": "ab",  # Only 2 chars
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# TEST: User Login
# ============================================================================

@pytest.mark.unit
class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, client, test_user):
        """Should successfully login with correct credentials"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "testpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == "testuser@example.com"
    
    def test_login_wrong_password(self, client, test_user):
        """Should reject login with incorrect password"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "incorrect email or password" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Should reject login for non-existent user"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_invalid_email_format(self, client):
        """Should reject login with invalid email format"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "invalid-email",
                "password": "password123"
            }
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# TEST: Get Current User
# ============================================================================

@pytest.mark.unit
class TestGetCurrentUser:
    """Test get current user endpoint"""
    
    def test_get_current_user_success(self, client, auth_headers):
        """Should return current user info with valid token"""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["username"] == "testuser"
        assert data["is_active"] == True
    
    def test_get_current_user_no_token(self, client):
        """Should reject request without authentication token"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_current_user_invalid_token(self, client):
        """Should reject request with invalid token"""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# TEST: Token Validation
# ============================================================================

@pytest.mark.unit
class TestTokenValidation:
    """Test JWT token validation"""
    
    def test_token_can_access_protected_endpoint(self, client, auth_headers):
        """Should be able to access protected endpoints with valid token"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
    
    def test_token_format(self, client, test_user):
        """Should return token in correct format"""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "testuser@example.com",
                "password": "testpassword123"
            }
        )
        
        data = response.json()
        assert "access_token" in data
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["token_type"] == "bearer"


# ============================================================================
# TEST: Integration Scenarios
# ============================================================================

@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flows"""
    
    def test_full_registration_and_login_flow(self, client):
        """Test complete flow: register -> login -> access protected endpoint"""
        # Step 1: Register
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": "flowtest@example.com",
                "username": "flowtest",
                "password": "password123"
            }
        )
        assert register_response.status_code == status.HTTP_201_CREATED
        register_token = register_response.json()["access_token"]
        
        # Step 2: Use registration token to access protected endpoint
        me_response_1 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {register_token}"}
        )
        assert me_response_1.status_code == status.HTTP_200_OK
        assert me_response_1.json()["email"] == "flowtest@example.com"
        
        # Step 3: Login with same credentials
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "flowtest@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        login_token = login_response.json()["access_token"]
        
        # Step 4: Use login token to access protected endpoint
        me_response_2 = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {login_token}"}
        )
        assert me_response_2.status_code == status.HTTP_200_OK
        assert me_response_2.json()["email"] == "flowtest@example.com"
    
    def test_cannot_register_twice_with_same_email(self, client):
        """Should prevent duplicate registration"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "password123"
        }
        
        # First registration
        response1 = client.post("/api/auth/register", json=user_data)
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second registration with same email
        user_data["username"] = "user2"  # Different username
        response2 = client.post("/api/auth/register", json=user_data)
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
