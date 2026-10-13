-- =============================================================================
-- AURA Facility Intelligence Platform — MySQL DDL Schema
-- Module: Core Facilities & Energy Intelligence
-- Database: aura_db
-- =============================================================================

CREATE DATABASE IF NOT EXISTS aura_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE aura_db;

-- -----------------------------------------------------------------------------
-- 1. Facilities Master Table
-- Stores configurable facility profiles (Hospital, College, Commercial, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS facilities (
    facility_id VARCHAR(32) NOT NULL,
    name VARCHAR(128) NOT NULL,
    facility_type VARCHAR(32) NOT NULL DEFAULT 'HOSPITAL',
    location VARCHAR(255) NULL,
    total_floors INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (facility_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 2. Energy Readings Telemetry Table
-- Stores raw ground-level electrical consumption telemetry at 15-minute intervals
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_readings (
    id BIGINT AUTO_INCREMENT NOT NULL,
    facility_id VARCHAR(32) NOT NULL,
    zone_id VARCHAR(32) NOT NULL,
    timestamp DATETIME NOT NULL,
    energy_kwh DECIMAL(10, 2) NOT NULL,
    occupancy_percent DECIMAL(5, 2) DEFAULT 0.00,
    temperature_c DECIMAL(5, 2) NULL,
    operational_status VARCHAR(32) DEFAULT 'NORMAL',
    energy_source VARCHAR(32) DEFAULT 'GRID',
    source VARCHAR(32) DEFAULT 'synthetic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_readings_facility FOREIGN KEY (facility_id)
        REFERENCES facilities (facility_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_energy_zone_time (facility_id, zone_id, timestamp DESC),
    INDEX idx_energy_timestamp (timestamp)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 3. Energy Intelligence Outputs Table
-- Stores AURA's processed operational intelligence contracts for audit and dashboards
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS energy_intelligence (
    id BIGINT AUTO_INCREMENT NOT NULL,
    facility_id VARCHAR(32) NOT NULL,
    zone_id VARCHAR(32) NOT NULL,
    timestamp DATETIME NOT NULL,
    current_energy_kwh DECIMAL(10, 2) NOT NULL,
    anomaly_detected BOOLEAN NOT NULL,
    anomaly_score DECIMAL(6, 3) NOT NULL,
    forecast_energy_kwh DECIMAL(10, 2) NOT NULL,
    forecast_horizon VARCHAR(32) DEFAULT 'next_1_hour',
    recommendation TEXT NOT NULL,
    source VARCHAR(32) DEFAULT 'synthetic',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_intel_facility FOREIGN KEY (facility_id)
        REFERENCES facilities (facility_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_intel_zone_time (facility_id, zone_id, timestamp DESC),
    INDEX idx_intel_anomaly (facility_id, anomaly_detected, timestamp DESC)
) ENGINE=InnoDB;
