BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

ALTER TABLE users ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();
ALTER TABLE categories ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();
ALTER TABLE books ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();
ALTER TABLE loans ADD COLUMN id_uuid UUID DEFAULT gen_random_uuid();

ALTER TABLE books ADD COLUMN category_id_uuid UUID;
ALTER TABLE loans ADD COLUMN user_id_uuid UUID;
ALTER TABLE loans ADD COLUMN book_id_uuid UUID;

UPDATE books
SET category_id_uuid = categories.id_uuid
FROM categories
WHERE books.category_id = categories.id;

UPDATE loans
SET user_id_uuid = users.id_uuid
FROM users
WHERE loans.user_id = users.id;

UPDATE loans
SET book_id_uuid = books.id_uuid
FROM books
WHERE loans.book_id = books.id;

ALTER TABLE books DROP CONSTRAINT books_category_id_fkey;
ALTER TABLE loans DROP CONSTRAINT loans_user_id_fkey;
ALTER TABLE loans DROP CONSTRAINT loans_book_id_fkey;

ALTER TABLE users DROP CONSTRAINT users_pkey;
ALTER TABLE categories DROP CONSTRAINT categories_pkey;
ALTER TABLE books DROP CONSTRAINT books_pkey;
ALTER TABLE loans DROP CONSTRAINT loans_pkey;

ALTER TABLE users DROP COLUMN id;
ALTER TABLE categories DROP COLUMN id;
ALTER TABLE books DROP COLUMN id;
ALTER TABLE books DROP COLUMN category_id;
ALTER TABLE loans DROP COLUMN id;
ALTER TABLE loans DROP COLUMN user_id;
ALTER TABLE loans DROP COLUMN book_id;

ALTER TABLE users RENAME COLUMN id_uuid TO id;
ALTER TABLE categories RENAME COLUMN id_uuid TO id;
ALTER TABLE books RENAME COLUMN id_uuid TO id;
ALTER TABLE books RENAME COLUMN category_id_uuid TO category_id;
ALTER TABLE loans RENAME COLUMN id_uuid TO id;
ALTER TABLE loans RENAME COLUMN user_id_uuid TO user_id;
ALTER TABLE loans RENAME COLUMN book_id_uuid TO book_id;

ALTER TABLE users ADD PRIMARY KEY (id);
ALTER TABLE categories ADD PRIMARY KEY (id);
ALTER TABLE books ADD PRIMARY KEY (id);
ALTER TABLE loans ADD PRIMARY KEY (id);

ALTER TABLE books
    ADD CONSTRAINT books_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL;
ALTER TABLE loans
    ALTER COLUMN user_id SET NOT NULL,
    ALTER COLUMN book_id SET NOT NULL;
ALTER TABLE loans
    ADD CONSTRAINT loans_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE loans
    ADD CONSTRAINT loans_book_id_fkey
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_books_category ON books(category_id);
CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);
CREATE INDEX IF NOT EXISTS idx_loans_book ON loans(book_id);

COMMIT;