from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.services.db import get_db
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
    get_current_user,
    COOKIE_NAME
)
from app.services.mongo_service import log_activity
from app.services.rate_limiter import limiter
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
@limiter.limit("30/minute")
def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    error = request.query_params.get("error")
    msg = request.query_params.get("msg")
    next_url = request.query_params.get("next", "/")
    return templates.TemplateResponse(request, "auth/login.html", {
        "error": error,
        "msg": msg,
        "next": next_url,
        "current_user": None
    })

@router.post("/login")
@limiter.limit("10/minute")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username.strip()).first()
    client_ip = request.client.host if request.client else ""

    if not user or not verify_password(password, user.hashed_password):
        log_activity(
            action="LOGIN_FAILED",
            username=username,
            role="unknown",
            ip_address=client_ip,
            details={"reason": "Invalid credentials"}
        )
        return RedirectResponse(
            url=f"/auth/login?error=Username+atau+password+salah&next={next}",
            status_code=status.HTTP_302_FOUND
        )

    if not user.is_active:
        log_activity(
            action="LOGIN_BLOCKED",
            username=username,
            role=user.role,
            user_id=user.id,
            ip_address=client_ip,
            details={"reason": "Account inactive"}
        )
        return RedirectResponse(
            url="/auth/login?error=Akun+dinonaktifkan.+Hubungi+administrator.",
            status_code=status.HTTP_302_FOUND
        )

    token = create_access_token(user.id, user.username, user.role)
    log_activity(
        action="LOGIN_SUCCESS",
        username=user.username,
        role=user.role,
        user_id=user.id,
        ip_address=client_ip
    )

    target_url = next if next and next.startswith("/") else "/"
    response = RedirectResponse(url=target_url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="lax",
        max_age=86400
    )
    return response

@router.get("/register", response_class=HTMLResponse)
@limiter.limit("30/minute")
def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    error = request.query_params.get("error")
    return templates.TemplateResponse(request, "auth/register.html", {
        "error": error,
        "current_user": None
    })

@router.post("/register")
@limiter.limit("10/minute")
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else ""
    username = username.strip()
    email = email.strip()
    full_name = full_name.strip()

    if len(username) < 3 or len(password) < 6:
        return RedirectResponse(
            url="/auth/register?error=Username+minimal+3+karakter+dan+password+minimal+6+karakter",
            status_code=status.HTTP_302_FOUND
        )

    if password != confirm_password:
        return RedirectResponse(
            url="/auth/register?error=Konfirmasi+password+tidak+cocok",
            status_code=status.HTTP_302_FOUND
        )

    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        return RedirectResponse(
            url="/auth/register?error=Username+atau+email+sudah+terdaftar",
            status_code=status.HTTP_302_FOUND
        )

    hashed = hash_password(password)
    user_count = db.query(User).count()
    assigned_role = "admin" if user_count == 0 else "member"

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed,
        role=assigned_role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_activity(
        action="REGISTER_SUCCESS",
        username=new_user.username,
        role=new_user.role,
        user_id=new_user.id,
        ip_address=client_ip
    )

    return RedirectResponse(
        url="/auth/login?msg=Pendaftaran+berhasil!+Silakan+masuk.",
        status_code=status.HTTP_302_FOUND
    )

@router.get("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    client_ip = request.client.host if request.client else ""
    if user:
        log_activity(
            action="LOGOUT",
            username=user.username,
            role=user.role,
            user_id=user.id,
            ip_address=client_ip
        )
    response = RedirectResponse(url="/auth/login?msg=Anda+telah+berhasil+keluar", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=COOKIE_NAME)
    return response

@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/auth/login?next=/auth/profile", status_code=status.HTTP_302_FOUND)
    msg = request.query_params.get("msg")
    error = request.query_params.get("error")
    return templates.TemplateResponse(request, "auth/profile.html", {
        "current_user": user,
        "msg": msg,
        "error": error
    })

@router.post("/profile")
def profile_update(
    request: Request,
    full_name: str = Form(...),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    user.full_name = full_name.strip()
    if new_password:
        if len(new_password) < 6:
            return RedirectResponse(url="/auth/profile?error=Password+baru+minimal+6+karakter", status_code=status.HTTP_302_FOUND)
        if new_password != confirm_password:
            return RedirectResponse(url="/auth/profile?error=Konfirmasi+password+baru+tidak+cocok", status_code=status.HTTP_302_FOUND)
        user.hashed_password = hash_password(new_password)

    db.commit()
    log_activity(
        action="PROFILE_UPDATED",
        username=user.username,
        role=user.role,
        user_id=user.id,
        ip_address=request.client.host if request.client else ""
    )
    return RedirectResponse(url="/auth/profile?msg=Profil+berhasil+diperbarui", status_code=status.HTTP_302_FOUND)
