CREATE DATABASE perpustakaan_digital;

\c perpustakaan_digital;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'member' NOT NULL CHECK (role IN ('admin', 'member')),
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100) NOT NULL,
    isbn VARCHAR(30) UNIQUE NOT NULL,
    publication_year INT NOT NULL CHECK (publication_year >= 1800 AND publication_year <= 2100),
    location VARCHAR(100) NOT NULL,
    stock INT DEFAULT 1 NOT NULL CHECK (stock >= 0),
    available_stock INT DEFAULT 1 NOT NULL CHECK (available_stock >= 0),
    cover_image VARCHAR(255) DEFAULT '/static/images/default_cover.png' NOT NULL,
    description TEXT,
    category_id INT REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    book_id INT REFERENCES books(id) ON DELETE CASCADE NOT NULL,
    loan_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    return_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'borrowed' NOT NULL CHECK (status IN ('borrowed', 'returned', 'overdue')),
    fine_amount INT DEFAULT 0 NOT NULL CHECK (fine_amount >= 0),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn);
CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);
CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);
CREATE INDEX IF NOT EXISTS idx_loans_book ON loans(book_id);
CREATE INDEX IF NOT EXISTS idx_loans_status ON loans(status);

INSERT INTO categories (name, description) VALUES
('Ilmu Komputer', 'Buku seputar pemrograman, rekayasa perangkat lunak, dan kecerdasan buatan'),
('Sains & Teknologi', 'Buku matematika, fisika modern, astronomi, dan riset teknologi'),
('Sastra & Fiksi', 'Novel, kumpulan cerpen, puisi, dan karya literatur klasik'),
('Bisnis & Manajemen', 'Buku kewirausahaan, keuangan, pemasaran, dan manajemen organisasi'),
('Sejarah & Filsafat', 'Kajian sejarah peradaban dunia, budaya nusantara, dan pemikiran filsafat')
ON CONFLICT (name) DO NOTHING;

INSERT INTO users (username, email, full_name, hashed_password, role, is_active) VALUES
('admin', 'admin@perpustakaan.lan', 'Administrator Perpustakaan', '$2b$12$6KxG6/QW9H1l7oY4jZfV2.B4zDqL.qYgX4.kF6w0sXJd1K5pBq2u.', 'admin', TRUE),
('member', 'member@perpustakaan.lan', 'Budi Pratama', '$2b$12$6KxG6/QW9H1l7oY4jZfV2.B4zDqL.qYgX4.kF6w0sXJd1K5pBq2u.', 'member', TRUE)
ON CONFLICT (username) DO NOTHING;

INSERT INTO books (title, author, publisher, isbn, publication_year, location, stock, available_stock, cover_image, description, category_id) VALUES
('Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 'Prentice Hall', '978-0132350884', 2008, 'Rak TI-01, Lantai 2', 5, 5, '/static/images/clean_code.jpg', 'Pedoman legendaris tentang penulisan kode yang bersih, mudah dibaca, dan mudah dipelihara.', 1),
('Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides', 'Addison-Wesley', '978-0201633610', 1994, 'Rak TI-02, Lantai 2', 4, 4, '/static/images/design_patterns.jpg', 'Koleksi 23 pola desain klasik berorientasi objek karya Gang of Four.', 1),
('Laskar Pelangi', 'Andrea Hirata', 'Bentang Pustaka', '978-9791227179', 2005, 'Rak SF-03, Lantai 1', 7, 7, '/static/images/laskar_pelangi.jpg', 'Kisah inspiratif perjuangan sepuluh anak di Belitung dalam menempuh pendidikan.', 3),
('Bumi Manusia', 'Pramoedya Ananta Toer', 'Hasta Mitra', '978-9799731234', 1980, 'Rak SF-04, Lantai 1', 6, 6, '/static/images/bumi_manusia.jpg', 'Mahakarya sastra Indonesia mengisahkan pergulatan Minke di era kolonial Hindia Belanda.', 3),
('A Brief History of Time', 'Stephen Hawking', 'Bantam Books', '978-0553380163', 1988, 'Rak SN-01, Lantai 2', 3, 3, '/static/images/brief_history.jpg', 'Eksplorasi kosmologi modern, lubang hitam, teori dentuman besar, dan sifat ruang-waktu.', 2),
('The Lean Startup', 'Eric Ries', 'Crown Business', '978-0307887894', 2011, 'Rak BM-01, Lantai 1', 5, 5, '/static/images/lean_startup.jpg', 'Metodologi inovasi berkelanjutan dan pembangunan bisnis rintisan yang teruji.', 4)
ON CONFLICT (isbn) DO NOTHING;
