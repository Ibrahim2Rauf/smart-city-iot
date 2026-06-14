from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from app import mysql

city_map = Blueprint('city_map', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@city_map.route('/city-map')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.device_id, d.device_code, d.device_type, d.status,
               d.latitude, d.longitude, z.zone_name, z.zone_id,
               (SELECT value FROM sensor_readings 
                WHERE device_id = d.device_id 
                ORDER BY recorded_at DESC LIMIT 1) as latest_value,
               (SELECT sensor_type FROM sensor_readings 
                WHERE device_id = d.device_id 
                ORDER BY recorded_at DESC LIMIT 1) as latest_type
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
    """)
    devices = cur.fetchall()

    cur.execute("""
        SELECT z.*, COUNT(d.device_id) as device_count,
               SUM(CASE WHEN a.is_resolved = FALSE THEN 1 ELSE 0 END) as open_alerts
        FROM city_zones z
        LEFT JOIN devices d ON z.zone_id = d.zone_id
        LEFT JOIN alerts a ON d.device_id = a.device_id
        GROUP BY z.zone_id
    """)
    zones = cur.fetchall()
    cur.close()
    return render_template('pages/city_map.html', devices=devices, zones=zones)