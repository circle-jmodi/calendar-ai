from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Focus time
    focus_hours_per_day: Mapped[int] = mapped_column(Integer, default=2)
    focus_days_per_week: Mapped[int] = mapped_column(Integer, default=5)
    focus_preferred_time: Mapped[str] = mapped_column(String(16), default="morning")  # morning | afternoon
    focus_min_block_minutes: Mapped[int] = mapped_column(Integer, default=60)
    focus_max_block_minutes: Mapped[int] = mapped_column(Integer, default=120)

    # Work hours
    work_start_hour: Mapped[int] = mapped_column(Integer, default=9)
    work_end_hour: Mapped[int] = mapped_column(Integer, default=18)
    work_timezone: Mapped[str] = mapped_column(String(64), default="America/New_York")
    work_days: Mapped[list] = mapped_column(JSON, default=lambda: [0, 1, 2, 3, 4])  # 0=Mon..6=Sun

    # Meeting rules
    meeting_buffer_minutes: Mapped[int] = mapped_column(Integer, default=5)
    allow_auto_move_meetings: Mapped[bool] = mapped_column(Boolean, default=False)
    no_meeting_days: Mapped[list] = mapped_column(JSON, default=lambda: [])  # e.g. [2] for Wednesday

    # Slack
    slack_status_sync_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    slack_focus_status_text: Mapped[str] = mapped_column(String(100), default="Focus Time")
    slack_focus_status_emoji: Mapped[str] = mapped_column(String(64), default=":dart:")

    # Gong
    gong_auto_record_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", back_populates="preferences")
