import pytest
from app import create_app, db
from app.models import User, Category, Book, Transaction, Reservation
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a fresh Flask application for automated tests."""
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()

        # Seed test category
        cat = Category(name="Computer Science")
        db.session.add(cat)

        # Seed test admin
        admin = User(name="Test Admin", email="admin@test.edu", role="admin", status="active")
        admin.set_password("AdminPass123")
        db.session.add(admin)

        # Seed test member
        member = User(name="Test Student", email="student@test.edu", student_id="STU-TEST-001", role="member", status="active")
        member.set_password("StudentPass123")
        db.session.add(member)

        # Seed sample test book
        book = Book(
            title="Python Testing Handbook",
            author="Test Author",
            category=cat,
            isbn="978-1111222233",
            total_copies=2,
            available_copies=2
        )
        db.session.add(book)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Test CLI runner."""
    return app.test_cli_runner()
