import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, mysql
import random
from datetime import datetime

app = create_app()

def generate_data():
    with app.app_context():
        cur = mysql.connection.cursor()

        # Check kitni readings aaj ki hain
        cur.execute("SELECT COUNT(*) as c FROM sensor_readings WHERE DATE(recorded_at) = CURDATE()")
        today_count = cur.fetchone()['c']

        # Agar 50 se zyada readings hain toh generate mat karo
        if today_count >= 50:
            print(f"⏸️ Enough data today ({today_count} readings). Skipping.")
            cur.close()
            return

        cur.execute("SELECT device_id, device_type FROM devices WHERE status = 'active'")
        devices = cur.fetchall()

        for device in devices:
            device_id = device['device_id']
            device_type = device['device_type']

            if device_type == 'AQI Sensor':
                value = random.randint(50, 350)
                cur.execute("INSERT INTO sensor_readings (device_id, sensor_type, value, unit) VALUES (%s, 'AQI', %s, 'AQI')",
                           (device_id, value))

            elif device_type == 'Traffic Sensor':
                speed = round(random.uniform(5, 100), 2)
                vehicles = random.randint(50, 800)
                if speed < 20: congestion = 'jam'
                elif speed < 40: congestion = 'heavy'
                elif speed < 70: congestion = 'moderate'
                else: congestion = 'free'

                # Check aaj ka traffic record exist karta hai?
                cur.execute("SELECT COUNT(*) as c FROM traffic_data WHERE device_id = %s AND DATE(recorded_at) = CURDATE()", (device_id,))
                if cur.fetchone()['c'] < 5:
                    cur.execute("INSERT INTO traffic_data (device_id, vehicle_count, average_speed, congestion_level) VALUES (%s, %s, %s, %s)",
                               (device_id, vehicles, speed, congestion))

                cur.execute("INSERT INTO sensor_readings (device_id, sensor_type, value, unit) VALUES (%s, 'Traffic', %s, 'km/h')",
                           (device_id, speed))

            elif device_type == 'Energy Meter':
                kwh = round(random.uniform(100, 600), 2)
                cost = kwh * 50

                cur.execute("SELECT zone_id FROM devices WHERE device_id = %s", (device_id,))
                zone = cur.fetchone()

                # Check aaj ka energy record exist karta hai?
                cur.execute("SELECT COUNT(*) as c FROM energy_usage WHERE device_id = %s AND recorded_date = CURDATE()", (device_id,))
                if cur.fetchone()['c'] < 3:
                    cur.execute("INSERT INTO energy_usage (zone_id, device_id, kwh_consumed, cost_pkr, recorded_date) VALUES (%s, %s, %s, %s, CURDATE())",
                               (zone['zone_id'], device_id, kwh, cost))

                cur.execute("INSERT INTO sensor_readings (device_id, sensor_type, value, unit) VALUES (%s, 'Energy', %s, 'kWh')",
                           (device_id, kwh))

        mysql.connection.commit()
        cur.close()
        print(f"✅ Data generated at {datetime.now().strftime('%H:%M:%S')}")

if __name__ == '__main__':
    generate_data()