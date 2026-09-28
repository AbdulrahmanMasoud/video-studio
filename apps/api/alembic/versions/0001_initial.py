"""initial schema (brief §5.7)

Revision ID: 0001
Revises:
Create Date: 2026-09-28
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True)),
        sa.Column("locale", sa.String(8), nullable=False, server_default="en"),
        sa.Column("plan", sa.String(16), nullable=False, server_default="free"),
        sa.Column("credits", sa.Integer, nullable=False, server_default="0"),
        sa.Column("ls_customer_id", sa.String(64)),
        sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "brand_kits",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("palette", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("fonts", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("logo_key", sa.String(512)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "projects",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("template", sa.String(32), nullable=False),
        sa.Column("lang", sa.String(16)),
        sa.Column("size", sa.String(16), nullable=False, server_default="9:16"),
        sa.Column("size_w", sa.Integer, nullable=False),
        sa.Column("size_h", sa.Integer, nullable=False),
        sa.Column("platform", sa.String(16), nullable=False, server_default="none"),
        sa.Column("brief", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(24), nullable=False, server_default="created"),
        sa.Column("progress", sa.Integer, nullable=False, server_default="0"),
        sa.Column("input_key", sa.String(512)),
        sa.Column("input_kind", sa.String(8)),
        sa.Column("script", sa.Text),
        sa.Column("plan", pg.JSONB),
        sa.Column("editable_fields", pg.JSONB),
        sa.Column("asset_slots", pg.JSONB),
        sa.Column("words", pg.JSONB),
        sa.Column("detected_lang", sa.String(16)),
        sa.Column("output_key", sa.String(512)),
        sa.Column("preview_key", sa.String(512)),
        sa.Column("sheet_key", sa.String(512)),
        sa.Column("duration_s", sa.Numeric(10, 3)),
        sa.Column("credits_reserved", sa.Integer, nullable=False, server_default="0"),
        sa.Column("credits_committed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("planner", sa.String(16)),
        sa.Column("llm_model", sa.String(128)),
        sa.Column("llm_tokens_in", sa.Integer, nullable=False, server_default="0"),
        sa.Column("llm_tokens_out", sa.Integer, nullable=False, server_default="0"),
        sa.Column("llm_cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failed_stage", sa.String(16)),
        sa.Column("rq_job_id", sa.String(64)),
        sa.Column("output_size", pg.JSONB),
        sa.Column("qa", pg.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("done_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_projects_user_created", "projects", ["user_id", sa.text("created_at DESC")])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_table(
        "project_assets",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", pg.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(8), nullable=False),
        sa.Column("key", sa.String(512), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("mime", sa.String(128), nullable=False),
        sa.Column("bytes", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("duration_s", sa.Numeric(10, 3)),
        sa.Column("has_alpha", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("description", sa.String(300), nullable=False, server_default=""),
        sa.Column("description_source", sa.String(8)),
        sa.Column("status", sa.String(16), nullable=False, server_default="pending"),
        sa.Column("error", sa.String(300)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind in ('image','clip')", name="ck_project_assets_kind"),
        sa.CheckConstraint("description_source is null or description_source in ('user','ai')", name="ck_project_assets_desc_source"),
    )
    op.create_index("ix_project_assets_project", "project_assets", ["project_id"])
    op.create_table(
        "template_requests",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("example_url", sa.String(1024)),
        sa.Column("file_key", sa.String(512)),
        sa.Column("status", sa.String(16), nullable=False, server_default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "job_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("project_id", pg.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(24)),
        sa.Column("to_status", sa.String(24), nullable=False),
        sa.Column("detail", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_job_events_project_id", "job_events", ["project_id"])
    op.create_table(
        "credit_ledger",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delta", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(16), nullable=False),
        sa.Column("project_id", pg.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL")),
        sa.Column("external_id", sa.String(128), unique=True),
        sa.Column("note", sa.String(300)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("reason in ('grant','plan_renewal','reserve','commit','release','refund','admin')", name="ck_credit_ledger_reason"),
    )
    op.create_index("ix_credit_ledger_user_id", "credit_ledger", ["user_id"])
    op.create_table(
        "subscriptions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(24), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False, unique=True),
        sa.Column("plan", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("cancel_at_period_end", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("raw", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_table(
        "webhook_events",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(24), nullable=False),
        sa.Column("external_event_id", sa.String(128), nullable=False, unique=True),
        sa.Column("payload", pg.JSONB, nullable=False, server_default="{}"),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_table(
        "template_flags",
        sa.Column("name", sa.String(32), primary_key=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("tier_required", sa.String(16), nullable=False, server_default="free"),
    )
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("value", pg.JSONB),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # seed: the 6 launch templates are enabled, everything else exists behind the flag
    flags = sa.table("template_flags", sa.column("name", sa.String), sa.column("enabled", sa.Boolean), sa.column("tier_required", sa.String))
    enabled = ["steps", "mirror", "quiz", "chat", "top-five", "hot-take"]
    others = ["before-after", "breaking", "cinema", "city-map", "counter", "echo", "flash-sale", "journey", "podcast", "recipe", "review", "screen",
              "showcase", "storytime", "terminal", "verdict", "whiteboard", "workout"]
    op.bulk_insert(flags, [{"name": n, "enabled": True, "tier_required": "free"} for n in enabled] + [{"name": n, "enabled": False, "tier_required": "pro"} for n in others])


def downgrade() -> None:
    for t in ("app_settings", "template_flags", "webhook_events", "subscriptions", "credit_ledger", "job_events", "template_requests", "project_assets",
              "projects", "brand_kits", "users"):
        op.drop_table(t)
