import os
from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() in ('true', '1')

    print(f"\n==================================================================")
    print(f" UNIVERSITY LIBRARY MANAGEMENT SYSTEM (SDG 4 - QUALITY EDUCATION)")
    print(f"==================================================================")
    print(f" * Server running on: http://{host}:{port}/")
    print(f" * Admin login:       admin@univ.edu    / Admin@123")
    print(f" * Student login:     student1@univ.edu / Student@123")
    print(f"==================================================================\n")

    app.run(host=host, port=port, debug=debug)
