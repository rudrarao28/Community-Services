from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Decorator that restricts view access strictly to users with the 'admin' role.
    Non-authenticated users are redirected to login.
    Non-admin authenticated users receive an HTTP 403 Forbidden error.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def active_member_required(f):
    """
    Decorator ensuring current user is an active registered member.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.status != 'active':
            flash('Your account has been deactivated. Please contact the librarian.', 'danger')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated_function
