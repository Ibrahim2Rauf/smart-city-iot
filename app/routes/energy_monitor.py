from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

energy_monitor = Blueprint('energy_monitor', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@energy_monitor.route('/energy-monitor')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT z.zone_id, z.zone_name,
            COALESCE(SUM(e.kwh_consumed), 0) as total_kwh,
            COALESCE(SUM(e.cost_pkr), 0) as total_cost,
            COALESCE(AVG(e.kwh_consumed), 0) as avg_kwh
        FROM city_zones z
        LEFT JOIN energy_usage e ON z.zone_id = e.zone_id
        GROUP BY z.zone_id, z.zone_name
        ORDER BY total_kwh DESC
    """)
    zone_energy = cur.fetchall()

    cur.execute("""
        SELECT d.device_id, d.device_code, z.zone_name,
            COALESCE((SELECT kwh_consumed FROM energy_usage 
             WHERE device_id = d.device_id 
             ORDER BY created_at DESC LIMIT 1), 0) as latest_kwh
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE d.device_type = 'Energy Meter' AND d.status = 'active'
    """)
    energy_devices = cur.fetchall()

    cur.execute("SELECT COALESCE(SUM(kwh_consumed), 0) as total FROM energy_usage")
    total_kwh = cur.fetchone()['total']

    cur.execute("SELECT COALESCE(SUM(cost_pkr), 0) as total FROM energy_usage")
    total_cost = cur.fetchone()['total']

    cur.close()
    return render_template('pages/energy_monitor.html',
        zone_energy=zone_energy,
        energy_devices=energy_devices,
        total_kwh=total_kwh,
        total_cost=total_cost)