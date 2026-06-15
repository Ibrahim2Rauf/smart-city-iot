-- ============================================================
-- SMART CITY IoT MONITORING & MANAGEMENT SYSTEM
-- Database Schema
-- Version: 2.0
-- Author: Ibrahim Rauf
-- ============================================================

CREATE DATABASE IF NOT EXISTS smart_city_iot;
USE smart_city_iot;

-- ============================================================
-- TABLE 1: USERS
-- Stores system users with roles
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    full_name     VARCHAR(100) NOT NULL,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    email         VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin', 'operator') DEFAULT 'operator',
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_email CHECK (email LIKE '%@%.%')
);

-- ============================================================
-- TABLE 2: CITY ZONES
-- Represents different areas/zones of the smart city
-- ============================================================
CREATE TABLE IF NOT EXISTS city_zones (
    zone_id    INT AUTO_INCREMENT PRIMARY KEY,
    zone_name  VARCHAR(100) NOT NULL,
    city       VARCHAR(100) NOT NULL,
    area_sq_km DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 3: DEVICES
-- IoT devices installed in city zones
-- ============================================================
CREATE TABLE IF NOT EXISTS devices (
    device_id   INT AUTO_INCREMENT PRIMARY KEY,
    device_code VARCHAR(50) UNIQUE NOT NULL,
    device_type ENUM('AQI Sensor','Traffic Sensor','Energy Meter',
                     'Weather Station','CCTV') NOT NULL,
    zone_id     INT NOT NULL,
    latitude    DECIMAL(10,6),
    longitude   DECIMAL(10,6),
    status      ENUM('active','maintenance','inactive') DEFAULT 'active',
    install_date DATE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES city_zones(zone_id) ON DELETE CASCADE,
    INDEX idx_devices_zone (zone_id),
    INDEX idx_devices_status (status)
);

-- ============================================================
-- TABLE 4: SENSOR READINGS
-- Raw data readings from IoT sensors
-- ============================================================
CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id  INT AUTO_INCREMENT PRIMARY KEY,
    device_id   INT NOT NULL,
    sensor_type ENUM('AQI','Traffic','Energy') NOT NULL,
    value       DECIMAL(10,2) NOT NULL,
    unit        VARCHAR(20),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_readings_device (device_id),
    INDEX idx_readings_date (recorded_at)
);

-- ============================================================
-- TABLE 5: ALERTS
-- Auto-generated and manual alerts for city issues
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    alert_id    INT AUTO_INCREMENT PRIMARY KEY,
    device_id   INT NOT NULL,
    alert_type  VARCHAR(100) NOT NULL,
    severity    ENUM('critical','high','medium','low') NOT NULL,
    message     TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by INT,
    resolved_at TIMESTAMP NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(user_id),
    INDEX idx_alerts_device (device_id),
    INDEX idx_alerts_severity (severity),
    INDEX idx_alerts_resolved (is_resolved)
);

-- ============================================================
-- TABLE 6: ENERGY USAGE
-- Tracks electricity consumption per zone and device
-- ============================================================
CREATE TABLE IF NOT EXISTS energy_usage (
    energy_id     INT AUTO_INCREMENT PRIMARY KEY,
    zone_id       INT NOT NULL,
    device_id     INT NOT NULL,
    kwh_consumed  DECIMAL(10,2) NOT NULL,
    cost_pkr      DECIMAL(10,2),
    recorded_date DATE NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (zone_id) REFERENCES city_zones(zone_id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_energy_zone (zone_id),
    INDEX idx_energy_date (recorded_date)
);

-- ============================================================
-- TABLE 7: TRAFFIC DATA
-- Vehicle count, speed and congestion monitoring
-- ============================================================
CREATE TABLE IF NOT EXISTS traffic_data (
    traffic_id       INT AUTO_INCREMENT PRIMARY KEY,
    device_id        INT NOT NULL,
    vehicle_count    INT,
    average_speed    DECIMAL(5,2),
    congestion_level ENUM('free','moderate','heavy','jam') NOT NULL,
    recorded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_traffic_device (device_id),
    INDEX idx_traffic_congestion (congestion_level)
);

-- ============================================================
-- TABLE 8: MAINTENANCE LOGS
-- Technician visits and device repair history
-- ============================================================
CREATE TABLE IF NOT EXISTS maintenance_logs (
    log_id           INT AUTO_INCREMENT PRIMARY KEY,
    device_id        INT NOT NULL,
    technician_name  VARCHAR(100) NOT NULL,
    maintenance_type VARCHAR(100),
    description      TEXT,
    cost_pkr         DECIMAL(10,2),
    maintenance_date DATE NOT NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(device_id) ON DELETE CASCADE,
    INDEX idx_maintenance_device (device_id),
    INDEX idx_maintenance_date (maintenance_date)
);

-- ============================================================
-- TABLE 9: AUDIT LOGS
-- Security tracking — who did what and when
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    audit_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id        INT,
    action_type    ENUM('INSERT','UPDATE','DELETE','LOGIN',
                        'ALERT_RESOLUTION','MAINTENANCE') NOT NULL,
    table_affected VARCHAR(50),
    record_id      INT,
    action_details TEXT,
    ip_address     VARCHAR(50),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action_type),
    INDEX idx_audit_date (created_at)
);

