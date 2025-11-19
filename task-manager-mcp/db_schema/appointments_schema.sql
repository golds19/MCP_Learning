-- Appointments Database Schema
-- Stores appointment data with Google Calendar integration

-- Main appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Event Details
    title TEXT NOT NULL,
    description TEXT,
    location TEXT,

    -- Timing
    start_datetime TEXT NOT NULL,  -- ISO 8601 format: 2025-11-25T14:00:00
    end_datetime TEXT NOT NULL,
    timezone TEXT DEFAULT 'UTC',
    all_day INTEGER DEFAULT 0,     -- Boolean: 0 = false, 1 = true

    -- Calendar Integration
    google_event_id TEXT UNIQUE,   -- Link to Google Calendar event ID
    calendar_id TEXT,              -- Which Google calendar (e.g., "primary")

    -- Attendees
    attendees TEXT,                -- JSON array of attendee emails
    organizer TEXT,                -- Email of organizer

    -- Status
    status TEXT DEFAULT 'confirmed', -- confirmed, cancelled, tentative

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Sync Status
    synced_to_calendar INTEGER DEFAULT 0,  -- Boolean: synced to Google Calendar
    last_sync_at TIMESTAMP,

    -- Additional fields
    color TEXT,                    -- Event color (if supported)
    reminders TEXT,                -- JSON array of reminder settings
    recurring_event_id TEXT,       -- For recurring events
    notes TEXT                     -- Additional notes
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_appointments_start_datetime
    ON appointments(start_datetime);

CREATE INDEX IF NOT EXISTS idx_appointments_google_event_id
    ON appointments(google_event_id);

CREATE INDEX IF NOT EXISTS idx_appointments_status
    ON appointments(status);

-- Sync log table (for debugging and audit trail)
CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER,
    action TEXT NOT NULL,          -- 'create', 'update', 'delete', 'sync'
    server TEXT NOT NULL,          -- 'google_calendar' or 'sqlite'
    status TEXT NOT NULL,          -- 'success', 'failed', 'pending'
    error_message TEXT,
    details TEXT,                  -- JSON with additional details
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
);

-- Index for sync log
CREATE INDEX IF NOT EXISTS idx_sync_log_appointment_id
    ON sync_log(appointment_id);

CREATE INDEX IF NOT EXISTS idx_sync_log_synced_at
    ON sync_log(synced_at);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_appointments_timestamp
    AFTER UPDATE ON appointments
    FOR EACH ROW
BEGIN
    UPDATE appointments
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
END;

-- Sample queries (commented out)
--
-- Get all upcoming appointments:
-- SELECT * FROM appointments
-- WHERE start_datetime > datetime('now')
-- ORDER BY start_datetime ASC;
--
-- Get appointments for a specific date:
-- SELECT * FROM appointments
-- WHERE date(start_datetime) = '2025-11-25';
--
-- Get appointments that are synced:
-- SELECT * FROM appointments
-- WHERE synced_to_calendar = 1 AND google_event_id IS NOT NULL;
--
-- Get sync history for an appointment:
-- SELECT * FROM sync_log
-- WHERE appointment_id = 1
-- ORDER BY synced_at DESC;
