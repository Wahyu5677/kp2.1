# SNAPDEPLOY Thorough Testing Checklist (Langkah 1–5)

Dokumen ini adalah runbook eksekusi testing detail setelah deploy ke SnapDeploy.

## 0) Data yang harus disiapkan dulu

- URL aplikasi dari SnapDeploy, contoh:
  - `https://your-app.snapdeploy.dev` (contoh)
- Akun login valid untuk aplikasi
- Akses dashboard SnapDeploy untuk lihat logs + env vars

---

## 1) Verifikasi Real Deploy dari Repository (Build Success)

### Tujuan
Memastikan SnapDeploy berhasil menarik source code dan melakukan build otomatis.

### Langkah Eksekusi
1. Buka dashboard SnapDeploy.
2. Pilih project/service aplikasi kamu.
3. Trigger deploy terbaru (redeploy jika perlu).
4. Pantau build log dari awal sampai selesai.

### Yang harus terlihat di log
- Clone/pull repository berhasil
- Deteksi Python app berhasil
- Install dependency dari `requirements.txt` berhasil
- Tidak ada error import/package conflict

### PASS / FAIL
- **PASS**: Build selesai status Success
- **FAIL**: Build error atau stop di tengah

### Jika FAIL
- Cek typo dependency di `requirements.txt`
- Pastikan versi package kompatibel
- Pastikan branch/repo yang dipilih benar

---

## 2) Verifikasi Runtime Online + Endpoint Root (curl)

### Tujuan
Memastikan aplikasi benar-benar berjalan online setelah build sukses.

### Langkah Eksekusi
1. Ambil URL public app dari SnapDeploy.
2. Jalankan command berikut di terminal lokal kamu:

```bash
curl -I https://<SNAPDEPLOY_APP_URL>/
```

(Contoh Windows CMD/PowerShell juga bisa sama)

3. Cek runtime log di dashboard saat request masuk.

### Expected
- HTTP response muncul (200/302/401 sesuai flow app)
- Tidak timeout
- Runtime tidak crash/restart loop

### PASS / FAIL
- **PASS**: URL merespons stabil
- **FAIL**: timeout / 5xx terus / service restart loop

### Jika FAIL
- Cek env vars belum lengkap
- Cek app startup error di logs
- Jika ada opsi start command manual, gunakan:
  - `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

---

## 3) Verifikasi Env Vars Wajib

## Env wajib
- `FLASK_SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SESSION_COOKIE_SECURE=true`

### Tujuan
Memastikan konfigurasi keamanan/session/database benar.

### Langkah Eksekusi
1. Buka service → Environment Variables.
2. Pastikan semua env di atas terisi.
3. Simpan perubahan.
4. Redeploy.
5. Cek startup logs.

### Indikator Error Umum
- `SUPABASE_SERVICE_ROLE_KEY belum di-set`
- Login/session gagal karena secret key tidak valid

### PASS / FAIL
- **PASS**: Startup normal, tidak ada error env
- **FAIL**: App gagal start karena env kosong/salah

---

## 4) Verifikasi End-to-End Login + Modul Utama

### Tujuan
Memastikan fitur bisnis tetap normal setelah pindah platform.

### Skenario Uji
1. Buka halaman login
2. Login dengan user valid
3. Buka dashboard
4. Uji modul:
   - Barang: tambah/edit/list
   - Barang kosong: tambah/edit/list
   - Keuangan: tambah/edit/list/cetak/export (jika dipakai)
   - Stock opname: tambah/list
5. Logout lalu login ulang
6. Refresh browser untuk cek session persistence

### PASS / FAIL
- **PASS**: Semua operasi inti berhasil, tidak ada 500
- **FAIL**: Ada route error, data tidak tersimpan, atau session putus

---

## 5) Verifikasi Error Path (Env Rusak → Recovery)

### Tujuan
Memastikan app fail-fast saat konfigurasi salah, dan bisa pulih setelah diperbaiki.

### Langkah Eksekusi
1. Sementara kosongkan env:
   - `SUPABASE_SERVICE_ROLE_KEY`
2. Redeploy.
3. Cek logs startup (harus muncul error validasi jelas).
4. Isi kembali env yang benar.
5. Redeploy ulang.
6. Ulangi smoke test endpoint root + login.

### PASS / FAIL
- **PASS**: App gagal dengan pesan jelas saat env rusak, lalu normal kembali setelah diperbaiki
- **FAIL**: Error tidak jelas / tetap gagal setelah env dipulihkan

---

## Template Laporan Hasil (Isi setelah testing)

- Deploy Build: PASS/FAIL
- Runtime URL + curl: PASS/FAIL
- Env Vars Validation: PASS/FAIL
- E2E Login & Modul: PASS/FAIL
- Error Path & Recovery: PASS/FAIL
- Catatan bug:
  - ...
- Tindakan perbaikan:
  - ...

---

## Keputusan Go-Live

Lanjut full produksi hanya jika seluruh poin PASS.

Jika ada FAIL:
1. Perbaiki penyebab
2. Redeploy
3. Ulangi checklist sampai semua PASS
