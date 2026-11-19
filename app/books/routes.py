import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import Book, Category, Transaction, Reservation, ActivityLog
from app.auth.decorators import admin_required, active_member_required
from app.books.forms import BookForm

books_bp = Blueprint('books', __name__)


def save_cover_image(form_picture):
    """Save uploaded book cover image with secure unique filename."""
    if not form_picture:
        return None
    filename = secure_filename(form_picture.filename)
    if not filename:
        return None
    import uuid
    unique_filename = f"{uuid.uuid4().hex[:10]}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    form_picture.save(file_path)
    return unique_filename


@books_bp.route('/catalogue')
def catalogue():
    """
    Public and student book catalogue with real-time search, category filter, 
    availability filter, sorting, and pagination.
    """
    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    availability = request.args.get('availability', 'all')
    sort_by = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 9

    # Base query joined with category
    query = Book.query.join(Category)

    # Search filter: Title, Author, ISBN, or exact Book ID
    if search_query:
        if search_query.isdigit():
            query = query.filter(
                or_(
                    Book.id == int(search_query),
                    Book.title.ilike(f"%{search_query}%"),
                    Book.author.ilike(f"%{search_query}%"),
                    Book.isbn.ilike(f"%{search_query}%")
                )
            )
        else:
            query = query.filter(
                or_(
                    Book.title.ilike(f"%{search_query}%"),
                    Book.author.ilike(f"%{search_query}%"),
                    Book.isbn.ilike(f"%{search_query}%")
                )
            )

    # Category filter
    if category_id:
        query = query.filter(Book.category_id == category_id)

    # Availability filter
    if availability == 'available':
        query = query.filter(Book.available_copies > 0)
    elif availability == 'unavailable':
        query = query.filter(Book.available_copies == 0)

    # Sorting
    if sort_by == 'title_asc':
        query = query.order_by(Book.title.asc())
    elif sort_by == 'title_desc':
        query = query.order_by(Book.title.desc())
    elif sort_by == 'author_asc':
        query = query.order_by(Book.author.asc())
    elif sort_by == 'copies':
        query = query.order_by(Book.available_copies.desc())
    else:  # 'newest'
        query = query.order_by(Book.id.desc())

    books_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.order_by(Category.name.asc()).all()

    # Support JSON response for live search autocomplete
    if request.headers.get('Accept') == 'application/json' or request.args.get('format') == 'json':
        items = []
        for b in books_paginated.items:
            items.append({
                'id': b.id,
                'title': b.title,
                'author': b.author,
                'category': b.category.name,
                'isbn': b.isbn,
                'total_copies': b.total_copies,
                'available_copies': b.available_copies,
                'is_available': b.is_available,
                'cover_image': url_for('static', filename=f"uploads/{b.cover_image}") if b.cover_image else None,
                'view_url': url_for('books.view_book', book_id=b.id)
            })
        return jsonify({
            'books': items,
            'total': books_paginated.total,
            'pages': books_paginated.pages,
            'current_page': books_paginated.page
        })

    return render_template(
        'books/catalogue.html',
        books=books_paginated,
        categories=categories,
        search_query=search_query,
        selected_category=category_id,
        availability=availability,
        sort_by=sort_by
    )


@books_bp.route('/view/<int:book_id>')
def view_book(book_id):
    """Display individual book details, copy status, and reservation button."""
    book = Book.query.get_or_404(book_id)
    
    # Check if current user already reserved or borrowed this book
    user_reservation = None
    user_has_borrowed = False
    if current_user.is_authenticated and not current_user.is_admin:
        user_reservation = Reservation.query.filter_by(
            user_id=current_user.id,
            book_id=book.id,
            status='pending'
        ).first()
        active_tx = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.book_id == book.id,
            Transaction.status.in_(['issued', 'overdue'])
        ).first()
        user_has_borrowed = bool(active_tx)

    return render_template(
        'books/view.html',
        book=book,
        user_reservation=user_reservation,
        user_has_borrowed=user_has_borrowed
    )


@books_bp.route('/manage')
@admin_required
def manage_books():
    """Admin table view for searching and managing all books."""
    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Book.query.join(Category)
    if search_query:
        query = query.filter(
            or_(
                Book.id == int(search_query) if search_query.isdigit() else False,
                Book.title.ilike(f"%{search_query}%"),
                Book.author.ilike(f"%{search_query}%"),
                Book.isbn.ilike(f"%{search_query}%")
            )
        )
    if category_id:
        query = query.filter(Book.category_id == category_id)

    books_paginated = query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.order_by(Category.name.asc()).all()

    return render_template(
        'books/manage.html',
        books=books_paginated,
        categories=categories,
        search_query=search_query,
        selected_category=category_id
    )


