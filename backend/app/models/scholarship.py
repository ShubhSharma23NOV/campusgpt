from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Numeric, ForeignKey, Boolean, BigInteger, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Scholarship(Base):
    __tablename__ = "scholarships"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum("merit", "need_based", "government", "sports", "minority", "other"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    eligibility_criteria = Column(JSON, nullable=False)
    application_start = Column(Date)
    application_end = Column(Date)
    academic_year = Column(String(10), nullable=False)
    min_attendance = Column(Numeric(5, 2), default=75.00)
    min_percentage = Column(Numeric(5, 2))
    max_income = Column(Numeric(12, 2))
    categories_eligible = Column(JSON)
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    applications = relationship("ScholarshipApplication", back_populates="scholarship")


class ScholarshipApplication(Base):
    __tablename__ = "scholarship_applications"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    scholarship_id = Column(Integer, ForeignKey("scholarships.id"), nullable=False)
    applied_date = Column(DateTime, server_default=func.now())
    status = Column(
        Enum("draft", "submitted", "under_review", "approved", "rejected", "disbursed"),
        default="draft"
    )
    approved_amount = Column(Numeric(10, 2))
    approved_by = Column(Integer)
    approval_date = Column(DateTime)
    remarks = Column(Text)
    documents = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="scholarship_applications")
    scholarship = relationship("Scholarship", back_populates="applications")
    payments = relationship("ScholarshipPayment", back_populates="application")


class ScholarshipPayment(Base):
    __tablename__ = "scholarship_payments"

    id = Column(BigInteger, primary_key=True)
    application_id = Column(Integer, ForeignKey("scholarship_applications.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(Enum("bank_transfer", "cheque", "dd"), default="bank_transfer")
    transaction_id = Column(String(100))
    academic_year = Column(String(10), nullable=False)
    remarks = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    application = relationship("ScholarshipApplication", back_populates="payments")
    student = relationship("Student")
