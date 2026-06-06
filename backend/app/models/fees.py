from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Numeric, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    academic_year = Column(String(10), nullable=False)
    fee_type = Column(Enum("tuition", "hostel", "exam", "library", "lab", "sports", "other"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    paid_amount = Column(Numeric(10, 2), default=0.00)
    discount_amount = Column(Numeric(10, 2), default=0.00)
    waiver_amount = Column(Numeric(10, 2), default=0.00)
    due_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    student = relationship("Student", back_populates="fees")
    payments = relationship("FeePayment", back_populates="fee")

    @property
    def net_amount(self) -> float:
        return float(self.total_amount) - float(self.discount_amount) - float(self.waiver_amount)

    @property
    def remaining_amount(self) -> float:
        return max(0, self.net_amount - float(self.paid_amount))

    @property
    def status(self) -> str:
        from datetime import date
        remaining = self.remaining_amount
        if remaining <= 0:
            return "paid"
        elif float(self.paid_amount) > 0:
            return "partially_paid"
        elif self.due_date and self.due_date < date.today():
            return "overdue"
        return "unpaid"


class FeePayment(Base):
    __tablename__ = "fee_payments"

    id = Column(BigInteger, primary_key=True)
    fee_id = Column(Integer, ForeignKey("fees.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(Enum("online", "cash", "dd", "cheque", "neft", "upi"), nullable=False)
    transaction_id = Column(String(100))
    receipt_number = Column(String(50), unique=True, nullable=False)
    installment_number = Column(Integer)
    remarks = Column(String(255))
    verified_by = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    fee = relationship("Fee", back_populates="payments")
    student = relationship("Student")
