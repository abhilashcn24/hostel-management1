from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'db/database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Home route
@app.route('/')
def home():
    return render_template('login.html')

# Login route
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    role = request.form['role']

    conn = get_db_connection()
    cursor = conn.cursor()

    if role == 'student':
        cursor.execute('SELECT * FROM student WHERE email = ? AND password = ?', (email, password))
    else:
        cursor.execute('SELECT * FROM admin WHERE email = ? AND password = ?', (email, password))
    
    user = cursor.fetchone()
    conn.close()

    if user:
        session['email'] = email
        session['role'] = role
        return redirect('/dashboard')
    else:
        flash('Invalid Credentials. Please try again.')
        return redirect('/')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/')
    return render_template('dashboard.html', role=session['role'])

# Mark Attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'email' not in session:
        return redirect('/')

    location = request.form['location']
    conn = get_db_connection()
    cursor = conn.cursor()

    if location == 'hostel':
        cursor.execute('INSERT INTO attendance (email, date, status) VALUES (?, ?, ?)', 
                       (session['email'], datetime.now().strftime('%Y-%m-%d'), 'Present'))
        conn.commit()
        flash('Attendance marked successfully!')
    else:
        flash('Attendance not marked. You are not inside hostel premises.')
    
    conn.close()
    return redirect('/dashboard')

# Guest Invite
@app.route('/guest_invite', methods=['POST'])
def guest_invite():
    if 'email' not in session:
        return redirect('/')

    guest_name = request.form['guest_name']
    visit_date = request.form['visit_date']
    invite_code = os.urandom(4).hex()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO guest_invite (student_email, guest_name, visit_date, invite_code) VALUES (?, ?, ?, ?)',
                   (session['email'], guest_name, visit_date, invite_code))
    conn.commit()
    conn.close()
    flash(f'Guest Invite Created! Share this code with guest: {invite_code}')
    return redirect('/dashboard')

# Verify Guest Invite
@app.route('/verify_invite', methods=['POST'])
def verify_invite():
    if 'email' not in session or session['role'] != 'admin':
        return redirect('/')

    invite_code = request.form['invite_code']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM guest_invite WHERE invite_code = ?', (invite_code,))
    invite = cursor.fetchone()
    conn.close()

    if invite:
        flash('Guest Invite Verified! Guest can enter.')
    else:
        flash('Invalid Invite Code!')
    
    return redirect('/dashboard')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

