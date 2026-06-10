import datetime
import hashlib
import sqlite3
from database.db_manager import get_db_connection

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

def hash_password(password):
    """Hash a password using bcrypt if available, otherwise SHA-256."""
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    else:
        # Fallback SHA-256 with simple salt
        salt = "vms_secure_salt_string_"
        return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def verify_password(password, hashed_val):
    """Verify a password against its hash."""
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_val.encode('utf-8'))
        except Exception:
            pass
    
    salt = "vms_secure_salt_string_"
    fallback_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
    return fallback_hash == hashed_val

class UserModel:
    @staticmethod
    def generate_session_token(user_id):
        import secrets
        token = secrets.token_hex(32)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET session_token = ? WHERE id = ?;", (token, user_id))
        conn.commit()
        conn.close()
        return token

    @staticmethod
    def authenticate_by_token(token):
        if not token:
            return None
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, email, role, is_active 
            FROM users 
            WHERE session_token = ? AND is_active = 1;
        """, (token,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user_data = dict(row)
            UserModel.update_last_login(user_data['id'])
            return user_data
        return None

    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate an operator by username or email and return user profile details."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, username, full_name, email, password_hash, role, is_active 
            FROM users 
            WHERE (username = ? OR email = ?) AND is_active = 1;
        """, (username_or_email, username_or_email))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            user_data = dict(row)
            if verify_password(password, user_data['password_hash']):
                # Update last login time
                UserModel.update_last_login(user_data['id'])
                del user_data['password_hash']
                return user_data
        return None

    @staticmethod
    def update_last_login(user_id):
        """Update last_login timestamp on successful authentication."""
        conn = get_db_connection()
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?;", (now_str, user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def create_user(username, fullname, email, password, role):
        """Register a new system operator."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            pwd_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, full_name, email, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, ?, 1);
            """, (username, fullname, email, pwd_hash, role))
            conn.commit()
            success = True
            err_msg = ""
        except sqlite3.IntegrityError:
            success = False
            err_msg = f"Operator username '{username}' already exists."
        except Exception as e:
            success = False
            err_msg = str(e)
        finally:
            conn.close()
        return success, err_msg

    @staticmethod
    def get_all_users():
        """Retrieve list of system operators."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, full_name, email, role, is_active, created_at, last_login FROM users ORDER BY username ASC;")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def delete_user(user_id):
        """Remove an operator account."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()
        conn.close()
        return True
