from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

aqi_monitor = Blueprint('aqi_monitor', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@aqi_monitor.route('/aqi-monitor')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.device_id, d.device_code, z.zone_name,
            (SELECT value FROM sensor_readings 
             WHERE device_id = d.device_id AND sensor_type = 'AQI' 
             ORDER BY recorded_at DESC LIMIT 1) as latest_aqi
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE d.device_type = 'AQI Sensor' AND d.status = 'active'
    """)
    aqi_devices = cur.fetchall()
    cur.close()
    return render_template('pages/aqi_monitor.html', aqi_devices=aqi_devices)