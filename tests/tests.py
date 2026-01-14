"""
Unit Tests for Health Monitoring System
"""
import unittest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    User, BloodPressure, GlucoseLevel, Weight, Exercise, HeartRate,
    HealthMetricFactory, HealthAnalyzer, Alert, HealthGoal, TimeRange,
    InvalidValueError, HealthMetricError
)


class TestHealthMetricClasses(unittest.TestCase):
    """Test cases for health metric classes"""

    def test_blood_pressure_creation(self):
        """Test BloodPressure class creation and validation"""
        # Valid BP
        bp = BloodPressure(120, 80)
        self.assertEqual(bp.systolic, 120)
        self.assertEqual(bp.diastolic, 80)
        self.assertTrue(bp.is_normal())
        self.assertEqual(bp.get_category(), "Normal")

        # High BP
        bp_high = BloodPressure(150, 95)
        self.assertFalse(bp_high.is_normal())
        self.assertEqual(bp_high.get_category(), "Stage 2 Hypertension")

        # Invalid BP - should raise error
        with self.assertRaises(InvalidValueError):
            BloodPressure(300, 200)

        with self.assertRaises(ValueError):
            BloodPressure(80, 120)  # Diastolic > systolic

    def test_glucose_level_creation(self):
        """Test GlucoseLevel class"""
        # Normal fasting glucose
        glucose = GlucoseLevel(95.5, is_fasting=True)
        self.assertTrue(glucose.is_normal())
        self.assertEqual(glucose.get_category(), "Normal")

        # High fasting glucose
        glucose_high = GlucoseLevel(130, is_fasting=True)
        self.assertFalse(glucose_high.is_normal())
        self.assertEqual(glucose_high.get_category(), "Diabetes")

        # Test factory methods
        fasting = GlucoseLevel.create_fasting(95.5)
        self.assertTrue(fasting.is_fasting)

        post_prandial = GlucoseLevel.create_post_prandial(140)
        self.assertFalse(post_prandial.is_fasting)

    def test_weight_calculation(self):
        """Test Weight class and BMI calculation"""
        weight = Weight(75, 175)  # 75kg, 175cm
        self.assertAlmostEqual(weight.bmi, 24.49, places=2)
        self.assertTrue(weight.is_normal())

        # Underweight
        weight_low = Weight(50, 175)
        self.assertFalse(weight_low.is_normal())
        self.assertEqual(weight_low.get_category(), "Underweight")

        # Overweight
        weight_high = Weight(90, 175)
        self.assertFalse(weight_high.is_normal())
        self.assertEqual(weight_high.get_category(), "Overweight")

    def test_exercise_tracking(self):
        """Test Exercise class"""
        exercise = Exercise(45, "Running", "Vigorous")
        self.assertTrue(exercise.is_normal())
        self.assertEqual(exercise.get_category(), "Moderate Activity")

        # Low exercise
        exercise_low = Exercise(20, "Walking", "Light")
        self.assertFalse(exercise_low.is_normal())
        self.assertEqual(exercise_low.get_category(), "Light Activity")

        # Calories burned calculation
        calories = exercise.calculate_calories_burned(75)
        self.assertGreater(calories, 0)

    def test_heart_rate_monitoring(self):
        """Test HeartRate class"""
        hr = HeartRate(72, age=30, condition="Resting")
        self.assertTrue(hr.is_normal())
        self.assertEqual(hr.get_category(), "Normal")

        # Bradycardia
        hr_low = HeartRate(55, age=30, condition="Resting")
        self.assertFalse(hr_low.is_normal())
        self.assertEqual(hr_low.get_category(), "Bradycardia")

        # Target zones
        zones = hr.get_target_zones()
        self.assertIn("Resting", zones)
        self.assertIn("Moderate", zones)

    def test_health_metric_factory(self):
        """Test HealthMetricFactory"""
        # Create BP metric
        bp = HealthMetricFactory.create_metric('blood_pressure', systolic=120, diastolic=80)
        self.assertIsInstance(bp, BloodPressure)
        self.assertEqual(bp.systolic, 120)

        # Create Glucose metric
        glucose = HealthMetricFactory.create_metric('glucose', level=95.5, is_fasting=True)
        self.assertIsInstance(glucose, GlucoseLevel)
        self.assertTrue(glucose.is_fasting)

        # Invalid metric type
        with self.assertRaises(HealthMetricError):
            HealthMetricFactory.create_metric('invalid_type')


