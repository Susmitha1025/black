from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

DB_FILE = 'student_management.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_FILE):
        conn = get_db_connection()
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                gender TEXT,
                dob DATE,
                phone TEXT,
                email TEXT,
                address TEXT,
                password TEXT DEFAULT 'student123'
            );
            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT,
                duration TEXT
            );
            CREATE TABLE IF NOT EXISTS faculty (
                faculty_id INTEGER PRIMARY KEY AUTOINCREMENT,
                faculty_name TEXT,
                subject TEXT,
                password TEXT DEFAULT 'faculty123'
            );
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                attendance_date DATE,
                status TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            );
            CREATE TABLE IF NOT EXISTS marks (
                mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                subject TEXT,
                marks INTEGER,
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            );
            CREATE TABLE IF NOT EXISTS fees (
                fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                amount DECIMAL(10,2),
                payment_date DATE,
                status TEXT,
                FOREIGN KEY(student_id) REFERENCES students(student_id)
            );
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                password TEXT
            );
            INSERT INTO admins (username, password) VALUES ('admin', 'admin123');
            INSERT INTO students (name, gender, dob, phone, email, address, password) VALUES ('Akhil', 'Male', '2004-08-15', '9876543210', 'akhil@gmail.com', 'Hyderabad', 'student123');
            INSERT INTO faculty (faculty_name, subject, password) VALUES ('Dr. Smith', 'Database Systems', 'faculty123');
        ''')
        conn.commit()
        conn.close()

init_db()

@app.route('/')
def index():
    if 'user_type' in session:
        if session['user_type'] == 'admin': return redirect(url_for('admin_dashboard'))
        elif session['user_type'] == 'student': return redirect(url_for('student_dashboard'))
        elif session['user_type'] == 'faculty': return redirect(url_for('faculty_dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_type = request.form.get('user_type')
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db_connection()
    user = None

    if user_type == 'admin':
        user = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_type'] = 'admin'
            session['user_id'] = user['admin_id']
            session['name'] = 'Admin'
    elif user_type == 'student':
        user = conn.execute('SELECT * FROM students WHERE email = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_type'] = 'student'
            session['user_id'] = user['student_id']
            session['name'] = user['name']
    elif user_type == 'faculty':
        user = conn.execute('SELECT * FROM faculty WHERE faculty_name = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_type'] = 'faculty'
            session['user_id'] = user['faculty_id']
            session['name'] = user['faculty_name']

    conn.close()

    if user:
        return redirect(url_for('index'))
    else:
        flash('Invalid credentials, please try again.')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if session.get('user_type') != 'admin': return redirect(url_for('index'))
    conn = get_db_connection()
    students = conn.execute('SELECT * FROM students').fetchall()
    faculty = conn.execute('SELECT * FROM faculty').fetchall()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('admin_dashboard.html', students=students, faculty=faculty, courses=courses)

@app.route('/student')
def student_dashboard():
    if session.get('user_type') != 'student': return redirect(url_for('index'))
    conn = get_db_connection()
    student = conn.execute('SELECT * FROM students WHERE student_id = ?', (session['user_id'],)).fetchone()
    attendance = conn.execute('SELECT * FROM attendance WHERE student_id = ?', (session['user_id'],)).fetchall()
    marks = conn.execute('SELECT * FROM marks WHERE student_id = ?', (session['user_id'],)).fetchall()
    fees = conn.execute('SELECT * FROM fees WHERE student_id = ?', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('student_dashboard.html', student=student, attendance=attendance, marks=marks, fees=fees)

@app.route('/faculty')
def faculty_dashboard():
    if session.get('user_type') != 'faculty': return redirect(url_for('index'))
    conn = get_db_connection()
    students = conn.execute('SELECT student_id, name FROM students').fetchall()
    conn.close()
    return render_template('faculty_dashboard.html', students=students)

@app.route('/add_student', methods=['POST'])
def add_student():
    if session.get('user_type') != 'admin': return redirect(url_for('index'))
    name = request.form['name']
    gender = request.form['gender']
    dob = request.form['dob']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO students (name, gender, dob, phone, email, address) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, gender, dob, phone, email, address))
    conn.commit()
    conn.close()
    flash('Student added successfully!')
    return redirect(url_for('admin_dashboard'))

@app.route('/add_marks', methods=['POST'])
def add_marks():
    if session.get('user_type') != 'faculty': return redirect(url_for('index'))
    student_id = request.form['student_id']
    subject = request.form['subject']
    marks = request.form['marks']

    conn = get_db_connection()
    conn.execute('INSERT INTO marks (student_id, subject, marks) VALUES (?, ?, ?)', (student_id, subject, marks))
    conn.commit()
    conn.close()
    flash('Marks added successfully!')
    return redirect(url_for('faculty_dashboard'))

@app.route('/add_attendance', methods=['POST'])
def add_attendance():
    if session.get('user_type') != 'faculty': return redirect(url_for('index'))
    student_id = request.form['student_id']
    date = request.form['date']
    status = request.form['status']

    conn = get_db_connection()
    conn.execute('INSERT INTO attendance (student_id, attendance_date, status) VALUES (?, ?, ?)', (student_id, date, status))
    conn.commit()
    conn.close()
    flash('Attendance recorded successfully!')
    return redirect(url_for('faculty_dashboard'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
