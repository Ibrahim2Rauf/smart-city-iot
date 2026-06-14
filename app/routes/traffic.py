from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql

traffic = Blueprint('traffic', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@traffic.route('/traffic')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT t.*, d.device_code, z.zone_name
        FROM traffic_data t
        JOIN devices d ON t.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        ORDER BY t.recorded_at DESC
        LIMIT 50
    """)
    traffic_records = cur.fetchall()

    cur.execute("""
        SELECT congestion_level, COUNT(*) as count
        FROM traffic_data
        GROUP BY congestion_level
    """)
    congestion_counts = cur.fetchall()

    cur.execute("""
        SELECT z.zone_name, AVG(t.average_speed) as avg_speed,
               AVG(t.vehicle_count) as avg_vehicles,
               MAX(t.vehicle_count) as max_vehicles
        FROM traffic_data t
        JOIN devices d ON t.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        GROUP BY z.zone_id, z.zone_name
    """)
    zone_traffic = cur.fetchall()

    cur.execute("""
        SELECT d.device_id, d.device_code, z.zone_name
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE d.device_type = 'Traffic Sensor' AND d.status = 'active'
    """)
    traffic_devices = cur.fetchall()

    cur.close()
    return render_template('pages/traffic.html',
        traffic_records=traffic_records,
        congestion_counts=congestion_counts,
        zone_traffic=zone_traffic,
        traffic_devices=traffic_devices)

@traffic.route('/traffic/add', methods=['POST'])
@login_required
def add():
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO traffic_data (device_id, vehicle_count, average_speed, congestion_level)
        VALUES (%s, %s, %s, %s)
    """, (
        request.form['device_id'],
        request.form['vehicle_count'],
        request.form['average_speed'],
        request.form['congestion_level']
    ))
    mysql.connection.commit()
    cur.close()
    flash('Traffic record added!', 'success')
    return redirect(url_for('traffic.index'))