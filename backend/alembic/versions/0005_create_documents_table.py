"""create documents table

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-08

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    document_type_enum = postgresql.ENUM(
        "id_proof", "income_proof", "bank_statement", name="document_type", create_type=True
    )
    document_type_enum.create(op.get_bind(), checkfirst=True)

    document_status_enum = postgresql.ENUM(
        "uploaded", "ocr_failed", "verified", "rejected", name="document_status", create_type=True
    )
    document_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("loan_application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "document_type",
            postgresql.ENUM(
                "id_proof", "income_proof", "bank_statement", name="document_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "uploaded", "ocr_failed", "verified", "rejected", name="document_status", create_type=False
            ),
            nullable=False,
            server_default="uploaded",
        ),
        sa.Column("ocr_raw_text", sa.Text(), nullable=True),
        sa.Column("ocr_extracted_fields", sa.JSON(), nullable=True),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("ocr_error_message", sa.String(length=500), nullable=True),
        sa.Column("ocr_processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column("verified_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["loan_application_id"], ["loan_applications.id"], name="fk_documents_loan_application_id"
        ),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], name="fk_documents_uploaded_by"),
        sa.ForeignKeyConstraint(["verified_by"], ["users.id"], name="fk_documents_verified_by"),
        sa.UniqueConstraint("stored_filename", name="uq_documents_stored_filename"),
        sa.UniqueConstraint("loan_application_id", "document_type", name="uq_document_loan_type"),
    )
    op.create_index("ix_documents_loan_application_id", "documents", ["loan_application_id"])
    op.create_index("ix_documents_status", "documents", ["status"])


def downgrade() -> None:
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_loan_application_id", table_name="documents")
    op.drop_table("documents")

    postgresql.ENUM(name="document_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="document_type").drop(op.get_bind(), checkfirst=True)