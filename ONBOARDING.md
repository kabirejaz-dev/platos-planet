# Plato's Planet — Onboarding Guide

Plato's Planet is a full-stack education web app for a UAE education center. It covers course browsing, cart/checkout enrollment, lesson watching, quizzes, a student dashboard, and an admin panel — all in a single-file Flask app backed by SQLite.

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Architecture at a Glance

- **`app.py`** — the entire backend: DB schema, auth, routes, helpers. No blueprints.
- **`data/database.db`** — SQLite, auto-created on first run.
- **`templates/`** — student-facing Jinja2 pages; `templates/admin/` for the admin panel.
- **`static/css/style.css`** — all custom styles.
- **`static/js/main.js`** — mobile nav toggle and toast auto-dismiss only.

## Default Admin Login

- URL: `/admin/login`
- Email: `admin@platosplanet.local`
- Password: `admin123`

## Adding Content

**Via CSV:** Edit `data/sample_courses.csv`, log in as admin, click "Seed Sample Courses." Seeding also auto-creates 4 lessons and a 3-question quiz per course.

**Via admin panel:** Go to `Courses` to add/edit courses, open each course row to manage lessons, and use `Quizzes` to add quizzes and questions.

## Key Flows

**Student:** Register → browse catalog → add to cart → checkout → watch lessons → mark complete → take quiz → view dashboard.

**Admin:** Login → seed or add courses → manage lessons/quizzes → review students and orders.

## Data Model

```
courses ──< lessons
courses ──< enrollments >── users
courses ──< quizzes ──< questions
quizzes ──< quiz_attempts >── users
lessons ──< lesson_progress >── users
orders ──< order_items >── courses
```

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Server bind address |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `0` | Set to `1` for debug/reloader |
