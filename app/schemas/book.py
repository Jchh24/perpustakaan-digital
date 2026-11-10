from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    publisher: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., min_length=13, max_length=17)
    publication_year: int = Field(..., ge=1800, le=2100)
    location: str = Field(..., min_length=1, max_length=100)
    stock: int = Field(..., ge=1)
    cover_image: Optional[str] = "/static/images/default_cover.png"
    description: Optional[str] = None
    category_id: Optional[str] = None

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    publisher: Optional[str] = Field(None, min_length=1, max_length=100)
    isbn: Optional[str] = Field(None, min_length=13, max_length=17)
    publication_year: Optional[int] = Field(None, ge=1800, le=2100)
    location: Optional[str] = Field(None, min_length=1, max_length=100)
    stock: Optional[int] = Field(None, ge=1)
    cover_image: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None

class BookResponse(BaseModel):
    id: str
    title: str
    author: str
    publisher: str
    isbn: str
    publication_year: int
    location: str
    stock: int
    available_stock: int
    cover_image: str
    description: Optional[str]
    category_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
