import os
from app import create_app, db

app = create_app()

# Create database tables when the application starts
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() in ('true', '1')

    print("UNIVERSITY LIBRARY MANAGEMENT SYSTEM")
    print(f"Server running on: http://{host}:{port}/")

    app.run(host=host, port=port, debug=debug)