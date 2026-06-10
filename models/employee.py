from database.db_manager import get_db_connection


class EmployeeModel:

    @staticmethod
    def get_all_departments():
        """Fetch all active departments."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM departments WHERE is_active = 1 ORDER BY name ASC;")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_employees_by_department(dept_id):
        """Fetch all active employees belonging to a specific department."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, full_name AS name, email, phone AS mobile
            FROM employees
            WHERE department_id = ? AND is_active = 1
            ORDER BY full_name ASC;
        """, (dept_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_all_employees():
        """Fetch all active employees with their department names."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.full_name AS name, e.email, e.phone AS mobile,
                   d.name AS department_name, e.department_id
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
        """Fetch a single employee by ID."""
        if emp_id is None:
            return None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.full_name AS name, e.email, e.phone AS mobile,
                   d.name AS department_name, e.department_id
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            WHERE e.id = ?;
        """, (emp_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
