import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from config import Config

# Extension instances initialized without app (Application Factory Pattern)
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()


def create_app(config_class=Config):
    """
    Application Factory constructing Flask app instances.
    Registers extensions, blueprints, error handlers, and template filters.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configure Flask-Login defaults
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'

    # Ensure upload directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # SQLite Foreign Key constraint enforcement
    if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            try:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
            except Exception:
                pass

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.member.routes import member_bp
    from app.books.routes import books_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(member_bp, url_prefix='/member')
    app.register_blueprint(books_bp, url_prefix='/books')

    # Register Global Template Filters and Context Processors
    @app.context_processor
    def inject_global_vars():
        return {
            'app_name': 'University Library Management System',
            'sdg_goal': 'SDG 4 - Quality Education',
            'fine_per_day': app.config.get('FINE_PER_DAY', 2.0),
            'max_borrow_limit': app.config.get('MAX_BORROW_LIMIT', 3)
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app
