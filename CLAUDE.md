# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -r requirements.txt
python app.py
```

App runs at `http://127.0.0.1:5000`. Set environment variables to change defaults:
- `HOST` (default `127.0.0.1`)
- `PORT` (default `5000`)
- `FLASK_DEBUG=1` to enable debug/reloader mode

Admin panel: `http://127.0.0.1:5000/admin/login` — default credentials `admin@platosplanet.local` / `admin123`.

## Architecture

Everything lives in a single file: `app.py`. It contains database schema, helper functions, auth decorators, and all Flask routes. There are no blueprints or separate modules.

**Database** (`data/database.db`) is SQLite, auto-created by `init_db()` on startup. Schema is defined inline in `init_db()`. The three thin DB helpers used throughout are `query_one`, `query_all`, and `execute`.

**Auth** uses two session-based decorators: `@login_required` (checks `session["user_id"]`) and `@admin_required` (checks `session["role"] == "admin"`). Students and admins have separate login routes (`/login` vs `/admin/login`). Passwords are SHA-256 hashed — suitable for local/dev use only.

**Cart** is stored entirely in the Flask session as a list of course IDs (`session["cart"]`). On checkout POST, orders and order_items rows are inserted and enrollments are created automatically.

**Enrollment & progress**: `enrollments` tracks per-student/per-course enrollment. `lesson_progress` tracks per-lesson completion. `update_progress()` recomputes `enrollments.progress_pct` after each lesson is marked complete.

**Seeding**: `seed_courses_from_csv()` reads `data/sample_courses.csv` and creates courses, 4 sample lessons, and a 3-question quiz per course. It is called automatically on the homepage if no courses exist, or manually via the admin "Seed Sample Courses" button (`POST /admin/seed`).

**Templates**: Jinja2 templates in `templates/` (student-facing) and `templates/admin/` (admin panel). `base.html` and `templates/admin/_layout.html` are the two layout bases. `_course_card.html` is a reusable partial. Global template variables (`cart_count`, `current_user`, `year`) are injected via `inject_globals()` context processor.

**Frontend**: `static/css/style.css` holds all custom styles. `static/js/main.js` handles the mobile nav toggle and auto-dismissing flash toasts only — no framework.

## Data model relationships

```
courses ──< lessons
courses ──< enrollments >── users
courses ──< quizzes ──< questions
courses ──< reviews >── users
quizzes ──< quiz_attempts >── users
lessons ──< lesson_progress >── users
orders ──< order_items >── courses
orders >── users
```
