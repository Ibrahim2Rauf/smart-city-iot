from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

analytics = Blueprint('analytics', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@analytics.route('/analytics')
@login_required
def index():
    cur = mysql.connection.cursor()

    # Device Health Score
    cur.execute("""
        SELECT d.device_code, z.zone_name, d.status,
            COUNT(m.log_id) as maintenance_count,
            COUNT(a.alert_id) as alert_count,
            CASE 
                WHEN d.status = 'inactive' THEN 0
                WHEN d.status = 'maintenance' THEN 40
                WHEN COUNT(a.alert_id) > 3 THEN 50
                WHEN COUNT(a.alert_id) > 1 THEN 70
                ELSE 100
            END as health_score
        FROM devices d
        LEFT JOIN city_zones z ON d.zone_id = z.zone_id
        LEFT JOIN maintenance_logs m ON d.device_id = m.device_id
        LEFT JOIN alerts a ON d.device_id = a.device_id AND a.is_resolved = FALSE
        GROUP BY d.device_id, d.device_code, z.zone_name, d.status
        ORDER BY health_score ASC
    """)
    device_health = cur.fetchall()

    # Above Average Energy Zones
    cur.execute("""
        SELECT z.zone_name, SUM(e.kwh_consumed) as total_kwh
        FROM energy_usage e
        JOIN city_zones z ON e.zone_id = z.zone_id
        GROUP BY z.zone_id, z.zone_name
        HAVING SUM(e.kwh_consumed) > (
            SELECT AVG(zone_total) FROM (
                SELECT SUM(kwh_consumed) as zone_total 
                FROM energy_usage 
                GROUP BY zone_id
            ) as zone_averages
        )
    """)
    above_avg_energy = cur.fetchall()

    # Top Polluted Zones
    cur.execute("""
        SELECT z.zone_name, AVG(sr.value) as avg_aqi, MAX(sr.value) as max_aqi
        FROM sensor_readings sr
        JOIN devices d ON sr.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE sr.sensor_type = 'AQI'
        GROUP BY z.zone_id, z.zone_name
        ORDER BY avg_aqi DESC
        LIMIT 5
    """)
    top_polluted = cur.fetchall()

    # Zone Analytics Report
    cur.execute("""
        SELECT z.zone_name,
            COUNT(DISTINCT d.device_id) as total_devices,
            COUNT(DISTINCT a.alert_id) as total_alerts,
            COUNT(DISTINCT m.log_id) as total_maintenance,
            SUM(e.kwh_consumed) as total_energy
        FROM city_zones z
        LEFT JOIN devices d ON z.zone_id = d.zone_id
        LEFT JOIN alerts a ON d.device_id = a.device_id
        LEFT JOIN maintenance_logs m ON d.device_id = m.device_id
        LEFT JOIN energy_usage e ON z.zone_id = e.zone_id
        GROUP BY z.zone_id, z.zone_name
        ORDER BY total_alerts DESC
    """)
    zone_report = cur.fetchall()

    cur.close()
    return render_template('pages/analytics.html',
        device_health=device_health,
        above_avg_energy=above_avg_energy,
        top_polluted=top_polluted,
        zone_report=zone_report)