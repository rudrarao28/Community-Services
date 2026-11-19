from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from app.models import Book


class BookForm(FlaskForm):
    """Admin form for adding or updating catalog book records."""
    title = StringField('Book Title', validators=[
        DataRequired(message="Book title is required."),
        Length(max=255)
    ])
    author = StringField('Author(s)', validators=[
        DataRequired(message="Author name is required."),
        Length(max=255)
    ])
    category_id = SelectField('Category / Subject', coerce=int, validators=[
        DataRequired(message="Please select a category.")
    ])
    isbn = StringField('ISBN', validators=[
        DataRequired(message="ISBN is required."),
        Length(min=5, max=20, message="ISBN must be between 5 and 20 characters.")
    ])
    total_copies = IntegerField('Total Inventory Copies', default=1, validators=[
        DataRequired(message="Total copies is required."),
        NumberRange(min=1, message="Total copies must be at least 1.")
    ])
    available_copies = IntegerField('Available On Shelf Copies', default=1, validators=[
        NumberRange(min=0, message="Available copies cannot be negative.")
    ])
    cover_image = FileField('Book Cover Image (Optional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Only JPG, PNG, and WebP images are allowed.')
    ])
    submit = SubmitField('Save Book Record')

    def __init__(self, original_isbn=None, *args, **kwargs):
        super(BookForm, self).__init__(*args, **kwargs)
        self.original_isbn = original_isbn

    def validate_isbn(self, isbn):
        cleaned_isbn = isbn.data.strip().replace('-', '').upper()
        if self.original_isbn and cleaned_isbn == self.original_isbn.replace('-', '').upper():
            return
        existing = Book.query.filter_by(isbn=isbn.data.strip()).first()
        if existing:
            raise ValidationError('A book with this ISBN already exists in the catalogue.')

    def validate_available_copies(self, available_copies):
        if available_copies.data is not None and self.total_copies.data is not None:
            if available_copies.data > self.total_copies.data:
                raise ValidationError('Available copies cannot exceed the total number of copies.')
