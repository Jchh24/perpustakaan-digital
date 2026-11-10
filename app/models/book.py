import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Uuid
from sqlalchemy.orm import relationship
from app.services.db import Base

class Book(Base):
    __tablename__ = "books"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(200), index=True, nullable=False)
    author = Column(String(100), index=True, nullable=False)
    publisher = Column(String(100), nullable=False)
    isbn = Column(String(30), unique=True, index=True, nullable=False)
    publication_year = Column(Integer, nullable=False)
    location = Column(String(100), nullable=False)
    stock = Column(Integer, default=1, nullable=False)
    available_stock = Column(Integer, default=1, nullable=False)
    cover_image = Column(String(255), default="/static/images/default_cover.png", nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(Uuid(as_uuid=False), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    category = relationship("Category", back_populates="books")
    loans = relationship("Loan", back_populates="book", cascade="all, delete-orphan")
