CREATE TABLE file_logs (
    id SERIAL PRIMARY KEY,
    sender_id BIGINT NOT NULL,
    sender_username TEXT,
    group_id BIGINT NOT NULL,
    group_name TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    file_hash TEXT UNIQUE NOT NULL,  -- Prevents duplicate file storage
    file_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexing for faster queries
CREATE INDEX idx_group_id ON file_logs(group_id);
CREATE INDEX idx_sender_id ON file_logs(sender_id);
CREATE INDEX idx_file_hash ON file_logs(file_hash);