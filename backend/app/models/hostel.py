from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Numeric, ForeignKey, Boolean, BigInteger, JSON, Text, SmallInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Hostel(Base):
    __tablename__ = "hostel"

    id = Column(Integer, primary_key=True)
    hostel_name = Column(String(100), nullable=False)
    block = Column(String(20))
    room_number = Column(String(20), nullable=False)
    floor = Column(SmallInteger)
    room_type = Column(Enum("single", "double", "triple", "dormitory"), nullable=False)
    capacity = Column(SmallInteger, default=1)
    amenities = Column(JSON)
    monthly_rent = Column(Numeric(8, 2), nullable=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    allocations = relationship("HostelAllocation", back_populates="hostel")


class HostelAllocation(Base):
    __tablename__ = "hostel_allocations"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    hostel_id = Column(Integer, ForeignKey("hostel.id"), nullable=False)
    allotment_date = Column(Date, nullable=False)
    vacating_date = Column(Date)
    academic_year = Column(String(10), nullable=False)
    status = Column(Enum("active", "vacated", "transferred"), default="active")
    total_fee = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00)
    next_due_date = Column(Date)
    remarks = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="hostel_allocations")
    hostel = relationship("Hostel", back_populates="allocations")
    payments = relationship("HostelPayment", back_populates="allocation")

    @property
    def remaining_fee(self) -> float:
        return max(0, float(self.total_fee) - float(self.paid_amount))


class HostelPayment(Base):
    __tablename__ = "hostel_payments"

    id = Column(BigInteger, primary_key=True)
    allocation_id = Column(Integer, ForeignKey("hostel_allocations.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(Enum("online", "cash", "dd", "cheque", "neft", "upi"), nullable=False)
    transaction_id = Column(String(100))
    receipt_number = Column(String(50), unique=True, nullable=False)
    month_year = Column(String(10), nullable=False)
    remarks = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

    allocation = relationship("HostelAllocation", back_populates="payments")
    student = relationship("Student")
