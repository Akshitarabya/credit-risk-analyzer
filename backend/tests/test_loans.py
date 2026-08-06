def _register(client, email, role="applicant"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test User",
            "email": email,
            "password": "StrongPass123",
            "role": role,
        },
    )
    return response.json()["access_token"]


VALID_APPLICATION = {
    "full_name": "Jordan Rivera",
    "date_of_birth": "1995-04-12",
    "annual_income": 68000,
    "employment_status": "employed",
    "existing_debt": 5000,
    "credit_history_years": 6,
    "loan_amount": 15000,
    "loan_purpose": "auto",
    "loan_tenure_months": 48,
}


def test_submit_loan_application_creates_profile_and_loan(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/v1/loans", json=VALID_APPLICATION, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["loan_amount"] == 15000
    assert body["loan_purpose"] == "auto"
    assert body["status"] == "submitted"

    profile_response = client.get("/api/v1/applicants/me", headers=headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["full_name"] == "Jordan Rivera"


def test_submit_rejects_non_positive_loan_amount(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {**VALID_APPLICATION, "loan_amount": 0}

    response = client.post("/api/v1/loans", json=payload, headers=headers)
    assert response.status_code == 422


def test_list_my_applications_returns_only_own(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")

    client.post(
        "/api/v1/loans", json=VALID_APPLICATION, headers={"Authorization": f"Bearer {token_a}"}
    )
    client.post(
        "/api/v1/loans", json=VALID_APPLICATION, headers={"Authorization": f"Bearer {token_b}"}
    )

    response = client.get("/api/v1/loans/me", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_submitting_twice_creates_two_applications_for_same_applicant(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/loans", json=VALID_APPLICATION, headers=headers)
    second_payload = {**VALID_APPLICATION, "loan_amount": 5000, "loan_purpose": "personal"}
    client.post("/api/v1/loans", json=second_payload, headers=headers)

    response = client.get("/api/v1/loans/me", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_owner_can_view_own_application_detail(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/loans", json=VALID_APPLICATION, headers=headers).json()

    response = client.get(f"/api/v1/loans/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["applicant"]["full_name"] == "Jordan Rivera"


def test_other_applicant_cannot_view_someone_elses_application(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")

    created = client.post(
        "/api/v1/loans", json=VALID_APPLICATION, headers={"Authorization": f"Bearer {token_a}"}
    ).json()

    response = client.get(
        f"/api/v1/loans/{created['id']}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert response.status_code == 403


def test_viewing_nonexistent_application_returns_404(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert response.status_code == 404


def test_staff_can_view_any_application(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")

    created = client.post(
        "/api/v1/loans",
        json=VALID_APPLICATION,
        headers={"Authorization": f"Bearer {applicant_token}"},
    ).json()

    response = client.get(
        f"/api/v1/loans/{created['id']}", headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 200


def test_staff_can_list_all_applications(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")

    client.post(
        "/api/v1/loans",
        json=VALID_APPLICATION,
        headers={"Authorization": f"Bearer {applicant_token}"},
    )

    response = client.get("/api/v1/loans", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_applicant_cannot_list_all_applications(client):
    applicant_token = _register(client, "jordan@example.com")
    response = client.get(
        "/api/v1/loans", headers={"Authorization": f"Bearer {applicant_token}"}
    )
    assert response.status_code == 403


def test_staff_cannot_submit_loan_applications(client):
    staff_token = _register(client, "alex@bank.com", role="staff")
    response = client.post(
        "/api/v1/loans", json=VALID_APPLICATION, headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert response.status_code == 403


def test_submit_requires_authentication(client):
    response = client.post("/api/v1/loans", json=VALID_APPLICATION)
    assert response.status_code == 401