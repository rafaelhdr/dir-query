import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

FILE_STATUSES = ("pending", "indexed", "failed")
EXCHANGE_STATUSES = ("pending", "answered", "failed")


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False, unique=True)
    owner_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    owner: Mapped[User | None] = relationship()
    files: Mapped[list["File"]] = relationship(back_populates="workspace")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="workspace"
    )


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(nullable=False)
    display_name: Mapped[str] = mapped_column(nullable=False)
    original_filename: Mapped[str] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(nullable=False, server_default="pending")

    workspace: Mapped[Workspace] = relationship(back_populates="files")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="file", passive_deletes=True
    )

    __table_args__ = (
        CheckConstraint(f"status IN {FILE_STATUSES}", name="files_status_check"),
        Index("ix_files_workspace_id", "workspace_id"),
        Index(
            "uq_files_workspace_id_display_name",
            "workspace_id",
            "display_name",
            unique=True,
        ),
        Index(
            "uq_files_workspace_id_original_filename",
            "workspace_id",
            "original_filename",
            unique=True,
        ),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    # No fixed dimension here: SQLAlchemy's insertmany fast path bakes
    # Vector(N)'s N into an explicit `::VECTOR(N)` cast in the generated SQL,
    # which would reject every insert once scripts/reset_embeddings.py
    # resizes the live column to a different provider's dimension. The
    # actual dimension is enforced by the live column's own type instead.
    embedding: Mapped[list[float]] = mapped_column(Vector(), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    file: Mapped[File] = relationship(back_populates="chunks")

    __table_args__ = (Index("ix_chunks_file_id", "file_id"),)


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    workspace: Mapped[Workspace] = relationship(back_populates="conversations")
    exchanges: Mapped[list["Exchange"]] = relationship(
        back_populates="conversation", passive_deletes=True
    )

    __table_args__ = (Index("ix_conversations_workspace_id", "workspace_id"),)


class Exchange(Base):
    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(nullable=False)
    answer: Mapped[str | None] = mapped_column(nullable=True)
    sources: Mapped[list[dict[str, str]] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, server_default="pending")
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="exchanges")

    __table_args__ = (
        CheckConstraint(f"status IN {EXCHANGE_STATUSES}", name="exchanges_status_check"),
        Index("ix_exchanges_conversation_id", "conversation_id"),
    )
