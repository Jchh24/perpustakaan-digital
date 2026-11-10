import uuid
from sqlalchemy import Column, String, Text, Uuid
from sqlalchemy.orm import relationship
from app.services.db import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    books = relationship("Book", back_populates="category")
