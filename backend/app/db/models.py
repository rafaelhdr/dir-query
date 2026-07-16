import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, ForeignKey, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 384

FILE_STATUSES = ("pending", "indexed", "failed")


class Base(DeclarativeBase):
    pass


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    slug: Mapped[str] = mapped_column(nullable=False, unique=True)
    owner_email: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    files: Mapped[list["File"]] = relationship(back_populates="workspace")


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    workspace_id: Mapped[int] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(nullable=False)
    original_name: Mapped[str] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(nullable=False, server_default="pending")

    workspace: Mapped[Workspace] = relationship(back_populates="files")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="file")

    __table_args__ = (
        CheckConstraint(f"status IN {FILE_STATUSES}", name="files_status_check"),
        Index("ix_files_workspace_id", "workspace_id"),
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    file: Mapped[File] = relationship(back_populates="chunks")

    __table_args__ = (Index("ix_chunks_file_id", "file_id"),)
