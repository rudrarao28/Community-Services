from app import db
from app.models import User
from app.auth.routes import generate_reset_token, verify_reset_token


def test_student_registration_success(client, app):
    """Test self-registration for new student members."""
    res = client.post('/register', data={
        'name': 'New Student',
        'student_id': 'STU-999',
        'email': 'newstudent@test.edu',
        'password': 'SecurePassword123',
        'confirm_password': 'SecurePassword123'
    }, follow_redirects=True)

    assert res.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='newstudent@test.edu').first()
        assert user is not None
        assert user.role == 'member'
        assert user.status == 'active'
        assert user.check_password('SecurePassword123')


def test_registration_duplicate_email(client, app):
    """Test validation prevents duplicate email registration."""
    res = client.post('/register', data={
        'name': 'Duplicate Person',
        'student_id': 'STU-UNIQUE',
        'email': 'student@test.edu',  # already seeded in conftest
        'password': 'Password123',
        'confirm_password': 'Password123'
    })
    assert b'An account with this email address already exists' in res.data


def test_login_success_and_logout(client):
    """Test authentication and session teardown."""
    login_res = client.post('/login', data={
        'email': 'student@test.edu',
        'password': 'StudentPass123'
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b'Welcome back, Test Student!' in login_res.data

    logout_res = client.get('/logout', follow_redirects=True)
    assert logout_res.status_code == 200
    assert b'You have been securely signed out' in logout_res.data


def test_login_invalid_password(client):
    """Test rejection with invalid password."""
    res = client.post('/login', data={
        'email': 'student@test.edu',
        'password': 'WrongPassword'
    }, follow_redirects=True)
    assert b'Invalid email or password' in res.data


def test_inactive_user_cannot_login(client, app):
    """Test deactivated members are blocked from logging in."""
    with app.app_context():
        user = User.query.filter_by(email='student@test.edu').first()
        user.status = 'inactive'
        db.session.commit()

    res = client.post('/login', data={
        'email': 'student@test.edu',
        'password': 'StudentPass123'
    }, follow_redirects=True)
    assert b'Your account has been deactivated' in res.data


def test_password_reset_token(app):
    """Test secure token generation and validation for password recovery."""
    with app.app_context():
        user = User.query.filter_by(email='student@test.edu').first()
        token = generate_reset_token(user.id)
        verified_id = verify_reset_token(token)
        assert verified_id == user.id
