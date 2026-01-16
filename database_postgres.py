"""
PostgreSQL Database Support Module
Handles all database operations using PostgreSQL with psycopg2
"""
import psycopg2
import psycopg2.extras  # Add this import
from psycopg2 import sql, Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import datetime
import json  # Add json module
from typing import List, Tuple, Optional, Dict, Any
import os

class PostgresDBManager:
    """Manages PostgreSQL database connection and operations"""

    def __init__(self, db_config=None):
        """Initialize PostgreSQL database connection"""
        try:
            # Get database configuration
            if db_config is None:
                # Try to import DB_CONFIG, but provide defaults if it fails
                try:
                    from config import DB_CONFIG
                    db_config = DB_CONFIG
                except ImportError:
                    # Default configuration if config.py doesn't exist
                    from dotenv import load_dotenv
                    load_dotenv()
                    db_config = {
                        'host': os.getenv('DB_HOST', 'localhost'),
                        'database': os.getenv('DB_NAME', 'health_monitor_db'),
                        'user': os.getenv('DB_USER', 'postgres'),
                        'password': os.getenv('DB_PASSWORD', 'password'),
                        'port': os.getenv('DB_PORT', '5432')
                    }

            self.db_config = db_config

            # First, connect to default database to check/create our database
            self._create_database_if_not_exists()

            # Now connect to our specific database
            self.connection = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port']
            )
            self.connection.autocommit = False
            self.cursor = self.connection.cursor()

            # Enable UUID extension if needed
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")

            self._create_tables()
            print("✅ Connected to PostgreSQL database successfully!")

        except Error as e:
            print(f"❌ Error connecting to PostgreSQL database: {e}")
            print("Troubleshooting tips:")
            print("1. Make sure PostgreSQL is running")
            print("2. Check your database credentials")
            print("3. Verify the database exists")
            raise

    def _create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        try:
            # Connect to default 'postgres' database
            conn = psycopg2.connect(
                host=self.db_config['host'],
                database='postgres',
                user=self.db_config['user'],
                password=self.db_config['password'],
                port=self.db_config['port']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s",
                         (self.db_config['database'],))

            if not cursor.fetchone():
                # Create the database
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(self.db_config['database'])
                ))
                print(f"✅ Created database: {self.db_config['database']}")

            cursor.close()
            conn.close()

        except Error as e:
            print(f"Error checking/creating database: {e}")
            raise

    def _create_tables(self):
        """Create all necessary tables with constraints and indexes"""

        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INTEGER CHECK(age > 0 AND age < 150),
                gender VARCHAR(10) CHECK(gender IN ('Male', 'Female', 'Other')),
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')

        # Create index on email for faster lookups
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_users_email 
            ON users(email);
        ''')

        # Health metrics table - using JSONB for flexible metric storage
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_metrics (
                metric_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                metric_type VARCHAR(20) NOT NULL CHECK(
                    metric_type IN ('BP', 'Glucose', 'Weight', 'Exercise', 'Heart_Rate')
                ),
                
                -- Blood Pressure fields
                systolic INTEGER CHECK(systolic IS NULL OR systolic BETWEEN 50 AND 250),
                diastolic INTEGER CHECK(diastolic IS NULL OR diastolic BETWEEN 30 AND 150),
                
                -- Glucose fields
                glucose_level DECIMAL(5,2) CHECK(glucose_level IS NULL OR glucose_level BETWEEN 20 AND 600),
                is_fasting BOOLEAN DEFAULT TRUE,
                
                -- Weight fields
                weight DECIMAL(5,2) CHECK(weight IS NULL OR weight BETWEEN 20 AND 300),
                height DECIMAL(4,1) CHECK(height IS NULL OR height BETWEEN 100 AND 250),
                
                -- Exercise fields
                exercise_minutes INTEGER CHECK(exercise_minutes IS NULL OR exercise_minutes BETWEEN 0 AND 1440),
                activity_type VARCHAR(50),
                
                -- Heart Rate fields
                heart_rate INTEGER CHECK(heart_rate IS NULL OR heart_rate BETWEEN 30 AND 220),
                
                -- Common fields
                recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                
                -- Store all data in JSONB for flexibility
                metric_data JSONB,
                
                -- Composite check to ensure at least one metric value is provided
                CHECK (
                    (systolic IS NOT NULL AND diastolic IS NOT NULL) OR
                    glucose_level IS NOT NULL OR
                    weight IS NOT NULL OR
                    exercise_minutes IS NOT NULL OR
                    heart_rate IS NOT NULL
                )
            )
        ''')

        # Create indexes for faster queries
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_user_date 
            ON health_metrics(user_id, recorded_date DESC);
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_type 
            ON health_metrics(metric_type);
        ''')

        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metrics_data 
            ON health_metrics USING GIN (metric_data);
        ''')

        # Alerts table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                alert_type VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                severity VARCHAR(10) CHECK(severity IN ('Low', 'Medium', 'High', 'Critical')),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                resolved BOOLEAN DEFAULT FALSE,
                resolved_date TIMESTAMP
            )
        ''')

        # Create index for unread alerts
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_alerts_user_unread 
            ON alerts(user_id) WHERE NOT is_read;
        ''')

        # Health goals table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_goals (
                goal_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                goal_type VARCHAR(50) NOT NULL,
                target_value DECIMAL(10,2),
                current_value DECIMAL(10,2),
                start_date DATE DEFAULT CURRENT_DATE,
                end_date DATE,
                is_completed BOOLEAN DEFAULT FALSE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User authentication table (simplified for demo)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_auth (
                auth_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                password_hash VARCHAR(255) NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Commit table creation
        self.connection.commit()
        print("✅ Database tables created/verified successfully!")

    def add_user(self, name: str, age: int, gender: str, email: str, phone: str = None) -> int:
        """Add a new user to the database"""
        try:
            self.cursor.execute('''
                INSERT INTO users (name, age, gender, email, phone)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id
            ''', (name, age, gender, email, phone))

            user_id = self.cursor.fetchone()[0]
            self.connection.commit()
            return user_id

        except Error as e:
            self.connection.rollback()
            if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
                raise ValueError(f"Email already exists: {email}") from e
            elif 'check constraint' in str(e).lower():
                raise ValueError(f"Invalid data: {e}") from e
            else:
                raise Exception(f"Database error: {e}") from e
        except Exception as e:
            self.connection.rollback()
            raise

    def get_user_by_email(self, email: str) -> Optional[Tuple]:
        """Get user by email"""
        try:
            self.cursor.execute('''
                SELECT user_id, name, age, gender, email, phone, created_date
                FROM users 
                WHERE email = %s AND is_active = TRUE
            ''', (email,))

            return self.cursor.fetchone()
        except Error as e:
            print(f"Error fetching user: {e}")
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    def add_health_metric(self, user_id: int, metric_type: str, **kwargs) -> int:
        """Add a health metric reading with transaction support"""
        try:
            # Prepare metric data for JSONB storage
            metric_data = {
                'user_id': user_id,
                'metric_type': metric_type,
                'recorded_date': datetime.datetime.now().isoformat(),
                **kwargs
            }

            # Build the query based on metric type
            if metric_type == 'BP':
                query = '''
                    INSERT INTO health_metrics 
                    (user_id, metric_type, systolic, diastolic, notes, metric_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING metric_id
                '''
                values = (
                    user_id,
                    metric_type,
                    kwargs.get('systolic'),
                    kwargs.get('diastolic'),
                    kwargs.get('notes', ''),
                    json.dumps(metric_data)
                )

            elif metric_type == 'Glucose':
                query = '''
                    INSERT INTO health_metrics 
                    (user_id, metric_type, glucose_level, is_fasting, notes, metric_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING metric_id
                '''
                values = (
                    user_id,
                    metric_type,
                    kwargs.get('glucose_level'),
                    kwargs.get('is_fasting', True),
                    kwargs.get('notes', ''),
                    json.dumps(metric_data)
                )

            elif metric_type == 'Weight':
                query = '''
                    INSERT INTO health_metrics 
                    (user_id, metric_type, weight, height, notes, metric_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING metric_id
                '''
                values = (
                    user_id,
                    metric_type,
                    kwargs.get('weight'),
                    kwargs.get('height'),
                    kwargs.get('notes', ''),
                    json.dumps(metric_data)
                )

            elif metric_type == 'Exercise':
                query = '''
                    INSERT INTO health_metrics 
                    (user_id, metric_type, exercise_minutes, activity_type, notes, metric_data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING metric_id
                '''
                values = (
                    user_id,
                    metric_type,
                    kwargs.get('exercise_minutes'),
                    kwargs.get('activity_type', 'General'),
                    kwargs.get('notes', ''),
                    json.dumps(metric_data)
                )

            else:
                # Generic insert for other metric types
                query = '''
                    INSERT INTO health_metrics 
                    (user_id, metric_type, heart_rate, notes, metric_data)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING metric_id
                '''
                values = (
                    user_id,
                    metric_type,
                    kwargs.get('heart_rate'),
                    kwargs.get('notes', ''),
                    json.dumps(metric_data)
                )

            self.cursor.execute(query, values)
            metric_id = self.cursor.fetchone()[0]

            # Check for abnormal readings and create alerts
            self._check_for_alerts(user_id, metric_type, kwargs)

            self.connection.commit()
            return metric_id

        except Error as e:
            self.connection.rollback()
            print(f"Error adding health metric: {e}")
            raise
        except Exception as e:
            self.connection.rollback()
            print(f"Error adding health metric: {e}")
            raise

    def _check_for_alerts(self, user_id: int, metric_type: str, data: dict):
        """Check metric data and create alerts if abnormal"""
        try:
            if metric_type == 'BP':
                systolic = data.get('systolic')
                diastolic = data.get('diastolic')

                if systolic and diastolic:
                    if systolic > 140 or diastolic > 90:
                        self.cursor.execute('''
                            INSERT INTO alerts (user_id, alert_type, message, severity)
                            VALUES (%s, %s, %s, %s)
                        ''', (
                            user_id, 'High Blood Pressure',
                            f'High BP detected: {systolic}/{diastolic} mmHg. Consider consulting a doctor.',
                            'High'
                        ))
                    elif systolic < 90 or diastolic < 60:
                        self.cursor.execute('''
                            INSERT INTO alerts (user_id, alert_type, message, severity)
                            VALUES (%s, %s, %s, %s)
                        ''', (
                            user_id, 'Low Blood Pressure',
                            f'Low BP detected: {systolic}/{diastolic} mmHg.',
                            'Medium'
                        ))

            elif metric_type == 'Glucose':
                glucose = data.get('glucose_level')
                is_fasting = data.get('is_fasting', True)

                if glucose:
                    if is_fasting and glucose > 126:
                        self.cursor.execute('''
                            INSERT INTO alerts (user_id, alert_type, message, severity)
                            VALUES (%s, %s, %s, %s)
                        ''', (
                            user_id, 'High Fasting Glucose',
                            f'High fasting glucose: {glucose} mg/dL. May indicate diabetes risk.',
                            'High'
                        ))
                    elif is_fasting and glucose < 70:
                        self.cursor.execute('''
                            INSERT INTO alerts (user_id, alert_type, message, severity)
                            VALUES (%s, %s, %s, %s)
                        ''', (
                            user_id, 'Low Fasting Glucose',
                            f'Low glucose: {glucose} mg/dL. Consider eating a snack.',
                            'Medium'
                        ))

        except Exception as e:
            print(f"Warning: Could not create alert: {e}")

    def get_user_metrics(self, user_id: int, metric_type: str = None,
                        limit: int = 100, offset: int = 0) -> List[Tuple]:
        """Retrieve user's health metrics with pagination"""
        try:
            query = '''
                SELECT 
                    metric_id, metric_type,
                    systolic, diastolic,
                    glucose_level, is_fasting,
                    weight, height,
                    exercise_minutes, activity_type,
                    heart_rate,
                    recorded_date, notes
                FROM health_metrics 
                WHERE user_id = %s
            '''

            params = [user_id]

            if metric_type:
                query += " AND metric_type = %s"
                params.append(metric_type)

            query += " ORDER BY recorded_date DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            self.cursor.execute(query, params)
            return self.cursor.fetchall()

        except Error as e:
            print(f"Error fetching metrics: {e}")
            return []
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return []

    def get_health_stats(self, user_id: int) -> dict:
        """Get comprehensive health statistics for a user"""
        try:
            stats = {}

            # Get average BP
            self.cursor.execute('''
                SELECT 
                    AVG(systolic) as avg_systolic,
                    AVG(diastolic) as avg_diastolic,
                    COUNT(*) as bp_count
                FROM health_metrics 
                WHERE user_id = %s AND metric_type = 'BP'
                AND recorded_date >= CURRENT_DATE - INTERVAL '30 days'
            ''', (user_id,))

            bp_stats = self.cursor.fetchone()
            stats['blood_pressure'] = {
                'avg_systolic': float(bp_stats[0]) if bp_stats[0] else None,
                'avg_diastolic': float(bp_stats[1]) if bp_stats[1] else None,
                'readings_count': bp_stats[2] or 0
            }

            # Get glucose stats
            self.cursor.execute('''
                SELECT 
                    AVG(glucose_level) as avg_glucose,
                    COUNT(*) as glucose_count
                FROM health_metrics 
                WHERE user_id = %s AND metric_type = 'Glucose'
                AND recorded_date >= CURRENT_DATE - INTERVAL '30 days'
            ''', (user_id,))

            glucose_stats = self.cursor.fetchone()
            stats['glucose'] = {
                'avg_level': float(glucose_stats[0]) if glucose_stats[0] else None,
                'readings_count': glucose_stats[1] or 0
            }

            # Get exercise stats
            self.cursor.execute('''
                SELECT 
                    SUM(exercise_minutes) as total_exercise,
                    COUNT(*) as exercise_days
                FROM health_metrics 
                WHERE user_id = %s AND metric_type = 'Exercise'
                AND recorded_date >= CURRENT_DATE - INTERVAL '30 days'
            ''', (user_id,))

            exercise_stats = self.cursor.fetchone()
            stats['exercise'] = {
                'total_minutes': exercise_stats[0] or 0,
                'days_count': exercise_stats[1] or 0
            }

            # Get unread alerts count
            self.cursor.execute('''
                SELECT COUNT(*) 
                FROM alerts 
                WHERE user_id = %s AND NOT is_read
            ''', (user_id,))

            stats['unread_alerts'] = self.cursor.fetchone()[0] or 0

            return stats

        except Error as e:
            print(f"Error getting stats: {e}")
            return {
                'blood_pressure': {'avg_systolic': None, 'avg_diastolic': None, 'readings_count': 0},
                'glucose': {'avg_level': None, 'readings_count': 0},
                'exercise': {'total_minutes': 0, 'days_count': 0},
                'unread_alerts': 0
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                'blood_pressure': {'avg_systolic': None, 'avg_diastolic': None, 'readings_count': 0},
                'glucose': {'avg_level': None, 'readings_count': 0},
                'exercise': {'total_minutes': 0, 'days_count': 0},
                'unread_alerts': 0
            }

    def execute_query(self, query: str, params: tuple = None):
        """Execute a custom query (for advanced operations)"""
        try:
            self.cursor.execute(query, params or ())

            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount

        except Error as e:
            self.connection.rollback()
            print(f"Query execution error: {e}")
            raise
        except Exception as e:
            self.connection.rollback()
            print(f"Query execution error: {e}")
            raise

    def close(self):
        """Close database connection"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                print("✅ Database connection closed.")
        except:
            pass  # Ignore errors during cleanup