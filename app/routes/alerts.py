from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import mysql
from app.routes.audit import log_action

alerts = Blueprint('alerts', __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@alerts.route('/alerts')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.*, d.device_code, z.zone_name
        FROM alerts a
        JOIN devices d ON a.device_id = d.device_id
        JOIN city_zones z ON d.zone_id = z.zone_id
        ORDER BY a.created_at DESC
    """)
    all_alerts = cur.fetchall()

    cur.execute("""
        SELECT severity, COUNT(*) as count
        FROM alerts WHERE is_resolved = FALSE
        GROUP BY severity
    """)
    severity_counts = cur.fetchall()
    cur.close()
    return render_template('pages/alerts.html', alerts=all_alerts, severity_counts=severity_counts)

@alerts.route('/alerts/resolve/<int:alert_id>')
@login_required
def resolve(alert_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE alerts SET is_resolved = TRUE, 
        resolved_by = %s, resolved_at = NOW()
        WHERE alert_id = %s
    """, (session['user_id'], alert_id))
    mysql.connection.commit()
    cur.close()
    log_action('ALERT_RESOLUTION', 'alerts', alert_id, f"Resolved alert ID {alert_id}")
    flash('Alert resolved!', 'success')
    return redirect(url_for('alerts.index'))