import datetime
import random
import pickle
import sqlite3
from database.db_manager import get_db_connection


class VisitorModel:

    # ------------------------------------------------------------------
    # ID / CODE GENERATION
    # ------------------------------------------------------------------
    @staticmethod
    def generate_visitor_code():
        """Generate a sequential unique visitor code in the format VIS-YYYYMMDD-XXXX."""
        today_str = datetime.date.today().strftime("%Y%m%d")
        prefix = f"VIS-{today_str}-"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT visitor_code FROM visitors WHERE visitor_code LIKE ? ORDER BY id DESC LIMIT 1;",
            (prefix + "%",)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            try:
                seq = int(row[0].split("-")[-1])
                new_seq = seq + 1
            except (ValueError, IndexError):
                new_seq = random.randint(1000, 9999)
        else:
            new_seq = 1

        return f"{prefix}{new_seq:04d}"

    @staticmethod
    def generate_visitor_id():
        """Generate a unique visitor code for a new registration session."""
        return VisitorModel.generate_visitor_code()

    # ------------------------------------------------------------------
    # DUPLICATE CHECK
    # ------------------------------------------------------------------
    @staticmethod
    def is_duplicate_visitor(mobile):
        """
        Check if a visitor with the given mobile is already registered.
        Returns the visitor dict (with status) if found, else None.
        """
        return VisitorModel.get_visitor_by_mobile(mobile)

    # ------------------------------------------------------------------
    # REGISTER
    # ------------------------------------------------------------------
    @staticmethod
    def register_visitor(data):
        """
        Insert a new visitor record plus a pending visit row to store host/dept/purpose.
        data keys: full_name, gender, mobile, email, address, company_name,
                   purpose, employee_id, department_id, id_proof_type, photo_path,
                   visitor_code (optional, auto-generated if absent)
        Returns (visitor_id, visitor_code).
        """
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate code if not supplied
        visitor_code = data.get('visitor_code') or VisitorModel.generate_visitor_code()

        # Serialise face encoding blob (optional)
        face_blob = None
        if data.get('face_encoding') is not None:
            try:
                face_blob = sqlite3.Binary(pickle.dumps(data['face_encoding']))
            except Exception as e:
                print(f"[VisitorModel] Error serializing face encoding: {e}")

        # Check if visitor already exists by mobile or email
        cursor.execute("SELECT id FROM visitors WHERE mobile = ?;", (data['mobile'],))
        existing_mobile = cursor.fetchone()

        existing_email = None
        if data.get('email'):
            cursor.execute("SELECT id FROM visitors WHERE email = ?;", (data['email'],))
            existing_email = cursor.fetchone()

        existing = existing_mobile or existing_email

        if existing:
            visitor_id = existing['id']
            # Update basic info to the latest name
            cursor.execute("""
                UPDATE visitors
                SET full_name = ?, gender = ?, email = ?, address = ?,
                    company = ?, photo_path = ?, face_encoding = ?
                WHERE id = ?;
            """, (
                data['full_name'], data['gender'],
                data.get('email'), data.get('address'),
                data.get('company_name'),
                data.get('photo_path'), face_blob,
                visitor_id
            ))
            # Cancel any previous visits that are pending or approved but not active/completed
            cursor.execute("""
                UPDATE visits
                SET status = 'cancelled', approval_status = 'rejected'
                WHERE visitor_id = ? AND status = 'cancelled';
            """, (visitor_id,))
            # If matched by email but not mobile, attempt to update mobile as well
            if not existing_mobile and existing_email:
                try:
                    cursor.execute("UPDATE visitors SET mobile = ? WHERE id = ?;", (data['mobile'], visitor_id))
                except sqlite3.IntegrityError:
                    pass
        else:
            cursor.execute("""
                INSERT INTO visitors (
                    visitor_code, full_name, gender, mobile, email, address,
                    company, photo_path, face_encoding
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                visitor_code,
                data['full_name'], data['gender'], data['mobile'],
                data.get('email'), data.get('address'),
                data.get('company_name'),
                data.get('photo_path'), face_blob
            ))
            visitor_id = cursor.lastrowid

        # Insert pending visit — awaiting host approval before QR/check-in allowed
        now = datetime.datetime.now()

        employee_id  = data.get('employee_id')
        department_id = data.get('department_id')

        # If department_id wasn't supplied, look it up from the employee record
        if not department_id and employee_id:
            cursor.execute("SELECT department_id FROM employees WHERE id = ?;", (employee_id,))
            emp_row = cursor.fetchone()
            if emp_row and emp_row['department_id']:
                department_id = emp_row['department_id']

        # Final safety fallback: use the first available department
        if not department_id:
            cursor.execute("SELECT id FROM departments LIMIT 1;")
            dept_row = cursor.fetchone()
            department_id = dept_row['id'] if dept_row else 1

        if not employee_id:
            raise ValueError("employee_id is required to register a visit.")

        cursor.execute("""
            INSERT INTO visits (
                visitor_id, employee_id, department_id, purpose,
                entry_date, entry_time, status, approval_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'cancelled', 'pending');
        """, (
            visitor_id,
            employee_id,
            department_id,
            data.get('purpose', 'Meeting'),
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S")
        ))

        conn.commit()
        conn.close()
        return visitor_id, visitor_code

    # ------------------------------------------------------------------
    # FETCH HELPERS  (single visitor)
    # ------------------------------------------------------------------
    _VISITOR_SELECT = """
        SELECT
            v.id,
            v.visitor_code,
            v.full_name,
            v.gender,
            v.mobile,
            v.email,
            v.address,
            v.company        AS company_name,
            v.photo_path,
            v.face_encoding,
            COALESCE(vt.purpose, 'Meeting')   AS purpose,
            vt.employee_id,
            e.full_name                        AS employee_name,
            vt.department_id,
            d.name                             AS department_name,
            COALESCE(vt.approval_status, 'pending') AS approval_status,
            CASE
                WHEN vt.status = 'active'     THEN 'CheckedIn'
                WHEN vt.status = 'completed'  THEN 'CheckedOut'
                ELSE 'Registered'
            END AS status,
            (vt.entry_date || ' ' || vt.entry_time) AS check_in_time,
            vt.exit_time                       AS check_out_time,
            vt.duration_minutes
        FROM visitors v
        LEFT JOIN (
            SELECT * FROM visits
            WHERE id IN (SELECT MAX(id) FROM visits GROUP BY visitor_id)
        ) vt ON v.id = vt.visitor_id
        LEFT JOIN employees e ON vt.employee_id = e.id
        LEFT JOIN departments d ON vt.department_id = d.id
    """

    @staticmethod
    def _row_to_dict(row):
        if row is None:
            return None
        v = dict(row)
        if v.get('face_encoding') is not None:
            try:
                v['face_encoding'] = pickle.loads(v['face_encoding'])
            except Exception:
                v['face_encoding'] = None
        return v

    @staticmethod
    def get_visitor_by_id(v_id):
        """Fetch a single visitor by integer id or visitor_code string."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            VisitorModel._VISITOR_SELECT + " WHERE v.id = ? OR v.visitor_code = ?;",
            (v_id, str(v_id))
        )
        row = cursor.fetchone()
        conn.close()
        return VisitorModel._row_to_dict(row)

    @staticmethod
    def get_visitor_by_mobile(mobile):
        """Find a visitor by mobile number."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            VisitorModel._VISITOR_SELECT + " WHERE v.mobile = ?;",
            (mobile,)
        )
        row = cursor.fetchone()
        conn.close()
        return VisitorModel._row_to_dict(row)

    @staticmethod
    def get_visitor_by_code(visitor_code):
        """Find a visitor by their unique visitor_code."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            VisitorModel._VISITOR_SELECT + " WHERE v.visitor_code = ?;",
            (visitor_code,)
        )
        row = cursor.fetchone()
        conn.close()
        return VisitorModel._row_to_dict(row)

    # ------------------------------------------------------------------
    # PAGINATED LIST
    # ------------------------------------------------------------------
    @staticmethod
    def get_visitors_paginated(limit=15, offset=0, search_query=None, filters=None):
        """Fetch visitors with pagination, optional search filter, and optional date filters."""
        conn = get_db_connection()
        cursor = conn.cursor()

        query = VisitorModel._VISITOR_SELECT
        where_clauses = []
        params = []

        if search_query:
            where_clauses.append("(v.full_name LIKE ? OR v.mobile LIKE ? OR v.company LIKE ? OR v.visitor_code LIKE ?)")
            pat = f"%{search_query}%"
            params.extend([pat, pat, pat, pat])

        if filters:
            if 'date_from' in filters and filters['date_from']:
                where_clauses.append("vt.entry_date >= ?")
                params.append(filters['date_from'])
            if 'date_to' in filters and filters['date_to']:
                where_clauses.append("vt.entry_date <= ?")
                params.append(filters['date_to'])

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY v.id DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [VisitorModel._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # CHECK-IN / CHECK-OUT
    # ------------------------------------------------------------------
    @staticmethod
    def check_in_visitor(visitor_id, operator_id=None):
        """Create an active visit record for the visitor."""
        conn = get_db_connection()
        cursor = conn.cursor()

        # Prevent double check-in
        cursor.execute(
            "SELECT id FROM visits WHERE visitor_id = ? AND status = 'active';",
            (visitor_id,)
        )
        if cursor.fetchone():
            conn.close()
            raise ValueError("Visitor is already checked in.")

        # Check if there is an approved but not yet active/completed visit
        cursor.execute("""
            SELECT id FROM visits 
            WHERE visitor_id = ? AND approval_status = 'approved' AND status = 'cancelled'
            ORDER BY id DESC LIMIT 1;
        """, (visitor_id,))
        pending_row = cursor.fetchone()

        now = datetime.datetime.now()
        if pending_row:
            # Activate the existing approved visit record
            cursor.execute("""
                UPDATE visits
                SET status = 'active',
                    entry_date = ?,
                    entry_time = ?
                WHERE id = ?;
            """, (now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), pending_row['id']))
        else:
            # Fallback: Copy host/dept/purpose from last visit and insert a new active visit
            cursor.execute("""
                SELECT employee_id, department_id, purpose
                FROM visits
                WHERE visitor_id = ?
                ORDER BY id DESC LIMIT 1;
            """, (visitor_id,))
            row = cursor.fetchone()

            employee_id   = row['employee_id']   if row else 1
            department_id = row['department_id'] if row else 1
            purpose       = row['purpose']       if row else 'Meeting'

            cursor.execute("""
                INSERT INTO visits (
                    visitor_id, employee_id, department_id, purpose,
                    entry_date, entry_time, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'active');
            """, (visitor_id, employee_id, department_id, purpose,
                  now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))

        conn.commit()
        conn.close()
        return True

    @staticmethod
    def check_out_visitor(visitor_id, operator_id=None):
        """Mark the active visit as completed and record exit time."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM visits WHERE visitor_id = ? AND status = 'active' ORDER BY id DESC LIMIT 1;",
            (visitor_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            raise ValueError("No active visit record found for this visitor.")

        visit_id = row['id']
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE visits
            SET exit_time = ?, status = 'completed'
            WHERE id = ?;
        """, (now_str, visit_id))

        conn.commit()
        conn.close()
        return True

    # ------------------------------------------------------------------
    # APPROVAL WORKFLOW
    # ------------------------------------------------------------------
    @staticmethod
    def get_pending_visits():
        """Return all visits awaiting host approval."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                vt.id           AS visit_id,
                vt.visitor_id,
                vt.employee_id,
                vt.department_id,
                vt.purpose,
                vt.entry_date,
                vt.entry_time,
                vt.approval_status,
                v.visitor_code,
                v.full_name     AS visitor_name,
                v.mobile,
                v.company       AS company_name,
                e.full_name     AS employee_name,
                d.name          AS department_name
            FROM visits vt
            JOIN visitors v    ON vt.visitor_id    = v.id
            JOIN employees e   ON vt.employee_id   = e.id
            JOIN departments d ON vt.department_id = d.id
            WHERE vt.approval_status = 'pending'
            ORDER BY vt.id DESC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def approve_visit(visit_id, approved_by_user_id, qr_code_path=None):
        """Approve a pending visit: set approval_status=approved and store QR path."""
        conn = get_db_connection()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE visits
            SET approval_status = 'approved',
                approved_by     = ?,
                approved_at     = ?,
                qr_code_path    = COALESCE(?, qr_code_path)
            WHERE id = ?;
        """, (approved_by_user_id, now_str, qr_code_path, visit_id))
        conn.commit()
        conn.close()

    @staticmethod
    def reject_visit(visit_id, approved_by_user_id):
        """Reject a pending visit: set approval_status=rejected, status=cancelled."""
        conn = get_db_connection()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("""
            UPDATE visits
            SET approval_status = 'rejected',
                status          = 'cancelled',
                approved_by     = ?,
                approved_at     = ?
            WHERE id = ?;
        """, (approved_by_user_id, now_str, visit_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_visit_approval_status(visitor_id):
        """Return the approval_status of the most recent visit for a visitor."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT approval_status, qr_code_path
            FROM visits
            WHERE visitor_id = ?
            ORDER BY id DESC LIMIT 1;
        """, (visitor_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
