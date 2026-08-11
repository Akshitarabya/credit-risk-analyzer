"""create audit_logs table

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    audit_action_enum = postgresql.ENUM(
        "loan_application_submitted",
        "loan_decision_approved",
        "loan_decision_rejected",
        "loan_decision_manual_review",
        "document_uploaded",
        "document_verified",
        "document_rejected",
        "document_deleted",
        name="audit_action",
        create_type=True,
    )
    audit_action_enum.create(op.get_bind(), checkfirst=True)

    audit_resource_type_enum = postgresql.ENUM(
        "loan_application", "document", name="audit_resource_type", create_type=True
    )
    audit_resource_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "action",
            postgresql.ENUM(
                "loan_application_submitted",
                "loan_decision_approved",
                "loan_decision_rejected",
                "loan_decision_manual_review",
                "document_uploaded",
                "document_verified",
                "document_rejected",
                "document_deleted",
                name="audit_action",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "resource_type",
            postgresql.ENUM(
                "loan_application", "document", name="audit_resource_type", create_type=False
            ),
            nullable=False,
        ),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_audit_logs_actor_id"),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_resource_type", "audit_logs", ["resource_type"])
    op.create_index("ix_audit_logs_resource_id", "audit_logs", ["resource_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    postgresql.ENUM(name="audit_resource_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="audit_action").drop(op.get_bind(), checkfirst=True)