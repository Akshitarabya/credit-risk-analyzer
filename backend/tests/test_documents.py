"""
Tests for the Module 5 document workflow:
  POST   /loans/{id}/documents
  GET    /loans/{id}/documents
  GET    /loans/{id}/documents/{document_id}
  GET    /loans/{id}/documents/{document_id}/file
  DELETE /loans/{id}/documents/{document_id}
  PATCH  /loans/{id}/documents/{document_id}/verify
"""
import io

from PIL import Image, ImageDraw


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


def _submit_application(client, applicant_headers):
    response = client.post("/api/v1/loans", json=VALID_APPLICATION, headers=applicant_headers)
    assert response.status_code == 201
    return response.json()


def _make_valid_png(text: str = "Annual Income: 65000") -> bytes:
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_valid_pdf(text: str = "Annual Income: 65000") -> bytes:
    """
    Hand-builds a minimal, structurally valid single-page PDF with a real
    text content stream (correct object offsets + xref table) — avoids
    adding a PDF-authoring dependency (e.g. reportlab) just for tests, since
    pypdf itself only reads/manipulates PDFs, it doesn't author text content.
    """
    content_stream = f"BT /F1 18 Tf 20 50 Td ({text}) Tj ET".encode()
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/MediaBox[0 0 300 150]/Contents 5 0 R>>",
        b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>",
        b"<</Length " + str(len(content_stream)).encode() + b">>\nstream\n" + content_stream + b"\nendstream",
    ]

    body = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body += f"{i} 0 obj".encode() + obj + b"endobj\n"

    xref_offset = len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF".encode()

    return bytes(body) + xref + trailer


def _make_blank_pdf_no_text() -> bytes:
    """A structurally valid PDF with a page but no content stream/text at all."""
    objects = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 150]>>",
    ]
    body = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body += f"{i} 0 obj".encode() + obj + b"endobj\n"
    xref_offset = len(body)
    xref = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        xref += f"{off:010d} 00000 n \n".encode()
    trailer = f"trailer<</Size {len(objects) + 1}/Root 1 0 R>>\nstartxref\n{xref_offset}\n%%EOF".encode()
    return bytes(body) + xref + trailer


