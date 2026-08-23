def test_register_patient(client):
    response = client.post("/api/v1/auth/register", json={
        "email": "newpatient@test.com",
        "password": "Password123!",
        "role": "PATIENT",
        "name": "Jane Patient"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["email"] == "newpatient@test.com"

def test_register_duplicate_email(client, test_patient_user):
    response = client.post("/api/v1/auth/register", json={
        "email": "patient@test.com",
        "password": "Password123!",
        "role": "PATIENT",
        "name": "Duplicate User"
    })
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "EMAIL_EXISTS"

def test_login_success(client, test_patient_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "patient@test.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]

def test_login_invalid_password(client, test_patient_user):
    response = client.post("/api/v1/auth/login", json={
        "email": "patient@test.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
