from database.db_manager import get_db_connection


class AuditLogModel:

    @staticmethod
    def log_event(user_id, action, details=None, module="System"):
        """Insert a system event into the audit logs table."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, module, details)
                VALUES (?, ?, ?, ?);
            """, (user_id, action, module, details))
            conn.commit()
        except Exception as e:
            print(f"[AuditLog] Failed to log event: {e}")
        finally:
            conn.close()

    @staticmethod
    def get_logs(limit=100, offset=0, search_query=None):
        """Fetch audit logs with join on users, supporting search and pagination."""
        conn = get_db_connection()
        cursor = conn.cursor()

        base_query = """
            SELECT l.id, l.action, l.module, l.details, l.timestamp,
                   u.username, u.role
            FROM audit_logs l
            LEFT JOIN users u ON l.user_id = u.id
        """

        params = []
        if search_query:
            base_query += " WHERE l.action LIKE ? OR l.details LIKE ? OR u.username LIKE ?"
            like_pat = f"%{search_query}%"
            params.extend([like_pat, like_pat, like_pat])

        base_query += " ORDER BY l.timestamp DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])

        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count(search_query=None):
        """Get total count of audit logs matching search query."""
        conn = get_db_connection()
        cursor = conn.cursor()

        base_query = """
            SELECT COUNT(*)
            FROM audit_logs l
            LEFT JOIN users u ON l.user_id = u.id
        """

        params = []
        if search_query:
            base_query += " WHERE l.action LIKE ? OR l.details LIKE ? OR u.username LIKE ?"
            like_pat = f"%{search_query}%"
            params.extend([like_pat, like_pat, like_pat])

        cursor.execute(base_query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def delete_logs(log_ids):
        """Completely delete multiple audit logs from the database by ID."""
        if not log_ids:
            return True
        conn = get_db_connection()
        try:
            placeholders = ",".join("?" for _ in log_ids)
            conn.execute(f"DELETE FROM audit_logs WHERE id IN ({placeholders});", tuple(log_ids))
            conn.commit()
        finally:
            conn.close()
        return True

