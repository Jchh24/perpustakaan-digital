from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.services.db import get_db
from app.services.auth_service import get_current_user_optional
from app.models.book import Book
from app.models.loan import Loan
from app.models.category import Category
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])
templates = Jinja2Templates(directory="templates")

def verify_admin_access(request: Request, db: Session):
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/auth/login?next=" + request.url.path}
        )
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak: Hanya administrator yang diizinkan"
        )
    return user

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def reports_index(
    request: Request,
    report_type: str = "loans",
    start_date: str = "",
    end_date: str = "",
    status_filter: str = "all",
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_access(request, db)

    total_books = db.query(func.count(Book.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_loans = db.query(func.count(Loan.id)).scalar() or 0
    active_loans = db.query(func.count(Loan.id)).filter(Loan.status == "borrowed").scalar() or 0
    returned_loans = db.query(func.count(Loan.id)).filter(Loan.status == "returned").scalar() or 0
    total_fines = db.query(func.sum(Loan.fine_amount)).scalar() or 0

    loans_data = []
    books_data = []

    if report_type in ["loans", "returns", "fines"]:
        loan_query = db.query(Loan)
        if report_type == "returns":
            loan_query = loan_query.filter(Loan.status == "returned")
        elif report_type == "fines":
            loan_query = loan_query.filter(Loan.fine_amount > 0)
        elif status_filter in ["borrowed", "returned"]:
            loan_query = loan_query.filter(Loan.status == status_filter)

        if start_date:
            try:
                sd = datetime.strptime(start_date, "%Y-%m-%d")
                loan_query = loan_query.filter(Loan.loan_date >= sd)
            except ValueError:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
                loan_query = loan_query.filter(Loan.loan_date <= ed)
            except ValueError:
                pass

        loans_data = loan_query.order_by(Loan.id.desc()).all()
    elif report_type == "books":
        books_data = db.query(Book).order_by(Book.title.asc()).all()

    return templates.TemplateResponse(request, "reports/index.html", {
        "current_user": admin_user,
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "status_filter": status_filter,
        "total_books": total_books,
        "total_users": total_users,
        "total_loans": total_loans,
        "active_loans": active_loans,
        "returned_loans": returned_loans,
        "total_fines": total_fines,
        "loans_data": loans_data,
        "books_data": books_data
    })