-- ============================================================
-- VIEWS
-- ============================================================

-- View 1: Active Devices with Zone Info
CREATE OR REPLACE VIEW view_active_devices AS
SELECT d.device_id, d.device_code, d.device_type, d.status,
       z.zone_name, z.city, d.latitude, d.longitude, d.install_date
FROM devices d
JOIN city_zones z ON d.zone_id = z.zone_id
WHERE d.status = 'active';

-- View 2: Open Alerts with Device and Zone
CREATE OR REPLACE VIEW view_open_alerts AS
SELECT a.alert_id, a.alert_type, a.severity, a.message,
       a.created_at, d.device_code, z.zone_name
FROM alerts a
JOIN devices d ON a.device_id = d.device_id
JOIN city_zones z ON d.zone_id = z.zone_id
WHERE a.is_resolved = FALSE
ORDER BY a.created_at DESC;

-- View 3: Zone Summary Report
CREATE OR REPLACE VIEW view_zone_summary AS
SELECT z.zone_id, z.zone_name, z.city, z.area_sq_km,
       COUNT(DISTINCT d.device_id) as total_devices,
       COUNT(DISTINCT CASE WHEN d.status='active' THEN d.device_id END) as active_devices,
       COUNT(DISTINCT CASE WHEN a.is_resolved=FALSE THEN a.alert_id END) as open_alerts,
       COALESCE(SUM(e.kwh_consumed), 0) as total_energy
FROM city_zones z
LEFT JOIN devices d ON z.zone_id = d.zone_id
LEFT JOIN alerts a ON d.device_id = a.device_id
LEFT JOIN energy_usage e ON z.zone_id = e.zone_id
GROUP BY z.zone_id, z.zone_name, z.city, z.area_sq_km;

-- View 4: Device Health Scores
CREATE OR REPLACE VIEW view_device_health AS
SELECT d.device_id, d.device_code, d.device_type, d.status, z.zone_name,
       COUNT(DISTINCT m.log_id) as maintenance_count,
       COUNT(DISTINCT a.alert_id) as alert_count,
       CASE
           WHEN d.status = 'inactive' THEN 0
           WHEN d.status = 'maintenance' THEN 40
           WHEN COUNT(DISTINCT a.alert_id) > 3 THEN 50
           WHEN COUNT(DISTINCT a.alert_id) > 1 THEN 70
           ELSE 100
       END as health_score
FROM devices d
LEFT JOIN city_zones z ON d.zone_id = z.zone_id
LEFT JOIN maintenance_logs m ON d.device_id = m.device_id
LEFT JOIN alerts a ON d.device_id = a.device_id AND a.is_resolved = FALSE
GROUP BY d.device_id, d.device_code, d.device_type, d.status, z.zone_name;

-- View 5: Latest Sensor Reading Per Device
CREATE OR REPLACE VIEW view_latest_readings AS
SELECT sr.reading_id, sr.sensor_type, sr.value, sr.unit, sr.recorded_at,
       d.device_code, d.device_type, z.zone_name
FROM sensor_readings sr
JOIN devices d ON sr.device_id = d.device_id
JOIN city_zones z ON d.zone_id = z.zone_id
WHERE sr.reading_id IN (
    SELECT MAX(reading_id) FROM sensor_readings GROUP BY device_id
);

-- ============================================================
-- STORED PROCEDURES
-- ============================================================

DELIMITER $$

-- Procedure 1: Get full zone report
CREATE PROCEDURE sp_zone_report(IN p_zone_id INT)
BEGIN
    SELECT z.zone_name, z.city, z.area_sq_km,
           COUNT(DISTINCT d.device_id) as total_devices,
           COUNT(DISTINCT a.alert_id) as total_alerts,
           COUNT(DISTINCT m.log_id) as total_maintenance,
           COALESCE(SUM(e.kwh_consumed), 0) as total_energy,
           COALESCE(SUM(e.cost_pkr), 0) as total_cost
    FROM city_zones z
    LEFT JOIN devices d ON z.zone_id = d.zone_id
    LEFT JOIN alerts a ON d.device_id = a.device_id
    LEFT JOIN maintenance_logs m ON d.device_id = m.device_id
    LEFT JOIN energy_usage e ON z.zone_id = e.zone_id
    WHERE z.zone_id = p_zone_id
    GROUP BY z.zone_id, z.zone_name, z.city, z.area_sq_km;