class TestUserClass(unittest.TestCase):
    """Test cases for User class"""

    def setUp(self):
        """Set up test user"""
        self.user = User(1, "Test User", 30, "Male", "test@example.com")

    def test_user_creation(self):
        """Test User creation and properties"""
        self.assertEqual(self.user.name, "Test User")
        self.assertEqual(self.user.age, 30)
        self.assertEqual(self.user.email, "test@example.com")

        # Test invalid age
        with self.assertRaises(ValueError):
            User(2, "Invalid", 150, "Male", "invalid@example.com")

    def test_metric_management(self):
        """Test adding and retrieving metrics"""
        bp = BloodPressure(120, 80)
        glucose = GlucoseLevel(95.5)

        self.user.add_metric(bp)
        self.user.add_metric(glucose)

        # Get metrics by type
        bp_metrics = self.user.get_metrics_by_type(BloodPressure)
        self.assertEqual(len(bp_metrics), 1)
        self.assertIsInstance(bp_metrics[0], BloodPressure)

        # Get recent metrics
        recent = self.user.get_recent_metrics(1)
        self.assertEqual(len(recent), 1)
        self.assertIsInstance(recent[0], GlucoseLevel)

    def test_health_summary(self):
        """Test health summary generation"""
        # Add some metrics
        self.user.add_metric(BloodPressure(120, 80))
        self.user.add_metric(BloodPressure(140, 90))  # Abnormal
        self.user.add_metric(GlucoseLevel(95.5))

        # Create time range
        time_range = TimeRange(
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        )

        summary = self.user.get_health_summary(time_range)

        self.assertEqual(summary['metrics_summary']['total_metrics'], 3)
        self.assertEqual(summary['metrics_summary']['normal_count'], 2)
        self.assertEqual(summary['metrics_summary']['abnormal_count'], 1)

        # Test without time range
        summary_no_range = self.user.get_health_summary()
        self.assertIsNotNone(summary_no_range)


class TestHealthAnalyzer(unittest.TestCase):
    """Test cases for HealthAnalyzer"""

    def setUp(self):
        """Set up test metrics"""
        self.metrics = [
            BloodPressure(120, 80),
            BloodPressure(140, 90),  # Abnormal
            GlucoseLevel(95.5),
            GlucoseLevel(130, is_fasting=True),  # Abnormal
            Weight(75, 175),
            Exercise(45, "Running")
        ]

    def test_analyze_metrics(self):
        """Test metric analysis"""
        analyzer = HealthAnalyzer()
        analysis = analyzer.analyze_metrics(self.metrics)

        self.assertEqual(analysis['total_metrics'], 6)
        self.assertEqual(analysis['normal_count'], 4)
        self.assertEqual(analysis['abnormal_count'], 2)

        # Check metric type distribution
        self.assertIn('BloodPressure', analysis['metric_types'])
        self.assertIn('GlucoseLevel', analysis['metric_types'])

        # Check percentages
        self.assertIn('normal_percentage', analysis)
        self.assertIn('abnormal_percentage', analysis)

    def test_trend_analysis(self):
        """Test trend analysis"""
        analyzer = HealthAnalyzer()

        # Test with insufficient data
        analysis = analyzer.analyze_trend([BloodPressure(120, 80)])
        self.assertIn('error', analysis)

        # Test with sufficient data
        metrics = [
            BloodPressure(120, 80),
            BloodPressure(118, 78),
            BloodPressure(122, 82)
        ]
        analysis = analyzer.analyze_trend(metrics)
        self.assertIn('period_days', analysis)
        self.assertIn('readings_count', analysis)
        self.assertIn('trend_direction', analysis)


