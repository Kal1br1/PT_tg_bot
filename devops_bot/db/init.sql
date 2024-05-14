CREATE USER repl_user WITH REPLICATION ENCRYPTED PASSWORD '13579';
SELECT pg_create_physical_replication_slot('replication_slot');
CREATE DATABASE email_phone;
\c email_phone;
CREATE TABLE emails (ID serial PRIMARY KEY, email VARCHAR(255) NOT NULL);
CREATE TABLE phones (ID serial PRIMARY KEY, phone_number VARCHAR(20) NOT NULL);
