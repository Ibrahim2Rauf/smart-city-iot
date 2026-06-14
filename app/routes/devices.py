from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql
from app.routes.audit import log_action
devices = Blueprint('devices', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@devices.route('/devices')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.*, z.zone_name 
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
        ORDER BY d.created_at DESC
    """)
    all_devices = cur.fetchall()
    cur.execute("SELECT * FROM city_zones")
    all_zones = cur.fetchall()
    cur.close()
    return render_template('pages/devices.html', devices=all_devices, zones=all_zones)

@devices.route('/devices/add', methods=['POST'])
@login_required

def add():
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO devices (device_code, device_type, zone_id, latitude, longitude, status, install_date) VALUES (%s, %s, %s, %s, %s, %s, %s)", (
        request.form['device_code'],
        request.form['device_type'],
        request.form['zone_id'],
        request.form['latitude'],
        request.form['longitude'],
        request.form['status'],
        request.form['install_date']
    ))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    log_action('INSERT', 'devices', new_id, f"Added device {request.form['device_code']}")
    flash('Device added successfully!', 'success')
    return redirect(url_for('devices.index'))

@devices.route('/devices/delete/<int:device_id>')
@login_required

def delete(device_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM devices WHERE device_id = %s", (device_id,))
    mysql.connection.commit()
    cur.close()
    log_action('DELETE', 'devices', device_id, f"Deleted device ID {device_id}")
    flash('Device deleted!', 'warning')
    return redirect(url_for('devices.index'))

@devices.route('/devices/update_status/<int:device_id>/<status>')
@login_required
def update_status(device_id, status):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE devices SET status = %s WHERE device_id = %s", (status, device_id))
    mysql.connection.commit()
    cur.close()
    log_action('UPDATE', 'devices', device_id, f"Status changed to {status} for device ID {device_id}")
    flash('Device status updated!', 'success')
    return redirect(url_for('devices.index'))