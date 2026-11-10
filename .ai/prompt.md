saya ingin membuat sebuah aplikasi untuk meminjam dan mengembalikan buku perpustakaan, nama aplikasinya perpustakaan digital, framework FastAPI dengan backend menggunakan python, database postgresql untuk datanya dan mongodb untuk activity log, struktur file project:

app:
  models
  routers
  schemas
  services
data
static
templates
main.py

security requirement:
SALT + PEPPER + hash password bcrypt
Error handling umum (berikan kode kepada pengguna untuk ditanya ke admin aplikasi)
Pakai https
httponly dan secure cookies
Rate limitting
Prepared statement dan parameterized query
Authorization check di server 
Pengguna harus login
Security requirement umum lainnya 

Pages requirement:
Login 
Register
Dashboard (tampilin cover buku dan judul buku, search bar, navbar untuk ganti akun dan logout)
Informasi detail buku (cover, judul buku, isbn, lokasi buku, dll serta tombol peminjaman buku)
Halaman lainnya yang umum di website perpustakaan

RBAC:
Administator ngelakuin penambahan/penghapusan daftar buku, ngeliat siapa meminjam buku apa
Pengguna ngelakuin peminjaman buku dan durasi peminjaman buku

langsung jadi dalam satu zip aja, kode program tidak perlu ada komen didalamnya