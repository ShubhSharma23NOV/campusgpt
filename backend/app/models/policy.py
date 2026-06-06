from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(
        Enum("attendance", "academic", "examination", "hostel", "scholarship",
             "fee", "conduct", "fine", "general"),
        nullable=False
    )
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    chroma_collection = Column(String(100))
    summary = Column(Text)
    language = Column(String(20), default="english")
    version = Column(String(20))
    effective_date = Column(Date)
    uploaded_by = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
