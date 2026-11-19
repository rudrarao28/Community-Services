from datetime import datetime, date, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


def utc_now():
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """
    User model representing both Librarians/Admins and Students/Members.
    Includes role-based attributes and account status.
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    student_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # 'admin' or 'member'
    status = db.Column(db.String(20), nullable=False, default='active')  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    transactions = db.relationship('Transaction', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    reservations = db.relationship('Reservation', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        """Hash and save user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify hashed password."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Check if user has librarian/admin privileges."""
        return self.role == 'admin'

    @property
    def is_active(self):
        """Used by Flask-Login to prevent inactive users from authenticating."""
        return self.status == 'active'

    def active_borrow_count(self):
        """Return the count of currently unreturned issued books."""
        return self.transactions.filter(Transaction.status.in_(['issued', 'overdue'])).count()

    def can_borrow(self, max_limit=3):
        """Evaluate if the member is eligible to borrow another book."""
        return self.status == 'active' and self.active_borrow_count() < max_limit

    def total_fines_accrued(self):
        """Sum of all fines accumulated across transactions."""
        return sum(tx.fine_amount for tx in self.transactions.all() if tx.fine_amount)

    def __repr__(self):
        return f"<User {self.id}: {self.name} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    return db.session.get(User, int(user_id))


class Category(db.Model):
    """Book categories for organization and statistical reporting."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)

    # Relationships
    books = db.relationship('Book', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f"<Category {self.id}: {self.name}>"


class Book(db.Model):
    """
    Book model storing catalog details, ISBN, and real-time inventory count.
    """
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    author = db.Column(db.String(255), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    cover_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    category = db.relationship('Category', back_populates='books')
    transactions = db.relationship('Transaction', back_populates='book', cascade='all, delete-orphan', lazy='dynamic')
    reservations = db.relationship('Reservation', back_populates='book', cascade='all, delete-orphan', lazy='dynamic')

    @property
    def is_available(self):
        """Check if at least one copy is available on shelf."""
        return self.available_copies > 0

    @property
    def issued_copies_count(self):
        """Compute number of currently borrowed copies."""
        return max(0, self.total_copies - self.available_copies)

    def __repr__(self):
        return f"<Book {self.id}: {self.title} by {self.author}>"


class Transaction(db.Model):
    """
    Borrowing transaction log tracking issues, due dates, returns, and fines.
    """
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date, nullable=True)
    fine_amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='issued')  # 'issued', 'returned', 'overdue'

    # Relationships
    user = db.relationship('User', back_populates='transactions')
    book = db.relationship('Book', back_populates='transactions')

    def calculate_current_fine(self, rate_per_day=2.0):
        """
        Calculates overdue fine at rate_per_day (Rs. 2.0/day).
        If already returned, uses return_date; otherwise uses today's date.
        """
        ref_date = self.return_date if self.return_date else date.today()
        if ref_date > self.due_date:
            late_days = (ref_date - self.due_date).days
            return round(late_days * rate_per_day, 2)
        return 0.0

    @property
    def is_overdue(self):
        """Determine if active transaction has passed its due date."""
        if self.status != 'returned' and date.today() > self.due_date:
            return True
        return False

    @property
    def days_overdue(self):
        """Calculate number of overdue days."""
        ref_date = self.return_date if self.return_date else date.today()
        if ref_date > self.due_date:
            return (ref_date - self.due_date).days
        return 0

    def __repr__(self):
        return f"<Transaction {self.id}: User {self.user_id} - Book {self.book_id} [{self.status}]>"


class Reservation(db.Model):
    """
    Book reservation queue for students requesting currently unavailable titles.
    """
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='pending')  # 'pending', 'notified', 'fulfilled', 'cancelled'
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='reservations')
    book = db.relationship('Book', back_populates='reservations')

    def __repr__(self):
        return f"<Reservation {self.id}: User {self.user_id} -> Book {self.book_id} [{self.status}]>"


class ActivityLog(db.Model):
    """
    Audit logging for administrative actions (who did what, when).
    """
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)

    # Relationships
    user = db.relationship('User', back_populates='activity_logs')

    def __repr__(self):
        return f"<ActivityLog {self.id}: {self.action} at {self.timestamp}>"
