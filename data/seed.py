import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.db import SessionLocal, init_db
from app.services.auth_service import hash_password
from app.models.user import User
from app.models.category import Category
from app.models.book import Book

def run_seed():
    init_db()
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@perpustakaan.lan",
                full_name="Administrator Perpustakaan",
                hashed_password=hash_password("Admin123!"),
                role="admin",
                is_active=True
            )
            db.add(admin)

        if not db.query(User).filter(User.username == "member").first():
            member = User(
                username="member",
                email="member@perpustakaan.lan",
                full_name="Budi Pratama",
                hashed_password=hash_password("Member123!"),
                role="member",
                is_active=True
            )
            db.add(member)

        categories_data = [
            ("Ilmu Komputer", "Buku seputar pemrograman, rekayasa perangkat lunak, dan kecerdasan buatan"),
            ("Sains & Teknologi", "Buku matematika, fisika modern, astronomi, dan riset teknologi"),
            ("Sastra & Fiksi", "Novel, kumpulan cerpen, puisi, dan karya literatur klasik"),
            ("Bisnis & Manajemen", "Buku kewirausahaan, keuangan, pemasaran, dan manajemen organisasi"),
            ("Sejarah & Filsafat", "Kajian sejarah peradaban dunia, budaya nusantara, dan pemikiran filsafat")
        ]

        cat_map = {}
        for name, desc in categories_data:
            cat = db.query(Category).filter(Category.name == name).first()
            if not cat:
                cat = Category(name=name, description=desc)
                db.add(cat)
                db.commit()
                db.refresh(cat)
            cat_map[name] = cat.id

        books_data = [
            {
                "title": "Clean Code: A Handbook of Agile Software Craftsmanship",
                "author": "Robert C. Martin",
                "publisher": "Prentice Hall",
                "isbn": "978-0132350884",
                "publication_year": 2008,
                "location": "Rak TI-01, Lantai 2",
                "stock": 5,
                "cover_image": "/static/images/clean_code.jpg",
                "description": "Pedoman legendaris tentang penulisan kode yang bersih, mudah dibaca, dan mudah dipelihara.",
                "category_id": cat_map.get("Ilmu Komputer")
            },
            {
                "title": "Design Patterns: Elements of Reusable Object-Oriented Software",
                "author": "Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
                "publisher": "Addison-Wesley",
                "isbn": "978-0201633610",
                "publication_year": 1994,
                "location": "Rak TI-02, Lantai 2",
                "stock": 4,
                "cover_image": "/static/images/design_patterns.jpg",
                "description": "Koleksi 23 pola desain klasik berorientasi objek karya Gang of Four.",
                "category_id": cat_map.get("Ilmu Komputer")
            },
            {
                "title": "Laskar Pelangi",
                "author": "Andrea Hirata",
                "publisher": "Bentang Pustaka",
                "isbn": "978-9791227179",
                "publication_year": 2005,
                "location": "Rak SF-03, Lantai 1",
                "stock": 7,
                "cover_image": "/static/images/laskar_pelangi.jpg",
                "description": "Kisah inspiratif perjuangan sepuluh anak di Belitung dalam menempuh pendidikan.",
                "category_id": cat_map.get("Sastra & Fiksi")
            },
            {
                "title": "Bumi Manusia",
                "author": "Pramoedya Ananta Toer",
                "publisher": "Hasta Mitra",
                "isbn": "978-9799731234",
                "publication_year": 1980,
                "location": "Rak SF-04, Lantai 1",
                "stock": 6,
                "cover_image": "/static/images/bumi_manusia.jpg",
                "description": "Mahakarya sastra Indonesia mengisahkan pergulatan Minke di era kolonial Hindia Belanda.",
                "category_id": cat_map.get("Sastra & Fiksi")
            },
            {
                "title": "A Brief History of Time",
                "author": "Stephen Hawking",
                "publisher": "Bantam Books",
                "isbn": "978-0553380163",
                "publication_year": 1988,
                "location": "Rak SN-01, Lantai 2",
                "stock": 3,
                "cover_image": "/static/images/brief_history.jpg",
                "description": "Eksplorasi kosmologi modern, lubang hitam, teori dentuman besar, dan sifat ruang-waktu.",
                "category_id": cat_map.get("Sains & Teknologi")
            },
            {
                "title": "The Lean Startup",
                "author": "Eric Ries",
                "publisher": "Crown Business",
                "isbn": "978-0307887894",
                "publication_year": 2011,
                "location": "Rak BM-01, Lantai 1",
                "stock": 5,
                "cover_image": "/static/images/lean_startup.jpg",
                "description": "Metodologi inovasi berkelanjutan dan pembangunan bisnis rintisan yang teruji.",
                "category_id": cat_map.get("Bisnis & Manajemen")
            }
        ]

        for b in books_data:
            if not db.query(Book).filter(Book.isbn == b["isbn"]).first():
                book = Book(
                    title=b["title"],
                    author=b["author"],
                    publisher=b["publisher"],
                    isbn=b["isbn"],
                    publication_year=b["publication_year"],
                    location=b["location"],
                    stock=b["stock"],
                    available_stock=b["stock"],
                    cover_image=b["cover_image"],
                    description=b["description"],
                    category_id=b["category_id"]
                )
                db.add(book)

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    run_seed()
