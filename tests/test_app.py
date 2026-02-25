import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    """Test the home endpoint returns 200 and correct keys"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data


def test_health_endpoint(client):
    """Test health check returns healthy status"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_info_endpoint(client):
    """Test info endpoint returns app metadata"""
    response = client.get('/info')
    assert response.status_code == 200
    data = response.get_json()
    assert "app" in data
    assert "description" in data


def test_invalid_route(client):
    """Test that unknown routes return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
