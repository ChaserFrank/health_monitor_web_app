"""
Database Tests for Health Monitoring System
"""
import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_postgres import PostgresDBManager
import config


class TestDatabaseOperations(unittest.TestCase):
    """Test database operations"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Use test database configuration
        test_config = {
            'host': 'localhost',
            'database': 'health_monitor_test',
            'user': 'postgres',
            'password': 'password',
            'port': '5432'
        }

        # Temporarily override config
        cls.original_config = config.DB_CONFIG
        config.DB_CONFIG = test_config

        # Create test database
        cls.db = PostgresDBManager()

        # Clear test data
        cls.db.cursor.execute("DELETE FROM health_metrics")
        cls.db.cursor.execute("DELETE FROM alerts")
        cls.db.cursor.execute("DELETE FROM users")
        cls.db.connection.commit()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        # Restore original config
        config.DB_CONFIG = cls.original_config
        cls.db.close()

    def setUp(self):
        """Set up before each test"""
        # Clear tables
        self.db.cursor.execute("DELETE FROM health_metrics")
        self.db.cursor.execute("DELETE FROM alerts")
        self.db.cursor.execute("DELETE FROM users")
        self.db.connection.commit()

    def test_user_operations(self):
        """Test user CRUD operations"""
        # Add user
        user_id = self.db.add_user(
            name="Test User",
            age=30,
            gender="Male",
            email="test@example.com",
            phone="+1234567890"
        )

        self.assertIsNotNone(user_id)
        self.assertGreater(user_id, 0)

        # Get user by email
        user_data = self.db.get_user_by_email("test@example.com")
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data[1], "Test User")  # Name
        self.assertEqual(user_data[2], 30)  # Age

        # Test duplicate email
        with self.assertRaises(Exception):
            self.db.add_user(
                name="Duplicate",
                age=25,
                gender="Female",
                email="test@example.com"
            )

    def test_health_metric_operations(self):
        """Test health metric CRUD operations"""
        # First add a user
        user_id = self.db.add_user(
            name="Test User",
            age=30,
            gender="Male",
            email="test@example.com"
        )

        # Add BP metric
        metric_id = self.db.add_health_metric(
            user_id=user_id,
            metric_type="BP",
            systolic=120,
            diastolic=80,
            notes="Morning reading"
        )

        self.assertIsNotNone(metric_id)
        self.assertGreater(metric_id, 0)

        # Add glucose metric
        glucose_id = self.db.add_health_metric(
            user_id=user_id,
            metric_type="Glucose",
            glucose_level=95.5,
            is_fasting=True
        )

        # Get user metrics
        metrics = self.db.get_user_metrics(user_id)
        self.assertEqual(len(metrics), 2)

        # Filter by type
        bp_metrics = self.db.get_user_metrics(user_id, metric_type="BP")
        self.assertEqual(len(bp_metrics), 1)

        # Test with high BP (should create alert)
        alert_bp_id = self.db.add_health_metric(
            user_id=user_id,
            metric_type="BP",
            systolic=150,
            diastolic=95
        )

        # Check if alert was created
        self.db.cursor.execute(
            "SELECT COUNT(*) FROM alerts WHERE user_id = %s",
            (user_id,)
        )
        alert_count = self.db.cursor.fetchone()[0]
        self.assertGreater(alert_count, 0)

    def test_health_stats(self):
        """Test health statistics calculation"""
        # Add user and metrics
        user_id = self.db.add_user(
            name="Stats User",
            age=35,
            gender="Female",
            email="stats@example.com"
        )

        # Add multiple metrics
        self.db.add_health_metric(user_id, "BP", systolic=120, diastolic=80)
        self.db.add_health_metric(user_id, "BP", systolic=118, diastolic=78)
        self.db.add_health_metric(user_id, "Glucose", glucose_level=95.5)
        self.db.add_health_metric(user_id, "Exercise", exercise_minutes=45)

        # Get statistics
        stats = self.db.get_health_stats(user_id)

        self.assertIn('blood_pressure', stats)
        self.assertIn('glucose', stats)
        self.assertIn('exercise', stats)
        self.assertIn('unread_alerts', stats)

        # Check specific stats
        if stats['blood_pressure'].get('readings_count', 0) > 0:
            self.assertIsNotNone(stats['blood_pressure']['avg_systolic'])
            self.assertIsNotNone(stats['blood_pressure']['avg_diastolic'])

    def test_error_handling(self):
        """Test database error handling"""
        # Test invalid user data
        with self.assertRaises(Exception):
            self.db.add_user(
                name="",  # Empty name
                age=30,
                gender="Male",
                email="invalid@example.com"
            )

        # Test invalid metric data
        user_id = self.db.add_user(
            name="Test",
            age=30,
            gender="Male",
            email="test2@example.com"
        )

        with self.assertRaises(Exception):
            self.db.add_health_metric(
                user_id=user_id,
                metric_type="BP",
                systolic=300,  # Invalid value
                diastolic=200  # Invalid value
            )


class TestDatabaseTransactions(unittest.TestCase):
    """Test database transactions"""

    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        test_config = {
            'host': 'localhost',
            'database': 'health_monitor_test',
            'user': 'postgres',
            'password': 'password',
            'port': '5432'
        }

        cls.original_config = config.DB_CONFIG
        config.DB_CONFIG = test_config
        cls.db = PostgresDBManager()

    def test_transaction_rollback(self):
        """Test that transactions roll back on error"""
        # Start transaction
        self.db.connection.autocommit = False

        try:
            # Add user
            user_id = self.db.add_user(
                name="Transaction User",
                age=30,
                gender="Male",
                email="transaction@example.com"
            )

            # This should fail and rollback
            self.db.add_health_metric(
                user_id=user_id,
                metric_type="InvalidType",  # Invalid type
                invalid_field="value"
            )

            # Should not reach here
            self.fail("Should have raised exception")

        except Exception:
            # Exception was raised, transaction should be rolled back
            self.db.connection.rollback()

            # Verify user was not added (due to rollback)
            self.db.cursor.execute(
                "SELECT COUNT(*) FROM users WHERE email = %s",
                ("transaction@example.com",)
            )
            count = self.db.cursor.fetchone()[0]
            self.assertEqual(count, 0)

        finally:
            self.db.connection.autocommit = True


if __name__ == '__main__':
    unittest.main()