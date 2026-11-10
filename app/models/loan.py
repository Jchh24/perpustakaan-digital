import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import relationship
from app.services.db import Base

class Loan(Base):
    __tablename__ = "loans"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Uuid(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Uuid(as_uuid=False), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    loan_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="borrowed", nullable=False)
    fine_amount = Column(Integer, default=0, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")
