from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql

maintenance = Blueprint('maintenance', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@maintenance.route('/maintenance')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT m.*, d.device_code, z.zone_name
        FROM maintenance_logs m
        JOIN devices d ON m.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        ORDER BY m.maintenance_date DESC
    """)
    logs = cur.fetchall()

    cur.execute("""
        SELECT SUM(cost_pkr) as total_cost, COUNT(*) as total_logs
        FROM maintenance_logs
    """)
    stats = cur.fetchone()

    cur.execute("""
        SELECT d.device_id, d.device_code, d.device_type, z.zone_name
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
    """)
    all_devices = cur.fetchall()

    cur.close()
    return render_template('pages/maintenance.html',
        logs=logs, stats=stats, devices=all_devices)

@maintenance.route('/maintenance/add', methods=['POST'])
@login_required
def add():
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO maintenance_logs 
        (device_id, technician_name, maintenance_type, description, cost_pkr, maintenance_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        request.form['device_id'],
        request.form['technician_name'],
        request.form['maintenance_type'],
        request.form['description'],
        request.form['cost_pkr'],
        request.form['maintenance_date']
    ))
    cur.execute("UPDATE devices SET status = 'active' WHERE device_id = %s",
                (request.form['device_id'],))
    mysql.connection.commit()
    cur.close()
    flash('Maintenance log added! Device set to active.', 'success')
    return redirect(url_for('maintenance.index'))