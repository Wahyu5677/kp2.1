import csv
import io

from flask import render_template, request, redirect, session, flash, abort, Response
from openpyxl import Workbook
from app import app
from config import Config
from supabase_rest import SupabaseRESTClient
from utils.validators import parse_int_non_negative, validate_date_yyyy_mm_dd
from utils.guards import require_login


def _supabase():
    return SupabaseRESTClient(
        url=Config.SUPABASE_URL,
        service_role_key=Config.SUPABASE_SERVICE_ROLE_KEY,
    )


@app.route('/stock-opname')
def stock_opname():
    login_guard = require_login()
    if login_guard:
        return login_guard

    sb = _supabase()

    try:
        opname_rows = sb.select("stock_opname", order="id_opname.asc")
        barang_rows = sb.select("barang", columns="id_barang,nama_barang")
    except Exception:
        flash("Terjadi gangguan sistem saat mengambil data stock opname.", "danger")
        opname_rows = []
        barang_rows = []

    barang_map = {b["id_barang"]: b["nama_barang"] for b in barang_rows}

    data = []
    for row in opname_rows:
        merged = dict(row)
        merged["nama_barang"] = barang_map.get(row.get("id_barang"), "-")
        data.append(merged)

    total_opname = len(data)
    total_selisih = sum((item.get("selisih") or 0) for item in data)
    positive_opname = sum(1 for item in data if (item.get("selisih") or 0) > 0)
    negative_opname = sum(1 for item in data if (item.get("selisih") or 0) < 0)

    return render_template(
        'stock_opname/data_stock_opname.html',
        data=data,
        total_opname=total_opname,
        total_selisih=total_selisih,
        positive_opname=positive_opname,
        negative_opname=negative_opname,
    )


@app.route('/stock-opname/export')
def export_stock_opname():
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    fmt = request.args.get('format', 'csv').lower()
    sb = _supabase()

    try:
        opname_rows = sb.select('stock_opname', order='id_opname.asc')
        barang_rows = sb.select('barang', columns='id_barang,nama_barang')
    except Exception:
        flash('Terjadi gangguan sistem saat mengambil data untuk ekspor stock opname.', 'danger')
        opname_rows = []
        barang_rows = []

    barang_map = {b['id_barang']: b['nama_barang'] for b in barang_rows}
    data = []
    for row in opname_rows:
        merged = dict(row)
        merged['nama_barang'] = barang_map.get(row.get('id_barang'), '-')
        data.append(merged)

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['No.', 'Nama Barang', 'Stok Sistem', 'Stok Fisik', 'Selisih', 'Tanggal Opname', 'Petugas'])
        for index, item in enumerate(data, start=1):
            writer.writerow([
                index,
                item.get('nama_barang', ''),
                item.get('stok_sistem', 0),
                item.get('stok_fisik', 0),
                item.get('selisih', 0),
                item.get('tanggal_opname', ''),
                item.get('petugas', ''),
            ])
        csv_data = '\ufeff' + output.getvalue()
        response = Response(csv_data, mimetype='text/csv; charset=utf-8')
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_stock_opname.csv'
        return response

    if fmt == 'xlsx':
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Stock Opname'
        sheet.append(['No.', 'Nama Barang', 'Stok Sistem', 'Stok Fisik', 'Selisih', 'Tanggal Opname', 'Petugas'])
        for index, item in enumerate(data, start=1):
            sheet.append([
                index,
                item.get('nama_barang', ''),
                item.get('stok_sistem', 0),
                item.get('stok_fisik', 0),
                item.get('selisih', 0),
                item.get('tanggal_opname', ''),
                item.get('petugas', ''),
            ])
        xlsx_buffer = io.BytesIO()
        workbook.save(xlsx_buffer)
        xlsx_buffer.seek(0)
        response = Response(xlsx_buffer.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_stock_opname.xlsx'
        return response

    return redirect('/stock-opname')


@app.route('/stock-opname/hapus/<int:id>', methods=['POST'])
def hapus_stock_opname(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    try:
        _supabase().delete_by_filter("stock_opname", {"id_opname": f"eq.{id}"})
        flash("Data stock opname berhasil dihapus.", "success")
    except Exception:
        flash("Terjadi gangguan sistem saat menghapus data stock opname.", "danger")

    return redirect('/stock-opname')


@app.route('/stock-opname/tambah', methods=['GET', 'POST'])
def tambah_stock_opname():
    login_guard = require_login()
    if login_guard:
        return login_guard

    sb = _supabase()

    form_data = {
        "id_barang": "",
        "stok_sistem": "",
        "stok_fisik": "",
        "tanggal_opname": "",
    }

    if request.method == 'POST':
        try:
            id_barang = parse_int_non_negative(request.form.get('id_barang'), "Barang")
            stok_sistem = parse_int_non_negative(request.form.get('stok_sistem'), "Stok Sistem")
            stok_fisik = parse_int_non_negative(request.form.get('stok_fisik'), "Stok Fisik")
            tanggal = validate_date_yyyy_mm_dd(request.form.get('tanggal_opname'), "Tanggal Opname")
            selisih = stok_fisik - stok_sistem
            petugas = session['username']

            payload = {
                "id_barang": id_barang,
                "stok_sistem": stok_sistem,
                "stok_fisik": stok_fisik,
                "selisih": selisih,
                "tanggal_opname": tanggal,
                "petugas": petugas,
            }

            sb.insert("stock_opname", payload)
            flash("Data stock opname berhasil ditambahkan.", "success")
            return redirect('/stock-opname')
        except ValueError as e:
            flash(str(e), "danger")
            form_data = {
                "id_barang": request.form.get('id_barang', ''),
                "stok_sistem": request.form.get('stok_sistem', ''),
                "stok_fisik": request.form.get('stok_fisik', ''),
                "tanggal_opname": request.form.get('tanggal_opname', ''),
            }
        except Exception:
            flash("Terjadi gangguan sistem saat menambah data stock opname.", "danger")
            form_data = {
                "id_barang": request.form.get('id_barang', ''),
                "stok_sistem": request.form.get('stok_sistem', ''),
                "stok_fisik": request.form.get('stok_fisik', ''),
                "tanggal_opname": request.form.get('tanggal_opname', ''),
            }

    try:
        barang = sb.select("barang", order="id_barang.asc")
    except Exception:
        flash("Terjadi gangguan sistem saat mengambil data barang.", "danger")
        barang = []

    return render_template(
        'stock_opname/tambah_stock_opname.html',
        barang=barang,
        form_data=form_data,
    )
