from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Enum, Text, SmallInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20))
    date_of_birth = Column(Date)
    gender = Column(Enum("male", "female", "other"))
    course = Column(String(100), nullable=False)
    branch = Column(String(100))
    semester = Column(SmallInteger, default=1)
    year = Column(SmallInteger, default=1)
    batch = Column(Integer, nullable=False)
    section = Column(String(10))
    roll_number = Column(String(20))
    category = Column(Enum("general", "obc", "sc", "st", "ews"), default="general")
    guardian_name = Column(String(100))
    guardian_phone = Column(String(20))
    address = Column(Text)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_hostel_student = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    attendance_records = relationship("Attendance", back_populates="student")
    attendance_summaries = relationship("AttendanceSummary", back_populates="student")
    fees = relationship("Fee", back_populates="student")
    hostel_allocations = relationship("HostelAllocation", back_populates="student")
    scholarship_applications = relationship("ScholarshipApplication", back_populates="student")
    fines = relationship("Fine", back_populates="student")
    notifications = relationship("Notification", back_populates="student",
                                 primaryjoin="and_(Student.id==Notification.user_id, Notification.user_type=='student')",
                                 foreign_keys="[Notification.user_id]")