def _upload(client, headers, loan_id, document_type="income_proof", content=None, filename="doc.png", mime="image/png"):
    if content is None:
        content = _make_valid_png()
    return client.post(
        f"/api/v1/loans/{loan_id}/documents",
        data={"document_type": document_type},
        files={"file": (filename, content, mime)},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


def test_upload_requires_authentication(client):
    response = client.post(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/documents",
        data={"document_type": "income_proof"},
        files={"file": ("doc.png", _make_valid_png(), "image/png")},
    )
    assert response.status_code == 401


def test_staff_cannot_upload_documents(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    response = _upload(client, staff_headers, loan["id"])
    assert response.status_code == 403


def test_applicant_cannot_upload_to_someone_elses_loan(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    loan = _submit_application(client, headers_a)
    response = _upload(client, headers_b, loan["id"])
    assert response.status_code == 403


def test_successful_png_upload_runs_ocr(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    response = _upload(client, headers, loan["id"], document_type="income_proof")
    assert response.status_code == 201
    body = response.json()
    assert body["document_type"] == "income_proof"
    assert body["status"] == "uploaded"
    assert body["mime_type"] == "image/png"
    assert body["ocr_confidence"] is not None


def test_successful_pdf_upload_with_text_layer(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    response = _upload(
        client, headers, loan["id"], document_type="bank_statement",
        content=_make_valid_pdf(), filename="statement.pdf", mime="application/pdf",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "uploaded"
    assert response.json()["mime_type"] == "application/pdf"


def test_pdf_with_no_text_layer_marks_ocr_failed_but_still_uploads(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    response = _upload(
        client, headers, loan["id"], document_type="bank_statement",
        content=_make_blank_pdf_no_text(), filename="scanned.pdf", mime="application/pdf",
    )
    assert response.status_code == 201
    assert response.json()["status"] == "ocr_failed"


def test_upload_rejects_disallowed_file_type(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    response = _upload(
        client, headers, loan["id"],
        content=b"just some plain text, not an image or pdf at all",
        filename="notes.txt", mime="text/plain",
    )
    assert response.status_code == 415


def test_upload_rejects_mime_spoofing(client):
    """A .pdf-labeled file whose actual bytes are plain text must be rejected —
    the server checks real content, not the client's declared MIME type."""
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    response = _upload(
        client, headers, loan["id"],
        content=b"not actually a pdf, just spoofed content-type below",
        filename="fake.pdf", mime="application/pdf",
    )
    assert response.status_code == 415


def test_upload_rejects_oversized_file(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    oversized_content = b"\xff\xd8\xff" + (b"0" * (10 * 1024 * 1024 + 1))  # valid JPEG magic bytes, oversized
    response = _upload(
        client, headers, loan["id"], content=oversized_content, filename="big.jpg", mime="image/jpeg"
    )
    assert response.status_code == 413


def test_duplicate_document_type_without_delete_returns_409(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    first = _upload(client, headers, loan["id"], document_type="id_proof")
    assert first.status_code == 201

    second = _upload(client, headers, loan["id"], document_type="id_proof")
    assert second.status_code == 409


# ---------------------------------------------------------------------------
# List / detail
# ---------------------------------------------------------------------------


def test_list_documents_requires_authentication(client):
    response = client.get("/api/v1/loans/00000000-0000-0000-0000-000000000000/documents")
    assert response.status_code == 401


def test_owner_can_list_own_documents(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    _upload(client, headers, loan["id"], document_type="id_proof")
    _upload(client, headers, loan["id"], document_type="income_proof")

    response = client.get(f"/api/v1/loans/{loan['id']}/documents", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_other_applicant_cannot_list_documents(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    loan = _submit_application(client, headers_a)
    _upload(client, headers_a, loan["id"])

    response = client.get(f"/api/v1/loans/{loan['id']}/documents", headers=headers_b)
    assert response.status_code == 403


def test_staff_can_list_any_applicants_documents(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    _upload(client, applicant_headers, loan["id"])

    response = client.get(f"/api/v1/loans/{loan['id']}/documents", headers=staff_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_list_view_excludes_ocr_raw_text(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    _upload(client, headers, loan["id"])

    response = client.get(f"/api/v1/loans/{loan['id']}/documents", headers=headers)
    assert "ocr_raw_text" not in response.json()[0]


def test_detail_view_includes_ocr_raw_text(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    created = _upload(client, headers, loan["id"]).json()

    response = client.get(f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=headers)
    assert response.status_code == 200
    assert "ocr_raw_text" in response.json()
    assert response.json()["ocr_raw_text"]


def test_document_id_from_different_loan_returns_404(client):
    """Cross-loan ID confusion: a real document_id that belongs to a DIFFERENT
    loan application (even one the same user owns) must not resolve when
    accessed through the wrong loan_application_id in the path."""
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan_a = _submit_application(client, headers)
    loan_b = client.post(
        "/api/v1/loans", json={**VALID_APPLICATION, "loan_amount": 5000}, headers=headers
    ).json()

    doc = _upload(client, headers, loan_a["id"]).json()

    response = client.get(f"/api/v1/loans/{loan_b['id']}/documents/{doc['id']}", headers=headers)
    assert response.status_code == 404


def test_nonexistent_document_returns_404(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)

    response = client.get(
        f"/api/v1/loans/{loan['id']}/documents/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# File download
# ---------------------------------------------------------------------------


def test_file_download_requires_authentication(client):
    response = client.get(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/documents/"
        "00000000-0000-0000-0000-000000000000/file"
    )
    assert response.status_code == 401


def test_owner_can_download_own_file(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    original_content = _make_valid_png("unique marker text")
    created = _upload(client, headers, loan["id"], content=original_content).json()

    response = client.get(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/file", headers=headers
    )
    assert response.status_code == 200
    assert response.content == original_content
    assert response.headers["content-type"] == "image/png"


def test_other_applicant_cannot_download_file(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    loan = _submit_application(client, headers_a)
    created = _upload(client, headers_a, loan["id"]).json()

    response = client.get(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/file", headers=headers_b
    )
    assert response.status_code == 403


def test_staff_can_download_any_applicants_file(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()

    response = client.get(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/file", headers=staff_headers
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_owner_can_delete_unverified_document(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    created = _upload(client, headers, loan["id"]).json()

    response = client.delete(f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=headers)
    assert response.status_code == 204

    follow_up = client.get(f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=headers)
    assert follow_up.status_code == 404


def test_delete_then_reupload_same_type_succeeds(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    created = _upload(client, headers, loan["id"], document_type="id_proof").json()

    client.delete(f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=headers)
    second = _upload(client, headers, loan["id"], document_type="id_proof")
    assert second.status_code == 201


def test_other_applicant_cannot_delete_document(client):
    token_a = _register(client, "jordan@example.com")
    token_b = _register(client, "taylor@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    loan = _submit_application(client, headers_a)
    created = _upload(client, headers_a, loan["id"]).json()

    response = client.delete(f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=headers_b)
    assert response.status_code == 403


def test_applicant_cannot_delete_verified_document(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()
    client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "verified"},
        headers=staff_headers,
    )

    response = client.delete(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=applicant_headers
    )
    assert response.status_code == 409


def test_staff_can_delete_verified_document(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()
    client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "verified"},
        headers=staff_headers,
    )

    response = client.delete(f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=staff_headers)
    assert response.status_code == 204


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------


def test_verify_requires_authentication(client):
    response = client.patch(
        "/api/v1/loans/00000000-0000-0000-0000-000000000000/documents/"
        "00000000-0000-0000-0000-000000000000/verify",
        json={"status": "verified"},
    )
    assert response.status_code == 401


def test_applicant_cannot_verify_documents(client):
    token = _register(client, "jordan@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    loan = _submit_application(client, headers)
    created = _upload(client, headers, loan["id"]).json()

    response = client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "verified"},
        headers=headers,
    )
    assert response.status_code == 403


def test_staff_can_verify_document(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()

    response = client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "verified", "notes": "Looks legitimate."},
        headers=staff_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "verified"
    assert body["verified_by"] is not None
    assert body["verifier_name"] == "Test User"
    assert body["verified_at"] is not None
    assert body["verification_notes"] == "Looks legitimate."


def test_staff_can_reject_document(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()

    response = client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "rejected", "notes": "Blurry, please re-upload."},
        headers=staff_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"


def test_verify_persists_across_requests(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()
    client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "verified"},
        headers=staff_headers,
    )

    fetched = client.get(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}", headers=staff_headers
    )
    assert fetched.json()["status"] == "verified"


def test_verify_blocked_once_loan_has_final_decision(client):
    applicant_token = _register(client, "jordan@example.com")
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}
    staff_headers = {"Authorization": f"Bearer {staff_token}"}

    loan = _submit_application(client, applicant_headers)
    created = _upload(client, applicant_headers, loan["id"]).json()

    client.patch(
        f"/api/v1/loans/{loan['id']}/decision",
        json={"decision": "approved"},
        headers=staff_headers,
    )

    response = client.patch(
        f"/api/v1/loans/{loan['id']}/documents/{created['id']}/verify",
        json={"status": "verified"},
        headers=staff_headers,
    )
    assert response.status_code == 409


def test_verify_nonexistent_document_returns_404(client):
    staff_token = _register(client, "alex@bank.com", role="staff")
    applicant_token = _register(client, "jordan@example.com")
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    applicant_headers = {"Authorization": f"Bearer {applicant_token}"}

    loan = _submit_application(client, applicant_headers)

    response = client.patch(
        f"/api/v1/loans/{loan['id']}/documents/00000000-0000-0000-0000-000000000000/verify",
        json={"status": "verified"},
        headers=staff_headers,
    )
    assert response.status_code == 404