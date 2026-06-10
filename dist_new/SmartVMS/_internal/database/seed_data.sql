-- Seed Departments (starter templates — add your own in the Employees tab)
INSERT INTO departments (name, is_active) VALUES
('Executive Suite',       1),
('Human Resources',       1),
('Information Technology',1),
('Finance Department',    1),
('Operations Division',   1);

-- NOTE: No employees are seeded.
-- All employees (hosts) must be registered manually through the 👤 Employees tab.

-- Seed Users (Operators / System Logins)
-- admin / admin123
-- reception / reception123
-- security / security123
INSERT INTO users (username, full_name, email, password_hash, role, is_active) VALUES
('admin',     'System Administrator',     'admin@smartvms.com',     '$2b$12$KPcxEswWeZpJ90BYNS1s6uZag6Bf.vv58UJ3aiiW.EAyyFveC8.7G', 'admin',        1),
('reception', 'Reception Desk Operator',  'reception@smartvms.com', '$2b$12$02NeR2BiHrNQrW8QDtg3v.oKUE/XIXOQph/XxPbOgyO8MiDIB8xae', 'receptionist', 1),
('security',  'Gate Security Officer',    'security@smartvms.com',  '$2b$12$S8nknhN3vzeIl4j9SUjNqeujpK3MK3r.pUDoiV32NrLIqFjop8rhy', 'security',     1);

-- Seed System Settings
INSERT INTO system_settings (key, value) VALUES
('app_name',               'Smart VMS'),
('version',                '1.0.0'),
('allow_unknown_visitors', '0'),
('save_raw_photos',        '1'),
('auto_checkout_minutes',  '480');
