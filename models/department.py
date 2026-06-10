from database.db_manager import get_db_connection

class DepartmentModel:
    @staticmethod
    def get_active_departments():
        """Retrieve list of active departments."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, head_name, floor, extension 
            FROM departments 
            WHERE is_active = 1 
            ORDER BY name ASC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_employees_by_department(dept_id):
        """Retrieve all active employees for a department."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, emp_code, full_name, email, phone, designation 
            FROM employees 
            WHERE department_id = ? AND is_active = 1 
            ORDER BY full_name ASC;
        """, (dept_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_all_employees():
        """Retrieve list of all active employees."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.emp_code, e.full_name, e.email, e.phone, e.designation, d.name as department_name
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE e.is_active = 1
            ORDER BY e.full_name ASC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_employee_by_id(emp_id):
        """Fetch details of a single employee by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.emp_code, e.full_name, e.email, e.phone, e.designation, d.name as department_name, e.department_id
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE e.id = ?;
        """, (emp_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
