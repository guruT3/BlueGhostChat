import os
import sqlite3
import threading
import time
from datetime import datetime, timedelta

class DatabaseManager:
    """SQLite Database Manager for BlueGhost Anonymous Bluetooth Chat."""
    
    def __init__(self, db_path='blueghost.db', uploads_dir='uploads'):
        self.db_path = db_path
        self.uploads_dir = uploads_dir
        os.makedirs(self.uploads_dir, exist_ok=True)
        self.init_db()
        self._start_cleanup_thread()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize required database tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    msg_id TEXT UNIQUE NOT NULL,
                    sender_ghost TEXT NOT NULL,
                    receiver_ghost TEXT NOT NULL,
                    content TEXT,
                    msg_type TEXT DEFAULT 'text',
                    file_path TEXT,
                    file_name TEXT,
                    file_size INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    self_destruct_seconds INTEGER DEFAULT 0,
                    expires_at DATETIME,
                    status TEXT DEFAULT 'sent'
                )
            ''')

            # Devices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    address TEXT UNIQUE NOT NULL,
                    ghost_name TEXT NOT NULL,
                    ble_name TEXT,
                    rssi INTEGER DEFAULT -70,
                    distance REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'available',
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Temporary files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS temporary_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME
                )
            ''')
            conn.commit()

    def save_message(self, msg_id, sender_ghost, receiver_ghost, content, msg_type='text', 
                     file_path=None, file_name=None, file_size=0, self_destruct_seconds=0):
        """Save a new message with optional self-destruct timer."""
        expires_at = None
        if self_destruct_seconds and self_destruct_seconds > 0:
            expires_at = (datetime.utcnow() + timedelta(seconds=self_destruct_seconds)).strftime('%Y-%m-%d %H:%M:%S')

        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (
                    msg_id, sender_ghost, receiver_ghost, content, msg_type,
                    file_path, file_name, file_size, timestamp, self_destruct_seconds, expires_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'sent')
            ''', (msg_id, sender_ghost, receiver_ghost, content, msg_type, 
                  file_path, file_name, file_size, timestamp, self_destruct_seconds, expires_at))
            conn.commit()

        return {
            'msg_id': msg_id,
            'sender_ghost': sender_ghost,
            'receiver_ghost': receiver_ghost,
            'content': content,
            'msg_type': msg_type,
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_size,
            'timestamp': timestamp,
            'self_destruct_seconds': self_destruct_seconds,
            'expires_at': expires_at,
            'status': 'sent'
        }

    def get_chat_history(self, ghost_1, ghost_2, limit=50):
        """Retrieve recent non-expired messages between two ghosts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                SELECT * FROM messages 
                WHERE ((sender_ghost = ? AND receiver_ghost = ?) OR (sender_ghost = ? AND receiver_ghost = ?))
                AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY id ASC LIMIT ?
            ''', (ghost_1, ghost_2, ghost_2, ghost_1, now, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def mark_messages_read(self, sender_ghost, receiver_ghost):
        """Mark messages sent by sender to receiver as read."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages SET status = 'read'
                WHERE sender_ghost = ? AND receiver_ghost = ? AND status != 'read'
            ''', (sender_ghost, receiver_ghost))
            conn.commit()

    def update_or_create_device(self, address, ghost_name, ble_name, rssi, distance, status='available'):
        """Upsert detected BLE device."""
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO devices (address, ghost_name, ble_name, rssi, distance, status, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(address) DO UPDATE SET
                    ghost_name = excluded.ghost_name,
                    ble_name = excluded.ble_name,
                    rssi = excluded.rssi,
                    distance = excluded.distance,
                    status = excluded.status,
                    last_seen = excluded.last_seen
            ''', (address, ghost_name, ble_name, rssi, distance, status, now))
            conn.commit()

    def get_known_devices(self):
        """Get all registered nearby devices."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM devices ORDER BY rssi DESC')
            return [dict(row) for row in cursor.fetchall()]

    def delete_expired_messages(self):
        """Find and remove messages whose self-destruct timers have passed."""
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        expired_msgs = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT msg_id, file_path FROM messages
                WHERE expires_at IS NOT NULL AND expires_at <= ?
            ''', (now,))
            rows = cursor.fetchall()
            expired_msgs = [dict(row) for row in rows]

            if expired_msgs:
                for msg in expired_msgs:
                    if msg['file_path'] and os.path.exists(msg['file_path']):
                        try:
                            os.remove(msg['file_path'])
                        except Exception:
                            pass
                cursor.execute('DELETE FROM messages WHERE expires_at IS NOT NULL AND expires_at <= ?', (now,))
                conn.commit()
        return [m['msg_id'] for m in expired_msgs]

    def _start_cleanup_thread(self):
        """Background daemon thread to auto-delete expired self-destruct messages."""
        def run_loop():
            while True:
                try:
                    self.delete_expired_messages()
                except Exception:
                    pass
                time.sleep(3)

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
