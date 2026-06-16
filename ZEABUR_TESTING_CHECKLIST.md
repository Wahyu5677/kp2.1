# Zeabur Deployment Testing Checklist (Detail 1-5)

Dokumen ini memandu pengujian detail setelah migrasi dari Render ke Zeabur.

## Prasyarat

- Repository sudah terhubung ke Zeabur.
- Service sudah dibuat sebagai Python service.
- Build command:
  ```bash
  pip install -r requirements.txt
  ```
- Start command:
  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
  ```

---

## 1) Uji Build di Zeabur

### Tujuan
Memastikan dependency Python terpasang sukses tanpa error.

### Langkah
1. Buka Zeabur Dashboard → Project → Service.
2. Trigger deploy terbaru (Redeploy).
3. Pantau build logs.

### Kriteria Lulus
- Log menunjukkan `pip install -r requirements.txt` sukses.
- Tidak ada error dependency conflict.
- Build status: **Success**.

### Jika Gagal
- Cek typo package di `requirements.txt`.
- Cek apakah ada package yang butuh system dependency tambahan.
- Pin versi package bila diperlukan.

---

## 2) Uji Start Command Gunicorn + PORT

### Tujuan
Memastikan service benar-benar listening di port yang diberikan Zeabur.

### Langkah
1. Setelah build sukses, cek runtime logs.
2. Pastikan Gunicorn start dengan command:
   ```bash
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
   ```
3. Buka URL service dari Zeabur.

### Kriteria Lulus
- Tidak ada `CrashLoopBackOff`/restart terus-menerus.
- Logs menunjukkan worker Gunicorn berhasil boot.
- URL service merespons (status HTTP 200/302 sesuai flow app).

### Jika Gagal
- Pastikan variable `$PORT` dipakai, bukan port hardcoded.
- Pastikan file entrypoint benar (`app.py` berisi `app` object).
- Turunkan workers jika resource kecil (contoh `--workers 1`).

---

## 3) Uji Environment Variables Wajib

### Variabel Wajib
- `FLASK_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SESSION_COOKIE_SECURE=true`

### Tujuan
Memastikan konfigurasi aman dan app tidak gagal boot karena env kosong.

### Langkah
1. Buka Zeabur → Service → Environment Variables.
2. Isi semua variable wajib di atas.
3. Redeploy service.
4. Cek logs startup.

### Kriteria Lulus
- Tidak muncul error:
  `SUPABASE_SERVICE_ROLE_KEY belum di-set`.
- Login/session berjalan normal.
- Koneksi ke Supabase berhasil.

### Jika Gagal
- Validasi tidak ada spasi tersembunyi pada value env.
- Regenerate `FLASK_SECRET_KEY` jika diperlukan.
- Verifikasi `SUPABASE_URL` dan key cocok dengan project Supabase aktif.

---

## 4) Uji Login/Session + Modul Utama Setelah Live

### Tujuan
Memastikan fitur bisnis tetap normal setelah pindah platform.

### Skenario Uji Fungsional (minimum)

1. **Autentikasi**
   - Akses halaman login.
   - Login dengan akun valid.
   - Logout dan login ulang.

2. **Session**
   - Setelah login, refresh halaman dashboard.
   - Pindah antar halaman modul.
   - Pastikan tidak force logout mendadak.

3. **Modul Barang**
   - Tambah data barang.
   - Edit data barang.
   - Lihat daftar data.

4. **Modul Barang Kosong**
   - Tambah & edit data.
   - Validasi data tampil benar.

5. **Modul Keuangan**
   - Tambah/edit data keuangan.
   - Cek halaman cetak/export (jika digunakan).

6. **Modul Stock Opname**
   - Tambah data stock opname.
   - Cek listing data.

### Kriteria Lulus
- Semua aksi utama berhasil tanpa error 500.
- Data tersimpan dan tampil konsisten.
- Session stabil di HTTPS.

---

## 5) Uji Fallback/Error Path (Env Belum Diset)

### Tujuan
Memastikan aplikasi fail-fast dengan pesan jelas saat konfigurasi belum lengkap.

### Langkah Uji
1. Buat test deploy dengan mengosongkan sementara:
   - `SUPABASE_SERVICE_ROLE_KEY`
2. Redeploy dan cek logs startup.
3. Kembalikan env variable benar, lalu redeploy ulang.

### Kriteria Lulus
- App gagal start dengan pesan error yang jelas (sesuai `Config.validate()`).
- Setelah env dipulihkan, app kembali normal.

---

## Verifikasi HTTP Endpoint (opsional via curl)

> Ganti `<ZEABUR_URL>` dengan domain Zeabur kamu.

```bash
curl -I https://<ZEABUR_URL>/
```

Expected:
- Respon HTTP (200/302), bukan timeout.

Untuk endpoint yang butuh auth, uji lewat browser setelah login.

---

## Template Hasil Uji (isi saat eksekusi)

- Build test: PASS/FAIL
- Gunicorn + PORT test: PASS/FAIL
- Env vars test: PASS/FAIL
- Login/session test: PASS/FAIL
- Modul bisnis test: PASS/FAIL
- Error path env kosong: PASS/FAIL
- Catatan bug/perbaikan: ...

---

## Rekomendasi Go-Live

Lanjut production penuh jika seluruh item:
- Build ✅
- Runtime ✅
- Env vars ✅
- Auth/session ✅
- Modul utama ✅
- Error path ✅

Jika ada satu FAIL, perbaiki dulu sebelum cutover total dari Render ke Zeabur.
