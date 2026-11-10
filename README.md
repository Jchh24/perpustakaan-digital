# Perpustakaan Digital

Aplikasi web modern manajemen peminjaman dan pengembalian buku perpustakaan berbasis FastAPI, PostgreSQL (Master & Transaksi), dan MongoDB (Activity Logs).

---

## Fitur Utama

### 1. File Master
- **Master Data Buku**: Penambahan, pengubahan, penghapusan, informasi ISBN, lokasi rak fisik, jumlah eksemplar, stok tersedia, dan cover visual.
- **Master Data Kategori**: Pengelompokan buku berdasarkan klasifikasi disiplin ilmu.
- **Master Data Anggota / Pengguna**: Pengelolaan hak akses dan status akun anggota.

### 2. File Transaksi
- **Peminjaman Buku**: Pemilihan durasi peminjaman (1 hingga 30 hari), validasi ketersediaan stok, pencegahan peminjaman ganda, serta pencatatan otomatis tanggal jatuh tempo.
- **Pengembalian Buku**: Restorasi kuota stok buku, validasi waktu pengembalian, dan perhitungan denda otomatis keterlambatan (Rp 1.000 / hari).

### 3. File Laporan (Report)
- **Laporan Peminjaman**: Riwayat peminjaman buku dengan filter tanggal dan status.
- **Laporan Pengembalian**: Rekapitulasi buku yang telah dikembalikan.
- **Laporan Denda**: Rekapitulasi akumulasi denda keterlambatan.
- **Laporan Master Buku**: Rekap data seluruh inventaris buku beserta lokasi rak.
- **Siap Cetak**: Dilengkapi tombol cetak laporan dengan tata letak resmi dan format ramah cetak (`@media print`).

### 4. Audit Log (MongoDB)
- Audit trail mencatat seluruh aktivitas autentikasi, transaksi buku, manipulasi master data, hingga insiden keamanan beserta alamat IP klien.

---

## Standar Keamanan

1. **SALT + PEPPER + Bcrypt**: Pengacakan password menggunakan pepper rahasia sisi server digabung salt dinamis per hash bcrypt.
2. **Error Handling Terpadu**: Halaman kesalahan menghasilkan kode referensi unik (`ERR-XXXXXX`) untuk mempermudah investigasi tanpa mengekspos rincian sensitif sistem ke pengguna umum.
3. **HTTPOnly & Secure Cookies**: Token sesi disimpan dalam cookie bertipe `HttpOnly`, `SameSite=Lax`, dan flag `Secure` pada koneksi HTTPS.
4. **Rate Limiting**: Pembatasan frekuensi permintaan pada aksi sensitif (login, registrasi, peminjaman).
5. **Parameterized Queries / Prepared Statements**: Eksekusi query basis data via SQLAlchemy ORM untuk mencegah SQL Injection.
6. **Server-Side RBAC**: Validasi kewenangan peran (Administrator dan Member) di backend pada setiap rute.
7. **Security Headers**: Penerapan header standar industri (`Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`).

---

## Kredensial Bawaan

| Peran | Username | Password | Akses |
|---|---|---|---|
| Administrator | `admin` | `Admin123!` | Akses penuh (Katalog, Master Buku, Kategori, Transaksi, Laporan, Log MongoDB) |
| Anggota (Member) | `member` | `Member123!` | Akses katalog, peminjaman buku, pengembalian buku, riwayat pinjaman |

---

## Cara Menjalankan Secara Lokal

### 1. Mengaktifkan Lingkungan Python
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.venv\Scripts\Activate.ps1
```

### 2. Menginisialisasi Basis Data (Opsional jika ingin menggunakan PostgreSQL langsung)
```powershell
.\app\schemas\setup_cli.ps1
```
*Catatan: Jika PostgreSQL belum terpasang di komputer lokal, aplikasi secara otomatis menggunakan SQLite bawaan di `./data/perpustakaan.db` sehingga dapat langsung berjalan tanpa konfigurasi tambahan.*

### 3. Menjalankan Server
```powershell
uvicorn main:app --reload --port 8000
```
Buka peramban di `http://localhost:8000`.

---

## Panduan Hosting Gratis (Free Hosting)

Aplikasi ini sudah dilengkapi berkas konfigurasi siap pakai:
- **Render.com**: Gunakan `render.yaml` untuk pembuatan PostgreSQL dan Web Service gratis secara otomatis.
- **Railway.app**: Pasang repository GitHub ke Railway, tambahkan plugin PostgreSQL dan MongoDB.
- **Koyeb / Fly.io**: Gunakan `Dockerfile` yang telah disediakan.
