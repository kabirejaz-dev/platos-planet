import csv
import hashlib
import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "database.db")
CSV_PATH = os.path.join(DATA_DIR, "sample_courses.csv")

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-for-production"


def hash_password(password):
    """Return a simple SHA-256 password hash for beginner-friendly local use."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_one(sql, params=()):
    return get_db().execute(sql, params).fetchone()


def query_all(sql, params=()):
    return get_db().execute(sql, params).fetchall()


def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required.", "danger")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals():
    cart = session.get("cart", [])
    current_user = None
    if session.get("user_id"):
        current_user = query_one("SELECT * FROM users WHERE id = ?", (session["user_id"],))
    return {
        "cart_count": len(cart),
        "current_user": current_user,
        "year": datetime.now().year,
    }


def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    schema = [
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            created_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            instructor TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            old_price REAL,
            image TEXT,
            level TEXT NOT NULL,
            duration_hrs REAL NOT NULL,
            rating REAL DEFAULT 0,
            total_students INTEGER DEFAULT 0,
            featured INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            video_url TEXT NOT NULL,
            duration_min INTEGER NOT NULL,
            order_num INTEGER NOT NULL,
            content_notes TEXT,
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )""",
        """CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            progress_pct INTEGER DEFAULT 0,
            enrolled_at TEXT NOT NULL,
            UNIQUE(user_id, course_id)
        )""",
        """CREATE TABLE IF NOT EXISTS lesson_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            completed INTEGER DEFAULT 0,
            watched_at TEXT,
            UNIQUE(user_id, lesson_id)
        )""",
        """CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            passing_score INTEGER NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            opt_a TEXT NOT NULL,
            opt_b TEXT NOT NULL,
            opt_c TEXT NOT NULL,
            opt_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quiz_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            passed INTEGER NOT NULL,
            taken_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            address TEXT NOT NULL,
            phone TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            price REAL NOT NULL
        )""",
        """CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""",
    ]
    for statement in schema:
        db.execute(statement)
    db.execute(
        """INSERT OR IGNORE INTO users (name, email, password, role, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        ("Admin", "admin@platosplanet.local", hash_password("admin123"), "admin", now()),
    )
    db.commit()
    db.close()


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def image_for(category):
    colors = {
        "IGCSE": "1B4332,D4A017",
        "CBSE": "0F766E,38BDF8",
        "Robotics": "1E3A8A,22C55E",
        "Brainobrain": "7C2D12,F59E0B",
        "Oratory": "9D174D,F9A8D4",
        "Languages": "312E81,A78BFA",
        "IELTS": "155E75,67E8F9",
        "SATs": "4C1D95,C4B5FD",
        "NEET & IIT-JEE": "064E3B,FBBF24",
    }
    return f"https://placehold.co/900x520/{colors.get(category, '1B4332,D4A017')}/FAF8F2?text={category}"


def seed_courses_from_csv():
    created = 0
    if not os.path.exists(CSV_PATH):
        return 0
    with open(CSV_PATH, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            existing = query_one("SELECT id FROM courses WHERE title = ?", (row["title"],))
            if existing:
                continue
            cur = execute(
                """INSERT INTO courses
                   (title, description, instructor, category, price, old_price, image, level,
                    duration_hrs, rating, total_students, featured, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["title"],
                    row["description"],
                    row["instructor"],
                    row["category"],
                    float(row["price"]),
                    float(row["old_price"] or 0),
                    image_for(row["category"]),
                    row["level"],
                    float(row["duration_hrs"]),
                    float(row["rating"]),
                    120 + created * 31,
                    int(row["featured"]),
                    now(),
                ),
            )
            course_id = cur.lastrowid
            create_sample_lessons_and_quiz(course_id, row["title"], row["category"])
            created += 1
    return created


