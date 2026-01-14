"""
Web Application Tests for Health Monitoring System
"""
import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db_manager, WebUser
from flask import url_for, session
import json


class TestWebApplication(unittest.TestCase):
    """Test web application routes and functionality"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

        # Clear test data
        with app.app_context():
            db_manager.cursor.execute("DELETE FROM health_metrics")
            db_manager.cursor.execute("DELETE FROM alerts")
            db_manager.cursor.execute("DELETE FROM users")
            db_manager.connection.commit()

    def test_home_page(self):
        """Test home page accessibility"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Health Monitor Pro', response.data)

    def test_registration_page(self):
        """Test registration page"""
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create Account', response.data)

    def test_login_page(self):
        """Test login page"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)

    def test_dashboard_redirect_when_not_logged_in(self):
        """Test that dashboard redirects to login when not authenticated"""
        response = self.app.get('/dashboard', follow_redirects=False)
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertIn('/login', response.location)

    def test_api_endpoints_require_auth(self):
        """Test that API endpoints require authentication"""
        endpoints = ['/api/metrics', '/api/add_metric']

        for endpoint in endpoints:
            response = self.app.get(endpoint)
            self.assertIn(response.status_code, [302, 401])  # Redirect or unauthorized

    def test_404_page(self):
        """Test 404 error handling"""
        response = self.app.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
        self.assertIn(b'Page not found', response.data)


class TestUserAuthentication(unittest.TestCase):
    """Test user authentication flows"""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Clear test data
        with app.app_context():
            db_manager.cursor.execute("DELETE FROM health_metrics")
            db_manager.cursor.execute("DELETE FROM alerts")
            db_manager.cursor.execute("DELETE FROM users")
            db_manager.connection.commit()

            # Add test user
            try:
                user_id = db_manager.add_user(
                    name="Test User",
                    age=30,
                    gender="Male",
                    email="test@example.com",
                    phone="+1234567890"
                )

                # Add test auth (simplified)
                db_manager.cursor.execute(
                    "INSERT INTO user_auth (user_id, password_hash) VALUES (%s, %s)",
                    (user_id, 'test_hash')
                )
                db_manager.connection.commit()

            except Exception as e:
                print(f"Setup error: {e}")
                db_manager.connection.rollback()

    def test_successful_login(self):
        """Test successful login"""
        with self.app:
            # For demo, we're not checking passwords
            response = self.app.post('/login', data={
                'email': 'test@example.com',
                'password': 'anypassword'
            }, follow_redirects=True)

            # Should redirect to dashboard
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Dashboard', response.data)

    def test_failed_login(self):
        """Test failed login"""
        response = self.app.post('/login', data={
            'email': 'wrong@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        self.assertIn(b'Invalid email or password', response.data)

    def test_logout(self):
        """Test logout functionality"""
        # First login
        with self.app as client:
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'anypassword'
            })

            # Then logout
            response = client.get('/logout', follow_redirects=True)
            self.assertIn(b'Login', response.data)


class TestHealthMetricsWorkflow(unittest.TestCase):
    """Test complete health metrics workflow"""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Setup test user and login
        with app.app_context():
            # Clear and setup
            db_manager.cursor.execute("DELETE FROM health_metrics")
            db_manager.cursor.execute("DELETE FROM alerts")
            db_manager.cursor.execute("DELETE FROM users")

            user_id = db_manager.add_user(
                name="Workflow User",
                age=35,
                gender="Female",
                email="workflow@example.com"
            )

            db_manager.connection.commit()

        # Login
        with self.app as client:
            client.post('/login', data={
                'email': 'workflow@example.com',
                'password': 'anypassword'
            })

    def test_add_blood_pressure(self):
        """Test adding blood pressure metric"""
        with self.app as client:
            response = client.post('/add_metric', data={
                'metric_type': 'BP',
                'systolic': '120',
                'diastolic': '80',
                'notes': 'Test reading'
            }, follow_redirects=True)

            self.assertEqual(response.status_code, 200)
            self.assertIn(b'recorded successfully', response.data)

    def test_view_metrics(self):
        """Test viewing metrics"""
        with self.app as client:
            # First add a metric
            client.post('/add_metric', data={
                'metric_type': 'BP',
                'systolic': '120',
                'diastolic': '80'
            })

            # Then view metrics
            response = client.get('/metrics')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Health Metrics', response.data)

    def test_analytics_page(self):
        """Test analytics page"""
        with self.app as client:
            response = client.get('/analytics')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Health Analytics', response.data)

    def test_alerts_page(self):
        """Test alerts page"""
        with self.app as client:
            response = client.get('/alerts')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'Health Alerts', response.data)

    def test_profile_page(self):
        """Test profile page"""
        with self.app as client:
            response = client.get('/profile')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'User Profile', response.data)


class TestAPIFunctionality(unittest.TestCase):
    """Test API endpoints"""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Setup test user
        with app.app_context():
            db_manager.cursor.execute("DELETE FROM health_metrics")
            db_manager.cursor.execute("DELETE FROM alerts")
            db_manager.cursor.execute("DELETE FROM users")

            user_id = db_manager.add_user(
                name="API User",
                age=40,
                gender="Male",
                email="api@example.com"
            )

            db_manager.connection.commit()

        # Login
        with self.app as client:
            client.post('/login', data={
                'email': 'api@example.com',
                'password': 'anypassword'
            })

    def test_api_get_metrics(self):
        """Test API endpoint to get metrics"""
        with self.app as client:
            # Add some metrics first
            client.post('/add_metric', data={
                'metric_type': 'BP',
                'systolic': '120',
                'diastolic': '80'
            })

            # Get metrics via API
            response = client.get('/api/metrics')
            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertIsInstance(data, list)

    def test_api_add_metric(self):
        """Test API endpoint to add metric"""
        with self.app as client:
            response = client.post('/api/add_metric',
                                   json={
                                       'type': 'BP',
                                       'systolic': 120,
                                       'diastolic': 80,
                                       'notes': 'API test'
                                   },
                                   content_type='application/json'
                                   )

            self.assertEqual(response.status_code, 200)

            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('metric_id', data)


class TestErrorHandling(unittest.TestCase):
    """Test error handling in web application"""

    def test_invalid_form_submission(self):
        """Test handling of invalid form submissions"""
        with self.app as client:
            # Login first
            with app.app_context():
                db_manager.cursor.execute("DELETE FROM users")
                user_id = db_manager.add_user(
                    name="Error User",
                    age=30,
                    gender="