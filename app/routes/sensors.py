from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql

sensors = Blueprint('sensors', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@sensors.route('/sensors')
@login_required
def index():
    cur = mysql.connection.cursor()

    # AQI Readings
    cur.execute("""
        SELECT sr.reading_id, sr.device_id, sr.sensor_type, sr.value, 
               sr.unit, sr.recorded_at, d.device_code, d.status as device_status, z.zone_name
        FROM sensor_readings sr
        JOIN devices d ON sr.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        ORDER BY sr.recorded_at DESC
        LIMIT 20
    """)
    aqi_readings = cur.fetchall()

    # Traffic Readings
    cur.execute("""
        SELECT t.traffic_id as reading_id, t.device_id, 'Traffic' as sensor_type,
               t.average_speed as value, 'km/h' as unit, t.recorded_at,
               d.device_code, d.status as device_status, z.zone_name,
               t.vehicle_count, t.congestion_level
        FROM traffic_data t
        JOIN devices d ON t.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        ORDER BY t.recorded_at DESC
        LIMIT 20
    """)
    traffic_readings = cur.fetchall()

    # Energy Readings
    cur.execute("""
        SELECT e.energy_id as reading_id, e.device_id, 'Energy' as sensor_type,
               e.kwh_consumed as value, 'kWh' as unit, e.created_at as recorded_at,
               d.device_code, d.status as device_status, z.zone_name
        FROM energy_usage e
        JOIN devices d ON e.device_id = d.device_id
        JOIN city_zones z ON e.zone_id = z.zone_id
        ORDER BY e.created_at DESC
        LIMIT 20
    """)
    energy_readings = cur.fetchall()

    # Latest per device
    cur.execute("""
        SELECT sr.*, d.device_code, z.zone_name
        FROM sensor_readings sr
        JOIN devices d ON sr.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE sr.reading_id IN (
            SELECT MAX(reading_id) FROM sensor_readings GROUP BY device_id
        )
        ORDER BY sr.recorded_at DESC
    """)
    latest_readings = cur.fetchall()

    cur.execute("""
        SELECT d.device_id, d.device_code, d.device_type, d.status, z.zone_name
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE d.status = 'active'
    """)
    active_devices = cur.fetchall()

    cur.close()
    return render_template('pages/sensors.html',
        aqi_readings=aqi_readings,
        traffic_readings=traffic_readings,
        energy_readings=energy_readings,
        latest_readings=latest_readings,
        active_devices=active_devices)

@sensors.route('/sensors/add', methods=['POST'])
@login_required
def add():
    device_id = request.form['device_id']
    sensor_type = request.form['sensor_type']
    value = request.form['value']
    unit = request.form['unit']

    cur = mysql.connection.cursor()
    cur.execute("SELECT status FROM devices WHERE device_id = %s", (device_id,))
    device = cur.fetchone()

    if device['status'] != 'active':
        flash('Cannot add reading — device is not active!', 'danger')
        return redirect(url_for('sensors.index'))

    cur.execute("INSERT INTO sensor_readings (device_id, sensor_type, value, unit) VALUES (%s, %s, %s, %s)",
                (device_id, sensor_type, value, unit))
    mysql.connection.commit()
    cur.close()
    flash('Sensor reading added!', 'success')
    return redirect(url_for('sensors.index'))