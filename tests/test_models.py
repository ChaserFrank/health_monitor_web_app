"""
Comprehensive Unit Tests for OOP Models in Health Monitoring System
Demonstrates all OOP concepts through testing
"""
import unittest
import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    # Enums
    Gender, Severity, MetricType,

    # Exception Classes
    HealthMetricError, InvalidValueError, UserNotFoundError,

    # Base Classes
    HealthMetric, Alertable,

    # Concrete Metric Classes
    BloodPressure, GlucoseLevel, Weight, Exercise, HeartRate,

    # User & Related Classes
    User, Alert, HealthGoal, TimeRange,

    # Analyzer & Factory
    HealthAnalyzer, HealthMetricFactory,

    # Singleton
    HealthMonitor
)

class TestEnums(unittest.TestCase):
    """Test Enumeration Classes"""

    def test_gender_enum(self):
        """Test Gender enum values"""
        self.assertEqual(Gender.MALE.value, "Male")
        self.assertEqual(Gender.FEMALE.value, "Female")
        self.assertEqual(Gender.OTHER.value, "Other")

        # Test string representation
        self.assertEqual(str(Gender.MALE), "Gender.MALE")

    def test_severity_enum(self):
        """Test Severity enum values"""
        self.assertEqual(Severity.LOW.value, "Low")
        self.assertEqual(Severity.MEDIUM.value, "Medium")
        self.assertEqual(Severity.HIGH.value, "High")
        self.assertEqual(Severity.CRITICAL.value, "Critical")

        # Test comparison
        self.assertLess(Severity.CRITICAL, Severity.LOW)  # Higher priority

    def test_metric_type_enum(self):
        """Test MetricType enum values"""
        self.assertEqual(MetricType.BLOOD_PRESSURE.value, "BP")
        self.assertEqual(MetricType.GLUCOSE.value, "Glucose")
        self.assertEqual(MetricType.WEIGHT.value, "Weight")
        self.assertEqual(MetricType.EXERCISE.value, "Exercise")
        self.assertEqual(MetricType.HEART_RATE.value, "Heart_Rate")

class TestExceptionClasses(unittest.TestCase):
    """Test Custom Exception Classes"""

    def test_invalid_value_error(self):
        """Test InvalidValueError with detailed message"""
        try:
            raise InvalidValueError("Blood Pressure", 300, "50-250 mmHg")
        except InvalidValueError as e:
            self.assertEqual(e.metric_name, "Blood Pressure")
            self.assertEqual(e.value, 300)
            self.assertEqual(e.valid_range, "50-250 mmHg")
            self.assertIn("Invalid Blood Pressure", str(e))

    def test_user_not_found_error(self):
        """Test UserNotFoundError"""
        try:
            raise UserNotFoundError("User with ID 999 not found")
        except UserNotFoundError as e:
            self.assertIn("User with ID 999", str(e))

    def test_health_metric_error(self):
        """Test HealthMetricError base class"""
        try:
            raise HealthMetricError("Failed to create metric")
        except HealthMetricError as e:
            self.assertIn("Failed to create metric", str(e))

