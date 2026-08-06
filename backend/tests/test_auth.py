def test_register_creates_account_and_returns_token(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jordan Rivera",
            "email": "jordan@example.com",
            "password": "StrongPass123",
            "role": "applicant",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "jordan@example.com"
    assert body["user"]["role"] == "applicant"


def test_register_rejects_duplicate_email(client):
    payload = {
        "full_name": "Jordan Rivera",
        "email": "jordan@example.com",
        "password": "StrongPass123",
        "role": "applicant",
    }
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_with_correct_credentials_succeeds(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jordan Rivera",
            "email": "jordan@example.com",
            "password": "StrongPass123",
            "role": "applicant",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jordan@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_fails(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jordan Rivera",
            "email": "jordan@example.com",
            "password": "StrongPass123",
            "role": "applicant",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "jordan@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


def test_me_endpoint_requires_valid_token(client):
    no_token_response = client.get("/api/v1/auth/me")
    assert no_token_response.status_code == 401

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jordan Rivera",
            "email": "jordan@example.com",
            "password": "StrongPass123",
            "role": "applicant",
        },
    )
    token = register_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "jordan@example.com"


def test_staff_registration_gets_staff_role(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Alex Chen",
            "email": "alex@bank.com",
            "password": "StrongPass123",
            "role": "staff",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "staff"
