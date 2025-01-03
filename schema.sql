-- Create the database (if not already created)
CREATE DATABASE telegram_cti;

-- Connect to the database (if running separately, use `\c telegram_cti` in psql)
\c telegram_cti;

-- Create a table to store file metadata & telemetry
CREATE TABLE file_logs (
    id SERIAL PRIMARY KEY,
    sender_id BIGINT NOT NULL,
    sender_username TEXT,
    group_id BIGINT NOT NULL,
    group_name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL, -- To prevent duplicate entries
    file_path TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create a table to store extracted credentials, usernames, passwords, and PII
CREATE TABLE indexed_data (
    id SERIAL PRIMARY KEY,
    file_id INT REFERENCES file_logs(id) ON DELETE CASCADE,
    data_type TEXT NOT NULL, -- Type of data (email, username, password, etc.)
    extracted_value TEXT NOT NULL, -- The actual extracted data
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes to optimize search queries
CREATE INDEX idx_group_id ON file_logs (group_id);
CREATE INDEX idx_extracted_value ON indexed_data (extracted_value);
CREATE INDEX idx_file_hash ON file_logs (file_hash);
CREATE INDEX idx_sender_id ON file_logs (sender_id);
CREATE INDEX idx_file_name ON file_logs (file_name);
CREATE INDEX idx_data_type ON indexed_data (data_type);