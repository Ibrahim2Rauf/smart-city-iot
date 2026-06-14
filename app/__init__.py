import os
from flask import Flask
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

mysql = MySQL()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    app = Flask(__name__, template_folder=template_dir)
    app.config.from_object(Config)
    mysql.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    from app.routes.auth import auth
    from app.routes.dashboard import dashboard
    from app.routes.zones import zones
    from app.routes.devices import devices
    from app.routes.alerts import alerts
    from app.routes.sensors import sensors
    from app.routes.energy import energy
    from app.routes.traffic import traffic
    from app.routes.maintenance import maintenance
    from app.routes.analytics import analytics
    from app.routes.camera import camera
    from app.routes.aqi_monitor import aqi_monitor
    from app.routes.energy_monitor import energy_monitor
    from app.routes.city_map import city_map
    from app.routes.audit import audit
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(zones)
    app.register_blueprint(devices)
    app.register_blueprint(alerts)
    app.register_blueprint(sensors)
    app.register_blueprint(energy)
    app.register_blueprint(traffic)
    app.register_blueprint(maintenance)
    app.register_blueprint(analytics)
    app.register_blueprint(camera)
    app.register_blueprint(aqi_monitor)
    app.register_blueprint(energy_monitor)
    app.register_blueprint(city_map)
    app.register_blueprint(audit)
    from app.models import load_user
    login_manager.user_loader(load_user)
   
    return app