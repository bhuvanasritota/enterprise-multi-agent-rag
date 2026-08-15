"""initial schema"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("email", sa.String(320), nullable=False, unique=True), sa.Column("hashed_password", sa.String(512), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("documents", sa.Column("id", sa.String(36), primary_key=True), sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("filename", sa.String(255), nullable=False), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("file_type", sa.String(20), nullable=False), sa.Column("file_size", sa.Integer(), nullable=False), sa.Column("storage_path", sa.String(1024), nullable=False), sa.Column("processing_status", sa.String(20), nullable=False), sa.Column("page_count", sa.Integer()), sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("processing_error", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"])
    op.create_table("document_chunks", sa.Column("id", sa.String(36), primary_key=True), sa.Column("document_id", sa.String(36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False), sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("chunk_index", sa.Integer(), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("page_number", sa.Integer()), sa.Column("embedding", Vector(384)), sa.Column("metadata", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("document_id", "chunk_index"))
    op.create_index("ix_chunks_owner_id", "document_chunks", ["owner_id"])
    op.create_table("conversations", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("title", sa.String(200), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table("messages", sa.Column("id", sa.String(36), primary_key=True), sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False), sa.Column("role", sa.String(20), nullable=False), sa.Column("content", sa.Text(), nullable=False), sa.Column("sources", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("rag_queries", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("conversation_id", sa.String(36), sa.ForeignKey("conversations.id", ondelete="SET NULL")), sa.Column("query", sa.Text(), nullable=False), sa.Column("retrieval_time", sa.Float(), nullable=False), sa.Column("generation_time", sa.Float(), nullable=False), sa.Column("total_time", sa.Float(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("evaluation_results", sa.Column("id", sa.String(36), primary_key=True), sa.Column("query_id", sa.String(36), sa.ForeignKey("rag_queries.id", ondelete="CASCADE"), nullable=False), sa.Column("metric_name", sa.String(100), nullable=False), sa.Column("metric_value", sa.Float(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    for table in ["evaluation_results", "rag_queries", "messages", "conversations", "document_chunks", "documents", "users"]: op.drop_table(table)
