import io
import csv
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app, Response
from flask_login import login_required, current_user
from sqlalchemy import or_, func, desc
from app import db
from app.models import User, Book, Category, Transaction, Reservation, ActivityLog
from app.auth.decorators import admin_required
from app.admin.forms import MemberForm, IssueBookForm, ReturnBookForm

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    Administrative Command Dashboard.
    Visualizes KPIs, circulation trends (Chart.js), categories, and audit events.
    """
    today = date.today()

    # Synchronize overdue statuses for active transactions
    overdue_txs = Transaction.query.filter(
        Transaction.status == 'issued',
        Transaction.due_date < today
    ).all()
    for tx in overdue_txs:
        tx.status = 'overdue'
    if overdue_txs:
        db.session.commit()

    # Primary Statistics
    total_titles = Book.query.count()
    total_copies_inventory = db.session.query(func.coalesce(func.sum(Book.total_copies), 0)).scalar()
    available_copies = db.session.query(func.coalesce(func.sum(Book.available_copies), 0)).scalar()
    issued_books_count = Transaction.query.filter(Transaction.status.in_(['issued', 'overdue'])).count()
    overdue_count = Transaction.query.filter(
        Transaction.status.in_(['issued', 'overdue']),
        Transaction.due_date < today
    ).count()
    total_members = User.query.filter_by(role='member').count()
    total_fines_collected = db.session.query(func.coalesce(func.sum(Transaction.fine_amount), 0.0)).scalar()
    pending_reservations = Reservation.query.filter_by(status='pending').count()

    # Chart 1: Category Distribution
    category_counts = db.session.query(
        Category.name, func.count(Book.id)
    ).join(Book, Book.category_id == Category.id).group_by(Category.name).all()
    cat_labels = [c[0] for c in category_counts]
    cat_data = [c[1] for c in category_counts]

    # Chart 2: Issues across recent months (6 months)
    six_months_ago = today - timedelta(days=180)
    month_expr = (
        func.strftime('%Y-%m', Transaction.issue_date)
        if 'sqlite' in current_app.config['SQLALCHEMY_DATABASE_URI']
        else func.date_format(Transaction.issue_date, '%Y-%m')
    )
    monthly_issues = db.session.query(
        month_expr.label('month_label'),
        func.count(Transaction.id)
    ).filter(Transaction.issue_date >= six_months_ago).group_by(month_expr).order_by(month_expr).all()

    month_labels = [m[0] for m in monthly_issues] or [today.strftime('%Y-%m')]
    month_data = [m[1] for m in monthly_issues] or [issued_books_count]

    # Recent Activity & Transactions
    recent_activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(8).all()
    recent_transactions = Transaction.query.order_by(Transaction.id.desc()).limit(6).all()

    return render_template(
        'admin/dashboard.html',
        total_titles=total_titles,
        total_copies_inventory=total_copies_inventory,
        available_copies=available_copies,
        issued_books_count=issued_books_count,
        overdue_count=overdue_count,
        total_members=total_members,
        total_fines_collected=total_fines_collected,
        pending_reservations=pending_reservations,
        cat_labels=cat_labels,
        cat_data=cat_data,
        month_labels=month_labels,
        month_data=month_data,
        recent_activities=recent_activities,
        recent_transactions=recent_transactions
    )


# ==============================================================================
# MEMBER MANAGEMENT
# ==============================================================================

@admin_bp.route('/members')
@admin_required
def members():
    """Member directory list with search, status filtering, and pagination."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = User.query.filter_by(role='member')
    if search_query:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                User.student_id.ilike(f"%{search_query}%")
            )
        )
    if status_filter in ['active', 'inactive']:
        query = query.filter_by(status=status_filter)

    members_paginated = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'admin/members.html',
        members=members_paginated,
        search_query=search_query,
        status_filter=status_filter
    )


