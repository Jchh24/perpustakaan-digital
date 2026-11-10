from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class LoanCreate(BaseModel):
    book_id: str
    duration_days: int = Field(7, ge=1, le=30)

class LoanReturn(BaseModel):
    notes: Optional[str] = None

class LoanResponse(BaseModel):
    id: str
    user_id: str
    book_id: str
    loan_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    status: str
    fine_amount: int
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
