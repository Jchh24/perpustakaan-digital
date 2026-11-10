import os
import uuid
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.services.auth_service import get_current_user_optional
from app.services.mongo_service import log_activity, get_recent_logs
from app.models.book import Book
from app.models.category import Category
from app.models.loan import Loan
from app.models.user import User
from app.services.isbn_validator import validate_isbn13, format_isbn13

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "static/images/uploads"
DEFAULT_NO_COVER = "/static/images/no_cover.svg"

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

async def save_uploaded_cover(file: UploadFile) -> str:
    if not file or not file.filename:
        return ""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        return ""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if not content:
        return ""
    with open(dest_path, "wb") as f:
        f.write(content)
    return f"/static/images/uploads/{filename}"

@router.get("/books", response_class=HTMLResponse)
def admin_books(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    books = db.query(Book).order_by(Book.id.desc()).all()
    categories = db.query(Category).order_by(Category.name.asc()).all()
    msg = request.query_params.get("msg")
    error = request.query_params.get("error")
    return templates.TemplateResponse(request, "admin/books.html", {
        "current_user": admin_user,
        "books": books,
        "categories": categories,
        "msg": msg,
        "error": error
    })

@router.post("/books/create")
async def admin_book_create(
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    publisher: str = Form(...),
    isbn: str = Form(...),
    publication_year: int = Form(...),
    location: str = Form(...),
    stock: int = Form(...),
    category_id: str = Form(""),
    cover_image_url: str = Form(""),
    cover_file: UploadFile = File(None),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_access(request, db)
    isbn = isbn.strip()
    if not validate_isbn13(isbn):
        return RedirectResponse(
            url="/admin/books?error=Nomor+ISBN+harus+format+ISBN-13+yang+valid+(contoh:+978-0-13-235088-4)",
            status_code=status.HTTP_302_FOUND
        )
    formatted_isbn = format_isbn13(isbn)
    existing = db.query(Book).filter(Book.isbn == formatted_isbn).first()
    if existing:
        return RedirectResponse(
            url="/admin/books?error=ISBN+sudah+terdaftar+pada+buku+lain",
            status_code=status.HTTP_302_FOUND
        )

    uploaded_path = await save_uploaded_cover(cover_file)
    if uploaded_path:
        final_cover = uploaded_path
    elif cover_image_url and cover_image_url.strip():
        final_cover = cover_image_url.strip()
    else:
        final_cover = DEFAULT_NO_COVER

    book = Book(
        title=title.strip(),
        author=author.strip(),
        publisher=publisher.strip(),
        isbn=formatted_isbn,
        publication_year=publication_year,
        location=location.strip(),
        stock=stock,
        available_stock=stock,
        category_id=category_id or None,
        cover_image=final_cover,
        description=description.strip() if description else None
    )
    db.add(book)
    db.commit()
    db.refresh(book)

    log_activity(
        action="BOOK_CREATED",
        username=admin_user.username,
        role=admin_user.role,
        user_id=admin_user.id,
        ip_address=request.client.host if request.client else "",
        details={"book_id": book.id, "title": book.title, "isbn": book.isbn}
    )

    return RedirectResponse(url="/admin/books?msg=Buku+berhasil+ditambahkan", status_code=status.HTTP_302_FOUND)

@router.post("/books/{book_id}/edit")
async def admin_book_edit(
    book_id: str,
    request: Request,
    title: str = Form(...),
    author: str = Form(...),
    publisher: str = Form(...),
    isbn: str = Form(...),
    publication_year: int = Form(...),
    location: str = Form(...),
    stock: int = Form(...),
    category_id: str = Form(""),
    cover_image_url: str = Form(""),
    cover_file: UploadFile = File(None),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_access(request, db)
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return RedirectResponse(url="/admin/books?error=Buku+tidak+ditemukan", status_code=status.HTTP_302_FOUND)

    isbn = isbn.strip()
    if not validate_isbn13(isbn):
        return RedirectResponse(
            url="/admin/books?error=Nomor+ISBN+harus+format+ISBN-13+yang+valid+(contoh:+978-0-13-235088-4)",
            status_code=status.HTTP_302_FOUND
        )
    formatted_isbn = format_isbn13(isbn)
    other_book = db.query(Book).filter(Book.isbn == formatted_isbn, Book.id != book_id).first()
    if other_book:
        return RedirectResponse(url="/admin/books?error=ISBN+sudah+digunakan+oleh+buku+lain", status_code=status.HTTP_302_FOUND)

    stock_diff = stock - book.stock
    book.stock = stock
    book.available_stock = max(0, book.available_stock + stock_diff)
    book.title = title.strip()
    book.author = author.strip()
    book.publisher = publisher.strip()
    book.isbn = formatted_isbn
    book.publication_year = publication_year
    book.location = location.strip()
    book.category_id = category_id or None

    uploaded_path = await save_uploaded_cover(cover_file)
    if uploaded_path:
        book.cover_image = uploaded_path
    elif cover_image_url and cover_image_url.strip():
        book.cover_image = cover_image_url.strip()

    book.description = description.strip() if description else None

    db.commit()

    log_activity(
        action="BOOK_UPDATED",
        username=admin_user.username,
        role=admin_user.role,
        user_id=admin_user.id,
        ip_address=request.client.host if request.client else "",
        details={"book_id": book.id, "title": book.title}
    )

    return RedirectResponse(url="/admin/books?msg=Buku+berhasil+diperbarui", status_code=status.HTTP_302_FOUND)

@router.post("/books/{book_id}/delete")
def admin_book_delete(book_id: str, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return RedirectResponse(url="/admin/books?error=Buku+tidak+ditemukan", status_code=status.HTTP_302_FOUND)

    active_loans = db.query(Loan).filter(Loan.book_id == book_id, Loan.status == "borrowed").count()
    if active_loans > 0:
        return RedirectResponse(
            url="/admin/books?error=Buku+tidak+dapat+dihapus+karena+masih+sedang+dipinjam",
            status_code=status.HTTP_302_FOUND
        )

    title = book.title
    db.delete(book)
    db.commit()

    log_activity(
        action="BOOK_DELETED",
        username=admin_user.username,
        role=admin_user.role,
        user_id=admin_user.id,
        ip_address=request.client.host if request.client else "",
        details={"book_id": book_id, "title": title}
    )

    return RedirectResponse(url="/admin/books?msg=Buku+berhasil+dihapus", status_code=status.HTTP_302_FOUND)

@router.get("/loans", response_class=HTMLResponse)
def admin_loans(request: Request, status_filter: str = "all", db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    query = db.query(Loan)
    if status_filter in ["borrowed", "returned"]:
        query = query.filter(Loan.status == status_filter)

    loans = query.order_by(Loan.id.desc()).all()
    msg = request.query_params.get("msg")
    error = request.query_params.get("error")

    return templates.TemplateResponse(request, "admin/loans.html", {
        "current_user": admin_user,
        "loans": loans,
        "status_filter": status_filter,
        "msg": msg,
        "error": error
    })

@router.get("/categories", response_class=HTMLResponse)
def admin_categories(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    categories = db.query(Category).order_by(Category.name.asc()).all()
    msg = request.query_params.get("msg")
    error = request.query_params.get("error")
    return templates.TemplateResponse(request, "admin/categories.html", {
        "current_user": admin_user,
        "categories": categories,
        "msg": msg,
        "error": error
    })

@router.post("/categories/create")
def admin_category_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    admin_user = verify_admin_access(request, db)
    name = name.strip()
    existing = db.query(Category).filter(Category.name.ilike(name)).first()
    if existing:
        return RedirectResponse(url="/admin/categories?error=Kategori+sudah+ada", status_code=status.HTTP_302_FOUND)

    category = Category(name=name, description=description.strip() if description else None)
    db.add(category)
    db.commit()

    log_activity(
        action="CATEGORY_CREATED",
        username=admin_user.username,
        role=admin_user.role,
        user_id=admin_user.id,
        ip_address=request.client.host if request.client else "",
        details={"category_name": name}
    )

    return RedirectResponse(url="/admin/categories?msg=Kategori+berhasil+ditambahkan", status_code=status.HTTP_302_FOUND)

@router.post("/categories/{category_id}/delete")
def admin_category_delete(category_id: str, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    category = db.query(Category).filter(Category.id == category_id).first()
    if category:
        db.delete(category)
        db.commit()
    return RedirectResponse(url="/admin/categories?msg=Kategori+berhasil+dihapus", status_code=status.HTTP_302_FOUND)

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    users = db.query(User).order_by(User.id.desc()).all()
    msg = request.query_params.get("msg")
    return templates.TemplateResponse(request, "admin/users.html", {
        "current_user": admin_user,
        "users": users,
        "msg": msg
    })

@router.post("/users/{user_id}/toggle-status")
def admin_user_toggle(user_id: str, request: Request, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    if user_id == admin_user.id:
        return RedirectResponse(url="/admin/users?error=Tidak+dapat+menonaktifkan+akun+sendiri", status_code=status.HTTP_302_FOUND)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = not user.is_active
        db.commit()
    return RedirectResponse(url="/admin/users?msg=Status+pengguna+berhasil+diperbarui", status_code=status.HTTP_302_FOUND)

@router.get("/logs", response_class=HTMLResponse)
def admin_logs(request: Request, limit: int = 100, db: Session = Depends(get_db)):
    admin_user = verify_admin_access(request, db)
    logs = get_recent_logs(limit=limit)
    return templates.TemplateResponse(request, "admin/logs.html", {
        "current_user": admin_user,
        "logs": logs,
        "limit": limit
    })
