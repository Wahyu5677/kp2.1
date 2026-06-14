from flask import render_template, request, redirect, flash
from app import app
from config import Config
from supabase_rest import SupabaseRESTClient
from utils.validators import require_text, parse_int_non_negative, parse_float_non_negative
from utils.guards import require_login


def _supabase():
    return SupabaseRESTClient(
        url=Config.SUPABASE_URL,
        service_role_key=Config.SUPABASE_SERVICE_ROLE_KEY,
    )


@app.route('/barang')
def barang():
    login_guard = require_login()
    if login_guard:
        return login_guard

    try:
        data = _supabase().select("barang", order="id_barang.asc")
    except Exception:
        flash("Terjadi gangguan sistem saat mengambil data barang.", "danger")
        data = []

    return render_template('barang/data_barang.html', barang=data)


@app.route('/barang/tambah', methods=['GET', 'POST'])
def tambah_barang():
    login_guard = require_login()
    if login_guard:
        return login_guard

    if request.method == 'POST':
        try:
            payload = {
                "kode_barang": require_text(request.form.get('kode_barang'), "Kode Barang"),
                "nama_barang": require_text(request.form.get('nama_barang'), "Nama Barang"),
                "kategori": require_text(request.form.get('kategori'), "Kategori"),
                "stok": parse_int_non_negative(request.form.get('stok'), "Stok"),
                "harga": parse_float_non_negative(request.form.get('harga'), "Harga"),
                "satuan": require_text(request.form.get('satuan'), "Satuan"),
            }
            _supabase().insert("barang", payload)
            flash("Data barang berhasil ditambahkan.", "success")
            return redirect('/barang')
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Terjadi gangguan sistem saat menambah data barang.", "danger")

    return render_template('barang/tambah_barang.html')


@app.route('/barang/edit/<int:id>', methods=['GET', 'POST'])
def edit_barang(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    sb = _supabase()

    if request.method == 'POST':
        try:
            payload = {
                "nama_barang": require_text(request.form.get('nama_barang'), "Nama Barang"),
                "kategori": require_text(request.form.get('kategori'), "Kategori"),
                "stok": parse_int_non_negative(request.form.get('stok'), "Stok"),
            }
            sb.update("barang", {"id_barang": f"eq.{id}"}, payload)
            flash("Data barang berhasil diperbarui.", "success")
            return redirect('/barang')
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Terjadi gangguan sistem saat memperbarui data barang.", "danger")

    try:
        data = sb.select_one_by_filters("barang", {"id_barang": f"eq.{id}"})
    except Exception:
        flash("Terjadi gangguan sistem saat mengambil data barang.", "danger")
        return redirect('/barang')

    if not data:
        flash("Data barang tidak ditemukan.", "danger")
        return redirect('/barang')

    return render_template('barang/edit_barang.html', barang=data)


@app.route('/barang/hapus/<int:id>', methods=['POST'])
def hapus_barang(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    try:
        _supabase().delete_by_filter("barang", {"id_barang": f"eq.{id}"})
        flash("Data barang berhasil dihapus.", "success")
    except Exception:
        flash("Terjadi gangguan sistem saat menghapus data barang.", "danger")
    return redirect('/barang', code=302)
