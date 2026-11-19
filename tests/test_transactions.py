from datetime import date, timedelta
from app import db
from app.models import User, Book, Transaction, Reservation


def login_as_admin(client):
    return client.post('/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'}, follow_redirects=True)


def login_as_student(client):
    return client.post('/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'}, follow_redirects=True)


def test_issue_book_success(client, app):
    """Test successful book issue decrements availability and creates transaction."""
    login_as_admin(client)
    with app.app_context():
        student = User.query.filter_by(role='member').first()
        book = Book.query.first()
        student_id = student.id
        book_id = book.id
        initial_avail = book.available_copies

    res = client.post('/admin/issue', data={
        'user_id': student_id,
        'book_id': book_id,
        'issue_date': str(date.today()),
        'due_date': str(date.today() + timedelta(days=14))
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        updated_book = db.session.get(Book, book_id)
        assert updated_book.available_copies == initial_avail - 1
        tx = Transaction.query.filter_by(user_id=student_id, book_id=book_id, status='issued').first()
        assert tx is not None
        assert tx.due_date == date.today() + timedelta(days=14)


def test_borrow_limit_enforced(client, app):
    """Test member cannot borrow more than MAX_BORROW_LIMIT (3 books)."""
    login_as_admin(client)
    with app.app_context():
        student = User.query.filter_by(role='member').first()
        book = Book.query.first()
        # Seed 3 existing active transactions
        for i in range(3):
            tx = Transaction(
                user_id=student.id,
                book_id=book.id,
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=14),
                status='issued'
            )
            db.session.add(tx)
        db.session.commit()
        student_id = student.id
        book_id = book.id

    # Attempt to issue 4th book
    res = client.post('/admin/issue', data={
        'user_id': student_id,
        'book_id': book_id,
        'issue_date': str(date.today()),
        'due_date': str(date.today() + timedelta(days=14))
    }, follow_redirects=True)

    assert b'Borrowing Limit Exceeded' in res.data


def test_return_book_and_fine_calculation(client, app):
    """Test returning overdue book calculates Rs. 2.0 per day fine and restores copy."""
    login_as_admin(client)
    with app.app_context():
        student = User.query.filter_by(role='member').first()
        book = Book.query.first()
        book.available_copies = 1

        # Seed an overdue transaction: due 4 days ago
        tx = Transaction(
            user_id=student.id,
            book_id=book.id,
            issue_date=date.today() - timedelta(days=18),
            due_date=date.today() - timedelta(days=4),
            status='overdue'
        )
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id
        book_id = book.id

    # Return today (4 days overdue * 2.0 = 8.0 Rs fine)
    res = client.post(f'/admin/return/{tx_id}', data={
        'transaction_id': tx_id,
        'return_date': str(date.today()),
        'fine_collected': 8.0
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        completed_tx = db.session.get(Transaction, tx_id)
        assert completed_tx.status == 'returned'
        assert completed_tx.fine_amount == 8.0
        restocked_book = db.session.get(Book, book_id)
        assert restocked_book.available_copies == 2


def test_student_reserve_out_of_stock_book(client, app):
    """Test student can place a reservation when copies == 0."""
    login_as_student(client)
    with app.app_context():
        book = Book.query.first()
        book.available_copies = 0
        db.session.commit()
        book_id = book.id

    res = client.post(f'/books/reserve/{book_id}', follow_redirects=True)
    assert res.status_code == 200
    assert b'Reservation confirmed' in res.data

    with app.app_context():
        student = User.query.filter_by(role='member').first()
        reservation = Reservation.query.filter_by(user_id=student.id, book_id=book_id).first()
        assert reservation is not None
        assert reservation.status == 'pending'
