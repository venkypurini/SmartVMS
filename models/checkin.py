import datetime
from database.db_manager import get_db_connection

class VisitModel:
    @staticmethod
    def create_visit(visitor_id, employee_id, department_id, purpose, qr_code_path=None):
        """Create a new check-in visit record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        entry_date = now.strftime("%Y-%m-%d")
        entry_time = now.strftime("%H:%M:%S")

        cursor.execute("""
            INSERT INTO visits (
                visitor_id, employee_id, department_id, purpose, 
                entry_date, entry_time, status, qr_code_path, host_notified
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', ?, 0);
        """, (visitor_id, employee_id, department_id, purpose, entry_date, entry_time, qr_code_path))
        
        visit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return visit_id

    @staticmethod
    def complete_visit(visit_id):
        """Perform a check-out, updating exit_time and setting status to completed.
        SQLite trigger trg_update_visit_duration calculates duration_minutes automatically."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE visits
            SET exit_time = ?, status = 'completed'
            WHERE id = ?;
        """, (now_str, visit_id))
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def cancel_visit(visit_id):
        """Cancel an active visit."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE visits
            SET status = 'cancelled'
            WHERE id = ?;
        """, (visit_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_visit(visit_id):
        """Completely delete a visit record from the database."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM visits WHERE id = ?;", (visit_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_visits(visit_ids):
        """Completely delete multiple visit records from the database."""
        if not visit_ids:
            return True
        conn = get_db_connection()
        cursor = conn.cursor()
        placeholders = ",".join("?" for _ in visit_ids)
        cursor.execute(f"DELETE FROM visits WHERE id IN ({placeholders});", tuple(visit_ids))
        conn.commit()
        conn.close()
        return True


    @staticmethod
    def get_visit_by_id(visit_id):
        """Fetch details of a single visit record."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.*, vis.full_name as visitor_name, vis.visitor_code, vis.mobile as visitor_mobile,
                   e.full_name as employee_name, d.name as department_name
            FROM visits v
            JOIN visitors vis ON v.visitor_id = vis.id
            JOIN employees e ON v.employee_id = e.id
            JOIN departments d ON v.department_id = d.id
            WHERE v.id = ?;
        """, (visit_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_active_visit_by_visitor(visitor_id):
        """Check if a visitor has an active visit currently inside the premises."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, visitor_id, status 
            FROM visits 
            WHERE visitor_id = ? AND status = 'active';
        """, (visitor_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_visits_history(limit=50, offset=0, filters=None):
        """Fetch historical records of visits with full joins and dynamic filters."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT v.id, v.purpose, v.entry_date, v.entry_time, v.exit_time, v.duration_minutes, v.status,
                   vis.visitor_code, vis.full_name as visitor_name, vis.mobile as visitor_mobile, vis.company as visitor_company,
                   e.full_name as employee_name, d.name as department_name
            FROM visits v
            JOIN visitors vis ON v.visitor_id = vis.id
            JOIN employees e ON v.employee_id = e.id
            JOIN departments d ON v.department_id = d.id
        """
        
        where_clauses = []
        params = []
        
        if filters:
            if filters.get('search'):
                search_pat = f"%{filters['search']}%"
                where_clauses.append("(vis.full_name LIKE ? OR vis.visitor_code LIKE ? OR vis.mobile LIKE ?)")
                params.extend([search_pat, search_pat, search_pat])
            if filters.get('status'):
                where_clauses.append("v.status = ?")
                params.append(filters['status'])
            if filters.get('department_id'):
                where_clauses.append("v.department_id = ?")
                params.append(filters['department_id'])
            if filters.get('date_from'):
                where_clauses.append("v.entry_date >= ?")
                params.append(filters['date_from'])
            if filters.get('date_to'):
                where_clauses.append("v.entry_date <= ?")
                params.append(filters['date_to'])
                
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " ORDER BY v.id DESC LIMIT ? OFFSET ?;"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_visits_count(filters=None):
        """Get total count of visits matching filters."""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT COUNT(*) 
            FROM visits v
            JOIN visitors vis ON v.visitor_id = vis.id
        """
        
        where_clauses = []
        params = []
        
        if filters:
            if filters.get('search'):
                search_pat = f"%{filters['search']}%"
                where_clauses.append("(vis.full_name LIKE ? OR vis.visitor_code LIKE ? OR vis.mobile LIKE ?)")
                params.extend([search_pat, search_pat, search_pat])
            if filters.get('status'):
                where_clauses.append("v.status = ?")
                params.append(filters['status'])
            if filters.get('department_id'):
                where_clauses.append("v.department_id = ?")
                params.append(filters['department_id'])
            if filters.get('date_from'):
                where_clauses.append("v.entry_date >= ?")
                params.append(filters['date_from'])
            if filters.get('date_to'):
                where_clauses.append("v.entry_date <= ?")
                params.append(filters['date_to'])
                
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def get_daily_stats():
        """Retrieve today's metrics from the vw_daily_stats view."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vw_daily_stats;")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        else:
            return {
                'stat_date': datetime.date.today().strftime("%Y-%m-%d"),
                'today_total': 0,
                'active_total': 0,
                'completed_today': 0,
                'cancelled_today': 0
            }

    @staticmethod
    def get_weekly_stats():
        """Retrieve visitor trends from the vw_weekly_stats view."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vw_weekly_stats;")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_dashboard_counters():
        """Retrieve daily, weekly, monthly aggregates for stats dashboard."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM visits WHERE entry_date = date('now', 'localtime')) AS today_total,
                (SELECT COUNT(*) FROM visits WHERE status = 'active') AS active_visitors,
                (SELECT COUNT(*) FROM visits WHERE status = 'completed' AND date(exit_time) = date('now', 'localtime')) AS checked_out_today,
                (SELECT COUNT(*) FROM visits WHERE date(entry_date) >= date('now', 'localtime', '-6 days')) AS weekly_total,
                (SELECT COUNT(*) FROM visits WHERE date(entry_date) >= date('now', 'localtime', '-29 days')) AS monthly_total;
        """)
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return {
            'today_total': 0,
            'active_visitors': 0,
            'checked_out_today': 0,
            'weekly_total': 0,
            'monthly_total': 0
        }

    @staticmethod
    def get_weekly_trend_data():
        """Retrieve weekly trend of visitors over rolling 7 days."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT entry_date AS date, COUNT(*) AS count
            FROM visits
            WHERE date(entry_date) >= date('now', 'localtime', '-6 days')
            GROUP BY entry_date
            ORDER BY entry_date ASC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_department_chart_data():
        """Retrieve visitor traffic groupings by department."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.name AS department_name, COUNT(*) AS count
            FROM visits v
            JOIN departments d ON v.department_id = d.id
            GROUP BY d.id
            ORDER BY count DESC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_hourly_chart_data():
        """Retrieve visitor traffic distribution by check-in hour."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT strftime('%H:00', entry_time) AS hour, COUNT(*) AS count
            FROM visits
            GROUP BY hour
            ORDER BY hour ASC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
