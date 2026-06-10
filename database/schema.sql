-- Enforce Foreign Keys
PRAGMA foreign_keys = ON;

-- 1. Users Table (Operators)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('admin', 'security', 'receptionist')) NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 2. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    head_name TEXT,
    floor TEXT,
    extension TEXT,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1))
);

-- 3. Employees Table (Hosts)
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_code TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT NOT NULL,
    department_id INTEGER,
    designation TEXT,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- 4. Visitors Table
CREATE TABLE IF NOT EXISTS visitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_code TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    gender TEXT NOT NULL,
    mobile TEXT UNIQUE NOT NULL,
    email TEXT,
    address TEXT,
    company TEXT,
    photo_path TEXT,
    id_proof_path TEXT,
    face_encoding BLOB, -- Holds numpy array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Visits Table (Check-In/Out Tracking)
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    purpose TEXT NOT NULL,
    entry_date TEXT NOT NULL, -- Format: YYYY-MM-DD
    entry_time TEXT NOT NULL, -- Format: HH:MM:SS
    exit_time TEXT,           -- Format: YYYY-MM-DD HH:MM:SS
    duration_minutes INTEGER,
    status TEXT CHECK(status IN ('active', 'completed', 'cancelled')) DEFAULT 'active',
    approval_status TEXT CHECK(approval_status IN ('pending', 'approved', 'rejected')) DEFAULT 'pending',
    approved_by INTEGER,      -- references users.id
    approved_at TIMESTAMP,
    qr_code_path TEXT,
    host_notified INTEGER DEFAULT 0 CHECK(host_notified IN (0, 1)),
    FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 6. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    module TEXT NOT NULL,
    details TEXT, -- Stores JSON as plain text
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 7. System Settings Table
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    visitor_id INTEGER,
    employee_id INTEGER,
    type TEXT NOT NULL, -- 'email', 'sms', 'system'
    message TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'sent', 'failed')),
    FOREIGN KEY (visitor_id) REFERENCES visitors(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- ==========================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_visitors_mobile ON visitors(mobile);
CREATE INDEX IF NOT EXISTS idx_visitors_code ON visitors(visitor_code);
CREATE INDEX IF NOT EXISTS idx_visits_status ON visits(status);
CREATE INDEX IF NOT EXISTS idx_visits_entry ON visits(entry_date, entry_time);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);

-- ==========================================
-- TRIGGERS
-- ==========================================
-- Auto-calculate duration_minutes when exit_time is updated (Check-Out)
CREATE TRIGGER IF NOT EXISTS trg_update_visit_duration
AFTER UPDATE OF exit_time ON visits
FOR EACH ROW
WHEN NEW.exit_time IS NOT NULL AND NEW.entry_date IS NOT NULL AND NEW.entry_time IS NOT NULL
BEGIN
    UPDATE visits
    SET duration_minutes = CAST((strftime('%s', NEW.exit_time) - strftime('%s', NEW.entry_date || ' ' || NEW.entry_time)) / 60 AS INTEGER)
    WHERE id = NEW.id;
END;

-- ==========================================
-- ANALYTICS VIEWS
-- ==========================================
-- 1. Daily Stats View
CREATE VIEW IF NOT EXISTS vw_daily_stats AS
SELECT 
    date('now', 'localtime') AS stat_date,
    (SELECT COUNT(*) FROM visits WHERE entry_date = date('now', 'localtime')) AS today_total,
    (SELECT COUNT(*) FROM visits WHERE status = 'active') AS active_total,
    (SELECT COUNT(*) FROM visits WHERE status = 'completed' AND date(exit_time) = date('now', 'localtime')) AS completed_today,
    (SELECT COUNT(*) FROM visits WHERE status = 'cancelled' AND entry_date = date('now', 'localtime')) AS cancelled_today;

-- 2. Weekly Stats View (Visitor counts for last 7 days)
CREATE VIEW IF NOT EXISTS vw_weekly_stats AS
SELECT 
    entry_date AS visit_date,
    COUNT(*) AS visitor_count,
    SUM(case when status = 'completed' then 1 else 0 end) AS completed_count,
    SUM(case when status = 'active' then 1 else 0 end) AS active_count
FROM visits
WHERE date(entry_date) >= date('now', 'localtime', '-6 days')
GROUP BY entry_date
ORDER BY entry_date ASC;
