from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Numeric, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Fine(Base):
    __tablename__ = "fines"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    fine_type = Column(
        Enum("attendance", "library", "hostel", "discipline", "property_damage",
             "exam_malpractice", "late_fee", "other"),
        nullable=False
    )
    reason = Column(Text, nullable=False)
    amount = Column(Numeric(8, 2), nullable=False)
    fine_date = Column(Date, nullable=False)
    due_date = Column(Date)
    paid_amount = Column(Numeric(8, 2), default=0.00)
    imposed_by = Column(Integer)
    remarks = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="fines")
    payments = relationship("FinePayment", back_populates="fine")

    @property
    def status(self) -> str:
        if float(self.paid_amount) >= float(self.amount):
            return "paid"
        elif float(self.paid_amount) > 0:
            return "partially_paid"
        return "unpaid"

    @property
    def remaining_amount(self) -> float:
        return max(0, float(self.amount) - float(self.paid_amount))


class FinePayment(Base):
    __tablename__ = "fine_payments"

    id = Column(BigInteger, primary_key=True)
    fine_id = Column(Integer, ForeignKey("fines.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(8, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(Enum("online", "cash", "upi"), nullable=False)
    transaction_id = Column(String(100))
    receipt_number = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    fine = relationship("Fine", back_populates="payments")
    student = relationship("Student")
