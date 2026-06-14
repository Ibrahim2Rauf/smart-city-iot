from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql

energy = Blueprint('energy', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@energy.route('/energy')
@login_required
def index():
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT z.zone_name, 
               SUM(e.kwh_consumed) as total_kwh,
               SUM(e.cost_pkr) as total_cost,
               COUNT(e.energy_id) as records,
               AVG(e.kwh_consumed) as avg_kwh
        FROM energy_usage e
        JOIN city_zones z ON e.zone_id = z.zone_id
        GROUP BY z.zone_id, z.zone_name
        ORDER BY total_kwh DESC
    """)
    zone_energy = cur.fetchall()

    cur.execute("""
        SELECT e.*, d.device_code, z.zone_name
        FROM energy_usage e
        JOIN devices d ON e.device_id = d.device_id
        JOIN city_zones z ON e.zone_id = z.zone_id
        ORDER BY e.recorded_date DESC
        LIMIT 20
    """)
    recent_energy = cur.fetchall()

    cur.execute("SELECT SUM(kwh_consumed) as total FROM energy_usage")
    total_kwh = cur.fetchone()['total'] or 0

    cur.execute("SELECT SUM(cost_pkr) as total FROM energy_usage")
    total_cost = cur.fetchone()['total'] or 0

    cur.execute("SELECT * FROM city_zones")
    all_zones = cur.fetchall()

    cur.execute("SELECT * FROM devices WHERE status = 'active'")
    active_devices = cur.fetchall()

    cur.close()
    return render_template('pages/energy.html',
        zone_energy=zone_energy,
        recent_energy=recent_energy,
        total_kwh=total_kwh,
        total_cost=total_cost,
        zones=all_zones,
        devices=active_devices)

@energy.route('/energy/add', methods=['POST'])
@login_required
def add():
    cur = mysql.connection.cursor()
    kwh = float(request.form['kwh_consumed'])
    cost = kwh * 50
    cur.execute("""
        INSERT INTO energy_usage (zone_id, device_id, kwh_consumed, cost_pkr, recorded_date)
        VALUES (%s, %s, %s, %s, %s)
    """, (request.form['zone_id'], request.form['device_id'], kwh, cost, request.form['recorded_date']))
    mysql.connection.commit()
    cur.close()
    flash('Energy record added!', 'success')
    return redirect(url_for('energy.index'))