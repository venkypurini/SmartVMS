import os
import sys
import unittest
import datetime

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from web.app import app
from database.db_manager import get_db_connection
from models.user import UserModel
from models.visitor import VisitorModel
from models.checkin import VisitModel

class TestAdminPortal(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.secret_key = 'smartvms_admin_session_secret_key_98765'
        self.app = app.test_client()
        
        # Ensure we have a test admin user and seed reference data
        conn = get_db_connection()
        
        # Clean up any previously inserted test employees to prevent duplicate errors
        conn.execute("DELETE FROM employees WHERE phone IN ('9876543210', '1234567890') OR email IN ('unique@test.com', 'dup@test.com', 'emp1@test.com', 'emp2@test.com');")
        conn.commit()
        
        # 1. Create admin operator
        row = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
        if not row:
            from models.user import hash_password
            conn.execute("""
                INSERT INTO users (username, full_name, email, password_hash, role, is_active)
                VALUES ('admin', 'System Admin', 'admin@example.com', ?, 'admin', 1);
            """, (hash_password('admin123'),))
        
        # 2. Create department
        d_row = conn.execute("SELECT id FROM departments LIMIT 1").fetchone()
        if d_row:
            self.dept_id = d_row['id']
        else:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO departments (name, head_name, floor) VALUES ('Admin Dept', 'Manager', '1st');")
            self.dept_id = cursor.lastrowid
            
        # 3. Create employee
        e_row = conn.execute("SELECT id FROM employees LIMIT 1").fetchone()
        if e_row:
            self.emp_id = e_row['id']
        else:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employees (emp_code, full_name, email, phone, department_id)
                VALUES ('EMP001', 'Host Person', 'host@example.com', '1234567890', ?);
            """, (self.dept_id,))
            self.emp_id = cursor.lastrowid
            
        conn.commit()
        conn.close()

    def test_unauthorized_dashboard_redirects(self):
        # Accessing dashboard without session should redirect to login page
        response = self.app.get('/admin', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login', response.location)

    def test_unauthorized_register_is_public(self):
        # Accessing visitor register page without session should succeed (200)
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Self Registration', response.data)

    def test_unauthorized_root_redirects(self):
        # Accessing root without session should redirect to dashboard (which redirects to login)
        response = self.app.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin', response.location)

    def test_login_page_renders(self):
        response = self.app.get('/admin/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Operator Web Administration Portal', response.data)

    def test_invalid_login(self):
        response = self.app.post('/admin/login', data={
            'username': 'admin',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid username or password', response.data)

    def test_valid_login_and_dashboard(self):
        with self.app as c:
            response = c.post('/admin/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'SmartVMS - Web Admin Console', response.data)
            
            from flask import session
            self.assertEqual(session.get('username'), 'admin')

            # Now test dashboard loads with user details
            response2 = c.get('/admin')
            self.assertEqual(response2.status_code, 200)
            self.assertIn(b'System Admin', response2.data)

    def test_actions_approve_reject_checkout(self):
        # 1. Create a pending visitor and visit
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Unique mobile and visitor code to avoid conflicts
        timestamp = int(datetime.datetime.now().timestamp())
        mobile = f"999{timestamp}"
        vis_code = f"VIS-TEST-{timestamp}"
        
        # Insert visitor
        cursor.execute("""
            INSERT INTO visitors (visitor_code, full_name, gender, mobile, email, company, photo_path)
            VALUES (?, 'Test Visitor', 'Male', ?, 'visitor@test.com', 'Test Corp', 'id_document.jpg');
        """, (vis_code, mobile))
        visitor_id = cursor.lastrowid
        
        # Insert pending visit
        cursor.execute("""
            INSERT INTO visits (visitor_id, employee_id, department_id, purpose, entry_date, entry_time, status, approval_status)
            VALUES (?, ?, ?, 'Test Meeting', '2026-06-10', '10:00:00', 'cancelled', 'pending');
        """, (visitor_id, self.emp_id, self.dept_id))
        visit_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Log in first to establish session
        with self.app as c:
            login_res = c.post('/admin/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=False)
            self.assertEqual(login_res.status_code, 302) # Redirect to dashboard
            
            # 2. Test Approval Endpoint
            approve_res = c.post(f'/admin/approve/{visit_id}', follow_redirects=True)
            self.assertEqual(approve_res.status_code, 200)
            self.assertIn(b'Successfully approved visit', approve_res.data)
            
            # Check DB state - should be approved
            visit_details = VisitModel.get_visit_by_id(visit_id)
            self.assertEqual(visit_details['approval_status'], 'approved')
            
            # 3. Simulate check-in (making visitor active on site)
            # Web dashboard checkout works on active visits. Let's make it active:
            conn = get_db_connection()
            conn.execute("UPDATE visits SET status = 'active' WHERE id = ?;", (visit_id,))
            conn.commit()
            conn.close()
            
            # 4. Test Checkout Endpoint
            checkout_res = c.post(f'/admin/checkout/{visit_id}', follow_redirects=True)
            self.assertEqual(checkout_res.status_code, 200)
            self.assertIn(b'Checked out visitor Test Visitor successfully', checkout_res.data)
            
            # Check DB state - should be completed
            visit_details_2 = VisitModel.get_visit_by_id(visit_id)
            self.assertEqual(visit_details_2['status'], 'completed')
            self.assertIsNotNone(visit_details_2['exit_time'])

    def test_employee_validation_compulsory_10_digits(self):
        # Log in first
        with self.app as c:
            c.post('/admin/login', data={
                'username': 'admin',
                'password': 'admin123'
            }, follow_redirects=False)

            # 1. Test invalid phone number (less than 10 digits)
            res = c.post('/admin/employee/add', data={
                'full_name': 'Test Emp 1',
                'email': 'emp1@test.com',
                'phone': '123456789', # 9 digits
                'designation': 'Staff',
                'department_id': self.dept_id
            }, follow_redirects=True)
            self.assertIn(b'Phone number must be exactly 10 digits.', res.data)

            # 2. Test invalid phone number (more than 10 digits)
            res = c.post('/admin/employee/add', data={
                'full_name': 'Test Emp 2',
                'email': 'emp2@test.com',
                'phone': '12345678901', # 11 digits
                'designation': 'Staff',
                'department_id': self.dept_id
            }, follow_redirects=True)
            self.assertIn(b'Phone number must be exactly 10 digits.', res.data)

            # 3. Test duplicate phone number
            # First insert an employee with valid phone
            res = c.post('/admin/employee/add', data={
                'full_name': 'Unique Emp',
                'email': 'unique@test.com',
                'phone': '9876543210', # 10 digits
                'designation': 'Staff',
                'department_id': self.dept_id
            }, follow_redirects=True)
            self.assertIn(b'Successfully registered employee Unique Emp', res.data)

            # Now try to insert another with duplicate phone
            res = c.post('/admin/employee/add', data={
                'full_name': 'Duplicate Emp',
                'email': 'dup@test.com',
                'phone': '9876543210', # Same phone
                'designation': 'Staff',
                'department_id': self.dept_id
            }, follow_redirects=True)
            self.assertIn(b'Mobile number already exists for another employee.', res.data)

    def test_visitor_duplicate_registration_updates_name_and_cancels_previous(self):
        # 1. Register a visitor first time: Name = John, Email = john@test.com
        res1 = self.app.post('/register', data={
            'visitor_name': 'John Doe First',
            'mobile': '1112223333',
            'email': 'john@test.com',
            'company': 'First Co',
            'purpose': 'First Visit',
            'host_id': self.emp_id
        })
        self.assertEqual(res1.status_code, 200)
        
        # Verify first visit is created and is pending
        conn = get_db_connection()
        first_visit = conn.execute("""
            SELECT v.id, v.visitor_id, vis.full_name, v.approval_status, v.status
            FROM visits v
            JOIN visitors vis ON v.visitor_id = vis.id
            WHERE vis.email = 'john@test.com'
            ORDER BY v.id DESC LIMIT 1;
        """).fetchone()
        self.assertIsNotNone(first_visit)
        self.assertEqual(first_visit['full_name'], 'John Doe First')
        self.assertEqual(first_visit['approval_status'], 'pending')
        self.assertEqual(first_visit['status'], 'cancelled') # waiting for check-in
        
        # Approve the first visit
        conn.execute("UPDATE visits SET approval_status = 'approved' WHERE id = ?;", (first_visit['id'],))
        conn.commit()
        
        # 2. Register same visitor second time with a different name but same email: Jane
        res2 = self.app.post('/register', data={
            'visitor_name': 'Jane Doe Latest',
            'mobile': '1112223333',
            'email': 'john@test.com',
            'company': 'Latest Co',
            'purpose': 'Latest Visit',
            'host_id': self.emp_id
        })
        self.assertEqual(res2.status_code, 200)
        
        # Verify visitor name is updated in the database to the latest
        visitor = conn.execute("SELECT full_name FROM visitors WHERE email = 'john@test.com';").fetchone()
        self.assertEqual(visitor['full_name'], 'Jane Doe Latest')
        
        # Verify the first visit is now rejected/cancelled
        old_visit = conn.execute("SELECT approval_status, status FROM visits WHERE id = ?;", (first_visit['id'],)).fetchone()
        self.assertEqual(old_visit['approval_status'], 'rejected')
        self.assertEqual(old_visit['status'], 'cancelled')
        
        # Verify the new visit is pending and belongs to Jane
        latest_visit = conn.execute("""
            SELECT v.id, v.visitor_id, vis.full_name, v.approval_status, v.status
            FROM visits v
            JOIN visitors vis ON v.visitor_id = vis.id
            WHERE vis.email = 'john@test.com'
            ORDER BY v.id DESC LIMIT 1;
        """).fetchone()
        self.assertNotEqual(latest_visit['id'], first_visit['id'])
        self.assertEqual(latest_visit['full_name'], 'Jane Doe Latest')
        self.assertEqual(latest_visit['approval_status'], 'pending')
        
        # Clean up database
        conn.execute("DELETE FROM visits WHERE visitor_id = ?;", (first_visit['visitor_id'],))
        conn.execute("DELETE FROM visitors WHERE id = ?;", (first_visit['visitor_id'],))
        conn.commit()
        conn.close()

if __name__ == '__main__':
    unittest.main()
