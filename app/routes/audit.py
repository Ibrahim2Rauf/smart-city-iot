from flask import Blueprint, render_template, session, redirect, url_for, request
from app import mysql
from functools import wraps

audit = Blueprint('audit', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def log_action(action_type, table_affected=None, record_id=None, details=None):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session.get('user_id'),
            action_type,
            table_affected,
            record_id,
            details,
            request.remote_addr
        ))
        mysql.connection.commit()
        cur.close()
    except:
        pass

@audit.route('/audit')
@login_required
def index():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT a.*, u.username, u.full_name
        FROM audit_logs a
        LEFT JOIN users u ON a.user_id = u.user_id
        ORDER BY a.created_at DESC
        LIMIT 100
    """)
    logs = cur.fetchall()

    cur.execute("""
        SELECT action_type, COUNT(*) as count
        FROM audit_logs
        GROUP BY action_type
    """)
    action_counts = cur.fetchall()

    cur.close()
    return render_template('pages/audit.html', logs=logs, action_counts=action_counts)