class TestAlertSystem(unittest.TestCase):
    """Test cases for Alert system"""

    def test_alert_creation(self):
        """Test Alert class"""
        alert = Alert(
            alert_type="High Blood Pressure",
            message="BP is 150/95 mmHg",
            severity="High"
        )

        self.assertEqual(alert.alert_type, "High Blood Pressure")
        self.assertEqual(alert.message, "BP is 150/95 mmHg")
        self.assertFalse(alert.is_read)
        self.assertFalse(alert.resolved)

        # Test priority
        self.assertEqual(alert.get_priority(), 2)  # High severity = priority 2

        # Mark as read and resolved
        alert.mark_read()
        alert.mark_resolved()

        self.assertTrue(alert.is_read)
        self.assertTrue(alert.resolved)
        self.assertIsNotNone(alert.resolved_date)

    def test_automatic_alerts(self):
        """Test automatic alert generation from metrics"""
        # High BP should generate alert
        bp_high = BloodPressure(150, 95)
        alerts = bp_high.check_for_alerts()

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, "High Blood Pressure")
        self.assertEqual(alerts[0].severity.value, "High")

        # Normal BP should not generate alert
        bp_normal = BloodPressure(120, 80)
        alerts = bp_normal.check_for_alerts()
        self.assertEqual(len(alerts), 0)

        # Low glucose should generate alert
        glucose_low = GlucoseLevel(65, is_fasting=True)
        alerts = glucose_low.check_for_alerts()

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].alert_type, "Low Glucose")


class TestHealthGoals(unittest.TestCase):
    """Test cases for HealthGoal class"""

    def test_goal_creation(self):
        """Test HealthGoal creation"""
        goal = HealthGoal(
            goal_type="Weight Loss",
            target_value=70,
            current_value=75,
            unit="kg"
        )

        self.assertEqual(goal.goal_type, "Weight Loss")
        self.assertEqual(goal.target_value, 70)
        self.assertEqual(goal.current_value, 75)
        self.assertEqual(goal.progress, (75 / 70) * 100)
        self.assertFalse(goal.is_completed)

        # Update current value to reach goal
        goal.current_value = 70
        self.assertTrue(goal.is_completed)
        self.assertEqual(goal.progress, 100)

        # Test remaining calculation
        goal.current_value = 68
        self.assertEqual(goal.get_remaining(), 2)

    def test_invalid_goal(self):
        """Test invalid goal creation"""
        with self.assertRaises(ValueError):
            HealthGoal("Invalid", target_value=0, current_value=0)

        with self.assertRaises(ValueError):
            HealthGoal("Invalid", target_value=10, current_value=5,
                       start_date=datetime(2024, 12, 31),
                       end_date=datetime(2024, 1, 1))


class TestTimeRange(unittest.TestCase):
    """Test cases for TimeRange class"""

    def test_time_range_validation(self):
        """Test TimeRange validation"""
        # Valid range
        time_range = TimeRange(
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        )
        self.assertTrue(time_range.is_valid())
        self.assertEqual(time_range.duration_days(), 365)

        # Invalid range (end before start)
        invalid_range = TimeRange(
            datetime(2024, 12, 31),
            datetime(2024, 1, 1)
        )
        self.assertFalse(invalid_range.is_valid())


class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def test_user_with_alerts(self):
        """Test user with automatic alert generation"""
        user = User(1, "Test User", 30, "Male", "test@example.com")

        # Add metric that should generate alert
        bp_high = BloodPressure(150, 95)
        user.add_metric(bp_high)

        # Check if alert was generated
        self.assertEqual(len(user.get_unread_alerts()), 1)

        # Mark alerts as read
        user.mark_alerts_read()
        self.assertEqual(len(user.get_unread_alerts()), 0)

    def test_complete_workflow(self):
        """Test complete workflow from metric creation to analysis"""
        # Create metrics
        metrics = [
            BloodPressure(120, 80),
            GlucoseLevel(95.5),
            Weight(75, 175),
            Exercise(45, "Running")
        ]

        # Create user and add metrics
        user = User(1, "Test User", 30, "Male", "test@example.com")
        for metric in metrics:
            user.add_metric(metric)

        # Analyze metrics
        analyzer = HealthAnalyzer()
        analysis = analyzer.analyze_metrics(user.get_recent_metrics())

        # Check results
        self.assertEqual(analysis['total_metrics'], 4)
        self.assertEqual(analysis['normal_count'], 4)
        self.assertEqual(analysis['abnormal_count'], 0)


if __name__ == '__main__':
    unittest.main()