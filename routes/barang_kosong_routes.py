from flask import render_template, request, redirect, session, abort, flash
from app import app
from config import Config
from supabase_rest import SupabaseRESTClient
from utils.validators import require_text, parse_allowed_choice, validate_date_yyyy_mm_dd
from utils.guards import require_login


def _supabase():
    return SupabaseRESTClient(
        url=Config.SUPABASE_URL,
        service_role_key=Config.SUPABASE_SERVICE_ROLE_KEY,
    )


@app.route('/barang-kosong')
def barang_kosong():
    login_guard = require_login()
    if login_guard:
        return login_guard

    try:
        data = _supabase().select("barang_kosong", order="id_kosong.asc")
    except Exception:
        flash("Terjadi gangguan sistem saat mengambil data barang kosong.", "danger")
        data = []

    return render_template(
        'barang_kosong/data_barang_kosong.html',
        barang=data
    )


@app.route('/barang-kosong/tambah', methods=['GET', 'POST'])
def tambah_barang_kosong():
    login_guard = require_login()
    if login_guard:
        return login_guard

    if request.method == 'POST':
        try:
            payload = {
                "nama_barang": require_text(request.form.get('nama_barang'), "Nama Barang"),
                "status_barang": parse_allowed_choice(
                    request.form.get('status_barang'),
                    "Status Barang",
                    {"Habis", "Hampir Habis"},
                ),
                "tanggal_input": validate_date_yyyy_mm_dd(request.form.get('tanggal_input'), "Tanggal Input"),
                "input_oleh": session['username'],
            }
            _supabase().insert("barang_kosong", payload)
            flash("Data barang kosong berhasil ditambahkan.", "success")
            return redirect('/barang-kosong')
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Terjadi gangguan sistem saat menambah data barang kosong.", "danger")

    return render_template('barang_kosong/tambah_barang_kosong.html')


@app.route('/barang-kosong/edit/<int:id>', methods=['GET', 'POST'])
def edit_barang_kosong(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    sb = _supabase()

    if request.method == 'POST':
        try:
            payload = {
                "nama_barang": require_text(request.form.get('nama_barang'), "Nama Barang"),
                "status_barang": parse_allowed_choice(
                    request.form.get('status_barang'),
                    "Status Barang",
                    {"Habis", "Hampir Habis"},
                ),
            }
            sb.update("barang_kosong", {"id_kosong": f"eq.{id}"}, payload)
            flash("Data barang kosong berhasil diperbarui.", "success")
            return redirect('/barang-kosong')
        except ValueError as e:
            flash(str(e), "danger")
        except Exception:
            flash("Terjadi gangguan sistem saat memperbarui data barang kosong.", "danger")

    try:
        barang = sb.select_one_by_filters("barang_kosong", {"id_kosong": f"eq.{id}"})
    except Exception:
        flash("Terjadi gangguan sistem saat mengambil data barang kosong.", "danger")
        return redirect('/barang-kosong')

    if not barang:
        flash("Data barang kosong tidak ditemukan.", "danger")
        return redirect('/barang-kosong')

    return render_template(
        'barang_kosong/edit_barang_kosong.html',
        barang=barang
    )


@app.route('/barang-kosong/hapus/<int:id>', methods=['POST'])
def hapus_barang_kosong(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    try:
        _supabase().delete_by_filter("barang_kosong", {"id_kosong": f"eq.{id}"})
        flash("Data barang kosong berhasil dihapus.", "success")
    except Exception:
        flash("Terjadi gangguan sistem saat menghapus data barang kosong.", "danger")
    return redirect('/barang-kosong', code=302)
