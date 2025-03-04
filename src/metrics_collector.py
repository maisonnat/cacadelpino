import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

class MetricsCollector:
    """Class for collecting and storing metrics about account performance."""
    
    def __init__(self, database_path: str = 'metrics.db'):
        self.database_path = database_path
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Create accounts table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                username TEXT PRIMARY KEY,
                last_login TIMESTAMP,
                total_logins INTEGER DEFAULT 0,
                successful_logins INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                last_points INTEGER DEFAULT 0
            )
            ''')
            
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                success BOOLEAN,
                points_earned INTEGER DEFAULT 0,
                daily_sets_completed INTEGER DEFAULT 0,
                more_activities_completed INTEGER DEFAULT 0,
                errors_encountered INTEGER DEFAULT 0,
                captchas_encountered INTEGER DEFAULT 0,
                rate_limits_encountered INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES accounts(username)
            )
            ''')
            
            # Create errors table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS errors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                username TEXT,
                timestamp TIMESTAMP,
                error_type TEXT,
                error_message TEXT,
                html_dump_path TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (username) REFERENCES accounts(username)
            )
            ''')
            
            conn.commit()
            conn.close()
            logging.info(f"Database initialized at {self.database_path}")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
    
    def register_account(self, username: str) -> None:
        """Register a new account in the database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check if account already exists
            cursor.execute("SELECT username FROM accounts WHERE username = ?", (username,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO accounts (username, last_login, total_logins) VALUES (?, ?, ?)",
                    (username, datetime.now().isoformat(), 0)
                )
                logging.info(f"Registered new account: {username}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error registering account {username}: {e}")
    
    def start_session(self, username: str) -> int:
        """Start a new session for an account and return the session ID."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Register account if not exists
            self.register_account(username)
            
            # Update account login stats
            cursor.execute(
                "UPDATE accounts SET last_login = ?, total_logins = total_logins + 1 WHERE username = ?",
                (datetime.now().isoformat(), username)
            )
            
            # Create new session
            cursor.execute(
                "INSERT INTO sessions (username, start_time, success) VALUES (?, ?, ?)",
                (username, datetime.now().isoformat(), False)
            )
            
            session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logging.info(f"Started session {session_id} for account {username}")
            return session_id
        except Exception as e:
            logging.error(f"Error starting session for {username}: {e}")
            return -1
    
    def end_session(self, session_id: int, success: bool, metrics: Dict) -> None:
        """End a session and update metrics."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute("SELECT username FROM sessions WHERE id = ?", (session_id,))
            result = cursor.fetchone()
            if not result:
                logging.error(f"Session {session_id} not found")
                conn.close()
                return
                
            username = result[0]
            
            # Update session
            cursor.execute(
                """UPDATE sessions SET 
                    end_time = ?, 
                    success = ?, 
                    points_earned = ?, 
                    daily_sets_completed = ?, 
                    more_activities_completed = ?, 
                    errors_encountered = ?, 
                    captchas_encountered = ?, 
                    rate_limits_encountered = ? 
                WHERE id = ?""",
                (
                    datetime.now().isoformat(),
                    success,
                    metrics.get('points_earned', 0),
                    metrics.get('daily_sets_completed', 0),
                    metrics.get('more_activities_completed', 0),
                    metrics.get('errors_encountered', 0),
                    metrics.get('captchas_encountered', 0),
                    metrics.get('rate_limits_encountered', 0),
                    session_id
                )
            )
            
            # Update account metrics if successful
            if success:
                cursor.execute(
                    "UPDATE accounts SET successful_logins = successful_logins + 1, total_points = total_points + ?, last_points = ? WHERE username = ?",
                    (metrics.get('points_earned', 0), metrics.get('final_points', 0), username)
                )
            
            conn.commit()
            conn.close()
            
            logging.info(f"Ended session {session_id} for account {username} with success={success}")
        except Exception as e:
            logging.error(f"Error ending session {session_id}: {e}")
    
    def log_error(self, session_id: int, username: str, error_type: str, error_message: str, html_dump_path: Optional[str] = None) -> None:
        """Log an error encountered during a session."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO errors (session_id, username, timestamp, error_type, error_message, html_dump_path) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, username, datetime.now().isoformat(), error_type, error_message, html_dump_path)
            )
            
            # Also increment the errors counter in the session
            cursor.execute(
                "UPDATE sessions SET errors_encountered = errors_encountered + 1 WHERE id = ?",
                (session_id,)
            )
            
            conn.commit()
            conn.close()
            
            logging.info(f"Logged error for session {session_id}, account {username}: {error_type}")
        except Exception as e:
            logging.error(f"Error logging error for session {session_id}: {e}")
    
    def get_account_stats(self, username: str) -> Dict:
        """Get statistics for a specific account."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get account info
            cursor.execute("SELECT * FROM accounts WHERE username = ?", (username,))
            account = cursor.fetchone()
            if not account:
                conn.close()
                return {}
            
            account_data = {
                'username': account[0],
                'last_login': account[1],
                'total_logins': account[2],
                'successful_logins': account[3],
                'total_points': account[4],
                'last_points': account[5],
                'success_rate': account[3] / account[2] if account[2] > 0 else 0
            }
            
            # Get session stats
            cursor.execute(
                """SELECT 
                    COUNT(*) as total_sessions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_sessions,
                    SUM(points_earned) as total_points_earned,
                    SUM(errors_encountered) as total_errors,
                    SUM(captchas_encountered) as total_captchas,
                    SUM(rate_limits_encountered) as total_rate_limits
                FROM sessions WHERE username = ?""",
                (username,)
            )
            
            session_stats = cursor.fetchone()
            if session_stats:
                account_data.update({
                    'total_sessions': session_stats[0],
                    'successful_sessions': session_stats[1],
                    'session_success_rate': session_stats[1] / session_stats[0] if session_stats[0] > 0 else 0,
                    'total_points_earned': session_stats[2],
                    'total_errors': session_stats[3],
                    'total_captchas': session_stats[4],
                    'total_rate_limits': session_stats[5]
                })
            
            # Get recent errors
            cursor.execute(
                "SELECT error_type, error_message, timestamp FROM errors WHERE username = ? ORDER BY timestamp DESC LIMIT 5",
                (username,)
            )
            
            recent_errors = [{
                'error_type': row[0],
                'error_message': row[1],
                'timestamp': row[2]
            } for row in cursor.fetchall()]
            
            account_data['recent_errors'] = recent_errors
            
            conn.close()
            return account_data
        except Exception as e:
            logging.error(f"Error getting stats for account {username}: {e}")
            return {}
    
    def get_all_accounts_summary(self) -> List[Dict]:
        """Get summary statistics for all accounts."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT username FROM accounts ORDER BY total_points DESC")
            usernames = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return [self.get_account_stats(username) for username in usernames]
        except Exception as e:
            logging.error(f"Error getting all accounts summary: {e}")
            return []
    
    def get_error_patterns(self) -> Dict:
        """Analyze error patterns across all accounts."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get error type distribution
            cursor.execute(
                """SELECT 
                    error_type, 
                    COUNT(*) as count 
                FROM errors 
                GROUP BY error_type 
                ORDER BY count DESC"""
            )
            
            error_types = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get accounts with most errors
            cursor.execute(
                """SELECT 
                    username, 
                    COUNT(*) as error_count 
                FROM errors 
                GROUP BY username 
                ORDER BY error_count DESC 
                LIMIT 5"""
            )
            
            accounts_with_most_errors = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Get time distribution of errors
            cursor.execute(
                """SELECT 
                    strftime('%H', timestamp) as hour, 
                    COUNT(*) as count 
                FROM errors 
                GROUP BY hour 
                ORDER BY hour"""
            )
            
            errors_by_hour = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'error_types': error_types,
                'accounts_with_most_errors': accounts_with_most_errors,
                'errors_by_hour': errors_by_hour
            }
        except Exception as e:
            logging.error(f"Error analyzing error patterns: {e}")
            return {}

# Example usage
if __name__ == "__main__":
    collector = MetricsCollector()
    
    # Register test account
    collector.register_account("test@example.com")
    
    # Start session
    session_id = collector.start_session("test@example.com")
    
    # Log some errors
    collector.log_error(session_id, "test@example.com", "CAPTCHA", "CAPTCHA detected")
    collector.log_error(session_id, "test@example.com", "RATE_LIMIT", "Too many requests")
    
    # End session
    collector.end_session(session_id, True, {
        'points_earned': 50,
        'daily_sets_completed': 3,
        'more_activities_completed': 2,
        'errors_encountered': 2,
        'captchas_encountered': 1,
        'rate_limits_encountered': 1,
        'final_points': 500
    })
    
    # Get stats
    stats = collector.get_account_stats("test@example.com")
    print(f"Account stats: {stats}")
    
    # Get error patterns
    patterns = collector.get_error_patterns()
    print(f"Error patterns: {patterns}")