def create_sample_lessons_and_quiz(course_id, course_title, category):
    lessons = [
        ("Foundations and Big Questions", 18, "Opening notes, learning goals, and historical context."),
        ("Core Concepts in Practice", 26, "Worked examples, guided reflection, and key vocabulary."),
        ("Applied Studio", 31, "A practical walkthrough that connects the ideas to real decisions."),
        ("Capstone Review", 22, "Summary prompts and next steps for independent study."),
    ]
    for index, (title, duration, notes) in enumerate(lessons, start=1):
        execute(
            """INSERT INTO lessons (course_id, title, video_url, duration_min, order_num, content_notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                course_id,
                f"{index}. {title}",
                "https://www.youtube.com/embed/8hly31xKli0",
                duration,
                index,
                f"{notes}\n\nFor {course_title}, complete the practice prompts and review your progress with a parent or counsellor.",
            ),
        )
    quiz_id = execute(
        "INSERT INTO quizzes (course_id, title, passing_score) VALUES (?, ?, ?)",
        (course_id, f"{course_title} Mastery Check", 70),
    ).lastrowid
    questions = [
        ("What is the best first habit for this course?", "Skip practice", "Ask precise questions", "Avoid notes", "Guess quickly", "B"),
        (f"Which field best describes this course?", category, "Cooking", "Sports", "Finance", "A"),
        ("A strong learner should connect lessons to what?", "Daily practice", "Random guesses", "Silence", "Only marks", "A"),
    ]
    for q in questions:
        execute(
            """INSERT INTO questions
               (quiz_id, question_text, opt_a, opt_b, opt_c, opt_d, correct_answer)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (quiz_id, *q),
        )


def is_enrolled(user_id, course_id):
    return bool(query_one("SELECT id FROM enrollments WHERE user_id = ? AND course_id = ?", (user_id, course_id)))


def update_progress(user_id, course_id):
    total = query_one("SELECT COUNT(*) AS count FROM lessons WHERE course_id = ?", (course_id,))["count"]
    if total == 0:
        progress = 0
    else:
        done = query_one(
            """SELECT COUNT(*) AS count FROM lesson_progress lp
               JOIN lessons l ON l.id = lp.lesson_id
               WHERE lp.user_id = ? AND l.course_id = ? AND lp.completed = 1""",
            (user_id, course_id),
        )["count"]
        progress = int((done / total) * 100)
    execute("UPDATE enrollments SET progress_pct = ? WHERE user_id = ? AND course_id = ?", (progress, user_id, course_id))


@app.route("/")
def index():
    if query_one("SELECT COUNT(*) AS count FROM courses")["count"] == 0:
        seed_courses_from_csv()
    featured = query_all("SELECT * FROM courses WHERE featured = 1 ORDER BY rating DESC LIMIT 6")
    categories = query_all("SELECT category, COUNT(*) AS count FROM courses GROUP BY category ORDER BY category")
    return render_template("index.html", featured=featured, categories=categories)


@app.route("/courses")
def courses():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "All")
    level = request.args.get("level", "All")
    sort = request.args.get("sort", "featured")
    sql = "SELECT * FROM courses WHERE 1 = 1"
    params = []
    if q:
        sql += " AND (title LIKE ? OR description LIKE ? OR instructor LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if cat and cat != "All":
        sql += " AND category = ?"
        params.append(cat)
    if level and level != "All":
        sql += " AND level = ?"
        params.append(level)
    order_by = {
        "price_asc": "price ASC",
        "price_desc": "price DESC",
        "rating": "rating DESC",
    }.get(sort, "featured DESC, rating DESC")
    rows = query_all(f"{sql} ORDER BY {order_by}", params)
    categories = ["All", "IGCSE", "CBSE", "Robotics", "Brainobrain", "Oratory", "Languages", "IELTS", "SATs", "NEET & IIT-JEE"]
    return render_template("courses.html", courses=rows, q=q, cat=cat, level=level, sort=sort, categories=categories)


@app.route("/course/<int:id>")
def course_detail(id):
    course = query_one("SELECT * FROM courses WHERE id = ?", (id,))
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))
    lessons = query_all("SELECT * FROM lessons WHERE course_id = ? ORDER BY order_num", (id,))
    reviews = query_all(
        """SELECT r.*, u.name FROM reviews r JOIN users u ON u.id = r.user_id
           WHERE r.course_id = ? ORDER BY r.created_at DESC""",
        (id,),
    )
    related = query_all("SELECT * FROM courses WHERE category = ? AND id != ? LIMIT 3", (course["category"], id))
    enrolled = session.get("user_id") and is_enrolled(session["user_id"], id)
    quiz = query_one("SELECT * FROM quizzes WHERE course_id = ? LIMIT 1", (id,))
    return render_template("course_detail.html", course=course, lessons=lessons, reviews=reviews, related=related, enrolled=enrolled, quiz=quiz)


