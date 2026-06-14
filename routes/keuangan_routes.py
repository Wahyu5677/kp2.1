import csv
import io
from datetime import datetime, timedelta

from flask import render_template, request, redirect, session, flash, abort, Response
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from app import app
from config import Config
from supabase_rest import SupabaseRESTClient
from utils.validators import validate_date_yyyy_mm_dd, parse_float_non_negative, require_text
from utils.guards import require_login


def _supabase():
    return SupabaseRESTClient(
        url=Config.SUPABASE_URL,
        service_role_key=Config.SUPABASE_SERVICE_ROLE_KEY,
    )


def _parse_keuangan_period(periode, periode_value):
    periode = (periode or '').lower()
    periode_value = (periode_value or '').strip()
    if periode == 'weekly' and periode_value:
        try:
            selected = datetime.strptime(periode_value, '%Y-%m-%d').date()
        except ValueError:
            return None, None, 'Semua Periode'
        start = selected - timedelta(days=selected.weekday())
        end = start + timedelta(days=6)
        label = f'Mingguan: {start.strftime("%d %b %Y")} - {end.strftime("%d %b %Y")} '
        return start, end, label
    if periode == 'monthly' and periode_value:
        try:
            selected = datetime.strptime(periode_value, '%Y-%m').date()
        except ValueError:
            return None, None, 'Semua Periode'
        start = selected.replace(day=1)
        next_month = (selected.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_month - timedelta(days=1)
        label = f'Bulanan: {selected.strftime("%B %Y")}'
        return start, end, label
    return None, None, 'Semua Periode'


def _filter_keuangan_data(data, periode, periode_value):
    start, end, label = _parse_keuangan_period(periode, periode_value)
    if start is None or end is None:
        return data, label

    filtered = []
    for item in data:
        tanggal = item.get('tanggal')
        if not tanggal:
            continue
        try:
            record_date = datetime.strptime(str(tanggal), '%Y-%m-%d').date()
        except (TypeError, ValueError):
            continue
        if start <= record_date <= end:
            filtered.append(item)

    return filtered, label


@app.route('/keuangan')
def keuangan():
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    periode = request.args.get('periode', 'all')
    periode_value = request.args.get('periode_value', '')

    try:
        raw_data = _supabase().select('keuangan', order='id_keuangan.asc')
    except Exception:
        flash('Terjadi gangguan sistem saat mengambil data keuangan.', 'danger')
        raw_data = []

    data, period_label = _filter_keuangan_data(raw_data, periode, periode_value)
    total_pemasukan = sum((item.get('pemasukan') or 0) for item in data)
    total_pengeluaran = sum((item.get('pengeluaran') or 0) for item in data)
    saldo = total_pemasukan - total_pengeluaran

    return render_template(
        'keuangan/data_keuangan.html',
        data=data,
        total_pemasukan=total_pemasukan,
        total_pengeluaran=total_pengeluaran,
        saldo=saldo,
        periode=periode,
        periode_value=periode_value,
        period_label=period_label,
    )


@app.route('/keuangan/export')
def export_keuangan():
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    fmt = request.args.get('format', 'csv').lower()
    periode = request.args.get('periode', 'all')
    periode_value = request.args.get('periode_value', '')

    try:
        raw_data = _supabase().select('keuangan', order='id_keuangan.asc')
    except Exception:
        flash('Terjadi gangguan sistem saat mengambil data untuk ekspor.', 'danger')
        raw_data = []

    data, period_label = _filter_keuangan_data(raw_data, periode, periode_value)
    total_pemasukan = sum((item.get('pemasukan') or 0) for item in data)
    total_pengeluaran = sum((item.get('pengeluaran') or 0) for item in data)
    saldo = total_pemasukan - total_pengeluaran

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['No.', 'Tanggal', 'Pemasukan', 'Pengeluaran', 'Keterangan'])
        for index, item in enumerate(data, start=1):
            writer.writerow([
                index,
                item.get('tanggal', ''),
                item.get('pemasukan', 0),
                item.get('pengeluaran', 0),
                item.get('keterangan', ''),
            ])
        csv_data = '\ufeff' + output.getvalue()
        response = Response(csv_data, mimetype='text/csv; charset=utf-8')
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_keuangan.csv'
        return response

    if fmt == 'xlsx':
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Laporan Keuangan'
        sheet.append(['No.', 'Tanggal', 'Pemasukan', 'Pengeluaran', 'Keterangan'])
        for index, item in enumerate(data, start=1):
            sheet.append([
                index,
                item.get('tanggal', ''),
                item.get('pemasukan', 0),
                item.get('pengeluaran', 0),
                item.get('keterangan', ''),
            ])
        xlsx_buffer = io.BytesIO()
        workbook.save(xlsx_buffer)
        xlsx_buffer.seek(0)
        response = Response(xlsx_buffer.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_keuangan.xlsx'
        return response

    if fmt == 'pdf':
        def format_rupiah(amount):
            try:
                value = float(amount or 0)
            except (TypeError, ValueError):
                return str(amount or '')
            return 'Rp ' + f'{value:,.0f}'.replace(',', '.')

        pdf_buffer = io.BytesIO()
        page = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4
        margin = 2 * cm
        x = margin
        y = height - margin

        page.setFont('Helvetica-Bold', 14)
        page.drawString(x, y, 'Laporan Keuangan')
        page.setFont('Helvetica', 10)
        y -= 1.2 * cm
        page.drawString(x, y, period_label)
        y -= 0.8 * cm
        page.drawString(x, y, f'Diunduh: {datetime.now():%d-%m-%Y %H:%M}')

        y -= 1.2 * cm
        page.setFont('Helvetica-Bold', 10)
        page.drawString(x, y, 'Total Pemasukan:')
        page.drawRightString(width - margin, y, format_rupiah(total_pemasukan))
        y -= 0.5 * cm
        page.drawString(x, y, 'Total Pengeluaran:')
        page.drawRightString(width - margin, y, format_rupiah(total_pengeluaran))
        y -= 0.5 * cm
        page.drawString(x, y, 'Saldo Bersih:')
        page.drawRightString(width - margin, y, format_rupiah(saldo))

        y -= 1.2 * cm
        page.setFont('Helvetica-Bold', 9)
        columns = ['No.', 'Tanggal', 'Pemasukan', 'Pengeluaran', 'Keterangan']
        widths = [1.2 * cm, 3.0 * cm, 3.5 * cm, 3.5 * cm, width - margin * 2 - 11.2 * cm]
        current_x = x
        for idx, col in enumerate(columns):
            page.drawString(current_x, y, col)
            current_x += widths[idx]

        y -= 0.6 * cm
        page.setFont('Helvetica', 9)
        for index, item in enumerate(data, start=1):
            if y < margin + 2 * cm:
                page.showPage()
                y = height - margin
                page.setFont('Helvetica-Bold', 9)
                current_x = x
                for idx, col in enumerate(columns):
                    page.drawString(current_x, y, col)
                    current_x += widths[idx]
                y -= 0.6 * cm
                page.setFont('Helvetica', 9)

            current_x = x
            page.drawString(current_x, y, str(index))
            current_x += widths[0]
            page.drawString(current_x, y, str(item.get('tanggal', '')))
            current_x += widths[1]
            page.drawRightString(current_x + widths[2] - 2, y, format_rupiah(item.get('pemasukan', 0)) if item.get('pemasukan', 0) else '-')
            current_x += widths[2]
            page.drawRightString(current_x + widths[3] - 2, y, format_rupiah(item.get('pengeluaran', 0)) if item.get('pengeluaran', 0) else '-')
            current_x += widths[3]
            page.drawString(current_x, y, str(item.get('keterangan', ''))[:80])
            y -= 0.5 * cm

        page.showPage()
        page.save()
        pdf_buffer.seek(0)
        response = Response(pdf_buffer.getvalue(), mimetype='application/pdf')
        response.headers['Content-Disposition'] = 'attachment; filename=laporan_keuangan.pdf'
        return response

    return redirect('/keuangan')


@app.route('/keuangan/tambah', methods=['GET', 'POST'])
def tambah_keuangan():
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    form_data = {
        "tanggal": "",
        "pemasukan": "0",
        "pengeluaran": "0",
        "keterangan": "",
    }

    if request.method == 'POST':
        try:
            payload = {
                "tanggal": validate_date_yyyy_mm_dd(request.form.get('tanggal'), "Tanggal"),
                "pemasukan": parse_float_non_negative(request.form.get('pemasukan'), "Pemasukan"),
                "pengeluaran": parse_float_non_negative(request.form.get('pengeluaran'), "Pengeluaran"),
                "keterangan": require_text(request.form.get('keterangan'), "Keterangan"),
            }
            _supabase().insert("keuangan", payload)
            flash("Data keuangan berhasil ditambahkan.", "success")
            return redirect('/keuangan')
        except ValueError as e:
            flash(str(e), "danger")
            form_data = {
                "tanggal": request.form.get('tanggal', ''),
                "pemasukan": request.form.get('pemasukan', '0'),
                "pengeluaran": request.form.get('pengeluaran', '0'),
                "keterangan": request.form.get('keterangan', ''),
            }
        except Exception:
            flash("Terjadi gangguan sistem saat menambah data keuangan.", "danger")
            form_data = {
                "tanggal": request.form.get('tanggal', ''),
                "pemasukan": request.form.get('pemasukan', '0'),
                "pengeluaran": request.form.get('pengeluaran', '0'),
                "keterangan": request.form.get('keterangan', ''),
            }

    return render_template('keuangan/tambah_keuangan.html', form_data=form_data)


@app.route('/keuangan/edit/<int:id>', methods=['GET', 'POST'])
def edit_keuangan(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    sb = _supabase()
    form_data = {
        "tanggal": "",
        "pemasukan": "0",
        "pengeluaran": "0",
        "keterangan": "",
    }

    if request.method == 'POST':
        try:
            payload = {
                "tanggal": validate_date_yyyy_mm_dd(request.form.get('tanggal'), "Tanggal"),
                "pemasukan": parse_float_non_negative(request.form.get('pemasukan'), "Pemasukan"),
                "pengeluaran": parse_float_non_negative(request.form.get('pengeluaran'), "Pengeluaran"),
                "keterangan": require_text(request.form.get('keterangan'), "Keterangan"),
            }
            sb.update("keuangan", {"id_keuangan": f"eq.{id}"}, payload)
            flash("Data keuangan berhasil diperbarui.", "success")
            return redirect('/keuangan')
        except ValueError as e:
            flash(str(e), "danger")
            form_data = {
                "tanggal": request.form.get('tanggal', ''),
                "pemasukan": request.form.get('pemasukan', '0'),
                "pengeluaran": request.form.get('pengeluaran', '0'),
                "keterangan": request.form.get('keterangan', ''),
            }
        except Exception:
            flash("Terjadi gangguan sistem saat memperbarui data keuangan.", "danger")
            form_data = {
                "tanggal": request.form.get('tanggal', ''),
                "pemasukan": request.form.get('pemasukan', '0'),
                "pengeluaran": request.form.get('pengeluaran', '0'),
                "keterangan": request.form.get('keterangan', ''),
            }
    else:
        record = sb.select_one_by_filters("keuangan", {"id_keuangan": f"eq.{id}"})
        if not record:
            return abort(404)
        form_data = {
            "tanggal": record.get('tanggal', ''),
            "pemasukan": str(record.get('pemasukan') or 0),
            "pengeluaran": str(record.get('pengeluaran') or 0),
            "keterangan": record.get('keterangan', ''),
        }

    return render_template('keuangan/edit_keuangan.html', form_data=form_data, id=id)


@app.route('/keuangan/hapus/<int:id>', methods=['POST'])
def hapus_keuangan(id):
    login_guard = require_login()
    if login_guard:
        return login_guard

    if session.get('role') != 'owner':
        return abort(403)

    try:
        _supabase().delete_by_filter("keuangan", {"id_keuangan": f"eq.{id}"})
        flash("Data keuangan berhasil dihapus.", "success")
    except Exception:
        flash("Terjadi gangguan sistem saat menghapus data keuangan.", "danger")

    return redirect('/keuangan')
