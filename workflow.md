# Plato's Planet Workflow

1. Run `pip install -r requirements.txt`.
2. Start the app with `python app.py`.
3. Open `http://127.0.0.1:5000`.
4. Register a student account, add programs to the cart, complete enrollment checkout, then open the dashboard.
5. Use `/admin/login` with the default admin account to add courses, lessons, quizzes, and seed CSV data.

Admin flow:
- Login as admin.
- Seed sample courses if needed.
- Add or edit programs such as IGCSE, CBSE, Robotics, Brainobrain, Oratory, Languages, IELTS, SATs, NEET, and IIT-JEE.
- Open lessons from each course row and add lesson content.
- Use the quizzes page to create quizzes and questions.
- Review students and orders from the admin sidebar.

Student flow:
- Browse or filter the program catalog.
- Add programs to the cart.
- Complete checkout to enroll.
- Watch lessons, mark them complete, and take quizzes.
