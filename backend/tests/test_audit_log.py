def _register(client, email, role="applicant"):
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Test User", "email": email, "password": "StrongPass123", "role": role},
    )
    return response.json()["access_token"]


VALID_APPLICATION = {
    "full_name": "Jordan Rivera",
    "date_of_birth": "1990-01-01",
    "annual_income": 80000,
    "existing_debt": 3000,
    "employment_status": "employed",
    "credit_history_years": 8,
    "loan_amount": 10000,
    "loan_purpose": "auto",
    "loan_tenure_months": 36,
}


def _submit(client, headers):
    response = client.post("/api/v1/loans", json=VALID_APPLICATION, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_audit_logs_requires_authentication(client):
    response = client.get("/api/v1/audit-logs")
    assert response.status_code == 401


def test_applicant_cannot_access_audit_logs(client):
    token = _register(client, "jordan@example.com")
    response = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_staff_can_access_audit_logs(client):
    token = _register(client, "alex@bank.com", role="staff")
    response = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_admin_can_access_audit_logs(client):
    token = _register(client, "admin@bank.com", role="admin")
    response = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_loan_submission_creates_audit_log(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit(client, applicant_headers)

    response = client.get(
        "/api/v1/audit-logs", params={"action": "loan_application_submitted"}, headers=staff_headers
    )
    body = response.json()
    assert body["total"] == 1
    entry = body["items"][0]
    assert entry["resource_id"] == loan["id"]
    assert entry["resource_type"] == "loan_application"
    assert entry["actor_name"] == "Test User"
    assert entry["details"]["loan_purpose"] == "auto"


def test_loan_approval_creates_audit_log_with_reviewer(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{loan['id']}/decision", json={"decision": "approved"}, headers=staff_headers
    )

    response = client.get(
        "/api/v1/audit-logs", params={"action": "loan_decision_approved"}, headers=staff_headers
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["resource_id"] == loan["id"]


def test_loan_rejection_creates_audit_log(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{loan['id']}/decision", json={"decision": "rejected"}, headers=staff_headers
    )

    response = client.get(
        "/api/v1/audit-logs", params={"action": "loan_decision_rejected"}, headers=staff_headers
    )
    assert response.json()["total"] == 1


def test_manual_review_creates_audit_log(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit(client, applicant_headers)
    client.patch(
        f"/api/v1/loans/{loan['id']}/decision",
        json={"decision": "manual_review"},
        headers=staff_headers,
    )

    response = client.get(
        "/api/v1/audit-logs", params={"action": "loan_decision_manual_review"}, headers=staff_headers
    )
    assert response.json()["total"] == 1


def test_document_upload_creates_audit_log(client):
    import io

    from PIL import Image, ImageDraw

    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit(client, applicant_headers)

    img = Image.new("RGB", (200, 60), "white")
    ImageDraw.Draw(img).text((5, 5), "Income 65000", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    upload = client.post(
        f"/api/v1/loans/{loan['id']}/documents",
        data={"document_type": "income_proof"},
        files={"file": ("doc.png", buf.getvalue(), "image/png")},
        headers=applicant_headers,
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    response = client.get(
        "/api/v1/audit-logs", params={"action": "document_uploaded"}, headers=staff_headers
    )
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["resource_id"] == document_id
    assert body["items"][0]["resource_type"] == "document"

    verify = client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{document_id}/verify",
        json={"status": "verified"},
        headers=staff_headers,
    )
    assert verify.status_code == 200

    verify_logs = client.get(
        "/api/v1/audit-logs", params={"action": "document_verified"}, headers=staff_headers
    )
    assert verify_logs.json()["total"] == 1

    delete = client.delete(
        f"/api/v1/loans/{loan['id']}/documents/{document_id}", headers=staff_headers
    )
    assert delete.status_code == 204

    delete_logs = client.get(
        "/api/v1/audit-logs", params={"action": "document_deleted"}, headers=staff_headers
    )
    assert delete_logs.json()["total"] == 1
    assert delete_logs.json()["items"][0]["resource_id"] == document_id


def test_filter_by_resource_type(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    _submit(client, applicant_headers)

    response = client.get(
        "/api/v1/audit-logs", params={"resource_type": "loan_application"}, headers=staff_headers
    )
    body = response.json()
    assert body["total"] >= 1
    assert all(item["resource_type"] == "loan_application" for item in body["items"])


def test_pagination_limit_and_offset(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    for _ in range(3):
        _submit(client, applicant_headers)

    response = client.get(
        "/api/v1/audit-logs",
        params={"action": "loan_application_submitted", "limit": 2, "offset": 0},
        headers=staff_headers,
    )
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0


def test_logs_ordered_most_recent_first(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    first = _submit(client, applicant_headers)
    second = _submit(client, applicant_headers)

    response = client.get(
        "/api/v1/audit-logs", params={"action": "loan_application_submitted"}, headers=staff_headers
    )
    items = response.json()["items"]
    assert items[0]["resource_id"] == second["id"]
    assert items[1]["resource_id"] == first["id"]