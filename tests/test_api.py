import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User, Lead, WorkflowRun

@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test public API root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Enterprise Sales Intelligence Platform API is active."}

@pytest.mark.asyncio
async def test_auth_registration_and_login(client: AsyncClient, db_session: AsyncSession):
    """Test user registration, login, and JWT retrieval."""
    # 1. Register User
    reg_payload = {
        "email": "agent@acme.com",
        "password": "strong_password_123",
        "role": "representative"
    }
    response = await client.post("/api/auth/register", json=reg_payload)
    assert response.status_code == 201
    user_data = response.json()
    assert user_data["email"] == "agent@acme.com"
    assert user_data["role"] == "representative"

    # 2. Login User
    login_data = {
        "username": "agent@acme.com",
        "password": "strong_password_123"
    }
    login_response = await client.post("/api/auth/login", data=login_data)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_rbac_and_lead_search_unauthorized(client: AsyncClient):
    """Test that unauthorized users or users with incorrect roles are blocked."""
    search_payload = {
        "target_criteria": {"industry": "Robotics"}
    }
    # Unauthenticated
    response = await client.post("/api/lead-search", json=search_payload)
    assert response.status_code == 401

    # Authenticate as representative (which does NOT have manager/admin access to trigger search)
    reg_payload = {
        "email": "rep@acme.com",
        "password": "rep_password_123",
        "role": "representative"
    }
    await client.post("/api/auth/register", json=reg_payload)
    login_response = await client.post("/api/auth/login", data={"username": "rep@acme.com", "password": "rep_password_123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Representative role must receive 403 Forbidden
    forbidden_response = await client.post("/api/lead-search", json=search_payload, headers=headers)
    assert forbidden_response.status_code == 403

@pytest.mark.asyncio
async def test_manager_lead_search_authorized(client: AsyncClient, db_session: AsyncSession):
    """Test that a Manager role user can trigger a lead search workflow."""
    # Register and Login as Manager
    reg_payload = {
        "email": "manager@acme.com",
        "password": "manager_password_123",
        "role": "manager"
    }
    await client.post("/api/auth/register", json=reg_payload)
    login_response = await client.post("/api/auth/login", data={"username": "manager@acme.com", "password": "manager_password_123"})
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    search_payload = {
        "target_criteria": {"industry": "Robotics"}
    }
    response = await client.post("/api/lead-search", json=search_payload, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert "workflow_run_id" in res_data
    assert res_data["status"] == "RUNNING"
