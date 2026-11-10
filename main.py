import os
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.services.db import init_db
from app.services.rate_limiter import limiter
from app.services.mongo_service import log_activity
from app.routers import auth_router, books_router, loans_router, admin_router, reports_router
from data.seed import run_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("perpustakaan_digital")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        run_seed()
    except Exception as e:
        logger.error(f"Seeding error: {e}")
    yield

app = FastAPI(
    title="Perpustakaan Digital",
    description="Sistem Peminjaman dan Pengembalian Buku Perpustakaan",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' https:; img-src 'self' data: https:;"
        return response

app.add_middleware(SecurityHeadersMiddleware)

templates = Jinja2Templates(directory="templates")

@app.exception_handler(RateLimitExceeded)
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    err_code = f"ERR-{uuid.uuid4().hex[:8].upper()}"
    log_activity(
        action="RATE_LIMIT_EXCEEDED",
        username="system",
        role="system",
        ip_address=request.client.host if request.client else "",
        details={"error_code": err_code, "path": request.url.path}
    )
    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "title": "Batas Permintaan Terlampaui",
            "detail": "Anda telah melakukan terlalu banyak permintaan dalam waktu singkat. Mohon tunggu beberapa saat.",
            "error_code": err_code,
            "current_user": None
        }, status_code=status.HTTP_429_TOO_MANY_REQUESTS)
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests", "error_code": err_code}
    )

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in [301, 302, 307, 308]:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(
            url=exc.headers.get("Location", "/"),
            status_code=exc.status_code
        )

    err_code = f"ERR-{uuid.uuid4().hex[:8].upper()}"
    client_ip = request.client.host if request.client else ""
    log_activity(
        action=f"HTTP_EXCEPTION_{exc.status_code}",
        username="guest",
        role="guest",
        ip_address=client_ip,
        details={"error_code": err_code, "path": request.url.path, "detail": str(exc.detail)}
    )

    if "text/html" in request.headers.get("accept", ""):
        title = "Halaman Tidak Ditemukan" if exc.status_code == 404 else ("Akses Ditolak" if exc.status_code == 403 else "Terjadi Kesalahan")
        return templates.TemplateResponse(request, "errors/error.html", {
            "title": title,
            "detail": str(exc.detail),
            "error_code": err_code,
            "current_user": None
        }, status_code=exc.status_code)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": err_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    err_code = f"ERR-{uuid.uuid4().hex[:8].upper()}"
    client_ip = request.client.host if request.client else ""
    logger.exception(f"Unhandled Exception [{err_code}]: {exc}")
    log_activity(
        action="SERVER_INTERNAL_ERROR",
        username="system",
        role="system",
        ip_address=client_ip,
        details={"error_code": err_code, "path": request.url.path, "error": str(exc)}
    )

    if "text/html" in request.headers.get("accept", ""):
        return templates.TemplateResponse(request, "errors/error.html", {
            "title": "Kesalahan Server Internal",
            "detail": "Terjadi gangguan teknis pada server kami. Silakan hubungi admin aplikasi dengan menyebutkan kode referensi di bawah ini.",
            "error_code": err_code,
            "current_user": None
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error", "error_code": err_code}
    )

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)
app.include_router(books_router)
app.include_router(loans_router)
app.include_router(admin_router)
app.include_router(reports_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
