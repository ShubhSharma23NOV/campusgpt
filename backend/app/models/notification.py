from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(Integer, nullable=False)
    user_type = Column(Enum("student", "admin"), default="student")
    type = Column(
        Enum("attendance_shortage", "fee_due", "hostel_fee_due", "scholarship_deadline",
             "exam_registration", "fine_reminder", "general", "system"),
        nullable=False
    )
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    channel = Column(String(50), default="in_app")
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    # Optional: link to student
    student = relationship(
        "Student",
        back_populates="notifications",
        primaryjoin="and_(Notification.user_id==Student.id, Notification.user_type=='student')",
        foreign_keys=[user_id],
    )
