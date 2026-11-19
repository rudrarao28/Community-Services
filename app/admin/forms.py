from datetime import date, timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, DateField, FloatField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional, ValidationError
from app.models import User, Book


class MemberForm(FlaskForm):
    """Admin form to add or edit members."""
    name = StringField('Full Name', validators=[
        DataRequired(message="Name is required."),
        Length(min=3, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email is required."),
        Email()
    ])
    student_id = StringField('Student / Roll ID', validators=[
        DataRequired(message="Student ID is required."),
        Length(min=3, max=50)
    ])
    password = PasswordField('Password (leave blank to keep unchanged)', validators=[
        Optional(),
        Length(min=6, message="Password must be at least 6 characters.")
    ])
    role = SelectField('Account Role', choices=[
        ('member', 'Student / Member'),
        ('admin', 'Librarian / Administrator')
    ], default='member')
    status = SelectField('Account Status', choices=[
        ('active', 'Active (Can borrow)'),
        ('inactive', 'Inactive / Deactivated')
    ], default='active')
    submit = SubmitField('Save Member')

    def __init__(self, original_user=None, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_email(self, email):
        cleaned_email = email.data.strip().lower()
        if self.original_user and cleaned_email == self.original_user.email.lower():
            return
        user = User.query.filter_by(email=cleaned_email).first()
        if user:
            raise ValidationError('Email is already registered to another user.')

    def validate_student_id(self, student_id):
        cleaned_id = student_id.data.strip().upper()
        if self.original_user and (self.original_user.student_id or '').upper() == cleaned_id:
            return
        user = User.query.filter_by(student_id=cleaned_id).first()
        if user:
            raise ValidationError('Student ID is already assigned to another user.')


class IssueBookForm(FlaskForm):
    """Form to issue a book to an eligible member."""
    user_id = SelectField('Select Member / Student', coerce=int, validators=[
        DataRequired(message="Please select a member.")
    ])
    book_id = SelectField('Select Book', coerce=int, validators=[
        DataRequired(message="Please select a book to issue.")
    ])
    issue_date = DateField('Issue Date', default=date.today, validators=[
        DataRequired(message="Issue date is required.")
    ])
    due_date = DateField('Due Date (Default: 14 Days)', default=lambda: date.today() + timedelta(days=14), validators=[
        DataRequired(message="Due date is required.")
    ])
    submit = SubmitField('Confirm & Issue Book')


class ReturnBookForm(FlaskForm):
    """Form to process return of borrowed book and record fines."""
    transaction_id = HiddenField('Transaction ID', validators=[DataRequired()])
    return_date = DateField('Return Date', default=date.today, validators=[
        DataRequired(message="Return date is required.")
    ])
    fine_collected = FloatField('Fine Collected (Rs.)', default=0.0)
    submit = SubmitField('Process Return')
