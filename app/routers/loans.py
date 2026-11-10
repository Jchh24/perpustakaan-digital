from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.services.auth_service import get_current_user_optional
from app.services.mongo_service import log_activity
from app.services.rate_limiter import limiter
from app.models.book import Book
from app.models.loan import Loan

router = APIRouter(prefix="/loans", tags=["loans"])
templates = Jinja2Templates(directory="templates")

DAILY_FINE = 1000

@router.post("/borrow")
@limiter.limit("15/minute")
def borrow_book(
    request: Request,
    book_id: str = Form(...),
    duration_days: int = Form(7),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    if duration_days < 1 or duration_days > 30:
        return RedirectResponse(
            url=f"/books/{book_id}?error=Durasi+peminjaman+antara+1+hingga+30+hari",
            status_code=status.HTTP_302_FOUND
        )

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return RedirectResponse(
            url="/?error=Buku+tidak+ditemukan",
            status_code=status.HTTP_302_FOUND
        )

    if book.available_stock <= 0:
        return RedirectResponse(
            url=f"/books/{book_id}?error=Stok+buku+saat+ini+sedang+kosong",
            status_code=status.HTTP_302_FOUND
        )

    active_same_loan = db.query(Loan).filter(
        Loan.user_id == current_user.id,
        Loan.book_id == book.id,
        Loan.status == "borrowed"
    ).first()
    if active_same_loan:
        return RedirectResponse(
            url=f"/books/{book_id}?error=Anda+sedang+meminjam+buku+ini",
            status_code=status.HTTP_302_FOUND
        )

    now = datetime.now(timezone.utc)
    due = now + timedelta(days=duration_days)

    loan = Loan(
        user_id=current_user.id,
        book_id=book.id,
        loan_date=now,
        due_date=due,
        status="borrowed",
        fine_amount=0,
        notes=notes.strip() if notes else None
    )
    book.available_stock -= 1

    db.add(loan)
    db.commit()
    db.refresh(loan)

    log_activity(
        action="BOOK_BORROWED",
        username=current_user.username,
        role=current_user.role,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else "",
        details={
            "loan_id": loan.id,
            "book_id": book.id,
            "book_title": book.title,
            "duration_days": duration_days,
            "due_date": due.isoformat()
        }
    )

    return RedirectResponse(
        url="/loans/my-loans?msg=Peminjaman+buku+berhasil+dilakukan",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/my-loans", response_class=HTMLResponse)
def my_loans(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login?next=/loans/my-loans", status_code=status.HTTP_302_FOUND)

    loans = db.query(Loan).filter(Loan.user_id == current_user.id).order_by(Loan.id.desc()).all()
    now = datetime.now(timezone.utc)

    for loan in loans:
        if loan.status == "borrowed":
            due = loan.due_date.replace(tzinfo=timezone.utc) if loan.due_date.tzinfo is None else loan.due_date
            if now > due:
                overdue_days = (now.date() - due.date()).days
                loan.calculated_fine = max(0, overdue_days * DAILY_FINE)
                loan.is_overdue = True
            else:
                loan.calculated_fine = 0
                loan.is_overdue = False
        else:
            loan.calculated_fine = loan.fine_amount
            loan.is_overdue = False

    msg = request.query_params.get("msg")
    error = request.query_params.get("error")

    return templates.TemplateResponse(request, "loans/my_loans.html", {
        "current_user": current_user,
        "loans": loans,
        "msg": msg,
        "error": error
    })

@router.post("/{loan_id}/return")
def return_book(
    loan_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        return RedirectResponse(url="/loans/my-loans?error=Data+peminjaman+tidak+ditemukan", status_code=status.HTTP_302_FOUND)

    if current_user.role != "admin" and loan.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak")

    if loan.status == "returned":
        return RedirectResponse(url="/loans/my-loans?error=Buku+ini+sudah+dikembalikan", status_code=status.HTTP_302_FOUND)

    now = datetime.now(timezone.utc)
    due = loan.due_date.replace(tzinfo=timezone.utc) if loan.due_date.tzinfo is None else loan.due_date
    fine = 0
    if now > due:
        overdue_days = (now.date() - due.date()).days
        fine = max(0, overdue_days * DAILY_FINE)

    loan.return_date = now
    loan.status = "returned"
    loan.fine_amount = fine

    book = db.query(Book).filter(Book.id == loan.book_id).first()
    if book:
        book.available_stock = min(book.stock, book.available_stock + 1)

    db.commit()

    log_activity(
        action="BOOK_RETURNED",
        username=current_user.username,
        role=current_user.role,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else "",
        details={
            "loan_id": loan.id,
            "book_id": book.id if book else None,
            "fine_amount": fine
        }
    )

    redirect_target = "/admin/loans" if (current_user.role == "admin" and request.headers.get("referer", "").endswith("/admin/loans")) else "/loans/my-loans"
    return RedirectResponse(
        url=f"{redirect_target}?msg=Buku+berhasil+dikembalikan.+Denda:+Rp+{fine:,}",
        status_code=status.HTTP_302_FOUND
    )
