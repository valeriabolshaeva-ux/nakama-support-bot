"""
SQLAlchemy models for Telegram Support Bot.

Models:
    - Client: Company/client
    - Project: Project within a client
    - UserBinding: Telegram user to project binding
    - Ticket: Support ticket
    - Message: Messages within ticket
    - Feedback: CSAT feedback after ticket close
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    
    pass


class Client(Base):
    """Company/client entity."""
    
    __tablename__ = "clients"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Topic for this client in support group (one topic per client)
    topic_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    support_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    
    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    predefined_users: Mapped[list["PredefinedUser"]] = relationship(
        "PredefinedUser",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}')>"


class Project(Base):
    """Project/environment within a client."""
    
    __tablename__ = "projects"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    invite_code: Mapped[Optional[str]] = mapped_column(
        String(50), 
        unique=True,
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="projects")
    user_bindings: Mapped[list["UserBinding"]] = relationship(
        "UserBinding",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        back_populates="project",
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_projects_invite_code", "invite_code"),
        Index("idx_projects_client_id", "client_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', invite_code='{self.invite_code}')>"


class UserBinding(Base):
    """Telegram user to project binding."""
    
    __tablename__ = "user_bindings"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tg_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tg_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="user_bindings")
    
    # Indexes
    __table_args__ = (
        Index("idx_user_bindings_tg_user_id", "tg_user_id"),
        Index("idx_user_bindings_project_id", "project_id"),
    )
    
    def __repr__(self) -> str:
        return f"<UserBinding(id={self.id}, tg_user_id={self.tg_user_id}, project_id={self.project_id})>"


class Ticket(Base):
    """Support ticket."""
    
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )
    tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        String(20), 
        default="normal",
        nullable=False
    )  # normal, urgent
    status: Mapped[str] = mapped_column(
        String(20), 
        default="new",
        nullable=False
    )  # new, in_progress, on_hold, completed, cancelled
    support_chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    topic_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assigned_to_tg_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    first_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tickets")
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )
    feedback: Mapped[Optional["Feedback"]] = relationship(
        "Feedback",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_tickets_tg_user_id", "tg_user_id"),
        Index("idx_tickets_status", "status"),
        Index("idx_tickets_project_id", "project_id"),
        Index("idx_tickets_topic_id", "topic_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, number={self.number}, status='{self.status}')>"


class Message(Base):
    """Message within a ticket."""
    
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False
    )
    direction: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )  # client, operator, system
    tg_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )  # text, photo, video, document, voice, audio
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    author_tg_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    
    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_messages_ticket_id", "ticket_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, ticket_id={self.ticket_id}, direction='{self.direction}')>"


class Feedback(Base):
    """CSAT feedback after ticket close."""
    
    __tablename__ = "feedback"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    csat: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )  # positive, negative
    # Detailed ratings (1-5 stars, optional)
    speed_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    quality_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    politeness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    
    # Relationships
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="feedback")
    
    # Indexes
    __table_args__ = (
        Index("idx_feedback_ticket_id", "ticket_id"),
    )
    
    def __repr__(self) -> str:
        return f"<Feedback(id={self.id}, ticket_id={self.ticket_id}, csat='{self.csat}')>"


class PredefinedUser(Base):
    """
    Predefined mapping of Telegram usernames to clients.
    
    Allows automatic client binding when user starts bot,
    without requiring invite code.
    """
    
    __tablename__ = "predefined_users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    client_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=func.now(),
        nullable=False
    )
    
    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="predefined_users")
    
    # Indexes
    __table_args__ = (
        Index("idx_predefined_users_tg_username", "tg_username"),
        Index("idx_predefined_users_client_id", "client_id"),
    )
    
    def __repr__(self) -> str:
        return f"<PredefinedUser(id={self.id}, tg_username='{self.tg_username}', client_id={self.client_id})>"