@admin_bp.route('/members/add', methods=['GET', 'POST'])
@admin_required
def add_member():
    """Admin manually adds a new student or administrator."""
    form = MemberForm()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data.strip(),
            email=form.email.data.strip().lower(),
            student_id=form.student_id.data.strip().upper(),
            role=form.role.data,
            status=form.status.data
        )
        password = form.password.data or 'Student@123'
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        log = ActivityLog(
            user_id=current_user.id,
            action=f"Created user account: {new_user.name} ({new_user.email}) as {new_user.role}"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"User account for '{new_user.name}' created successfully.", 'success')
        return redirect(url_for('admin.members'))

    return render_template('admin/member_form.html', form=form, title="Add New Member")


@admin_bp.route('/members/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_member(user_id):
    """Admin updates member account details or resets password."""
    user = User.query.get_or_404(user_id)
    form = MemberForm(original_user=user)

    if form.validate_on_submit():
        user.name = form.name.data.strip()
        user.email = form.email.data.strip().lower()
        user.student_id = form.student_id.data.strip().upper()
        user.role = form.role.data
        user.status = form.status.data

        if form.password.data:
            user.set_password(form.password.data)

        log = ActivityLog(
            user_id=current_user.id,
            action=f"Updated profile for user '{user.name}' (ID #{user.id})"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Member '{user.name}' details updated.", 'success')
        return redirect(url_for('admin.members'))

    elif request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.student_id.data = user.student_id
        form.role.data = user.role
        form.status.data = user.status

    return render_template('admin/member_form.html', form=form, title="Edit Member", user=user)


@admin_bp.route('/members/toggle-status/<int:user_id>', methods=['POST'])
@admin_required
def toggle_member_status(user_id):
    """Activate or deactivate a student membership."""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own administrative account.", 'warning')
        return redirect(url_for('admin.members'))

    user.status = 'inactive' if user.status == 'active' else 'active'
    
    log = ActivityLog(
        user_id=current_user.id,
        action=f"Changed user status for '{user.name}' to '{user.status}'"
    )
    db.session.add(log)
    db.session.commit()

    flash(f"Account status for {user.name} changed to {user.status.upper()}.", 'info')
    return redirect(url_for('admin.members'))


@admin_bp.route('/members/history/<int:user_id>')
@admin_required
def member_history(user_id):
    """View complete borrowing, return, and fine record for a specific member."""
    user = User.query.get_or_404(user_id)
    transactions = user.transactions.order_by(Transaction.id.desc()).all()
    reservations = user.reservations.order_by(Reservation.id.desc()).all()
    active_borrows = [tx for tx in transactions if tx.status in ['issued', 'overdue']]

    return render_template(
        'admin/member_history.html',
        member=user,
        transactions=transactions,
        reservations=reservations,
        active_borrows=active_borrows
    )


# ==============================================================================
# BOOK ISSUE & RETURN WORKFLOW
# ==============================================================================

@admin_bp.route('/issue', methods=['GET', 'POST'])
@admin_required
def issue_book():
    """
    Issue a book to a member.
    Enforces business rules:
    - Member must be active
    - Member cannot exceed MAX_BORROW_LIMIT (3 books)
    - Book must have available_copies > 0
    - Auto-sets issue_date (today) and due_date (today + 14 days)
    - Updates available_copies (-1)
    """
    form = IssueBookForm()
    max_limit = current_app.config.get('MAX_BORROW_LIMIT', 3)

    # Populate dropdown choices with informative labels
    active_members = User.query.filter_by(role='member', status='active').order_by(User.name.asc()).all()
    form.user_id.choices = [
        (u.id, f"{u.name} (ID: {u.student_id or 'N/A'}) - Borrowed: {u.active_borrow_count()}/{max_limit}")
        for u in active_members
    ]

    available_books = Book.query.filter(Book.available_copies > 0).order_by(Book.title.asc()).all()
    form.book_id.choices = [
        (b.id, f"{b.title} by {b.author} [Available: {b.available_copies}/{b.total_copies}]")
        for b in available_books
    ]

    # Pre-select book if passed via query string
    prefill_book_id = request.args.get('prefill_book_id', type=int)
    if request.method == 'GET' and prefill_book_id:
        form.book_id.data = prefill_book_id

    if form.validate_on_submit():
        user = User.query.get_or_404(form.user_id.data)
        book = Book.query.get_or_404(form.book_id.data)

        # Enforce Rule 1: Member Status
        if user.status != 'active':
            flash(f"Cannot issue book: Member {user.name} is deactivated.", 'danger')
            return render_template('admin/issue_form.html', form=form)

        # Enforce Rule 2: Borrowing Limit
        if user.active_borrow_count() >= max_limit:
            flash(f"Borrowing Limit Exceeded! {user.name} already has {user.active_borrow_count()} books issued (Max limit is {max_limit}).", 'danger')
            return render_template('admin/issue_form.html', form=form)

        # Enforce Rule 3: Book Availability
        if book.available_copies < 1:
            flash(f"Sorry, no copies of '{book.title}' are currently available on the shelf.", 'danger')
            return render_template('admin/issue_form.html', form=form)

        # Create Transaction
        transaction = Transaction(
            user_id=user.id,
            book_id=book.id,
            issue_date=form.issue_date.data,
            due_date=form.due_date.data,
            status='issued',
            fine_amount=0.0
        )
        # Decrement availability
        book.available_copies -= 1

        db.session.add(transaction)
        
        # Log action
        log = ActivityLog(
            user_id=current_user.id,
            action=f"Issued book '{book.title}' to student {user.name} ({user.student_id}). Due: {form.due_date.data}"
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Success! '{book.title}' has been issued to {user.name}. Due Date: {form.due_date.data.strftime('%b %d, %Y')}.", 'success')
        return redirect(url_for('admin.transactions'))

    return render_template('admin/issue_form.html', form=form)


@admin_bp.route('/return/<int:transaction_id>', methods=['GET', 'POST'])
@admin_required
def return_book(transaction_id):
    """
    Process book return and late fine calculation.
    Enforces rules:
    - Auto-calculates fine at Rs. 2.00 per day if returned past due_date
    - Increments book.available_copies (+1)
    - Checks pending reservations queue and notifies librarian
    """
    tx = Transaction.query.get_or_404(transaction_id)
    if tx.status == 'returned':
        flash('This transaction has already been completed and returned.', 'info')
        return redirect(url_for('admin.transactions'))

    fine_rate = current_app.config.get('FINE_PER_DAY', 2.0)
    today = date.today()
    calculated_fine = tx.calculate_current_fine(rate_per_day=fine_rate)

    form = ReturnBookForm()
    if request.method == 'GET':
        form.transaction_id.data = tx.id
        form.return_date.data = today
        form.fine_collected.data = calculated_fine

    if form.validate_on_submit():
        tx.return_date = form.return_date.data
        tx.fine_amount = float(form.fine_collected.data or 0.0)
        tx.status = 'returned'

        # Restore inventory
        if tx.book.available_copies < tx.book.total_copies:
            tx.book.available_copies += 1

        # Check reservation waiting list
        pending_reservation = Reservation.query.filter_by(
            book_id=tx.book.id,
            status='pending'
        ).order_by(Reservation.created_at.asc()).first()

        reservation_msg = ""
        if pending_reservation:
            pending_reservation.status = 'notified'
            reservation_msg = f" Note: Student {pending_reservation.user.name} has a pending reservation for this book!"

        log = ActivityLog(
            user_id=current_user.id,
            action=f"Processed return of '{tx.book.title}' from {tx.user.name}. Fine assessed: Rs. {tx.fine_amount:.2f}."
        )
        db.session.add(log)
        db.session.commit()

        flash(f"Book '{tx.book.title}' successfully returned by {tx.user.name}. Fine: Rs. {tx.fine_amount:.2f}.{reservation_msg}", 'success')
        return redirect(url_for('admin.transactions'))

    return render_template('admin/return_form.html', form=form, transaction=tx, calculated_fine=calculated_fine)


@admin_bp.route('/transactions')
@admin_required
def transactions():
    """Transaction audit table with multi-parameter filtering and search."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Transaction.query.join(User).join(Book)

    if search_query:
        query = query.filter(
            or_(
                User.name.ilike(f"%{search_query}%"),
                User.student_id.ilike(f"%{search_query}%"),
                Book.title.ilike(f"%{search_query}%"),
                Book.isbn.ilike(f"%{search_query}%")
            )
        )

    if status_filter in ['issued', 'returned', 'overdue']:
        query = query.filter(Transaction.status == status_filter)

    if date_from:
        try:
            df = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Transaction.issue_date >= df)
        except ValueError:
            pass

    if date_to:
        try:
            dt = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Transaction.issue_date <= dt)
        except ValueError:
            pass

    txs_paginated = query.order_by(Transaction.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'admin/transactions.html',
        transactions=txs_paginated,
        search_query=search_query,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to
    )


# ==============================================================================
# RESERVATIONS MANAGEMENT
# ==============================================================================

@admin_bp.route('/reservations')
@admin_required
def reservations():
    """Manage student book reservation requests and queues."""
    reservations_list = Reservation.query.order_by(Reservation.created_at.desc()).all()
    return render_template('admin/reservations.html', reservations=reservations_list)


@admin_bp.route('/reservations/update-status/<int:res_id>/<string:new_status>', methods=['POST'])
@admin_required
def update_reservation_status(res_id, new_status):
    """Mark a reservation fulfilled or cancelled."""
    res = Reservation.query.get_or_404(res_id)
    if new_status in ['pending', 'notified', 'fulfilled', 'cancelled']:
        res.status = new_status
        db.session.commit()
        flash(f"Reservation status updated to {new_status}.", 'info')
    return redirect(url_for('admin.reservations'))


# ==============================================================================
# AUDIT LOGS & REPORTS
# ==============================================================================

@admin_bp.route('/activity-logs')
@admin_required
def activity_logs():
    """Administrative action audit history."""
    page = request.args.get('page', 1, type=int)
    logs_paginated = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/activity_logs.html', logs=logs_paginated)


@admin_bp.route('/reports')
@admin_required
def reports():
    """
    Consolidated Library Reporting Center:
    - Overdue books and late fee liabilities
    - Most frequently issued books
    - Top active member borrowers
    """
    today = date.today()

    # 1. Overdue List
    overdue_txs = Transaction.query.filter(
        Transaction.status.in_(['issued', 'overdue']),
        Transaction.due_date < today
    ).order_by(Transaction.due_date.asc()).all()

    # 2. Most Issued Books
    most_issued = db.session.query(
        Book, func.count(Transaction.id).label('borrow_count')
    ).join(Transaction, Book.id == Transaction.book_id)\
     .group_by(Book.id)\
     .order_by(desc('borrow_count'))\
     .limit(10).all()

    # 3. Top Active Members
    top_members = db.session.query(
        User, func.count(Transaction.id).label('total_borrows')
    ).join(Transaction, User.id == Transaction.user_id)\
     .filter(User.role == 'member')\
     .group_by(User.id)\
     .order_by(desc('total_borrows'))\
     .limit(10).all()

    return render_template(
        'admin/reports.html',
        overdue_txs=overdue_txs,
        most_issued=most_issued,
        top_members=top_members
    )


@admin_bp.route('/reports/export-csv')
@admin_required
def export_csv():
    """Export library reports to standard CSV format."""
    report_type = request.args.get('type', 'transactions')
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'overdue':
        today = date.today()
        writer.writerow(['Transaction ID', 'Student ID', 'Student Name', 'Book Title', 'ISBN', 'Issue Date', 'Due Date', 'Days Overdue', 'Accrued Fine (Rs)'])
        overdues = Transaction.query.filter(
            Transaction.status.in_(['issued', 'overdue']),
            Transaction.due_date < today
        ).all()
        for tx in overdues:
            days_late = (today - tx.due_date).days
            fine = days_late * current_app.config.get('FINE_PER_DAY', 2.0)
            writer.writerow([
                tx.id, tx.user.student_id or 'N/A', tx.user.name,
                tx.book.title, tx.book.isbn, tx.issue_date, tx.due_date,
                days_late, f"{fine:.2f}"
            ])
        filename = f"library_overdue_report_{today}.csv"

    elif report_type == 'most_issued':
        writer.writerow(['Book ID', 'Title', 'Author', 'Category', 'ISBN', 'Total Copies', 'Total Times Borrowed'])
        records = db.session.query(
            Book, func.count(Transaction.id).label('borrow_count')
        ).join(Transaction, Book.id == Transaction.book_id).group_by(Book.id).order_by(desc('borrow_count')).all()
        for b, count in records:
            writer.writerow([b.id, b.title, b.author, b.category.name, b.isbn, b.total_copies, count])
        filename = f"most_issued_books_{date.today()}.csv"

    else:  # 'transactions'
        writer.writerow(['Transaction ID', 'Member ID', 'Member Name', 'Book Title', 'ISBN', 'Issue Date', 'Due Date', 'Return Date', 'Status', 'Fine Amount'])
        txs = Transaction.query.order_by(Transaction.id.desc()).all()
        for tx in txs:
            writer.writerow([
                tx.id, tx.user.student_id or 'N/A', tx.user.name,
                tx.book.title, tx.book.isbn, tx.issue_date, tx.due_date,
                tx.return_date or 'Not Returned', tx.status, f"{tx.fine_amount:.2f}"
            ])
        filename = f"library_transactions_{date.today()}.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@admin_bp.route('/reports/export-pdf')
@admin_required
def export_pdf():
    """Generate and download a professional PDF overdue report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        elements = []
        styles = getSampleStyleSheet()

        # Header Title
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=6
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748b'),
            spaceAfter=15
        )

        elements.append(Paragraph("University Library Management System", title_style))
        elements.append(Paragraph(f"Official Overdue Books Report &bull; Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", subtitle_style))
        elements.append(Spacer(1, 10))

        # Data Table
        today = date.today()
        overdue_txs = Transaction.query.filter(
            Transaction.status.in_(['issued', 'overdue']),
            Transaction.due_date < today
        ).all()

        data = [['Tx ID', 'Student Name', 'ID Number', 'Book Title', 'Due Date', 'Days Late', 'Fine (Rs)']]
        for tx in overdue_txs:
            days_late = (today - tx.due_date).days
            fine = days_late * current_app.config.get('FINE_PER_DAY', 2.0)
            data.append([
                str(tx.id),
                tx.user.name[:20],
                tx.user.student_id or 'N/A',
                tx.book.title[:25],
                tx.due_date.strftime('%Y-%m-%d'),
                str(days_late),
                f"Rs. {fine:.2f}"
            ])

        if len(data) == 1:
            data.append(['-', 'No overdue books recorded at this time.', '-', '-', '-', '-', '-'])

        table = Table(data, colWidths=[40, 95, 75, 150, 65, 55, 60])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
            ('TOPPADDING', (0, 0), (-1, 0), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("UN SDG 4: Quality & Inclusive Education &bull; University Community Services Project", subtitle_style))

        doc.build(elements)
        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"overdue_report_{today}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        flash(f"PDF generation failed: {str(e)}. Exporting as CSV instead.", 'warning')
        return redirect(url_for('admin.export_csv', type='overdue'))