@app.route("/lesson/<int:id>")
@login_required
def lesson(id):
    lesson_row = query_one("SELECT l.*, c.title AS course_title, c.id AS course_id FROM lessons l JOIN courses c ON c.id = l.course_id WHERE l.id = ?", (id,))
    if not lesson_row or not is_enrolled(session["user_id"], lesson_row["course_id"]):
        flash("Enroll in the course to unlock lessons.", "warning")
        return redirect(url_for("course_detail", id=lesson_row["course_id"] if lesson_row else 1))
    prev_lesson = query_one("SELECT * FROM lessons WHERE course_id = ? AND order_num < ? ORDER BY order_num DESC LIMIT 1", (lesson_row["course_id"], lesson_row["order_num"]))
    next_lesson = query_one("SELECT * FROM lessons WHERE course_id = ? AND order_num > ? ORDER BY order_num ASC LIMIT 1", (lesson_row["course_id"], lesson_row["order_num"]))
    completed = query_one("SELECT * FROM lesson_progress WHERE user_id = ? AND lesson_id = ? AND completed = 1", (session["user_id"], id))
    return render_template("lesson.html", lesson=lesson_row, prev_lesson=prev_lesson, next_lesson=next_lesson, completed=completed)


@app.route("/lesson/<int:id>/complete", methods=["POST"])
@login_required
def complete_lesson(id):
    lesson_row = query_one("SELECT * FROM lessons WHERE id = ?", (id,))
    if not lesson_row:
        flash("Lesson not found.", "danger")
        return redirect(url_for("dashboard"))
    execute(
        """INSERT INTO lesson_progress (user_id, lesson_id, completed, watched_at)
           VALUES (?, ?, 1, ?)
           ON CONFLICT(user_id, lesson_id) DO UPDATE SET completed = 1, watched_at = excluded.watched_at""",
        (session["user_id"], id, now()),
    )
    update_progress(session["user_id"], lesson_row["course_id"])
    flash("Lesson marked complete.", "success")
    return redirect(url_for("lesson", id=id))


@app.route("/quiz/<int:id>")
@login_required
def quiz(id):
    quiz_row = query_one("SELECT q.*, c.title AS course_title FROM quizzes q JOIN courses c ON c.id = q.course_id WHERE q.id = ?", (id,))
    if not quiz_row or not is_enrolled(session["user_id"], quiz_row["course_id"]):
        flash("Enroll in the course to take the quiz.", "warning")
        return redirect(url_for("courses"))
    questions = query_all("SELECT * FROM questions WHERE quiz_id = ?", (id,))
    return render_template("quiz.html", quiz=quiz_row, questions=questions)


@app.route("/quiz/<int:id>/submit", methods=["POST"])
@login_required
def submit_quiz(id):
    quiz_row = query_one("SELECT * FROM quizzes WHERE id = ?", (id,))
    questions = query_all("SELECT * FROM questions WHERE quiz_id = ?", (id,))
    correct = 0
    review = []
    for question in questions:
        answer = request.form.get(f"q{question['id']}")
        ok = answer == question["correct_answer"]
        correct += 1 if ok else 0
        review.append({"question": question, "answer": answer, "ok": ok})
    score = int((correct / len(questions)) * 100) if questions else 0
    passed = score >= quiz_row["passing_score"]
    execute(
        "INSERT INTO quiz_attempts (user_id, quiz_id, score, passed, taken_at) VALUES (?, ?, ?, ?, ?)",
        (session["user_id"], id, score, int(passed), now()),
    )
    return render_template("quiz_result.html", quiz=quiz_row, score=score, passed=passed, review=review)


@app.route("/cart")
def cart():
    ids = session.get("cart", [])
    items = []
    total = 0
    if ids:
        placeholders = ",".join("?" for _ in ids)
        items = query_all(f"SELECT * FROM courses WHERE id IN ({placeholders})", ids)
        total = sum(item["price"] for item in items)
    return render_template("cart.html", items=items, total=total)


@app.route("/cart/add/<int:id>", methods=["POST"])
def add_to_cart(id):
    course = query_one("SELECT * FROM courses WHERE id = ?", (id,))
    if not course:
        flash("Course not found.", "danger")
        return redirect(url_for("courses"))
    cart_items = session.get("cart", [])
    if id not in cart_items:
        cart_items.append(id)
        session["cart"] = cart_items
        flash("Course added to cart.", "success")
    else:
        flash("That course is already in your cart.", "info")
    return redirect(request.referrer or url_for("cart"))


