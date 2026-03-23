from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, DateTime, func, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class SchedulingLink(Base):
    __tablename__ = "scheduling_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    buffer_before: Mapped[int] = mapped_column(Integer, default=0)   # minutes
    buffer_after: Mapped[int] = mapped_column(Integer, default=0)    # minutes
    rolling_days_available: Mapped[int] = mapped_column(Integer, default=14)  # how many days ahead
    custom_availability: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # override work hours per weekday
    questions: Mapped[list] = mapped_column(JSON, default=lambda: [])  # [{label, required}]
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="scheduling_links")


class GongInvite(Base):
    __tablename__ = "gong_invites"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    google_event_id: Mapped[str] = mapped_column(String(256), nullable=False)
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="gong_invites")

    __table_args__ = (
        UniqueConstraint("user_id", "google_event_id", name="uq_gong_invites_user_event"),
    )
