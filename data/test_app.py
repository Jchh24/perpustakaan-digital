import os
import sys
import asyncio
import urllib.parse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.services.db import SessionLocal, init_db
from app.models.book import Book
from data.seed import run_seed

async def asgi_request(app, method="GET", path="/", headers=None, body=b"", cookies=None):
    parsed = urllib.parse.urlparse(path)
    path_only = parsed.path
    query_string = parsed.query.encode("utf-8")
    
    hdr_list = []
    if headers:
        for k, v in headers.items():
            hdr_list.append((k.lower().encode("utf-8"), v.encode("utf-8")))
    if cookies:
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        hdr_list.append((b"cookie", cookie_str.encode("utf-8")))
    
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path_only,
        "raw_path": path_only.encode("utf-8"),
        "query_string": query_string,
        "headers": hdr_list,
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 8000),
        "scheme": "http",
    }
    
    messages = []
    body_sent = False
    
    async def receive():
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}
        
    async def send(message):
        messages.append(message)
        
    await app(scope, receive, send)
    
    status_code = None
    resp_headers = {}
    resp_body = b""
    
    for msg in messages:
        if msg["type"] == "http.response.start":
            status_code = msg["status"]
            for hk, hv in msg.get("headers", []):
                resp_headers[hk.decode("utf-8").lower()] = hv.decode("utf-8")
        elif msg["type"] == "http.response.body":
            resp_body += msg.get("body", b"")
            
    return status_code, resp_headers, resp_body.decode("utf-8", errors="replace")

def parse_set_cookie(cookie_header):
    if not cookie_header:
        return {}
    cookies = {}
    for part in cookie_header.split(";"):
        if "=" in part:
            k, v = part.strip().split("=", 1)
            if k not in ["path", "expires", "domain", "samesite", "httponly", "secure", "max-age"]:
                cookies[k] = v
    return cookies

async def run_tests():
    init_db()
    run_seed()
    status, headers, text = await asgi_request(app, "GET", "/auth/login")
    assert status == 200
    assert "Masuk ke Akun" in text
    
    body = urllib.parse.urlencode({"username": "admin", "password": "wrongpassword"}).encode("utf-8")
    status, headers, text = await asgi_request(
        app, "POST", "/auth/login",
        headers={"content-type": "application/x-www-form-urlencoded"},
        body=body
    )
    assert status == 302
    assert "error=" in headers.get("location", "")
    
    body = urllib.parse.urlencode({"username": "admin", "password": "Admin123!"}).encode("utf-8")
    status, headers, text = await asgi_request(
        app, "POST", "/auth/login",
        headers={"content-type": "application/x-www-form-urlencoded"},
        body=body
    )
    assert status == 302
    admin_cookie = parse_set_cookie(headers.get("set-cookie")).get("access_token")
    assert admin_cookie is not None
    
    body = urllib.parse.urlencode({"username": "member", "password": "Member123!"}).encode("utf-8")
    status, headers, text = await asgi_request(
        app, "POST", "/auth/login",
        headers={"content-type": "application/x-www-form-urlencoded"},
        body=body
    )
    assert status == 302
    member_cookie = parse_set_cookie(headers.get("set-cookie")).get("access_token")
    assert member_cookie is not None

    db = SessionLocal()
    book_id = str(db.query(Book).filter(Book.isbn == "978-0132350884").one().id)
    db.close()
    
    status, headers, text = await asgi_request(
        app, "GET", "/",
        cookies={"access_token": member_cookie}
    )
    assert status == 200
    assert "Katalog Buku" in text
    assert "Clean Code" in text
    
    status, headers, text = await asgi_request(
        app, "GET", f"/books/{book_id}",
        cookies={"access_token": member_cookie}
    )
    assert status == 200
    assert "Robert C. Martin" in text
    assert "Form Peminjaman Buku" in text
    
    db = SessionLocal()
    b_before = db.query(Book).filter(Book.id == book_id).first()
    stock_before = b_before.available_stock
    db.close()
    
    body = urllib.parse.urlencode({"book_id": book_id, "duration_days": "7", "notes": "Riset"}).encode("utf-8")
    status, headers, text = await asgi_request(
        app, "POST", "/loans/borrow",
        headers={"content-type": "application/x-www-form-urlencoded"},
        body=body,
        cookies={"access_token": member_cookie}
    )
    assert status == 302
    
    db = SessionLocal()
    b_after = db.query(Book).filter(Book.id == book_id).first()
    assert b_after.available_stock == stock_before - 1
    db.close()
    
    status, headers, text = await asgi_request(
        app, "GET", "/loans/my-loans",
        cookies={"access_token": member_cookie}
    )
    assert status == 200
    assert "Clean Code" in text
    assert "Sedang Dipinjam" in text
    
    status, headers, text = await asgi_request(
        app, "GET", "/admin/books",
        cookies={"access_token": member_cookie}
    )
    assert status in [403, 307]
    
    status, headers, text = await asgi_request(
        app, "GET", "/admin/books",
        cookies={"access_token": admin_cookie}
    )
    assert status == 200
    assert "Manajemen Master Data Buku" in text
    
    status, headers, text = await asgi_request(
        app, "GET", "/reports",
        cookies={"access_token": admin_cookie}
    )
    assert status == 200
    assert "LAPORAN" in text
    
    status, headers, text = await asgi_request(
        app, "GET", "/admin/logs",
        cookies={"access_token": admin_cookie}
    )
    assert status == 200
    assert "Activity Logs" in text
    
    status, headers, text = await asgi_request(
        app, "GET", "/halaman-yang-tidak-ada-404"
    )
    assert status == 404
    assert "ERR-" in text
    
    status, headers, text = await asgi_request(app, "GET", "/auth/login")
    assert headers.get("x-frame-options") == "DENY"
    assert headers.get("x-content-type-options") == "nosniff"
    assert "content-security-policy" in headers
    
    print("ALL 15 INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_tests())
