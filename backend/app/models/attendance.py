from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Text, UniqueConstraint, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    course = Column(String(100), nullable=False)
    semester = Column(Integer, nullable=False)
    credits = Column(Integer, default=3)
    type = Column(Enum("theory", "lab", "elective"), default="theory")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    attendance_records = relationship("Attendance", back_populates="subject")
    summaries = relationship("AttendanceSummary", back_populates="subject")


from sqlalchemy import Boolean


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum("present", "absent", "late", "medical_leave", "on_duty"), nullable=False)
    marked_by = Column(Integer)
    remarks = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "date", name="uq_student_subject_date"),
    )

    student = relationship("Student", back_populates="attendance_records")
    subject = relationship("Subject", back_populates="attendance_records")


class AttendanceSummary(Base):
    __tablename__ = "attendance_summary"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    academic_year = Column(String(10), nullable=False)
    semester = Column(Integer, nullable=False)
    total_classes = Column(Integer, default=0)
    attended_classes = Column(Integer, default=0)
    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "academic_year", name="uq_student_subject_year"),
    )

    student = relationship("Student", back_populates="attendance_summaries")
    subject = relationship("Subject", back_populates="summaries")

    @property
    def percentage(self) -> float:
        if self.total_classes == 0:
            return 0.0
        return round((self.attended_classes / self.total_classes) * 100, 2)