@books_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_book():
    """Add a new book title to the catalogue."""
    form = BookForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()]

    if form.validate_on_submit():
        cover_filename = None
        if form.cover_image.data:
            cover_filename = save_cover_image(form.cover_image.data)

        new_book = Book(
            title=form.title.data.strip(),
            author=form.author.data.strip(),
            category_id=form.category_id.data,
            isbn=form.isbn.data.strip(),
            total_copies=form.total_copies.data,
            available_copies=form.available_copies.data if form.available_copies.data is not None else form.total_copies.data,
            cover_image=cover_filename
        )
        db.session.add(new_book)
        db.session.commit()

        # Log admin activity
        log = ActivityLog(
            user_id=current_user.id,
            action=f"Added book '{new_book.title}' by {new_book.author} (ISBN: {new_book.isbn}, Copies: {new_book.total_copies})"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Book '{new_book.title}' has been successfully added to the catalog.", 'success')
        return redirect(url_for('books.manage_books'))

    return render_template('books/form.html', form=form, title="Add New Book")


@books_bp.route('/edit/<int:book_id>', methods=['GET', 'POST'])
@admin_required
def edit_book(book_id):
    """Edit book details, category, or inventory copy counts."""
    book = Book.query.get_or_404(book_id)
    form = BookForm(original_isbn=book.isbn)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name.asc()).all()]

    if form.validate_on_submit():
        if form.cover_image.data:
            book.cover_image = save_cover_image(form.cover_image.data)

        # Validate that available copies cannot be adjusted below the copies currently checked out
        issued_count = book.total_copies - book.available_copies
        if form.total_copies.data < issued_count:
            flash(f"Total copies cannot be less than currently issued copies ({issued_count}).", 'danger')
            return render_template('books/form.html', form=form, title="Edit Book", book=book)

        book.title = form.title.data.strip()
        book.author = form.author.data.strip()
        book.category_id = form.category_id.data
        book.isbn = form.isbn.data.strip()
        book.total_copies = form.total_copies.data
        book.available_copies = form.available_copies.data

        # Log admin activity
        log = ActivityLog(
            user_id=current_user.id,
            action=f"Updated book ID #{book.id} ('{book.title}') details"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Book '{book.title}' was successfully updated.", 'success')
        return redirect(url_for('books.manage_books'))

    elif request.method == 'GET':
        form.title.data = book.title
        form.author.data = book.author
        form.category_id.data = book.category_id
        form.isbn.data = book.isbn
        form.total_copies.data = book.total_copies
        form.available_copies.data = book.available_copies

    return render_template('books/form.html', form=form, title="Edit Book", book=book)


@books_bp.route('/delete/<int:book_id>', methods=['POST'])
@admin_required
def delete_book(book_id):
    """Delete a book from catalog only if no copies are actively borrowed."""
    book = Book.query.get_or_404(book_id)

    # Check for active borrows
    active_borrows = Transaction.query.filter(
        Transaction.book_id == book.id,
        Transaction.status.in_(['issued', 'overdue'])
    ).count()

    if active_borrows > 0:
        flash(f"Cannot delete '{book.title}': {active_borrows} copy/copies are currently issued to members.", 'danger')
        return redirect(url_for('books.manage_books'))

    book_title = book.title
    db.session.delete(book)
    
    log = ActivityLog(
        user_id=current_user.id,
        action=f"Deleted book '{book_title}' (ID #{book_id})"
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Book '{book_title}' was successfully removed from the system.", 'success')
    return redirect(url_for('books.manage_books'))


@books_bp.route('/reserve/<int:book_id>', methods=['POST'])
@login_required
@active_member_required
def reserve_book(book_id):
    """Reserve a book when 0 copies are available."""
    book = Book.query.get_or_404(book_id)

    # If book is already available, reservation is not required
    if book.available_copies > 0:
        flash(f"'{book.title}' has copies available right now. Visit the library counter to borrow.", 'info')
        return redirect(url_for('books.view_book', book_id=book.id))

    # Check if student already holds a pending reservation
    existing_reservation = Reservation.query.filter_by(
        user_id=current_user.id,
        book_id=book.id,
        status='pending'
    ).first()

    if existing_reservation:
        flash(f"You already have a pending reservation for '{book.title}'.", 'warning')
        return redirect(url_for('books.view_book', book_id=book.id))

    # Create new reservation
    reservation = Reservation(
        user_id=current_user.id,
        book_id=book.id,
        status='pending'
    )
    db.session.add(reservation)

    log = ActivityLog(
        user_id=current_user.id,
        action=f"Member {current_user.name} placed a reservation on '{book.title}'"
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Reservation confirmed for '{book.title}'. You will be notified when a copy is returned.", 'success')
    return redirect(url_for('books.view_book', book_id=book.id))
