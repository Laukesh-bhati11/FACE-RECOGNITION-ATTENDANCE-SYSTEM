from flask import Flask, render_template, request, redirect, session, flash, url_for
import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime
import mysql.connector  # ✅ You missed this import earlier
from db_connection import get_db_connection

app = Flask(__name__)
app.secret_key = "secret123"

# -------------------------------
# CONFIGURATION
# -------------------------------
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# -------------------------------
# HOME PAGE
# -------------------------------
@app.route('/')
def home():
    return render_template('index.html')


# -------------------------------
# STUDENT SIGNUP
# -------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        email = request.form.get('email')
        password = request.form.get('password')
        image_file = request.files.get('face_image')

        if not image_file:
            flash("Please upload your face image!", "danger")
            return redirect(url_for('signup'))

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        image_file.save(image_path)

        img = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(img)
        if len(encodings) == 0:
            flash("No face detected! Please upload a clear face photo.", "danger")
            os.remove(image_path)
            return redirect(url_for('signup'))

        face_encoding = encodings[0].tobytes()

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO students (name, roll_no, email, password, face_encoding)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, roll_no, email, password, face_encoding))
        db.commit()
        cur.close()
        db.close()

        flash("Signup successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('signup.html')


# -------------------------------
# STUDENT LOGIN
# -------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cur = db.cursor(dictionary=True)

        # 1️⃣ First check if the user is a teacher
        cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
        teacher = cur.fetchone()

        if teacher:
            session['teacher_id'] = teacher['id']
            session['teacher_name'] = teacher['name']
            session['role'] = 'teacher'
            cur.close()
            db.close()
            flash("Welcome, Teacher!", "success")
            return redirect(url_for('teacher_dashboard'))

        # 2️⃣ If not a teacher, check student table
        cur.execute("SELECT * FROM students WHERE email=%s AND password=%s", (email, password))
        student = cur.fetchone()
        cur.close()
        db.close()

        if student:
            session['student_id'] = student['id']
            session['student_name'] = student['name']
            session['role'] = 'student'
            flash("Login successful!", "success")
            return redirect(url_for('student_dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))

    return render_template('student_login.html')


# -------------------------------
# STUDENT DASHBOARD
# -------------------------------
@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))
    return render_template('student_dashboard.html', name=session['student_name'])


# -------------------------------
# STUDENT DETAILS PAGE
# -------------------------------
@app.route('/know_details')
def my_details():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT name, roll_no, email FROM students WHERE id=%s", (session['student_id'],))
    student = cur.fetchone()
    cur.close()
    db.close()

    return render_template('student_details.html', student=student)


# -------------------------------
# SHOW ATTENDANCE
# -------------------------------
@app.route('/show_attendance')
def show_attendance():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("""
        SELECT date, time FROM attendance
        WHERE student_id=%s ORDER BY date DESC, time DESC
    """, (session['student_id'],))
    records = cur.fetchall()
    cur.close()
    db.close()

    return render_template('show_attendance.html', records=records)


# -------------------------------
# MARK ATTENDANCE
# -------------------------------
@app.route('/mark_attendance')
def mark_attendance():
    if 'student_id' not in session:
        return redirect(url_for('login'))

    student_id = session['student_id']
    student_name = session['student_name']

    db = get_db_connection()
    cur = db.cursor()
    cur.execute("SELECT face_encoding FROM students WHERE id=%s", (student_id,))
    data = cur.fetchone()
    cur.close()
    db.close()

    if not data or not data[0]:
        flash("No face data found for this student.", "danger")
        return redirect(url_for('student_dashboard'))

    known_encoding = np.frombuffer(data[0], dtype=np.float64)

    cam = cv2.VideoCapture(0)
    recognized = False

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locs = face_recognition.face_locations(rgb)
        face_encs = face_recognition.face_encodings(rgb, face_locs)

        for enc in face_encs:
            matches = face_recognition.compare_faces([known_encoding], enc)
            if matches[0]:
                recognized = True
                db = get_db_connection()
                cur = db.cursor()
                now = datetime.now()
                cur.execute("""
                    INSERT INTO attendance (student_id, date, time)
                    VALUES (%s, %s, %s)
                """, (student_id, now.date(), now.time()))
                db.commit()
                cur.close()
                db.close()
                flash("Attendance marked successfully!", "success")
                break

        cv2.imshow("Mark Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q') or recognized:
            break

    cam.release()
    cv2.destroyAllWindows()
    return redirect(url_for('show_attendance'))


# -------------------------------
# TEACHER SIGNUP
# -------------------------------
@app.route('/teacher_signup', methods=['GET', 'POST'])
def teacher_signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        subject = request.form['subject']

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO teachers (name, email, password, subject)
            VALUES (%s, %s, %s, %s)
        """, (name, email, password, subject))
        db.commit()
        cur.close()
        db.close()

        flash("Teacher registered successfully!", "success")
        return redirect(url_for('teacher_login'))
    return render_template('teacher_signup.html')


# -------------------------------
# TEACHER LOGIN
# -------------------------------
@app.route('/teacher_login', methods=['GET', 'POST'])
def teacher_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db_connection()
        cur = db.cursor(dictionary=True)
        cur.execute("SELECT * FROM teachers WHERE email=%s AND password=%s", (email, password))
        teacher = cur.fetchone()
        cur.close()
        db.close()

        if teacher:
            session['teacher_id'] = teacher['id']
            session['teacher_name'] = teacher['name']
            session['role'] = 'teacher'
            flash("Teacher login successful!", "success")
            return redirect(url_for('teacher_dashboard'))
        else:
            flash("Invalid credentials!", "danger")
    return render_template('teacher_login.html')


# -------------------------------
# TEACHER DASHBOARD
# -------------------------------
@app.route('/teacher_dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))
    return render_template('teacher_dashboard.html', name=session['teacher_name'])


# -------------------------------
# ADD NEW STUDENT (Teacher)
# -------------------------------
@app.route('/register_student', methods=['GET', 'POST'])
def add_student():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    if request.method == 'POST':
        name = request.form.get('name')
        roll_no = request.form.get('roll_no')
        email = request.form.get('email')
        password = request.form.get('password')

        db = get_db_connection()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO students (name, roll_no, email, password)
            VALUES (%s, %s, %s, %s)
        """, (name, roll_no, email, password))
        db.commit()
        cur.close()
        db.close()
        flash("Student added successfully!", "success")
        return redirect(url_for('teacher_dashboard'))

    return render_template('register_student.html')


# -------------------------------
# VIEW ALL STUDENTS (Teacher)
# -------------------------------
@app.route('/student')
def students_list():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_login'))

    db = get_db_connection()
    cur = db.cursor(dictionary=True)
    cur.execute("SELECT id, name, roll_no, email FROM students")
    students = cur.fetchall()
    cur.close()
    db.close()

    return render_template('know_details.html', students=students)


# -------------------------------
# LOGOUT
# -------------------------------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))


# -------------------------------
# RUN APP
# -------------------------------
if __name__ == '__main__':
    app.run(debug=True)
