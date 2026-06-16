# Deploy Flask App ke SnapDeploy (Pengganti Render/Zeabur)

Dokumen ini menyesuaikan project Flask + Gunicorn kamu agar bisa dideploy di SnapDeploy.

## 1) Ringkasan Project

Stack aplikasi:
- Flask
- Gunicorn
- Supabase REST (service role key)

File penting yang sudah ada:
- `app.py`
- `requirements.txt`
- `Procfile` (opsional, tetap berguna)
- `config.py` (membaca env vars)

## 2) Persiapan Repo

Pastikan branch/repo yang kamu deploy sudah berisi:
- `requirements.txt`
- `app.py`
- `Procfile` (opsional)
- `.gitignore` aman (jangan commit `.env`)

## 3) Langkah Deploy di SnapDeploy

Berdasarkan UI yang kamu kirim (“Deploy Your Docker App”), ada 2 jalur umum:

---

### Opsi A — Deploy langsung dari source (jika SnapDeploy mendukung Build/Start command)

1. Klik **Deploy Free**.
2. Hubungkan akun GitHub.
3. Pilih repository project ini.
4. Set command:
   - Build Command:
     ```bash
     pip install -r requirements.txt
     ```
   - Start Command:
     ```bash
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
     ```
5. Isi Environment Variables:
   - `FLASK_SECRET_KEY` = string random aman
   - `SUPABASE_URL` = URL Supabase
   - `SUPABASE_SERVICE_ROLE_KEY` = key Supabase
   - `SESSION_COOKIE_SECURE` = `true`
6. Deploy.

---

### Opsi B — Deploy via Docker (paling kompatibel dengan landing page SnapDeploy)

Jika SnapDeploy fokus Docker, gunakan `Dockerfile` + `.dockerignore` (disiapkan di langkah 4).

Proses:
1. Klik **Deploy Free**.
2. Pilih deploy dari repo GitHub.
3. Pastikan SnapDeploy mendeteksi `Dockerfile`.
4. Tambahkan env vars yang sama.
5. Deploy.

---

## 4) Runtime & Port

Aplikasi harus bind ke port dari platform:
- Gunakan `--bind 0.0.0.0:$PORT` (sudah benar).
- Jangan hardcode port (misal 5000 statis) di mode production.

## 5) Environment Variables Wajib

Wajib diisi di dashboard SnapDeploy:
- `FLASK_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SESSION_COOKIE_SECURE=true`

Jika `SUPABASE_SERVICE_ROLE_KEY` kosong, app akan gagal start (sesuai validasi di `config.py`).

## 6) Verifikasi Setelah Deploy

1. Buka URL app SnapDeploy.
2. Uji login.
3. Uji CRUD modul:
   - Barang
   - Barang kosong
   - Keuangan
   - Stock opname
4. Cek logs runtime jika ada error.

## 7) Troubleshooting

### App crash saat startup
- Cek env vars belum lengkap.
- Cek logs error `SUPABASE_SERVICE_ROLE_KEY belum di-set`.

### URL tidak bisa diakses
- Pastikan app bind ke `$PORT`.
- Cek status deploy berhasil.

### Session/login tidak stabil
- Pastikan HTTPS aktif.
- `SESSION_COOKIE_SECURE=true` dipakai di production.

---

## 8) Cutover dari Render/Zeabur

Setelah SnapDeploy stabil:
1. Matikan auto deploy Render.
2. Jangan deploy ganda dari banyak platform.
3. Jadikan domain SnapDeploy endpoint utama.
