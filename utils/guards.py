from flask import session, redirect, abort


def require_login():
    if 'username' not in session:
        return redirect('/')
    return None


def require_owner():
    if 'username' not in session:
        return redirect('/')
    if session.get('role') != 'owner':
        return abort(403)
    return None
