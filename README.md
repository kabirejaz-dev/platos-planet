# Plato's Planet

[![GitHub repo](https://img.shields.io/badge/github-kabirejaz--dev%2Fplatos--planet-blue?logo=github)](https://github.com/kabirejaz-dev/platos-planet)
[![License](https://img.shields.io/badge/license-All%20Rights%20Reserved-red)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2%2B-black?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/sqlite-3-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Open in Claude Code](https://img.shields.io/badge/Claude%20Code-Onboarding-blueviolet?logo=anthropic)](https://claude.ai/claude-code/onboard/xH2e0peD0DQ8)

Plato's Planet is a full-stack education web app for a UAE education center, with academic programs, course browsing, enrollment checkout, lessons, quizzes, student dashboards, and an admin panel.

## Prerequisites

- Python 3.8+
- pip

## Setup

1. Download or open the `Plato's Planet` folder.
2. Install Flask:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the local server:

   ```bash
   python app.py
   ```

4. Open:

   ```text
   http://127.0.0.1:5000
   ```

SQLite creates `data/database.db` automatically on first run.

## Default Admin Login

- URL: `http://127.0.0.1:5000/admin/login`
- Email: `admin@platosplanet.local`
- Password: `admin123`

Change these credentials before using the app beyond local development.

## Add Courses

CSV option:
- Edit `data/sample_courses.csv`.
- Log in as admin.
- Click `Seed Sample Courses` from the admin dashboard or courses page.

Admin panel option:
- Log in at `/admin/login`.
- Open `Courses`.
- Fill in the add-course form.
- Add lessons from each course row.
- Add quizzes and questions from `Quizzes`.

## Folder Structure

```text
app.py                  Flask routes, database setup, auth, cart, checkout, admin
templates/              Jinja2 templates for student pages
templates/admin/        Jinja2 templates for admin pages
static/css/style.css    All custom styling
static/js/main.js       Menu and toast behavior
static/images/          Reserved for local course images
data/database.db        Auto-created SQLite database
data/sample_courses.csv CSV seed data
workflow.md             Common operating workflows
questions.md            Product questions and extension ideas
```

## Extend With AI Features

Good next additions:
- AI quiz generation from lesson notes.
- AI study plans based on progress and quiz results.
- AI summaries for each lesson.
- AI tutor chat per course.
- AI feedback on written reflections.

Keep AI features behind authenticated routes, save generated content to SQLite, and let admins review generated quizzes before students see them.