END$$

-- Procedure 2: Get device full history
CREATE PROCEDURE sp_device_history(IN p_device_id INT)
BEGIN
    SELECT 'Sensor Reading' as record_type,
           sensor_type as details,
           CAST(value AS CHAR) as value,
           recorded_at as record_date
    FROM sensor_readings WHERE device_id = p_device_id
    UNION ALL
    SELECT 'Maintenance', maintenance_type,
           CAST(cost_pkr AS CHAR), maintenance_date
    FROM maintenance_logs WHERE device_id = p_device_id
    UNION ALL
    SELECT 'Alert', alert_type, severity, created_at
    FROM alerts WHERE device_id = p_device_id
    ORDER BY record_date DESC;
END$$

-- Procedure 3: Resolve all alerts in a zone
CREATE PROCEDURE sp_resolve_zone_alerts(IN p_zone_id INT, IN p_user_id INT)
BEGIN
    UPDATE alerts a
    JOIN devices d ON a.device_id = d.device_id
    SET a.is_resolved = TRUE,
        a.resolved_by = p_user_id,
        a.resolved_at = NOW()
    WHERE d.zone_id = p_zone_id AND a.is_resolved = FALSE;
    SELECT ROW_COUNT() as alerts_resolved;
END$$

-- Procedure 4: City-wide statistics
CREATE PROCEDURE sp_city_stats()
BEGIN
    SELECT
        (SELECT COUNT(*) FROM devices) as total_devices,
        (SELECT COUNT(*) FROM devices WHERE status='active') as active_devices,
        (SELECT COUNT(*) FROM alerts WHERE is_resolved=FALSE) as open_alerts,
        (SELECT COUNT(*) FROM city_zones) as total_zones,
        (SELECT COALESCE(SUM(kwh_consumed),0) FROM energy_usage) as total_energy,
        (SELECT COALESCE(SUM(cost_pkr),0) FROM energy_usage) as total_cost,
        (SELECT COUNT(*) FROM sensor_readings WHERE DATE(recorded_at)=CURDATE()) as readings_today,
        (SELECT COUNT(*) FROM maintenance_logs) as total_maintenance;
END$$

-- ============================================================
-- SCALAR FUNCTIONS
-- ============================================================

-- Function 1: Get AQI health status label
CREATE FUNCTION fn_aqi_status(aqi_value DECIMAL(10,2))
RETURNS VARCHAR(30) DETERMINISTIC
BEGIN
    DECLARE status VARCHAR(30);
    IF aqi_value <= 50 THEN SET status = 'Good';
    ELSEIF aqi_value <= 100 THEN SET status = 'Moderate';
    ELSEIF aqi_value <= 150 THEN SET status = 'Unhealthy (Sensitive)';
    ELSEIF aqi_value <= 200 THEN SET status = 'Unhealthy';
    ELSEIF aqi_value <= 300 THEN SET status = 'Very Unhealthy';
    ELSE SET status = 'Hazardous';
    END IF;
    RETURN status;
END$$

-- Function 2: Calculate energy cost in PKR
CREATE FUNCTION fn_energy_cost(kwh DECIMAL(10,2))
RETURNS DECIMAL(10,2) DETERMINISTIC
BEGIN
    RETURN kwh * 50;
END$$

-- Function 3: Calculate device health score
CREATE FUNCTION fn_device_health(p_device_id INT)
RETURNS INT DETERMINISTIC
BEGIN
    DECLARE health INT DEFAULT 100;
    DECLARE alert_count INT;
    DECLARE dev_status VARCHAR(20);
    SELECT status INTO dev_status FROM devices WHERE device_id = p_device_id;
    SELECT COUNT(*) INTO alert_count FROM alerts
    WHERE device_id = p_device_id AND is_resolved = FALSE;
    IF dev_status = 'inactive' THEN SET health = 0;
    ELSEIF dev_status = 'maintenance' THEN SET health = 40;
    ELSEIF alert_count > 3 THEN SET health = 50;
    ELSEIF alert_count > 1 THEN SET health = 70;
    END IF;
    RETURN health;
