from app import db
from app.models import Book, Category, Transaction, User


def login_as_admin(client):
    return client.post('/login', data={'email': 'admin@test.edu', 'password': 'AdminPass123'}, follow_redirects=True)


def login_as_student(client):
    return client.post('/login', data={'email': 'student@test.edu', 'password': 'StudentPass123'}, follow_redirects=True)


def test_catalogue_search_public(client):
    """Test public can search and view book catalogue."""
    res = client.get('/books/catalogue')
    assert res.status_code == 200
    assert b'Python Testing Handbook' in res.data

    # Live search query
    search_res = client.get('/books/catalogue?q=Testing')
    assert b'Python Testing Handbook' in search_res.data


def test_admin_add_book(client, app):
    """Test administrator can add a new book title."""
    login_as_admin(client)
    with app.app_context():
        cat = Category.query.first()
        cat_id = cat.id

    res = client.post('/books/add', data={
        'title': 'Flask Web Development',
        'author': 'Miguel Grinberg',
        'category_id': cat_id,
        'isbn': '978-1491991732',
        'total_copies': 3,
        'available_copies': 3
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        b = Book.query.filter_by(isbn='978-1491991732').first()
        assert b is not None
        assert b.title == 'Flask Web Development'
        assert b.available_copies == 3


def test_student_cannot_add_book(client, app):
    """Test student role is forbidden (403) from accessing admin book addition."""
    login_as_student(client)
    res = client.get('/books/add')
    assert res.status_code == 403


def test_cannot_delete_book_with_active_loans(client, app):
    """Test business rule: book cannot be deleted while copies are checked out."""
    login_as_admin(client)
    with app.app_context():
        book = Book.query.first()
        student = User.query.filter_by(role='member').first()
        # Create an active loan
        tx = Transaction(
            user_id=student.id,
            book_id=book.id,
            issue_date=db.func.current_date(),
            due_date=db.func.current_date(),
            status='issued'
        )
        db.session.add(tx)
        db.session.commit()
        book_id = book.id

    del_res = client.post(f'/books/delete/{book_id}', follow_redirects=True)
    assert b'Cannot delete' in del_res.data
    with app.app_context():
        assert db.session.get(Book, book_id) is not None
