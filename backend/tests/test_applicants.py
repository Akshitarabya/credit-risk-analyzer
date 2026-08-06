def _register_applicant(client, email="jordan@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Jordan Rivera",
            "email": email,
            "password": "StrongPass123",
            "role": "applicant",
        },
    )
    return response.json()["access_token"]


VALID_PROFILE = {
    "full_name": "Jordan Rivera",
    "date_of_birth": "1995-04-12",
    "annual_income": 68000,
    "employment_status": "employed",
    "existing_debt": 5000,
    "credit_history_years": 6,
}


def test_get_profile_before_creation_returns_404(client):
    token = _register_applicant(client)
    response = client.get("/api/v1/applicants/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404


def test_patch_creates_then_get_returns_profile(client):
    token = _register_applicant(client)
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.patch("/api/v1/applicants/me", json=VALID_PROFILE, headers=headers)
    assert create_response.status_code == 200
    assert create_response.json()["full_name"] == "Jordan Rivera"
    assert create_response.json()["annual_income"] == 68000

    get_response = client.get("/api/v1/applicants/me", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["employment_status"] == "employed"


def test_patch_updates_existing_profile_in_place(client):
    token = _register_applicant(client)
    headers = {"Authorization": f"Bearer {token}"}

    client.patch("/api/v1/applicants/me", json=VALID_PROFILE, headers=headers)
    updated_payload = {**VALID_PROFILE, "annual_income": 90000}
    response = client.patch("/api/v1/applicants/me", json=updated_payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["annual_income"] == 90000


def test_profile_rejects_applicant_under_18(client):
    token = _register_applicant(client)
    headers = {"Authorization": f"Bearer {token}"}
    underage_payload = {**VALID_PROFILE, "date_of_birth": "2015-01-01"}

    response = client.patch("/api/v1/applicants/me", json=underage_payload, headers=headers)
    assert response.status_code == 422


def test_staff_cannot_access_applicant_profile_endpoint(client):
    staff_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Alex Chen",
            "email": "alex@bank.com",
            "password": "StrongPass123",
            "role": "staff",
        },
    )
    token = staff_response.json()["access_token"]
    response = client.get(
        "/api/v1/applicants/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


def test_profile_endpoint_requires_auth(client):
    response = client.get("/api/v1/applicants/me")
    assert response.status_code == 401
