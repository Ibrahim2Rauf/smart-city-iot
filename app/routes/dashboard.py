from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

dashboard = Blueprint('dashboard', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@dashboard.route('/')
@login_required
def index():
    cur = mysql.connection.cursor()

    # Total Devices
    cur.execute("SELECT COUNT(*) as total FROM devices")
    total_devices = cur.fetchone()['total']

    # Open Alerts
    cur.execute("SELECT COUNT(*) as total FROM alerts WHERE is_resolved = FALSE")
    open_alerts = cur.fetchone()['total']

    # Total Zones
    cur.execute("SELECT COUNT(*) as total FROM city_zones")
    total_zones = cur.fetchone()['total']

    # Readings Today
    cur.execute("SELECT COUNT(*) as total FROM sensor_readings WHERE DATE(recorded_at) = CURDATE()")
    readings_today = cur.fetchone()['total']

    # Recent Critical Alerts
    cur.execute("""
        SELECT a.*, d.device_code, z.zone_name 
        FROM alerts a
        JOIN devices d ON a.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE a.is_resolved = FALSE
        ORDER BY a.created_at DESC LIMIT 5
    """)
    recent_alerts = cur.fetchall()

    # Device Status Count
    cur.execute("""
        SELECT status, COUNT(*) as count 
        FROM devices 
        GROUP BY status
    """)
    device_status = cur.fetchall()

    cur.close()

    return render_template('pages/dashboard.html',
        total_devices=total_devices,
        open_alerts=open_alerts,
        total_zones=total_zones,
        readings_today=readings_today,
        recent_alerts=recent_alerts,
        device_status=device_status
    )