from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

camera = Blueprint('camera', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@camera.route('/camera')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT d.*, z.zone_name 
        FROM devices d
        JOIN city_zones z ON d.zone_id = z.zone_id
        WHERE d.status = 'active'
    """)
    devices = cur.fetchall()
    cur.close()
    return render_template('pages/camera.html', devices=devices)