@app.route("/cart/remove/<int:id>", methods=["POST"])
def remove_from_cart(id):
    session["cart"] = [course_id for course_id in session.get("cart", []) if course_id != id]
    flash("Course removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    ids = session.get("cart", [])
    if not ids:
        flash("Your cart is empty.", "warning")
        return redirect(url_for("courses"))
    placeholders = ",".join("?" for _ in ids)
    items = query_all(f"SELECT * FROM courses WHERE id IN ({placeholders})", ids)
    total = sum(item["price"] for item in items)
    if request.method == "POST":
        order_id = execute(
            """INSERT INTO orders (user_id, total, status, name, email, address, phone, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session["user_id"],
                total,
                "Paid",
                request.form["name"],
                request.form["email"],
                request.form["address"],
                request.form["phone"],
                now(),
            ),
        ).lastrowid
        for item in items:
            execute("INSERT INTO order_items (order_id, course_id, price) VALUES (?, ?, ?)", (order_id, item["id"], item["price"]))
            execute(
                """INSERT OR IGNORE INTO enrollments (user_id, course_id, progress_pct, enrolled_at)
                   VALUES (?, ?, 0, ?)""",
                (session["user_id"], item["id"], now()),
            )
            execute("UPDATE courses SET total_students = total_students + 1 WHERE id = ?", (item["id"],))
        session["cart"] = []
        flash("Order placed. Your courses are now in your dashboard.", "success")
        return redirect(url_for("dashboard"))
    return render_template("checkout.html", items=items, total=total)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = query_one("SELECT * FROM users WHERE email = ? AND role = 'student'", (request.form["email"].lower(),))
        if user and user["password"] == hash_password(request.form["password"]):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("Welcome back.", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Invalid student credentials.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            user_id = execute(
                "INSERT INTO users (name, email, password, role, created_at) VALUES (?, ?, ?, 'student', ?)",
                (request.form["name"], request.form["email"].lower(), hash_password(request.form["password"]), now()),
            ).lastrowid
            session.clear()
            session["user_id"] = user_id
            session["role"] = "student"
            flash("Your account is ready.", "success")
            return redirect(url_for("dashboard"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    enrollments = query_all(
        """SELECT e.*, c.title, c.image, c.category, c.duration_hrs
           FROM enrollments e JOIN courses c ON c.id = e.course_id
           WHERE e.user_id = ? ORDER BY e.enrolled_at DESC""",
        (session["user_id"],),
    )
    attempts = query_all(
        """SELECT qa.*, q.title, c.title AS course_title
           FROM quiz_attempts qa
           JOIN quizzes q ON q.id = qa.quiz_id
           JOIN courses c ON c.id = q.course_id
           WHERE qa.user_id = ? ORDER BY qa.taken_at DESC""",
        (session["user_id"],),
    )
    orders = query_all("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (session["user_id"],))
    return render_template("dashboard.html", enrollments=enrollments, attempts=attempts, orders=orders)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        user = query_one("SELECT * FROM users WHERE email = ? AND role = 'admin'", (request.form["email"].lower(),))
        if user and user["password"] == hash_password(request.form["password"]):
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = "admin"
            flash("Admin session started.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid admin credentials.", "danger")
    return render_template("admin/login.html")


@app.route("/admin/")
@admin_required
def admin_dashboard():
    stats = {
        "students": query_one("SELECT COUNT(*) AS count FROM users WHERE role = 'student'")["count"],
        "courses": query_one("SELECT COUNT(*) AS count FROM courses")["count"],
        "revenue": query_one("SELECT COALESCE(SUM(total), 0) AS total FROM orders WHERE status = 'Paid'")["total"],
    }
    orders = query_all("SELECT * FROM orders ORDER BY created_at DESC LIMIT 6")
    return render_template("admin/dashboard.html", stats=stats, orders=orders)


@app.route("/admin/courses")
@admin_required
def admin_courses():
    rows = query_all("SELECT * FROM courses ORDER BY created_at DESC")
    return render_template("admin/courses.html", courses=rows)


@app.route("/admin/courses/add", methods=["POST"])
@admin_required
def admin_add_course():
    execute(
        """INSERT INTO courses
           (title, description, instructor, category, price, old_price, image, level, duration_hrs,
            rating, total_students, featured, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (
            request.form["title"],
            request.form["description"],
            request.form["instructor"],
            request.form["category"],
            float(request.form["price"]),
            float(request.form.get("old_price") or 0),
            request.form.get("image") or image_for(request.form["category"]),
            request.form["level"],
            float(request.form["duration_hrs"]),
            float(request.form.get("rating") or 4.7),
            1 if request.form.get("featured") else 0,
            now(),
        ),
    )
    flash("Course added.", "success")
    return redirect(url_for("admin_courses"))


@app.route("/admin/courses/edit/<int:id>", methods=["POST"])
@admin_required
def admin_edit_course(id):
    execute(
        """UPDATE courses SET title=?, description=?, instructor=?, category=?, price=?, old_price=?,
           image=?, level=?, duration_hrs=?, rating=?, featured=? WHERE id=?""",
        (
            request.form["title"],
            request.form["description"],
            request.form["instructor"],
            request.form["category"],
            float(request.form["price"]),
            float(request.form.get("old_price") or 0),
            request.form.get("image") or image_for(request.form["category"]),
            request.form["level"],
            float(request.form["duration_hrs"]),
            float(request.form.get("rating") or 4.7),
            1 if request.form.get("featured") else 0,
            id,
        ),
    )
    flash("Course updated.", "success")
    return redirect(url_for("admin_courses"))


@app.route("/admin/courses/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_course(id):
    execute("DELETE FROM courses WHERE id = ?", (id,))
    flash("Course deleted.", "info")
    return redirect(url_for("admin_courses"))


@app.route("/admin/lessons/<int:course_id>")
@admin_required
def admin_lessons(course_id):
    course = query_one("SELECT * FROM courses WHERE id = ?", (course_id,))
    lessons = query_all("SELECT * FROM lessons WHERE course_id = ? ORDER BY order_num", (course_id,))
    return render_template("admin/lessons.html", course=course, lessons=lessons)


@app.route("/admin/lessons/add", methods=["POST"])
@admin_required
def admin_add_lesson():
    execute(
        """INSERT INTO lessons (course_id, title, video_url, duration_min, order_num, content_notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            int(request.form["course_id"]),
            request.form["title"],
            request.form["video_url"],
            int(request.form["duration_min"]),
            int(request.form["order_num"]),
            request.form["content_notes"],
        ),
    )
    flash("Lesson added.", "success")
    return redirect(url_for("admin_lessons", course_id=request.form["course_id"]))


@app.route("/admin/lessons/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_lesson(id):
    lesson_row = query_one("SELECT * FROM lessons WHERE id = ?", (id,))
    execute("DELETE FROM lessons WHERE id = ?", (id,))
    flash("Lesson deleted.", "info")
    return redirect(url_for("admin_lessons", course_id=lesson_row["course_id"]))


@app.route("/admin/students")
@admin_required
def admin_students():
    students = query_all(
        """SELECT u.*, COUNT(e.id) AS enrollment_count
           FROM users u LEFT JOIN enrollments e ON e.user_id = u.id
           WHERE u.role = 'student'
           GROUP BY u.id ORDER BY u.created_at DESC"""
    )
    return render_template("admin/students.html", students=students)


@app.route("/admin/orders")
@admin_required
def admin_orders():
    orders = query_all("SELECT * FROM orders ORDER BY created_at DESC")
    return render_template("admin/orders.html", orders=orders)


@app.route("/admin/quizzes", methods=["GET", "POST"])
@admin_required
def admin_quizzes():
    if request.method == "POST":
        quiz_id = request.form.get("quiz_id")
        if request.form.get("action") == "quiz":
            execute(
                "INSERT INTO quizzes (course_id, title, passing_score) VALUES (?, ?, ?)",
                (int(request.form["course_id"]), request.form["title"], int(request.form["passing_score"])),
            )
            flash("Quiz added.", "success")
        elif quiz_id:
            execute(
                """INSERT INTO questions
                   (quiz_id, question_text, opt_a, opt_b, opt_c, opt_d, correct_answer)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    int(quiz_id),
                    request.form["question_text"],
                    request.form["opt_a"],
                    request.form["opt_b"],
                    request.form["opt_c"],
                    request.form["opt_d"],
                    request.form["correct_answer"],
                ),
            )
            flash("Question added.", "success")
        return redirect(url_for("admin_quizzes"))
    courses_rows = query_all("SELECT id, title FROM courses ORDER BY title")
    quizzes = query_all(
        """SELECT q.*, c.title AS course_title,
           (SELECT COUNT(*) FROM questions WHERE quiz_id = q.id) AS question_count
           FROM quizzes q JOIN courses c ON c.id = q.course_id ORDER BY q.id DESC"""
    )
    return render_template("admin/quizzes.html", courses=courses_rows, quizzes=quizzes)


@app.route("/admin/seed", methods=["POST"])
@admin_required
def admin_seed():
    created = seed_courses_from_csv()
    flash(f"Seed complete. Added {created} new courses.", "success")
    return redirect(url_for("admin_courses"))


if __name__ == "__main__":
    init_db()
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug, use_reloader=False)