END$$

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Trigger 1: Auto alert on high AQI reading
CREATE TRIGGER auto_alert_on_reading
AFTER INSERT ON sensor_readings
FOR EACH ROW
BEGIN
    IF NEW.sensor_type = 'AQI' AND NEW.value > 200 THEN
        INSERT INTO alerts (device_id, alert_type, severity, message, is_resolved)
        VALUES (NEW.device_id, 'High AQI',
            CASE WHEN NEW.value > 300 THEN 'critical'
                 WHEN NEW.value > 250 THEN 'high' ELSE 'medium' END,
            CONCAT('AQI level ', NEW.value, ' detected on device ', NEW.device_id), FALSE);
    END IF;
    IF NEW.sensor_type = 'Energy' AND NEW.value > 400 THEN
        INSERT INTO alerts (device_id, alert_type, severity, message, is_resolved)
        VALUES (NEW.device_id, 'High Energy Consumption', 'high',
            CONCAT('Energy consumption ', NEW.value, ' kWh detected'), FALSE);
    END IF;
    IF NEW.sensor_type = 'Traffic' AND NEW.value < 10 THEN
        INSERT INTO alerts (device_id, alert_type, severity, message, is_resolved)
        VALUES (NEW.device_id, 'Traffic Jam', 'critical',
            CONCAT('Very low speed ', NEW.value, ' km/h — possible traffic jam'), FALSE);
    END IF;
END$$

-- Trigger 2: Audit device delete
CREATE TRIGGER audit_device_delete
AFTER DELETE ON devices FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'DELETE', 'devices', OLD.device_id,
            CONCAT('Device ', OLD.device_code, ' deleted'), 'MySQL-Direct');
END$$

-- Trigger 3: Audit device insert
CREATE TRIGGER audit_device_insert
AFTER INSERT ON devices FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'INSERT', 'devices', NEW.device_id,
            CONCAT('Device ', NEW.device_code, ' added'), 'MySQL-Direct');
END$$

-- Trigger 4: Audit device status update
CREATE TRIGGER audit_device_update
AFTER UPDATE ON devices FOR EACH ROW
BEGIN
    IF NEW.status != OLD.status THEN
        INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
        VALUES (NULL, 'UPDATE', 'devices', NEW.device_id,
                CONCAT('Device ', NEW.device_code, ' status: ', OLD.status, ' → ', NEW.status), 'APP');
    END IF;
END$$

-- Trigger 5: Audit zone delete
CREATE TRIGGER audit_zone_delete
AFTER DELETE ON city_zones FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'DELETE', 'city_zones', OLD.zone_id,
            CONCAT('Zone ', OLD.zone_name, ' deleted'), 'MySQL-Direct');
END$$

-- Trigger 6: Audit zone insert
CREATE TRIGGER audit_zone_insert
AFTER INSERT ON city_zones FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'INSERT', 'city_zones', NEW.zone_id,
            CONCAT('Zone ', NEW.zone_name, ' added in ', NEW.city), 'MySQL-Direct');
END$$

-- Trigger 7: Audit alert resolve
CREATE TRIGGER audit_alert_resolve
AFTER UPDATE ON alerts FOR EACH ROW
BEGIN
    IF NEW.is_resolved = TRUE AND OLD.is_resolved = FALSE THEN
        INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
        VALUES (NEW.resolved_by, 'ALERT_RESOLUTION', 'alerts', NEW.alert_id,
                CONCAT('Alert resolved: ', NEW.alert_type, ' - ', NEW.severity), 'APP');
    END IF;
END$$

-- Trigger 8: Audit maintenance insert
CREATE TRIGGER audit_maintenance_insert
AFTER INSERT ON maintenance_logs FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'MAINTENANCE', 'maintenance_logs', NEW.log_id,
            CONCAT('Maintenance by ', NEW.technician_name, ' - ', NEW.maintenance_type), 'AUTO-TRIGGER');
END$$

-- Trigger 9: Audit sensor reading
CREATE TRIGGER audit_sensor_insert
AFTER INSERT ON sensor_readings FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'INSERT', 'sensor_readings', NEW.reading_id,
            CONCAT('Reading: ', NEW.sensor_type, ' = ', NEW.value, ' ', NEW.unit), 'AUTO-TRIGGER');
END$$

-- Trigger 10: Audit energy insert
CREATE TRIGGER audit_energy_insert
AFTER INSERT ON energy_usage FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'INSERT', 'energy_usage', NEW.energy_id,
            CONCAT('Energy: ', NEW.kwh_consumed, ' kWh, Cost: Rs', NEW.cost_pkr), 'AUTO-TRIGGER');
END$$

-- Trigger 11: Audit traffic insert
CREATE TRIGGER audit_traffic_insert
AFTER INSERT ON traffic_data FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, table_affected, record_id, action_details, ip_address)
    VALUES (NULL, 'INSERT', 'traffic_data', NEW.traffic_id,
            CONCAT('Traffic: ', NEW.congestion_level, ', Speed: ', NEW.average_speed, ' km/h'), 'AUTO-TRIGGER');
END$$

DELIMITER ;

-- ============================================================
-- END OF SCHEMA
-- Smart City IoT v2.0
-- ============================================================