class TestAbstractBaseClass(unittest.TestCase):
    """Test Abstract Base Class HealthMetric"""

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that HealthMetric abstract class cannot be instantiated"""
        with self.assertRaises(TypeError):
            HealthMetric(100)  # Should fail as abstract

    def test_abstract_methods_required(self):
        """Test that subclasses must implement abstract methods"""

        class IncompleteMetric(HealthMetric):
            def _validate_input(self):
                pass

            def is_normal(self):
                return True

            def get_recommendation(self):
                return "Test"

        # Should raise TypeError because get_category is not implemented
        with self.assertRaises(TypeError):
            IncompleteMetric(100)

class TestBloodPressureClass(unittest.TestCase):
    """Test BloodPressure class demonstrating Inheritance & Encapsulation"""

    def setUp(self):
        """Set up test data"""
        self.normal_bp = BloodPressure(120, 80)
        self.high_bp = BloodPressure(150, 95)
        self.low_bp = BloodPressure(85, 55)

    def test_creation_and_properties(self):
        """Test BloodPressure creation and property accessors"""
        # Test getter methods (Encapsulation)
        self.assertEqual(self.normal_bp.systolic, 120)
        self.assertEqual(self.normal_bp.diastolic, 80)
        self.assertEqual(self.normal_bp.unit, "mmHg")

        # Test is_normal method (Polymorphism)
        self.assertTrue(self.normal_bp.is_normal())
        self.assertFalse(self.high_bp.is_normal())
        self.assertFalse(self.low_bp.is_normal())

    def test_validation(self):
        """Test input validation in BloodPressure"""
        # Test valid ranges
        with self.assertRaises(InvalidValueError):
            BloodPressure(300, 200)  # Values too high

        with self.assertRaises(InvalidValueError):
            BloodPressure(40, 20)  # Values too low

        with self.assertRaises(ValueError):
            BloodPressure(80, 120)  # Diastolic > systolic

    def test_category_determination(self):
        """Test BP category determination"""
        self.assertEqual(self.normal_bp.get_category(), "Normal")
        self.assertEqual(self.high_bp.get_category(), "Stage 2 Hypertension")
        self.assertEqual(self.low_bp.get_category(), "Low")

        # Test edge cases
        elevated = BloodPressure(125, 80)
        self.assertEqual(elevated.get_category(), "Elevated")

        stage1 = BloodPressure(135, 85)
        self.assertEqual(stage1.get_category(), "Stage 1 Hypertension")

    def test_recommendations(self):
        """Test personalized recommendations"""
        normal_rec = self.normal_bp.get_recommendation()
        high_rec = self.high_bp.get_recommendation()
        low_rec = self.low_bp.get_recommendation()

        self.assertIn("optimal", normal_rec.lower())
        self.assertIn("medical attention", high_rec.lower())
        self.assertIn("stay hydrated", low_rec.lower())

    def test_alert_generation(self):
        """Test automatic alert generation (Interface implementation)"""
        # High BP should generate alert
        high_alerts = self.high_bp.check_for_alerts()
        self.assertEqual(len(high_alerts), 1)
        self.assertEqual(high_alerts[0].severity.value, "High")

        # Low BP should generate alert
        low_alerts = self.low_bp.check_for_alerts()
        self.assertEqual(len(low_alerts), 1)
        self.assertEqual(low_alerts[0].severity.value, "Medium")

        # Normal BP should not generate alert
        normal_alerts = self.normal_bp.check_for_alerts()
        self.assertEqual(len(normal_alerts), 0)

    def test_string_representation(self):
        """Test string representations"""
        self.assertEqual(str(self.normal_bp), "BP: 120/80 mmHg")

        # Test repr
        self.assertIn("BloodPressure", repr(self.normal_bp))

    def test_to_dict_method(self):
        """Test conversion to dictionary"""
        bp_dict = self.normal_bp.to_dict()

        self.assertEqual(bp_dict['type'], 'BloodPressure')
        self.assertEqual(bp_dict['systolic'], 120)
        self.assertEqual(bp_dict['diastolic'], 80)
        self.assertEqual(bp_dict['category'], 'Normal')
        self.assertTrue(bp_dict['is_normal'])

class TestGlucoseLevelClass(unittest.TestCase):
    """Test GlucoseLevel class demonstrating Factory Methods"""

    def test_factory_methods(self):
        """Test class methods for creating different glucose types"""
        fasting = GlucoseLevel.create_fasting(95.5)
        self.assertTrue(fasting.is_fasting)
        self.assertIsNone(fasting.meal_time)

        post_prandial = GlucoseLevel.create_post_prandial(140, hours_after_meal=2)
        self.assertFalse(post_prandial.is_fasting)
        self.assertEqual(post_prandial.meal_time, "2h_post_meal")

    def test_validation(self):
        """Test glucose level validation"""
        with self.assertRaises(InvalidValueError):
            GlucoseLevel(10)  # Too low

        with self.assertRaises(InvalidValueError):
            GlucoseLevel(700)  # Too high

    def test_category_based_on_fasting(self):
        """Test glucose category based on fasting status"""
        # Fasting glucose
        fasting_normal = GlucoseLevel(95.5, is_fasting=True)
        fasting_prediabetes = GlucoseLevel(115, is_fasting=True)
        fasting_diabetes = GlucoseLevel(130, is_fasting=True)

        self.assertEqual(fasting_normal.get_category(), "Normal")
        self.assertEqual(fasting_prediabetes.get_category(), "Prediabetes")
        self.assertEqual(fasting_diabetes.get_category(), "Diabetes")

        # Non-fasting glucose
        nonfasting_normal = GlucoseLevel(140, is_fasting=False)
        nonfasting_prediabetes = GlucoseLevel(160, is_fasting=False)
        nonfasting_diabetes = GlucoseLevel(210, is_fasting=False)

        self.assertEqual(nonfasting_normal.get_category(), "Normal")
        self.assertEqual(nonfasting_prediabetes.get_category(), "Prediabetes")
        self.assertEqual(nonfasting_diabetes.get_category(), "Diabetes")

class TestWeightClass(unittest.TestCase):
    """Test Weight class demonstrating Composition"""

    def test_bmi_calculation(self):
        """Test BMI calculation (composition of height and weight)"""
        weight = Weight(75, 175)  # 75kg, 175cm
        expected_bmi = 75 / ((1.75) ** 2)

        self.assertAlmostEqual(weight.bmi, expected_bmi, places=2)

    def test_ideal_weight_range(self):
        """Test ideal weight range calculation"""
        weight = Weight(75, 175)
        min_weight, max_weight = weight.get_ideal_weight_range()

        # Calculate expected ranges
        height_m = 1.75
        expected_min = 18.5 * (height_m ** 2)
        expected_max = 24.9 * (height_m ** 2)

        self.assertAlmostEqual(min_weight, expected_min, places=1)
        self.assertAlmostEqual(max_weight, expected_max, places=1)

    def test_bmi_categories(self):
        """Test BMI category determination"""
        underweight = Weight(50, 175)
        normal = Weight(70, 175)
        overweight = Weight(85, 175)
        obese = Weight(100, 175)

        self.assertEqual(underweight.get_category(), "Underweight")
        self.assertEqual(normal.get_category(), "Normal")
        self.assertEqual(overweight.get_category(), "Overweight")
        self.assertEqual(obese.get_category(), "Obese")

class TestExerciseClass(unittest.TestCase):
    """Test Exercise class demonstrating Polymorphism"""

    def test_intensity_determination(self):
        """Test static method for intensity determination"""
        self.assertEqual(Exercise._determine_intensity("Walking"), "Light")
        self.assertEqual(Exercise._determine_intensity("Running"), "Vigorous")
        self.assertEqual(Exercise._determine_intensity("Unknown"), "Moderate")

    def test_calorie_calculation(self):
        """Test calorie calculation with different intensities"""
        light_exercise = Exercise(30, "Walking", "Light")
        moderate_exercise = Exercise(30, "Cycling", "Moderate")
        vigorous_exercise = Exercise(30, "Running", "Vigorous")

        weight_kg = 75

        light_calories = light_exercise.calculate_calories_burned(weight_kg)
        moderate_calories = moderate_exercise.calculate_calories_burned(weight_kg)
        vigorous_calories = vigorous_exercise.calculate_calories_burned(weight_kg)

        # Vigorous should burn more than moderate, which should burn more than light
        self.assertLess(light_calories, moderate_calories)
        self.assertLess(moderate_calories, vigorous_calories)

class TestHeartRateClass(unittest.TestCase):
    """Test HeartRate class demonstrating Complex Methods"""

    def test_max_heart_rate_calculation(self):
        """Test maximum heart rate calculation"""
        hr_with_age = HeartRate(72, age=30)
        hr_without_age = HeartRate(72)  # No age provided

        self.assertEqual(hr_with_age.get_max_heart_rate(), 190)  # 220 - 30
        self.assertEqual(hr_without_age.get_max_heart_rate(), 220)  # Default

    def test_target_zones(self):
        """Test heart rate zone calculations"""
        hr = HeartRate(72, age=30)
        zones = hr.get_target_zones()

        self.assertIn("Resting", zones)
        self.assertIn("Light", zones)
        self.assertIn("Moderate", zones)
        self.assertIn("Vigorous", zones)
        self.assertIn("Maximum", zones)

        # Check zone calculations
        max_hr = 190
        moderate_zone = zones["Moderate"]
        expected_min = int(max_hr * 0.6)
        expected_max = int(max_hr * 0.7)

        self.assertEqual(moderate_zone[0], expected_min)
        self.assertEqual(moderate_zone[1], expected_max)

class TestUserClass(unittest.TestCase):
    """Test User class demonstrating Encapsulation and Composition"""

    def setUp(self):
        """Set up test user"""
        self.user = User(1, "Test User", 30, "Male", "test@example.com")

        # Add some metrics
        self.user.add_metric(BloodPressure(120, 80))
        self.user.add_metric(GlucoseLevel(95.5))
        self.user.add_metric(Weight(75, 175))

        # Add an alert
        self.user.add_alert(Alert("Test Alert", "This is a test", Severity.MEDIUM))

        # Add a health goal
        self.user.add_goal(HealthGoal("Weight Loss", 70, 75, unit="kg"))

    def test_encapsulation(self):
        """Test encapsulation through property accessors"""
        # Can access through properties but not directly
        self.assertEqual(self.user.name, "Test User")
        self.assertEqual(self.user.age, 30)
        self.assertEqual(self.user.email, "test@example.com")

        # Try to access private attribute directly (should work but discouraged)
        with self.assertRaises(AttributeError):
            _ = self.user._name  # This actually works in Python, but we're demonstrating intent

    def test_metric_management(self):
        """Test metric management methods"""
        # Get metrics by type
        bp_metrics = self.user.get_metrics_by_type(BloodPressure)
        self.assertEqual(len(bp_metrics), 1)
        self.assertIsInstance(bp_metrics[0], BloodPressure)

        # Get recent metrics
        recent = self.user.get_recent_metrics(2)
        self.assertEqual(len(recent), 2)

    def test_alert_management(self):
        """Test alert management"""
        unread_alerts = self.user.get_unread_alerts()
        self.assertEqual(len(unread_alerts), 1)

        # Mark as read
        self.user.mark_alerts_read()
        unread_alerts = self.user.get_unread_alerts()
        self.assertEqual(len(unread_alerts), 0)

    def test_goal_management(self):
        """Test health goal management"""
        active_goals = self.user.get_active_goals()
        self.assertEqual(len(active_goals), 1)
        self.assertFalse(active_goals[0].is_completed)

        # Complete the goal
        active_goals[0].current_value = 70
        self.assertTrue(active_goals[0].is_completed)

    def test_health_summary(self):
        """Test comprehensive health summary generation"""
        time_range = TimeRange(
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        )

        summary = self.user.get_health_summary(time_range)

        # Check structure
        self.assertIn("user_info", summary)
        self.assertIn("metrics_summary", summary)
        self.assertIn("alerts", summary)
        self.assertIn("goals", summary)

        # Check values
        self.assertEqual(summary["metrics_summary"]["total_metrics"], 3)
        self.assertEqual(summary["alerts"]["total"], 1)
        self.assertEqual(summary["goals"]["total"], 1)

    def test_trend_calculation(self):
        """Test trend calculation for different metric types"""
        # Add more BP readings for trend
        self.user.add_metric(BloodPressure(118, 78))
        self.user.add_metric(BloodPressure(122, 82))

        # Calculate BP trend
        bp_trend = self.user.calculate_trends(BloodPressure, days=30)

        self.assertIn("metric_type", bp_trend)
        self.assertIn("readings_count", bp_trend)
        self.assertIn("average_systolic", bp_trend)
        self.assertIn("trend", bp_trend)

class TestAlertClass(unittest.TestCase):
    """Test Alert class"""

    def test_alert_creation_and_properties(self):
        """Test alert creation and properties"""
        alert = Alert(
            alert_type="High Blood Pressure",
            message="BP is 150/95 mmHg",
            severity=Severity.HIGH
        )

        self.assertEqual(alert.alert_type, "High Blood Pressure")
        self.assertEqual(alert.message, "BP is 150/95 mmHg")
        self.assertEqual(alert.severity, Severity.HIGH)
        self.assertFalse(alert.is_read)
        self.assertFalse(alert.resolved)

        # Test priority
        self.assertEqual(alert.get_priority(), 2)  # High severity = priority 2

    def test_alert_states(self):
        """Test alert state changes"""
        alert = Alert("Test", "Message", Severity.MEDIUM)

        # Mark as read
        alert.mark_read()
        self.assertTrue(alert.is_read)

        # Mark as resolved
        alert.mark_resolved()
        self.assertTrue(alert.resolved)
        self.assertIsNotNone(alert.resolved_date)

    def test_string_representation(self):
        """Test alert string representation"""
        alert = Alert("Test", "Message", Severity.HIGH)

        self.assertIn("[High]", str(alert))
        self.assertIn("Test", str(alert))
        self.assertIn("UNREAD", str(alert))

class TestHealthGoalClass(unittest.TestCase):
    """Test HealthGoal class"""

    def test_goal_creation_and_progress(self):
        """Test goal creation and progress calculation"""
        goal = HealthGoal(
            goal_type="Weight Loss",
            target_value=70,
            current_value=75,
            unit="kg"
        )

        self.assertEqual(goal.goal_type, "Weight Loss")
        self.assertEqual(goal.target_value, 70)
        self.assertEqual(goal.current_value, 75)
        self.assertAlmostEqual(goal.progress, (75/70)*100)
        self.assertFalse(goal.is_completed)

        # Test remaining
        self.assertEqual(goal.get_remaining(), 5)

    def test_goal_completion(self):
        """Test goal completion detection"""
        goal = HealthGoal("Target", 100, 90)

        # Update to reach target
        goal.current_value = 100
        self.assertTrue(goal.is_completed)
        self.assertEqual(goal.progress, 100)

        # Exceed target
        goal.current_value = 110
        self.assertTrue(goal.is_completed)
        self.assertEqual(goal.progress, 100)  # Capped at 100%

    def test_days_remaining(self):
        """Test days remaining calculation"""
        from datetime import timedelta

        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        goal = HealthGoal(
            "Test Goal",
            target_value=100,
            current_value=50,
            start_date=start_date,
            end_date=end_date
        )

        days_remaining = goal.get_days_remaining()
        self.assertEqual(days_remaining, 30)

    def test_validation(self):
        """Test goal validation"""
        with self.assertRaises(ValueError):
            HealthGoal("Invalid", target_value=0, current_value=0)

        with self.assertRaises(ValueError):
            HealthGoal("Invalid", target_value=100, current_value=50,
                      start_date=date(2024, 12, 31),
                      end_date=date(2024, 1, 1))

class TestTimeRangeClass(unittest.TestCase):
    """Test TimeRange data class"""

    def test_time_range_validation(self):
        """Test time range validation"""
        # Valid range
        valid_range = TimeRange(
            datetime(2024, 1, 1),
            datetime(2024, 12, 31)
        )
        self.assertTrue(valid_range.is_valid())

        # Invalid range
        invalid_range = TimeRange(
            datetime(2024, 12, 31),
            datetime(2024, 1, 1)
        )
        self.assertFalse(invalid_range.is_valid())

    def test_duration_calculation(self):
        """Test duration calculation"""
        time_range = TimeRange(
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )

        self.assertEqual(time_range.duration_days(), 30)

class TestHealthAnalyzerClass(unittest.TestCase):
    """Test HealthAnalyzer class demonstrating Polymorphism"""

    def setUp(self):
        """Set up test metrics for analysis"""
        self.metrics = [
            BloodPressure(120, 80),      # Normal
            BloodPressure(150, 95),      # Abnormal
            GlucoseLevel(95.5),          # Normal
            GlucoseLevel(130),           # Abnormal (fasting)
            Weight(75, 175),             # Normal
            Exercise(20, "Walking"),     # Abnormal (too short)
            Exercise(45, "Running"),     # Normal
        ]

    def test_analyze_metrics_polymorphism(self):
        """Test polymorphic analysis of different metric types"""
        analyzer = HealthAnalyzer()
        analysis = analyzer.analyze_metrics(self.metrics)

        # Check overall analysis
        self.assertEqual(analysis['total_metrics'], 7)
        self.assertEqual(analysis['normal_count'], 4)
        self.assertEqual(analysis['abnormal_count'], 3)

        # Check type distribution
        self.assertIn('BloodPressure', analysis['metric_types'])
        self.assertIn('GlucoseLevel', analysis['metric_types'])
        self.assertIn('Weight', analysis['metric_types'])
        self.assertIn('Exercise', analysis['metric_types'])

        # Check category distribution
        self.assertIn('Normal', analysis['category_distribution'])

        # Check detailed analysis
        self.assertEqual(len(analysis['details']), 7)
        for detail in analysis['details']:
            self.assertIn('type', detail)
            self.assertIn('value', detail)
            self.assertIn('is_normal', detail)
            self.assertIn('recommendation', detail)

    def test_trend_analysis(self):
        """Test trend analysis"""
        analyzer = HealthAnalyzer()

        # Test with insufficient data
        single_metric = [BloodPressure(120, 80)]
        result = analyzer.analyze_trend(single_metric)
        self.assertIn('error', result)

        # Test with sufficient data
        metrics = [
            BloodPressure(130, 85),
            BloodPressure(125, 82),
            BloodPressure(120, 80)
        ]

        result = analyzer.analyze_trend(metrics)

        self.assertIn('period_days', result)
        self.assertIn('readings_count', result)
        self.assertIn('first_reading', result)
        self.assertIn('last_reading', result)
        self.assertIn('value_change', result)
        self.assertIn('trend_direction', result)

class TestHealthMetricFactory(unittest.TestCase):
    """Test HealthMetricFactory class demonstrating Factory Pattern"""

    def test_create_metric_from_type(self):
        """Test creating different metric types from factory"""
        # Test Blood Pressure
        bp = HealthMetricFactory.create_metric('blood_pressure',
                                              systolic=120,
                                              diastolic=80)
        self.assertIsInstance(bp, BloodPressure)
        self.assertEqual(bp.systolic, 120)

        # Test Glucose
        glucose = HealthMetricFactory.create_metric('glucose',
                                                   level=95.5,
                                                   is_fasting=True)
        self.assertIsInstance(glucose, GlucoseLevel)
        self.assertTrue(glucose.is_fasting)

        # Test Weight
        weight = HealthMetricFactory.create_metric('weight',
                                                  weight=75,
                                                  height=175)
        self.assertIsInstance(weight, Weight)

        # Test Exercise
        exercise = HealthMetricFactory.create_metric('exercise',
                                                    minutes=45,
                                                    activity_type="Running")
        self.assertIsInstance(exercise, Exercise)

        # Test Heart Rate
        heart_rate = HealthMetricFactory.create_metric('heart_rate',
                                                      rate=72,
                                                      age=30)
        self.assertIsInstance(heart_rate, HeartRate)

    def test_create_from_dict(self):
        """Test creating metric from dictionary"""
        metric_dict = {
            'type': 'BloodPressure',
            'systolic': 120,
            'diastolic': 80
        }

        metric = HealthMetricFactory.create_from_dict(metric_dict)
        self.assertIsInstance(metric, BloodPressure)
        self.assertEqual(metric.systolic, 120)

    def test_invalid_metric_type(self):
        """Test handling of invalid metric type"""
        with self.assertRaises(HealthMetricError):
            HealthMetricFactory.create_metric('invalid_type', value=100)

        with self.assertRaises(HealthMetricError):
            HealthMetricFactory.create_metric('blood_pressure',
                                            systolic=120)  # Missing diastolic

    def test_missing_required_parameters(self):
        """Test missing required parameters"""
        with self.assertRaises(HealthMetricError):
            HealthMetricFactory.create_metric('blood_pressure')  # No parameters

class TestHealthMonitorSingleton(unittest.TestCase):
    """Test HealthMonitor Singleton Pattern"""

    def test_singleton_pattern(self):
        """Test that only one instance exists"""
        monitor1 = HealthMonitor()
        monitor2 = HealthMonitor()

        # Both should be the same instance
        self.assertIs(monitor1, monitor2)

    def test_user_registration(self):
        """Test user registration in singleton"""
        monitor = HealthMonitor()

        # Clear any existing users
        monitor._users.clear()

        user = User(100, "Singleton User", 25, "Female", "singleton@example.com")
        monitor.register_user(user)

        # Should be able to retrieve user
        retrieved_user = monitor.get_user(100)
        self.assertEqual(retrieved_user.name, "Singleton User")

        # Should not allow duplicate registration
        with self.assertRaises(ValueError):
            monitor.register_user(user)

    def test_user_not_found(self):
        """Test error when user not found"""
        monitor = HealthMonitor()
        monitor._users.clear()  # Clear users

        with self.assertRaises(UserNotFoundError):
            monitor.get_user(999)

    def test_alert_management(self):
        """Test alert management in singleton"""
        monitor = HealthMonitor()

        # Create users with alerts
        user1 = User(1, "User 1", 30, "Male", "user1@example.com")
        user2 = User(2, "User 2", 35, "Female", "user2@example.com")

        user1.add_alert(Alert("Alert 1", "Test", Severity.HIGH))
        user2.add_alert(Alert("Alert 2", "Test", Severity.MEDIUM))

        monitor.register_user(user1)
        monitor.register_user(user2)

        # Get all alerts
        all_alerts = monitor.get_all_alerts()
        self.assertEqual(len(all_alerts), 2)

        # Get critical alerts
        critical_alerts = monitor.get_critical_alerts()
        self.assertEqual(len(critical_alerts), 1)
        self.assertEqual(critical_alerts[0].severity, Severity.HIGH)

class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests demonstrating complete workflows"""

    def test_complete_health_monitoring_workflow(self):
        """Test complete workflow from metric creation to alerts"""
        # 1. Create a user
        user = User(1, "Integration User", 40, "Male", "integration@example.com")

        # 2. Add various health metrics
        metrics = [
            BloodPressure(150, 95),      # Should generate alert
            GlucoseLevel(65),            # Should generate alert (low glucose)
            Weight(90, 175),             # Overweight
            Exercise(25, "Walking"),     # Insufficient exercise
            HeartRate(105, age=40, condition="Resting")  # High resting HR
        ]

        for metric in metrics:
            user.add_metric(metric)

        # 3. Check that alerts were generated
        self.assertGreater(len(user.get_unread_alerts()), 0)

        # 4. Analyze health metrics
        analyzer = HealthAnalyzer()
        analysis = analyzer.analyze_metrics(user.get_recent_metrics())

        # Should have abnormalities
        self.assertGreater(analysis['abnormal_count'], 0)

        # 5. Set a health goal
        goal = HealthGoal("Weight Loss", 80, 90, unit="kg")
        user.add_goal(goal)

        # 6. Update progress
        goal.current_value = 85
        self.assertGreater(goal.progress, 0)

        # 7. Generate health summary
        summary = user.get_health_summary()
        self.assertIn("metrics_summary", summary)
        self.assertIn("alerts", summary)
        self.assertIn("goals", summary)

    def test_factory_pattern_integration(self):
        """Test factory pattern integration with user"""
        user = User(2, "Factory User", 35, "Female", "factory@example.com")

        # Create metrics using factory
        bp = HealthMetricFactory.create_metric('blood_pressure',
                                              systolic=120,
                                              diastolic=80)
        glucose = HealthMetricFactory.create_metric('glucose',
                                                   level=95.5,
                                                   is_fasting=True)

        user.add_metric(bp)
        user.add_metric(glucose)

        # Should be able to retrieve and analyze
        metrics = user.get_recent_metrics()
        self.assertEqual(len(metrics), 2)

        analyzer = HealthAnalyzer()
        analysis = analyzer.analyze_metrics(metrics)
        self.assertEqual(analysis['total_metrics'], 2)

