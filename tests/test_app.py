import pytest
from app import app, db
from flask import json

@pytest.fixture
def test_client():
    """
    Provides a test client with an in-memory SQLite database for isolated testing.
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def register_user(client, username, password):
    """
    Registers a new user.
    """
    return client.post('/register', json={
        'username': username,
        'password': password
    })

def login_user(client, username, password):
    """
    Logs in a user and returns the success status and authentication cookie.
    """
    response = client.post('/login', json={
        'username': username,
        'password': password
    })
    return response.json.get('message') == "Login successful", response.headers.get('Set-Cookie')

def test_register_and_login(test_client):
    """
    Tests user registration and login functionality.
    """
    # Test user registration
    response = register_user(test_client, 'testuser', 'testpassword')
    assert response.status_code == 201

    # Test login
    success, cookie = login_user(test_client, 'testuser', 'testpassword')
    assert success
    assert cookie is not None

def test_create_lead(test_client):
    """
    Tests creating a new lead.
    """
    # Register and login a user
    register_user(test_client, 'testuser', 'testpassword')
    _, cookie = login_user(test_client, 'testuser', 'testpassword')

    # Create a lead
    response = test_client.post('/api/leads', json={
        'name': 'Test Lead',
        'email': 'test@example.com',
        'phone': '1234567890',
        'score': 0.95,
        'status': 'New'
    }, headers={'Cookie': cookie})
    assert response.status_code == 201
    assert response.json.get('message') == "Lead created successfully"

def test_get_leads(test_client):
    """
    Tests retrieving all leads.
    """
    # Register and login a user
    register_user(test_client, 'testuser', 'testpassword')
    _, cookie = login_user(test_client, 'testuser', 'testpassword')

    # Add a lead
    test_client.post('/api/leads', json={
        'name': 'Test Lead',
        'email': 'test@example.com',
        'phone': '1234567890',
        'score': 0.95,
        'status': 'New'
    }, headers={'Cookie': cookie})

    # Fetch all leads
    response = test_client.get('/api/leads', headers={'Cookie': cookie})
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['name'] == 'Test Lead'

def test_update_lead(test_client):
    """
    Tests updating a lead.
    """
    # Register and login a user
    register_user(test_client, 'testuser', 'testpassword')
    _, cookie = login_user(test_client, 'testuser', 'testpassword')

    # Add a lead
    test_client.post('/api/leads', json={
        'name': 'Test Lead',
        'email': 'test@example.com',
        'phone': '1234567890',
        'score': 0.95,
        'status': 'New'
    }, headers={'Cookie': cookie})

    # Update the lead
    response = test_client.put('/api/leads/1', json={
        'name': 'Updated Lead',
        'email': 'updated@example.com',
        'phone': '0987654321',
        'score': 0.90,
        'status': 'Contacted'
    }, headers={'Cookie': cookie})
    assert response.status_code == 200
    assert response.json.get('message') == "Lead updated successfully"

def test_delete_lead(test_client):
    """
    Tests deleting a lead.
    """
    # Register and login a user
    register_user(test_client, 'testuser', 'testpassword')
    _, cookie = login_user(test_client, 'testuser', 'testpassword')

    # Add a lead
    test_client.post('/api/leads', json={
        'name': 'Test Lead',
        'email': 'test@example.com',
        'phone': '1234567890',
        'score': 0.95,
        'status': 'New'
    }, headers={'Cookie': cookie})

    # Delete the lead
    response = test_client.delete('/api/leads/1', headers={'Cookie': cookie})
    assert response.status_code == 200
    assert response.json.get('message') == "Lead deleted successfully"

def test_unauthorized_access(test_client):
    """
    Tests unauthorized access to protected endpoints.
    """
    # Attempt to access leads without logging in
    response = test_client.get('/api/leads')
    assert response.status_code == 401
    assert response.json.get('error') == "Unauthorized"

