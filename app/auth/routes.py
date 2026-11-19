import sys
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from app import db
from app.models import User, ActivityLog
from app.auth.forms import (
    LoginForm, RegistrationForm, ForgotPasswordForm,
    ResetPasswordForm, ProfileForm, ChangePasswordForm
)

auth_bp = Blueprint('auth', __name__)


def generate_reset_token(user_id):
    """Generate a cryptographic time-limited password reset token (1 hour valid)."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps({'user_id': user_id}, salt='password-reset-salt')


def verify_reset_token(token, max_age_seconds=3600):
    """Verify validity and expiration of password reset token."""
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = s.loads(token, salt='password-reset-salt', max_age=max_age_seconds)
        return data.get('user_id')
    except (SignatureExpired, BadTimeSignature, Exception):
        return None


@auth_bp.route('/')
def index():
    """Root entry point: redirects authenticated users to their dashboard, otherwise landing page."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('member.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles authentication for both Librarians and Students."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('member.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        
        if user and user.check_password(form.password.data):
            if user.status != 'active':
                flash('Your account has been deactivated. Please contact the librarian.', 'danger')
                return render_template('auth/login.html', form=form)

            login_user(user, remember=form.remember_me.data)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Log admin login activity
            if user.is_admin:
                log = ActivityLog(user_id=user.id, action=f"Admin {user.name} signed in")
                db.session.add(log)
                db.session.commit()

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            
            return redirect(url_for('admin.dashboard') if user.is_admin else url_for('member.dashboard'))
        else:
            flash('Invalid email or password. Please verify your credentials.', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Logs the user out and clears the session."""
    user_name = current_user.name
    is_admin = current_user.is_admin
    user_id = current_user.id
    
    if is_admin:
        log = ActivityLog(user_id=user_id, action=f"Admin {user_name} signed out")
        db.session.add(log)
        db.session.commit()

    logout_user()
    flash('You have been securely signed out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Self-registration for Students/Members only."""
    if current_user.is_authenticated:
        return redirect(url_for('member.dashboard'))

    form = RegistrationForm()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            student_id=form.student_id.data.strip().upper(),
            role='member',
            status='active'
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()

        # Log new registration
        log = ActivityLog(user_id=new_user.id, action=f"New member registered: {new_user.name} ({new_user.student_id})")
        db.session.add(log)
        db.session.commit()

        flash('Registration successful! You may now sign in with your credentials.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset link via token."""
    form = ForgotPasswordForm()
    dev_reset_url = None

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user:
            token = generate_reset_token(user.id)
            dev_reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Print to stdout/console for local development viva demonstration
            print(f"\n================ PASSWORD RESET LINK ================\nUser: {user.email}\nURL:  {dev_reset_url}\n=====================================================\n", file=sys.stdout)
            
            flash('Password reset instructions generated! For local testing, use the reset link displayed below.', 'info')
        else:
            flash('If that email is registered in our records, password instructions have been sent.', 'info')

    return render_template('auth/forgot_password.html', form=form, dev_reset_url=dev_reset_url)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Confirm new password using secure time-limited token."""
    user_id = verify_reset_token(token)
    if not user_id:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.get_or_404(user_id)
    form = ResetPasswordForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        log = ActivityLog(user_id=user.id, action=f"Password reset completed for {user.email}")
        db.session.add(log)
        db.session.commit()

        flash('Your password has been successfully reset! Please sign in with your new password.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update current user account details."""
    form = ProfileForm(original_user=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.email = form.email.data.strip().lower()
        if not current_user.is_admin and form.student_id.data:
            current_user.student_id = form.student_id.data.strip().upper()
        
        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
        form.student_id.data = current_user.student_id

    return render_template('auth/profile.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change account password securely after verifying current password."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Incorrect current password.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('auth.profile'))

    return render_template('auth/change_password.html', form=form)
