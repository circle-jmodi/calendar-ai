from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    google_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tokens: Mapped[list["OAuthToken"]] = relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    preferences: Mapped["UserPreferences | None"] = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    scheduling_links: Mapped[list["SchedulingLink"]] = relationship("SchedulingLink", back_populates="user", cascade="all, delete-orphan")
    gong_invites: Mapped[list["GongInvite"]] = relationship("GongInvite", back_populates="user", cascade="all, delete-orphan")
