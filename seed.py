"""
University Library Management System (SDG 4 - Quality Education)
Comprehensive Database Seeding Script.

Seeds:
- 1 Admin / Librarian account
- 10 Student / Member accounts
- 8 Academic Categories
- 32 Curated Textbooks and Academic Books
- Real-world Transactions (Active, Overdue with fines, and Returned)
- Book Reservations in waiting list
- System Audit Activity Logs
"""

from datetime import date, timedelta, datetime
from app import create_app, db
from app.models import User, Category, Book, Transaction, Reservation, ActivityLog


def seed_database():
    app = create_app()
    with app.app_context():
        print("[INFO] Creating database schema tables...")
        db.create_all()

        # Check if database already has data
        if User.query.filter_by(role='admin').first():
            print("[INFO] Admin user already exists. Database already seeded.")
            return

        print("[INFO] Seeding Categories...")
        categories_data = [
            "Computer Science & IT",
            "Data Science & AI",
            "Mathematics & Statistics",
            "Physics & Astronomy",
            "Chemistry & Materials Science",
            "Environmental Science & Sustainability",
            "Economics & Management",
            "Literature & Philosophy"
        ]
        category_objects = {}
        for cat_name in categories_data:
            cat = Category(name=cat_name)
            db.session.add(cat)
            category_objects[cat_name] = cat
        db.session.commit()

        print("[INFO] Seeding Administrator Account...")
        admin = User(
            name="Dr. Sarah Mitchell",
            email="admin@univ.edu",
            student_id=None,
            role="admin",
            status="active"
        )
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()

        print("[INFO] Seeding 10 Student Member Accounts...")
        members_data = [
            ("Alex Johnson", "student1@univ.edu", "STU-2026-001"),
            ("Priya Sharma", "student2@univ.edu", "STU-2026-002"),
            ("David Chen", "student3@univ.edu", "STU-2026-003"),
            ("Fatima Al-Mansoor", "student4@univ.edu", "STU-2026-004"),
            ("Rahul Verma", "student5@univ.edu", "STU-2026-005"),
            ("Elena Rostova", "student6@univ.edu", "STU-2026-006"),
            ("Michael Chang", "student7@univ.edu", "STU-2026-007"),
            ("Amina Yusuf", "student8@univ.edu", "STU-2026-008"),
            ("Lucas Silva", "student9@univ.edu", "STU-2026-009"),
            ("Ananya Patel", "student10@univ.edu", "STU-2026-010"),
        ]
        student_users = []
        for name, email, stu_id in members_data:
            stu = User(
                name=name,
                email=email,
                student_id=stu_id,
                role="member",
                status="active"
            )
            stu.set_password("Student@123")
            db.session.add(stu)
            student_users.append(stu)
        db.session.commit()

        print("[INFO] Seeding 32 Books across Categories...")
        books_data = [
            # Computer Science & IT
            ("Introduction to Algorithms", "Thomas H. Cormen, Charles E. Leiserson", "Computer Science & IT", "978-0262033848", 5, 4),
            ("Clean Code: A Handbook of Agile Software Craftsmanship", "Robert C. Martin", "Computer Science & IT", "978-0132350884", 4, 3),
            ("Designing Data-Intensive Applications", "Martin Kleppmann", "Computer Science & IT", "978-1449373320", 3, 2),
            ("Computer Networking: A Top-Down Approach", "James Kurose, Keith Ross", "Computer Science & IT", "978-0133594140", 4, 4),
            ("Operating System Concepts", "Abraham Silberschatz, Peter B. Galvin", "Computer Science & IT", "978-1118063330", 4, 3),
            
            # Data Science & AI
            ("Deep Learning", "Ian Goodfellow, Yoshua Bengio, Aaron Courville", "Data Science & AI", "978-0262035613", 4, 3),
            ("Pattern Recognition and Machine Learning", "Christopher M. Bishop", "Data Science & AI", "978-0387310732", 3, 2),
            ("Hands-On Machine Learning with Scikit-Learn and TensorFlow", "Aurélien Géron", "Data Science & AI", "978-1492032649", 5, 4),
            ("Python for Data Analysis", "Wes McKinney", "Data Science & AI", "978-1491957660", 4, 3),
            ("Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig", "Data Science & AI", "978-0136042594", 4, 2),

            # Mathematics & Statistics
            ("Linear Algebra and Its Applications", "Gilbert Strang", "Mathematics & Statistics", "978-0030105678", 5, 5),
            ("Calculus: Early Transcendentals", "James Stewart", "Mathematics & Statistics", "978-1285741550", 6, 5),
            ("All of Statistics: A Concise Course in Statistical Inference", "Larry Wasserman", "Mathematics & Statistics", "978-0387402727", 3, 2),
            ("Discrete Mathematics and Its Applications", "Kenneth H. Rosen", "Mathematics & Statistics", "978-0073383095", 4, 4),

            # Physics & Astronomy
            ("University Physics with Modern Physics", "Hugh D. Young, Roger A. Freedman", "Physics & Astronomy", "978-0133978049", 4, 3),
            ("The Feynman Lectures on Physics", "Richard P. Feynman", "Physics & Astronomy", "978-0465023820", 3, 2),
            ("Introduction to Electrodynamics", "David J. Griffiths", "Physics & Astronomy", "978-1108420419", 4, 4),
            ("Astrophysics for People in a Hurry", "Neil deGrasse Tyson", "Physics & Astronomy", "978-0393609394", 5, 5),

            # Chemistry & Materials Science
            ("Organic Chemistry", "Paula Yurkanis Bruice", "Chemistry & Materials Science", "978-0134042282", 4, 4),
            ("Physical Chemistry", "Peter Atkins, Julio de Paula", "Chemistry & Materials Science", "978-0199543373", 3, 3),
            ("Materials Science and Engineering: An Introduction", "William D. Callister", "Chemistry & Materials Science", "978-1118324578", 4, 3),
            ("Inorganic Chemistry", "Gary L. Miessler, Paul J. Fischer", "Chemistry & Materials Science", "978-0321811059", 3, 3),

            # Environmental Science & Sustainability (SDG 4 & SDG 13)
            ("Silent Spring", "Rachel Carson", "Environmental Science & Sustainability", "978-0618249060", 4, 3),
            ("Sustainability: A Comprehensive Foundation", "Tom Theis, Jonathan Tomkin", "Environmental Science & Sustainability", "978-1934332535", 4, 4),
            ("Drawdown: The Most Comprehensive Plan to Reverse Global Warming", "Paul Hawken", "Environmental Science & Sustainability", "978-0143130444", 5, 4),
            ("Renewable Energy: Physics, Engineering, Environmental Impacts", "Bent Sorensen", "Environmental Science & Sustainability", "978-0128045671", 3, 2),

            # Economics & Management
            ("Principles of Economics", "N. Gregory Mankiw", "Economics & Management", "978-1305585126", 5, 4),
            ("Thinking, Fast and Slow", "Daniel Kahneman", "Economics & Management", "978-0374533557", 6, 5),
            ("Good Strategy Bad Strategy", "Richard Rumelt", "Economics & Management", "978-0307886231", 3, 3),
            ("Zero to One: Notes on Startups", "Peter Thiel", "Economics & Management", "978-0804139298", 4, 3),

            # Literature & Philosophy
            ("Meditations", "Marcus Aurelius", "Literature & Philosophy", "978-0140449334", 4, 4),
            ("Justice: What's the Right Thing to Do?", "Michael J. Sandel", "Literature & Philosophy", "978-0374532505", 4, 3)
        ]

        book_objects = []
        for title, author, cat_name, isbn, total, avail in books_data:
            book = Book(
                title=title,
                author=author,
                category=category_objects[cat_name],
                isbn=isbn,
                total_copies=total,
                available_copies=avail
            )
            db.session.add(book)
            book_objects.append(book)
        db.session.commit()

        print("[INFO] Seeding Sample Transactions (Active, Overdue, Returned)...")
        today = date.today()

        # 1. On-time active loans (Student 1 & Student 2)
        tx1 = Transaction(
            user=student_users[0],
            book=book_objects[0],  # Introduction to Algorithms
            issue_date=today - timedelta(days=5),
            due_date=today + timedelta(days=9),
            status="issued",
            fine_amount=0.0
        )
        tx2 = Transaction(
            user=student_users[1],
            book=book_objects[1],  # Clean Code
            issue_date=today - timedelta(days=3),
            due_date=today + timedelta(days=11),
            status="issued",
            fine_amount=0.0
        )

        # 2. Overdue loan with late fines accrued (Student 1 has an overdue book: 5 days late @ Rs 2/day = Rs. 10)
        tx_overdue = Transaction(
            user=student_users[0],
            book=book_objects[2],  # Designing Data-Intensive Applications
            issue_date=today - timedelta(days=19),
            due_date=today - timedelta(days=5),  # Due 5 days ago
            status="overdue",
            fine_amount=0.0
        )

        # 3. Another overdue loan (Student 3)
        tx_overdue2 = Transaction(
            user=student_users[2],
            book=book_objects[5],  # Deep Learning
            issue_date=today - timedelta(days=22),
            due_date=today - timedelta(days=8),  # Due 8 days ago
            status="overdue",
            fine_amount=0.0
        )

        # 4. Returned loans with past fine settled
        tx_returned1 = Transaction(
            user=student_users[1],
            book=book_objects[6],
            issue_date=today - timedelta(days=30),
            due_date=today - timedelta(days=16),
            return_date=today - timedelta(days=14),  # Returned 2 days late
            status="returned",
            fine_amount=4.0  # 2 days late * Rs. 2.0 = Rs. 4.0
        )

        # 5. Returned loan on time (fine = 0.0)
        tx_returned2 = Transaction(
            user=student_users[3],
            book=book_objects[7],
            issue_date=today - timedelta(days=25),
            due_date=today - timedelta(days=11),
            return_date=today - timedelta(days=12),
            status="returned",
            fine_amount=0.0
        )

        # 6. More historical transactions for monthly charts
        for i in range(1, 5):
            past_date = today - timedelta(days=30 * i)
            tx_hist = Transaction(
                user=student_users[i % len(student_users)],
                book=book_objects[8 + i],
                issue_date=past_date,
                due_date=past_date + timedelta(days=14),
                return_date=past_date + timedelta(days=13),
                status="returned",
                fine_amount=0.0
            )
            db.session.add(tx_hist)

        db.session.add_all([tx1, tx2, tx_overdue, tx_overdue2, tx_returned1, tx_returned2])
        db.session.commit()

        print("[INFO] Seeding Reservations...")
        # Make one book 0 copies to test reservation queue
        book_objects[9].available_copies = 0  # Artificial Intelligence
        res1 = Reservation(
            user=student_users[4],
            book=book_objects[9],
            status="pending",
            created_at=datetime.utcnow() - timedelta(days=2)
        )
        res2 = Reservation(
            user=student_users[5],
            book=book_objects[9],
            status="pending",
            created_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add_all([res1, res2])
        db.session.commit()

        print("[INFO] Seeding Audit Logs...")
        audit_entries = [
            (admin.id, "System initialized with SDG 4 Community Library base catalog"),
            (admin.id, f"Added 32 academic textbook titles to University Catalog"),
            (admin.id, f"Issued book 'Introduction to Algorithms' to student Alex Johnson"),
            (admin.id, f"Issued book 'Clean Code' to student Priya Sharma"),
            (admin.id, f"Processed return of 'Pattern Recognition' from Priya Sharma. Fine collected: Rs. 4.00"),
            (student_users[4].id, f"Member Rahul Verma placed a reservation request on 'Artificial Intelligence'"),
        ]
        for user_id, action in audit_entries:
            log = ActivityLog(user_id=user_id, action=action, timestamp=datetime.utcnow() - timedelta(hours=1))
            db.session.add(log)
        db.session.commit()

        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("Default Librarian / Admin Credentials:")
        print("  Email:    admin@univ.edu")
        print("  Password: Admin@123")
        print("\nDefault Student / Member Credentials:")
        print("  Email:    student1@univ.edu  (or student2@univ.edu ... student10@univ.edu)")
        print("  Password: Student@123")
        print("="*60 + "\n")


if __name__ == '__main__':
    seed_database()
