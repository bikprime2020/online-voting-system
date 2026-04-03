from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

def connect_db():
    return sqlite3.connect("database.db")

@app.route('/')
def home():
    return redirect('/login')

# Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        conn = connect_db()
        conn.execute("INSERT INTO users (username,password) VALUES (?,?)",(user,pwd))
        conn.commit()
        conn.close()

        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']

        conn = connect_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(user,pwd))
        data = cur.fetchone()
        conn.close()

        if data:
            session['user'] = user
            session['user_id'] = data[0]
            return redirect('/vote')
        else:
            return "Invalid Login"
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Vote
@app.route('/vote', methods=['GET','POST'])
def vote():
    if 'user' not in session:
        return redirect('/login')

    conn = connect_db()
    cur = conn.cursor()

    # Check if already voted
    cur.execute("SELECT * FROM votes WHERE user_id=?", (session['user_id'],))
    already = cur.fetchone()

    if request.method == 'POST':
        if already:
            return "You have already voted!"

        cid = request.form['candidate']

        cur.execute("UPDATE candidates SET votes = votes + 1 WHERE id=?", (cid,))
        cur.execute("INSERT INTO votes (user_id, candidate_id) VALUES (?,?)",
                    (session['user_id'], cid))

        conn.commit()
        conn.close()
        return redirect('/result')

    cur.execute("SELECT * FROM candidates")
    candidates = cur.fetchall()
    conn.close()

    return render_template('vote.html', candidates=candidates, voted=already)

# Result
@app.route('/result')
def result():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT name, votes FROM candidates")
    data = cur.fetchall()
    conn.close()

    return render_template('result.html', data=data)

# Admin Panel
@app.route('/admin')
def admin():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT name, votes FROM candidates")
    data = cur.fetchall()
    conn.close()

    return render_template('admin.html', data=data)
def init_db():
    import sqlite3
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS candidates (id INTEGER PRIMARY KEY, name TEXT, votes INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS votes (user_id INTEGER, candidate_id INTEGER)")

    # Add default candidates if empty
    c.execute("SELECT COUNT(*) FROM candidates")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO candidates (name, votes) VALUES ('Candidate A', 0)")
        c.execute("INSERT INTO candidates (name, votes) VALUES ('Candidate B', 0)")
        c.execute("INSERT INTO candidates (name, votes) VALUES ('Candidate C', 0)")

    conn.commit()
    conn.close()

import os

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
