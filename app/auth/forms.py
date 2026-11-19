from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from app.models import User


class LoginForm(FlaskForm):
    """User login form with remember me capability."""
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required.")
    ])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    """Student/Member registration form."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=3, max=100, message="Name must be between 3 and 100 characters.")
    ])
    student_id = StringField('Student / Member ID', validators=[
        DataRequired(message="Student ID is required."),
        Length(min=3, max=50, message="ID must be between 3 and 50 characters."),
        Regexp(r'^[A-Za-z0-9\-_]+$', message="Student ID can only contain letters, numbers, hyphens, and underscores.")
    ])
    email = StringField('University Email', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid university email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Create Student Account')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.strip().lower()).first()
        if user:
            raise ValidationError('An account with this email address already exists.')

    def validate_student_id(self, student_id):
        user = User.query.filter_by(student_id=student_id.data.strip().upper()).first()
        if user:
            raise ValidationError('This Student ID is already registered in the library system.')


class ForgotPasswordForm(FlaskForm):
    """Request password reset link."""
    email = StringField('Registered Email Address', validators=[
        DataRequired(message="Email is required."),
        Email(message="Please enter a valid email address.")
    ])
    submit = SubmitField('Send Reset Instructions')


class ResetPasswordForm(FlaskForm):
    """Form to enter a new password after verifying reset token."""
    password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('password', message="Passwords must match.")
    ])
    submit = SubmitField('Update Password')


class ProfileForm(FlaskForm):
    """Profile editing form for members."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Full name is required."),
        Length(min=3, max=100)
    ])
    student_id = StringField('Student / Member ID', validators=[
        DataRequired(message="Student ID is required."),
        Length(min=3, max=50)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email()
    ])
    submit = SubmitField('Save Profile Changes')

    def __init__(self, original_user, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_email(self, email):
        if email.data.strip().lower() != self.original_user.email.lower():
            user = User.query.filter_by(email=email.data.strip().lower()).first()
            if user:
                raise ValidationError('This email is already in use by another user.')

    def validate_student_id(self, student_id):
        if student_id.data and student_id.data.strip().upper() != (self.original_user.student_id or '').upper():
            user = User.query.filter_by(student_id=student_id.data.strip().upper()).first()
            if user:
                raise ValidationError('This Student ID is already registered to another user.')


class ChangePasswordForm(FlaskForm):
    """Form to update account password."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required.")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required."),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('new_password', message="New passwords must match.")
    ])
    submit = SubmitField('Change Password')
