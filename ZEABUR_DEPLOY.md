# Deploy Flask App ke Zeabur (Migrasi dari Render)

Dokumen ini untuk mengganti deployment dari Render ke Zeabur agar tidak terganggu popup billing/credit card Render.

## 1) Ringkasan Arsitektur App

Aplikasi ini menggunakan:

- Python + Flask
- Gunicorn sebagai production server
- Environment variable:
  - `FLASK_SECRET_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SESSION_COOKIE_SECURE`

Command start yang dipakai project:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
```

## 2) Persiapan Repository

Pastikan file berikut ada di root project:

- `app.py`
- `requirements.txt`
- `Procfile` (opsional untuk Zeabur, tapi tetap aman dipertahankan)

`requirements.txt` minimal sudah berisi:

- Flask
- gunicorn
- requests
- Werkzeug

## 3) Langkah Deploy ke Zeabur

1. Login ke Zeabur Dashboard.
2. Klik **New Project**.
3. Pilih **Deploy from GitHub/Git Repository**.
4. Pilih repository project ini.
5. Saat service terdeteksi sebagai Python service, set konfigurasi:

   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```

   - **Start Command**:
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
     ```

6. Tambahkan Environment Variables di Zeabur:

   - `FLASK_SECRET_KEY` = isi random string kuat
   - `SUPABASE_URL` = `https://srqtaildhnwmtxwuxfoe.supabase.co` (atau URL project Supabase kamu)
   - `SUPABASE_SERVICE_ROLE_KEY` = service role key Supabase
   - `SESSION_COOKIE_SECURE` = `true`

7. Trigger deploy (manual/redeploy).
8. Setelah berhasil, buka domain yang diberikan Zeabur.

## 4) Konfigurasi Domain & HTTPS

- Gunakan domain bawaan Zeabur untuk tes awal.
- Jika custom domain:
  - arahkan DNS sesuai instruksi Zeabur
  - tunggu SSL issuance selesai
- Pastikan app diakses via HTTPS (penting untuk cookie secure).

## 5) Migrasi dari Render (Yang Perlu Dihentikan)

Agar tidak bingung/config bentrok:

1. Nonaktifkan auto deploy di Render.
2. (Opsional) Suspend/Delete service di Render jika sudah stabil di Zeabur.
3. Pastikan semua traffic produksi berpindah ke domain Zeabur.

## 6) Troubleshooting Umum

### A. App tidak start / crash loop

Cek:

- `SUPABASE_SERVICE_ROLE_KEY` terisi (wajib).  
  Jika kosong, app akan error dari `Config.validate()`.

- `Start Command` benar dan pakai `$PORT`.

### B. Login/session bermasalah setelah pindah platform

Cek:

- `FLASK_SECRET_KEY` konsisten (jangan berubah-ubah antar deploy)
- `SESSION_COOKIE_SECURE=true` saat akses HTTPS
- Browser cache/cookie lama dibersihkan saat testing

### C. Build gagal

Cek:

- `requirements.txt` valid
- Python runtime Zeabur kompatibel
- Tidak ada dependency private tanpa credential

### D. Masalah popup credit card (Render)

Ini berasal dari kebijakan billing Render, bukan bug aplikasi.
Pindah ke Zeabur menghilangkan kebutuhan flow billing Render untuk deployment utama.

## 7) Checklist Go-Live

- [ ] Build sukses
- [ ] App status running
- [ ] Login berhasil
- [ ] CRUD barang berjalan
- [ ] Keuangan & stock opname berjalan
- [ ] Session aman di HTTPS
- [ ] Render service dinonaktifkan (opsional, setelah validasi Zeabur)

---

Jika dibutuhkan, file `render.yaml` dapat dipertahankan hanya sebagai arsip historis.
