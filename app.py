import secrets
from flask import Flask, session, request, abort, render_template
from config import Config

app = Flask(__name__)

# Config App
app.config.from_object(Config)
app.secret_key = Config.FLASK_SECRET_KEY
Config.validate()


@app.template_filter('rupiah')
def rupiah_filter(value):
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return value
    formatted = f"{amount:,.0f}"
    return formatted.replace(",", ".")


def _ensure_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": _ensure_csrf_token}


@app.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get("_csrf_token")
        form_token = request.form.get("_csrf_token")
        if not token or not form_token or token != form_token:
            abort(400)


@app.after_request
def set_security_headers(response):
    # Basic hardening without breaking Bootstrap/CDN usage
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"

    # CSP yang aman untuk penggunaan bootstrap bundle + icon via CDN
    # Note: mengizinkan inline style yang ada di base.html (tag <style>) dan script dari CDN.
    response.headers[
        "Content-Security-Policy"
    ] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
    )
    return response


@app.errorhandler(400)
def bad_request(_e):
    return render_template("errors/400.html"), 400


@app.errorhandler(403)
def forbidden(_e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(_e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(_e):
    # Log exception traceback untuk debugging (tidak bocorkan detail ke user)
    app.logger.exception("Unhandled 500 error at %s %s", request.method, request.path)
    return render_template("errors/500.html"), 500


# Import Routes
from routes.auth_routes import *
from routes.barang_routes import *
from routes.barang_kosong_routes import *
from routes.keuangan_routes import *
from routes.stock_opname_routes import *

if __name__ == '__main__':
    app.run(debug=True)
