from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql
from app.routes.audit import log_action

zones = Blueprint('zones', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@zones.route('/zones')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT z.*, COUNT(d.device_id) as device_count 
        FROM city_zones z
        LEFT JOIN devices d ON z.zone_id = d.zone_id
        GROUP BY z.zone_id
        ORDER BY z.created_at DESC
    """)
    all_zones = cur.fetchall()
    cur.close()
    return render_template('pages/zones.html', zones=all_zones)

@zones.route('/zones/add', methods=['POST'])
@login_required
def add():
    zone_name = request.form['zone_name']
    city = request.form['city']
    area = request.form['area_sq_km']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO city_zones (zone_name, city, area_sq_km) VALUES (%s, %s, %s)",
                (zone_name, city, area))
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    log_action('INSERT', 'city_zones', new_id, f"Added zone {zone_name} in {city}")
    flash('Zone added successfully!', 'success')
    return redirect(url_for('zones.index'))

@zones.route('/zones/delete/<int:zone_id>')
@login_required

def delete(zone_id):

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM city_zones WHERE zone_id = %s", (zone_id,))
    mysql.connection.commit()
    cur.close()
    log_action('DELETE', 'city_zones', zone_id, f"Deleted zone ID {zone_id}")
    flash('Zone deleted!', 'warning')
    return redirect(url_for('zones.index'))
