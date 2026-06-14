from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app import mysql, bcrypt

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            from app.routes.audit import log_action
            log_action('LOGIN', details=f"User {username} logged in")

            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

from flask import jsonify

@auth.route('/api/stats')
def stats():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as c FROM devices")
    devices = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM alerts WHERE is_resolved = FALSE")
    alerts = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM city_zones")
    zones = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) as c FROM sensor_readings WHERE DATE(recorded_at) = CURDATE()")
    readings = cur.fetchone()['c']
    cur.close()
    return jsonify(devices=devices, alerts=alerts, zones=zones, readings=readings)
from functools import wraps
from flask import abort

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated