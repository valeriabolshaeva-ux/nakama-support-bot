"""
Health Check Endpoint Tests.

Tests for the /health endpoint.
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check_returns_200(self, client: TestClient) -> None:
        """
        Test that health check returns 200 OK.
        
        The /health endpoint should always return a successful response
        when the application is running.
        """
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_check_returns_healthy_status(self, client: TestClient) -> None:
        """
        Test that health check returns healthy status.
        
        The response should include a 'status' field with value 'healthy'.
        """
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_check_includes_environment(self, client: TestClient) -> None:
        """
        Test that health check includes environment info.
        
        The response should include 'environment' and 'debug' fields.
        """
        response = client.get("/health")
        data = response.json()
        
        assert "environment" in data
        assert "debug" in data
    
    def test_root_endpoint_returns_200(self, client: TestClient) -> None:
        """
        Test that root endpoint returns 200 OK.
        """
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_endpoint_returns_welcome_message(self, client: TestClient) -> None:
        """
        Test that root endpoint returns welcome message.
        """
        response = client.get("/")
        data = response.json()
        
        assert "message" in data
        assert "Welcome" in data["message"]
