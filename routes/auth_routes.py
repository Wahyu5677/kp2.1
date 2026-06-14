from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import render_template, request, redirect, session, flash, make_response, jsonify
from werkzeug.security import check_password_hash
from app import app
from config import Config
from supabase_rest import SupabaseRESTClient


def _get_refresh_serializer():
    return URLSafeTimedSerializer(app.secret_key, salt="refresh-token")


def _create_refresh_token(user_data: dict) -> str:
    serializer = _get_refresh_serializer()
    payload = {
        "username": user_data.get("username"),
        "role": user_data.get("role"),
    }
    return serializer.dumps(payload)


def _verify_refresh_token(token: str) -> dict | None:
    serializer = _get_refresh_serializer()
    try:
        return serializer.loads(token, max_age=Config.REFRESH_TOKEN_MAX_AGE)
    except (SignatureExpired, BadSignature):
        return None


def _access_expired() -> bool:
    expires_at = session.get('access_expiry')
    if not expires_at:
        return True
    try:
        return datetime.utcnow() > datetime.fromisoformat(expires_at)
    except ValueError:
        return True


@app.before_request
def enforce_access_expiry():
    allowed_paths = ['/login', '/', '/forgot-password', '/refresh-session']
    if request.path.startswith('/static') or request.path in allowed_paths:
        return None

    if not session.get('login'):
        return None

    if not _access_expired():
        return None

    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        session.clear()
        return redirect('/login')

    refresh_data = _verify_refresh_token(refresh_token)
    if not refresh_data:
        response = make_response(redirect('/login'))
        response.set_cookie('refresh_token', '', expires=0, httponly=True, secure=Config.SESSION_COOKIE_SECURE, samesite=Config.SESSION_COOKIE_SAMESITE)
        session.clear()
        return response

    session['login'] = True
    session['username'] = refresh_data['username']
    session['role'] = refresh_data['role']
    session['access_expiry'] = (datetime.utcnow() + timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)).isoformat()
    return None


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():

    # 1. PENGAMAN UTAMA: jika user sudah login, langsung arahkan ke dashboard.
    if session.get('login') and session.get('username') and session.get('role'):
        if session.get('role') == 'owner':
            return redirect('/dashboard-owner')
        return redirect('/dashboard-karyawan')

    # 2. Auto-login dengan refresh token saat ada cookie HttpOnly.
    refresh_token = request.cookies.get('refresh_token')
    if refresh_token:
        refresh_data = _verify_refresh_token(refresh_token)
        if refresh_data:
            session['login'] = True
            session['username'] = refresh_data['username']
            session['role'] = refresh_data['role']
            session.permanent = True
            session['access_expiry'] = (datetime.utcnow() + timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)).isoformat()
            return redirect('/dashboard-owner' if session['role'] == 'owner' else '/dashboard-karyawan')

    # 3. Proses login POST dengan Remember Me / Refresh Token.
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember_me = request.form.get('remember_me') == 'on'

        supabase = SupabaseRESTClient(
            url=Config.SUPABASE_URL,
            service_role_key=Config.SUPABASE_SERVICE_ROLE_KEY,
        )

        user = supabase.select_one_by_filters(
            table="users",
            filters={"username": f"eq.{username}"},
            columns="*",
        )

        if user and check_password_hash(user.get('password', ''), password):
            session['login'] = True
            session['username'] = user.get('username')
            session['role'] = user.get('role')
            session.permanent = remember_me
            session['access_expiry'] = (datetime.utcnow() + timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)).isoformat()
            app.permanent_session_lifetime = timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)

            response = make_response(
                redirect('/dashboard-owner' if session['role'] == 'owner' else '/dashboard-karyawan')
            )

            if remember_me:
                token = _create_refresh_token(user)
                response.set_cookie(
                    'refresh_token',
                    token,
                    httponly=True,
                    secure=Config.SESSION_COOKIE_SECURE,
                    samesite=Config.SESSION_COOKIE_SAMESITE,
                    max_age=Config.REFRESH_TOKEN_MAX_AGE,
                )
            else:
                response.set_cookie(
                    'refresh_token',
                    '',
                    expires=0,
                    httponly=True,
                    secure=Config.SESSION_COOKIE_SECURE,
                    samesite=Config.SESSION_COOKIE_SAMESITE,
                )

            return response

        flash('Login gagal! Username atau Password salah.', 'danger')
        return render_template('login.html', username=username)

    # 4. Tampilkan halaman login bersih jika belum login sama sekali.
    return render_template('login.html')


@app.route('/refresh-session', methods=['GET'])
def refresh_session():
    if session.get('login') and not _access_expired():
        session.permanent = True
        session['access_expiry'] = (datetime.utcnow() + timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)).isoformat()
        return jsonify({'status': 'ok'})

    refresh_token = request.cookies.get('refresh_token')
    if not refresh_token:
        return jsonify({'status': 'expired'}), 401

    refresh_data = _verify_refresh_token(refresh_token)
    if not refresh_data:
        response = make_response(jsonify({'status': 'expired'}), 401)
        response.set_cookie('refresh_token', '', expires=0, httponly=True, secure=Config.SESSION_COOKIE_SECURE, samesite=Config.SESSION_COOKIE_SAMESITE)
        session.clear()
        return response

    session['login'] = True
    session['username'] = refresh_data['username']
    session['role'] = refresh_data['role']
    session.permanent = True
    session['access_expiry'] = (datetime.utcnow() + timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)).isoformat()
    app.permanent_session_lifetime = timedelta(seconds=Config.ACCESS_TOKEN_LIFETIME_SECONDS)
    return jsonify({'status': 'ok'})


@app.route('/logout')
def logout():
    # Menghapus total semua cookie/session lama agar bersih saat ganti akun
    response = make_response(redirect('/login'))
    response.set_cookie('refresh_token', '', expires=0, httponly=True, secure=Config.SESSION_COOKIE_SECURE, samesite=Config.SESSION_COOKIE_SAMESITE)
    session.clear()
    flash('Anda telah logout. Sampai jumpa!', 'info')
    return response


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Placeholder untuk fitur lupa password"""
    if request.method == 'POST':
        # Di masa depan, integrasikan dengan email service atau SMS gateway
        username = request.form.get('username', '').strip()
        if username:
            flash('Instruksi reset password telah dikirim (fitur sedang dalam pengembangan).', 'warning')
        return redirect('/login')
    
    return render_template('forgot_password.html')


@app.route('/dashboard-owner')
def dashboard_owner():
    # Validasi ketat: Hanya izinkan jika rolenya benar-benar owner
    if session.get('login') and session.get('role') == 'owner':
        return render_template('dashboard_owner.html')
    session.clear() # Bersihkan jika coba-coba masuk ilegal
    return redirect('/login')


@app.route('/dashboard-karyawan')
def dashboard_karyawan():
    # Validasi ketat: Hanya izinkan jika rolenya karyawan atau owner
    if session.get('login') and session.get('role') in ['karyawan', 'owner']:
        return render_template('dashboard_karyawan.html')
    session.clear()
    return redirect('/login')