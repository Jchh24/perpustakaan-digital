from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.services.db import get_db
from app.services.auth_service import get_current_user_optional
from app.models.book import Book
from app.models.category import Category

router = APIRouter(tags=["books"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    q: str = "",
    category_id: str = "",
    db: Session = Depends(get_db)
):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    query = db.query(Book)
    if q.strip():
        term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Book.title.ilike(term),
                Book.author.ilike(term),
                Book.isbn.ilike(term),
                Book.location.ilike(term)
            )
        )
    if category_id:
        query = query.filter(Book.category_id == category_id)

    books = query.order_by(Book.id.desc()).all()
    categories = db.query(Category).order_by(Category.name.asc()).all()

    return templates.TemplateResponse(request, "dashboard/index.html", {
        "current_user": current_user,
        "books": books,
        "categories": categories,
        "q": q,
        "category_id": category_id
    })

@router.get("/books/{book_id}", response_class=HTMLResponse)
def book_detail(book_id: str, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_optional(request, db)
    if not current_user:
        return RedirectResponse(url=f"/auth/login?next=/books/{book_id}", status_code=status.HTTP_302_FOUND)

    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buku tidak ditemukan")

    msg = request.query_params.get("msg")
    error = request.query_params.get("error")

    return templates.TemplateResponse(request, "books/detail.html", {
        "current_user": current_user,
        "book": book,
        "msg": msg,
        "error": error
    })
