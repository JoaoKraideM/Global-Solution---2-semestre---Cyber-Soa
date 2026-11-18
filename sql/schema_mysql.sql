-- SombraViva — Referência de esquema MySQL 8.4 (versão 003).
-- IMPORTANTE: NÃO EXECUTE este arquivo se já utilizar Docker + Alembic.
-- Os comandos de produção são: docker compose up -d --build; alembic upgrade head.
-- Para novas bases vazias apenas: este SQL é uma representação documental, sem dados de seed.
CREATE DATABASE IF NOT EXISTS sombraviva CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sombraviva;

CREATE TABLE audit_findings (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	category VARCHAR(80) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	source VARCHAR(60) NOT NULL, 
	sink VARCHAR(60) NOT NULL, 
	field VARCHAR(80) NOT NULL, 
	action VARCHAR(30) NOT NULL, 
	evidence_redacted VARCHAR(200) NOT NULL, 
	is_demo BOOL NOT NULL, 
	remediation TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE security_events (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	category VARCHAR(50) NOT NULL, 
	severity VARCHAR(20) NOT NULL, 
	outcome VARCHAR(30) NOT NULL, 
	summary VARCHAR(300) NOT NULL, 
	is_demo BOOL NOT NULL, 
	triage_status VARCHAR(20) NOT NULL, 
	triage_note VARCHAR(300) NOT NULL, 
	triaged_at DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE stations (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	code VARCHAR(60) NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	setting VARCHAR(120) NOT NULL, 
	simulated BOOL NOT NULL, 
	api_key_hash VARCHAR(128) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_stations_code ON stations (code);

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	`role` VARCHAR(30) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE readings (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	station_id INTEGER NOT NULL, 
	temperature_c FLOAT NOT NULL, 
	humidity_pct FLOAT NOT NULL, 
	is_simulated BOOL NOT NULL, 
	measured_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(station_id) REFERENCES stations (id)
);
CREATE INDEX ix_readings_station_id ON readings (station_id);
CREATE INDEX ix_readings_measured_at ON readings (measured_at);

CREATE TABLE security_triage_actions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	event_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	previous_status VARCHAR(20) NOT NULL, 
	next_status VARCHAR(20) NOT NULL, 
	note VARCHAR(300) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(event_id) REFERENCES security_events (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);
CREATE INDEX ix_security_triage_actions_event_id ON security_triage_actions (event_id);