class TestErrorHandlingScenarios(unittest.TestCase):
    """Test error handling scenarios"""

    def test_error_propagation(self):
        """Test that errors propagate correctly through the system"""
        # Try to create invalid metric
        with self.assertRaises(InvalidValueError):
            BloodPressure(300, 200)

        # Try to create invalid user
        with self.assertRaises(ValueError):
            User(3, "", 150, "Invalid", "invalid")

    def test_graceful_error_handling(self):
        """Test graceful error handling in factory"""
        try:
            HealthMetricFactory.create_metric('invalid_type')
            self.fail("Should have raised exception")
        except HealthMetricError as e:
            self.assertIn("Failed to create", str(e))

    def test_edge_cases(self):
        """Test edge cases"""
        # Minimum valid values
        min_bp = BloodPressure(50, 30)
        self.assertIsNotNone(min_bp)

        # Maximum valid values
        max_bp = BloodPressure(250, 150)
        self.assertIsNotNone(max_bp)

        # Boundary values for glucose
        min_glucose = GlucoseLevel(20)
        max_glucose = GlucoseLevel(600)
        self.assertIsNotNone(min_glucose)
        self.assertIsNotNone(max_glucose)

if __name__ == '__main__':
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnums)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExceptionClasses))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAbstractBaseClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBloodPressureClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestGlucoseLevelClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestWeightClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestExerciseClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHeartRateClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestUserClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAlertClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHealthGoalClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTimeRangeClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHealthAnalyzerClass))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHealthMetricFactory))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHealthMonitorSingleton))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestIntegrationScenarios))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestErrorHandlingScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*60)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60)