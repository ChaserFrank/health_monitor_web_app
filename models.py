"""
Models Module for Health Monitoring System
Demonstrating Object-Oriented Programming Concepts
"""
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


# ==================== ENUMS (For Type Safety) ====================

class Gender(Enum):
    """Enumeration for gender types"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class Severity(Enum):
    """Enumeration for alert severity levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class MetricType(Enum):
    """Enumeration for health metric types"""
    BLOOD_PRESSURE = "BP"
    GLUCOSE = "Glucose"
    WEIGHT = "Weight"
    EXERCISE = "Exercise"
    HEART_RATE = "Heart_Rate"


# ==================== EXCEPTION CLASSES (Custom Error Handling) ====================

class HealthMetricError(Exception):
    """Base exception for health metric errors"""
    pass


class InvalidValueError(HealthMetricError):
    """Raised when a health metric value is invalid"""

    def __init__(self, metric_name: str, value: Any, valid_range: str):
        self.metric_name = metric_name
        self.value = value
        self.valid_range = valid_range
        super().__init__(f"Invalid {metric_name}: {value}. Valid range: {valid_range}")


class UserNotFoundError(HealthMetricError):
    """Raised when user is not found"""
    pass


# ==================== ABSTRACT BASE CLASSES (Abstraction) ====================

class HealthMetric(ABC):
    """
    Abstract Base Class for all health metrics
    Demonstrates: Abstraction, Encapsulation, Inheritance
    """

    def __init__(self, value: float, timestamp: datetime = None):
        # Encapsulation: Protected attributes
        self._value = value
        self._timestamp = timestamp or datetime.now()
        self._unit = ""
        self._validate_input()

    @abstractmethod
    def _validate_input(self):
        """Validate input values - must be implemented by subclasses"""
        pass

    @abstractmethod
    def is_normal(self) -> bool:
        """Check if metric is within normal range"""
        pass

    @abstractmethod
    def get_recommendation(self) -> str:
        """Get health recommendation based on value"""
        pass

    @abstractmethod
    def get_category(self) -> str:
        """Get category/status of the reading"""
        pass

    # Encapsulation: Property getters and setters with validation
    @property
    def value(self) -> float:
        """Get the metric value"""
        return self._value

    @value.setter
    def value(self, new_value: float):
        """Set the metric value with validation"""
        if not isinstance(new_value, (int, float)):
            raise ValueError("Value must be a number")
        self._value = new_value
        self._validate_input()

    @property
    def timestamp(self) -> datetime:
        """Get the timestamp"""
        return self._timestamp

    @property
    def unit(self) -> str:
        """Get the unit of measurement"""
        return self._unit

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary for database storage"""
        return {
            'type': self.__class__.__name__,
            'value': self._value,
            'unit': self._unit,
            'timestamp': self._timestamp.isoformat(),
            'is_normal': self.is_normal(),
            'recommendation': self.get_recommendation(),
            'category': self.get_category()
        }

    def __str__(self):
        """String representation of the metric"""
        return f"{self._value:.1f} {self._unit}"

    def __repr__(self):
        """Official string representation"""
        return f"{self.__class__.__name__}(value={self._value}, unit='{self._unit}')"


# ==================== INTERFACE CLASS (For Polymorphism) ====================

class Alertable(ABC):
    """Interface for objects that can generate alerts"""

    @abstractmethod
    def check_for_alerts(self) -> List['Alert']:
        """Check if this reading should generate alerts"""
        pass


# ==================== COMPOSITION CLASSES ====================

@dataclass
class TimeRange:
    """Represents a time range for data queries"""
    start_date: datetime
    end_date: datetime

    def is_valid(self) -> bool:
        """Check if time range is valid"""
        return self.start_date <= self.end_date

    def duration_days(self) -> int:
        """Get duration in days"""
        delta = self.end_date - self.start_date
        return delta.days


# ==================== CONCRETE METRIC CLASSES (Inheritance) ====================

class BloodPressure(HealthMetric, Alertable):
    """
    Blood Pressure metric class
    Demonstrates: Inheritance, Polymorphism, Encapsulation
    """

    def __init__(self, systolic: int, diastolic: int, timestamp: datetime = None):
        # Store as tuple for systolic/diastolic
        self._systolic = systolic
        self._diastolic = diastolic
        # Calculate mean arterial pressure as representative value
        map_value = diastolic + (systolic - diastolic) / 3
        super().__init__(map_value, timestamp)
        self._unit = "mmHg"
        self._validate_input()

    def _validate_input(self):
        """Validate blood pressure values"""
        if not (50 <= self._systolic <= 250):
            raise InvalidValueError("Systolic BP", self._systolic, "50-250 mmHg")
        if not (30 <= self._diastolic <= 150):
            raise InvalidValueError("Diastolic BP", self._diastolic, "30-150 mmHg")
        if self._systolic <= self._diastolic:
            raise ValueError("Systolic must be greater than diastolic")

    @property
    def systolic(self) -> int:
        """Get systolic blood pressure"""
        return self._systolic

    @property
    def diastolic(self) -> int:
        """Get diastolic blood pressure"""
        return self._diastolic

    def is_normal(self) -> bool:
        """Check if blood pressure is normal"""
        return (90 <= self._systolic <= 120) and (60 <= self._diastolic <= 80)

    def get_category(self) -> str:
        """Get BP category"""
        if self._systolic < 90 or self._diastolic < 60:
            return "Low"
        elif 90 <= self._systolic <= 120 and 60 <= self._diastolic <= 80:
            return "Normal"
        elif 121 <= self._systolic <= 129 and self._diastolic <= 80:
            return "Elevated"
        elif 130 <= self._systolic <= 139 or 80 <= self._diastolic <= 89:
            return "Stage 1 Hypertension"
        else:
            return "Stage 2 Hypertension"

    def get_recommendation(self) -> str:
        """Get BP-specific recommendations"""
        category = self.get_category()

        recommendations = {
            "Low": "Low blood pressure. Stay hydrated and consider increasing salt intake.",
            "Normal": "Blood pressure is optimal. Maintain healthy lifestyle.",
            "Elevated": "Elevated blood pressure. Consider lifestyle changes.",
            "Stage 1 Hypertension": "Stage 1 hypertension. Consult healthcare provider.",
            "Stage 2 Hypertension": "Stage 2 hypertension. Seek medical attention."
        }

        return recommendations.get(category, "Monitor your blood pressure regularly.")

    def check_for_alerts(self) -> List['Alert']:
        """Generate alerts for abnormal blood pressure"""
        alerts = []
        if self._systolic > 140 or self._diastolic > 90:
            alerts.append(Alert(
                alert_type="High Blood Pressure",
                message=f"High BP detected: {self._systolic}/{self._diastolic} mmHg",
                severity=Severity.HIGH
            ))
        elif self._systolic < 90 or self._diastolic < 60:
            alerts.append(Alert(
                alert_type="Low Blood Pressure",
                message=f"Low BP detected: {self._systolic}/{self._diastolic} mmHg",
                severity=Severity.MEDIUM
            ))
        return alerts

    def __str__(self):
        return f"BP: {self._systolic}/{self._diastolic} mmHg"

    def to_dict(self) -> Dict[str, Any]:
        """Extended dictionary representation"""
        base_dict = super().to_dict()
        base_dict.update({
            'systolic': self._systolic,
            'diastolic': self._diastolic,
            'category': self.get_category()
        })
        return base_dict


class GlucoseLevel(HealthMetric, Alertable):
    """
    Blood Glucose metric class
    Demonstrates: Multiple constructors (factory method)
    """

    def __init__(self, level: float, is_fasting: bool = True,
                 timestamp: datetime = None, meal_time: Optional[str] = None):
        super().__init__(level, timestamp)
        self._is_fasting = is_fasting
        self._meal_time = meal_time  # "before_meal", "after_meal", "random"
        self._unit = "mg/dL"
        self._validate_input()

    @classmethod
    def create_fasting(cls, level: float, timestamp: datetime = None):
        """Factory method for fasting glucose"""
        return cls(level, is_fasting=True, timestamp=timestamp, meal_time=None)

    @classmethod
    def create_post_prandial(cls, level: float, hours_after_meal: int = 2,
                             timestamp: datetime = None):
        """Factory method for post-prandial glucose"""
        meal_time = f"{hours_after_meal}h_post_meal"
        return cls(level, is_fasting=False, timestamp=timestamp, meal_time=meal_time)

    def _validate_input(self):
        """Validate glucose level"""
        if not (20 <= self._value <= 600):
            raise InvalidValueError("Glucose level", self._value, "20-600 mg/dL")

    @property
    def is_fasting(self) -> bool:
        return self._is_fasting

    @property
    def meal_time(self) -> Optional[str]:
        return self._meal_time

    def is_normal(self) -> bool:
        """Check if glucose level is normal"""
        if self._is_fasting:
            return 70 <= self._value <= 100
        else:
            # Post-prandial (2 hours after meal)
            return self._value < 140

    def get_category(self) -> str:
        """Get glucose category"""
        if self._is_fasting:
            if self._value < 70:
                return "Hypoglycemia"
            elif 70 <= self._value <= 100:
                return "Normal"
            elif 101 <= self._value <= 125:
                return "Prediabetes"
            else:
                return "Diabetes"
        else:
            if self._value < 140:
                return "Normal"
            elif 140 <= self._value <= 199:
                return "Prediabetes"
            else:
                return "Diabetes"

    def get_recommendation(self) -> str:
        """Get glucose-specific recommendations"""
        category = self.get_category()

        recommendations = {
            "Hypoglycemia": "Low glucose level. Eat a snack with carbohydrates.",
            "Normal": "Glucose levels are normal. Maintain healthy diet.",
            "Prediabetes": "Prediabetes range. Consider lifestyle changes and consult doctor.",
            "Diabetes": "Diabetes range. Consult healthcare provider immediately."
        }

        return recommendations.get(category, "Monitor glucose levels regularly.")

    def check_for_alerts(self) -> List['Alert']:
        """Generate alerts for abnormal glucose"""
        alerts = []
        category = self.get_category()

        if category == "Hypoglycemia":
            alerts.append(Alert(
                alert_type="Low Glucose",
                message=f"Low glucose detected: {self._value} mg/dL",
                severity=Severity.HIGH
            ))
        elif category == "Diabetes":
            alerts.append(Alert(
                alert_type="High Glucose",
                message=f"High glucose detected: {self._value} mg/dL",
                severity=Severity.HIGH
            ))
        elif category == "Prediabetes":
            alerts.append(Alert(
                alert_type="Elevated Glucose",
                message=f"Elevated glucose: {self._value} mg/dL",
                severity=Severity.MEDIUM
            ))

        return alerts


class Weight(HealthMetric):
    """
    Weight metric class with BMI calculation
    Demonstrates: Composition (BMI calculation)
    """

    def __init__(self, weight: float, height: float, timestamp: datetime = None):
        super().__init__(weight, timestamp)
        self._height = height  # in cm
        self._unit = "kg"
        self._bmi = self._calculate_bmi()
        self._validate_input()

    def _validate_input(self):
        """Validate weight and height"""
        if not (20 <= self._value <= 300):
            raise InvalidValueError("Weight", self._value, "20-300 kg")
        if not (100 <= self._height <= 250):
            raise InvalidValueError("Height", self._height, "100-250 cm")

    def _calculate_bmi(self) -> float:
        """Calculate Body Mass Index"""
        height_m = self._height / 100
        return self._value / (height_m ** 2)

    @property
    def height(self) -> float:
        return self._height

    @property
    def bmi(self) -> float:
        return self._bmi

    def is_normal(self) -> bool:
        """Check if weight/BMI is normal"""
        return 18.5 <= self._bmi <= 24.9

    def get_category(self) -> str:
        """Get BMI category"""
        if self._bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self._bmi <= 24.9:
            return "Normal"
        elif 25 <= self._bmi <= 29.9:
            return "Overweight"
        else:
            return "Obese"

    def get_recommendation(self) -> str:
        """Get weight-specific recommendations"""
        category = self.get_category()

        recommendations = {
            "Underweight": "Underweight. Consider increasing calorie intake with nutrient-dense foods.",
            "Normal": "Healthy weight. Maintain balanced diet and regular exercise.",
            "Overweight": "Overweight. Consider portion control and increased physical activity.",
            "Obese": "Obese. Consult healthcare provider for weight management plan."
        }

        return recommendations.get(category, "Maintain healthy lifestyle.")

    def get_ideal_weight_range(self) -> Tuple[float, float]:
        """Calculate ideal weight range for height"""
        height_m = self._height / 100
        min_bmi, max_bmi = 18.5, 24.9
        min_weight = min_bmi * (height_m ** 2)
        max_weight = max_bmi * (height_m ** 2)
        return round(min_weight, 1), round(max_weight, 1)

    def __str__(self):
        return f"Weight: {self._value} kg, Height: {self._height} cm, BMI: {self._bmi:.1f}"


class Exercise(HealthMetric):
    """
    Exercise metric class
    Demonstrates: Polymorphism with different activity types
    """

    # Class variable for exercise intensity levels
    INTENSITY_LEVELS = {
        'Walking': 'Light',
        'Yoga': 'Light',
        'Cycling': 'Moderate',
        'Swimming': 'Moderate',
        'Running': 'Vigorous',
        'HIIT': 'Vigorous'
    }

    def __init__(self, minutes: int, activity_type: str = "General",
                 intensity: Optional[str] = None, timestamp: datetime = None):
        super().__init__(minutes, timestamp)
        self._activity_type = activity_type
        self._intensity = intensity or self._determine_intensity(activity_type)
        self._unit = "minutes"
        self._validate_input()

    @staticmethod
    def _determine_intensity(activity_type: str) -> str:
        """Determine intensity based on activity type"""
        return Exercise.INTENSITY_LEVELS.get(activity_type, "Moderate")

    def _validate_input(self):
        """Validate exercise minutes"""
        if not (0 <= self._value <= 1440):  # Max 24 hours
            raise InvalidValueError("Exercise minutes", self._value, "0-1440 minutes")

    @property
    def activity_type(self) -> str:
        return self._activity_type

    @property
    def intensity(self) -> str:
        return self._intensity

    def is_normal(self) -> bool:
        """Check if exercise is sufficient"""
        # WHO recommends at least 150 minutes of moderate exercise per week
        # This is a daily check, so we'll use 30 minutes as daily target
        return self._value >= 30

    def get_category(self) -> str:
        """Get exercise category"""
        if self._value == 0:
            return "Sedentary"
        elif 1 <= self._value <= 29:
            return "Light Activity"
        elif 30 <= self._value <= 59:
            return "Moderate Activity"
        elif 60 <= self._value <= 119:
            return "Active"
        else:
            return "Very Active"

    def get_recommendation(self) -> str:
        """Get exercise recommendations"""
        category = self.get_category()

        recommendations = {
            "Sedentary": "No exercise recorded. Aim for at least 30 minutes daily.",
            "Light Activity": f"Only {self._value} minutes of exercise. Try to reach 30 minutes.",
            "Moderate Activity": f"Good! {self._value} minutes of exercise. Keep it up!",
            "Active": f"Excellent! {self._value} minutes of exercise. You're meeting goals!",
            "Very Active": f"Outstanding! {self._value} minutes of exercise. Maintain this level."
        }

        return recommendations.get(category, "Stay active!")

    def calculate_calories_burned(self, weight_kg: float) -> float:
        """Estimate calories burned based on activity"""
        # MET values for different intensities
        met_values = {
            'Light': 3.5,
            'Moderate': 5.0,
            'Vigorous': 8.0
        }

        met = met_values.get(self._intensity, 5.0)
        hours = self._value / 60
        calories = met * weight_kg * hours
        return round(calories, 1)

    def __str__(self):
        return f"Exercise: {self._value} min {self._activity_type} ({self._intensity})"


class HeartRate(HealthMetric, Alertable):
    """
    Heart Rate metric class
    Demonstrates: Complex validation with age consideration
    """

    def __init__(self, rate: int, age: Optional[int] = None,
                 condition: str = "Resting", timestamp: datetime = None):
        super().__init__(rate, timestamp)
        self._age = age
        self._condition = condition  # Resting, During Exercise, After Exercise
        self._unit = "bpm"
        self._validate_input()

    def _validate_input(self):
        """Validate heart rate"""
        if not (30 <= self._value <= 220):
            raise InvalidValueError("Heart rate", self._value, "30-220 bpm")

    @property
    def condition(self) -> str:
        return self._condition

    def get_max_heart_rate(self) -> int:
        """Calculate maximum heart rate (220 - age)"""
        if self._age:
            return 220 - self._age
        return 220  # Default if age not provided

    def get_target_zones(self) -> Dict[str, Tuple[int, int]]:
        """Calculate heart rate zones"""
        max_hr = self.get_max_heart_rate()

        return {
            "Resting": (60, 100),
            "Light": (int(max_hr * 0.5), int(max_hr * 0.6)),
            "Moderate": (int(max_hr * 0.6), int(max_hr * 0.7)),
            "Vigorous": (int(max_hr * 0.7), int(max_hr * 0.85)),
            "Maximum": (int(max_hr * 0.85), max_hr)
        }

    def is_normal(self) -> bool:
        """Check if heart rate is normal for condition"""
        if self._condition == "Resting":
            return 60 <= self._value <= 100
        else:
            # During/after exercise, higher rates are normal
            return True

    def get_category(self) -> str:
        """Get heart rate category"""
        if self._condition == "Resting":
            if self._value < 60:
                return "Bradycardia"
            elif 60 <= self._value <= 100:
                return "Normal"
            else:
                return "Tachycardia"
        else:
            zones = self.get_target_zones()
            for zone_name, (min_zone, max_zone) in zones.items():
                if min_zone <= self._value <= max_zone:
                    return f"In {zone_name} Zone"
            return "Above Maximum"

    def get_recommendation(self) -> str:
        """Get heart rate recommendations"""
        category = self.get_category()

        if self._condition == "Resting":
            recommendations = {
                "Bradycardia": "Low resting heart rate. Consult doctor if symptomatic.",
                "Normal": "Normal resting heart rate. Good cardiovascular health.",
                "Tachycardia": "High resting heart rate. Consider stress reduction techniques."
            }
            return recommendations.get(category, "Monitor heart rate regularly.")
        else:
            return f"Heart rate is {category} for {self._condition.lower()} condition."

    def check_for_alerts(self) -> List['Alert']:
        """Generate alerts for abnormal heart rate"""
        alerts = []
        if self._condition == "Resting":
            if self._value > 100:
                alerts.append(Alert(
                    alert_type="High Resting Heart Rate",
                    message=f"High resting heart rate: {self._value} bpm",
                    severity=Severity.MEDIUM
                ))
            elif self._value < 60:
                alerts.append(Alert(
                    alert_type="Low Resting Heart Rate",
                    message=f"Low resting heart rate: {self._value} bpm",
                    severity=Severity.MEDIUM
                ))
        return alerts


# ==================== USER & RELATED CLASSES ====================

class User:
    """
    User class with comprehensive health tracking
    Demonstrates: Encapsulation, Composition, Methods
    """

    def __init__(self, user_id: int, name: str, age: int, gender: str, email: str):
        # Private attributes (Encapsulation)
        self._user_id = user_id
        self._name = name
        self._age = age
        self._gender = gender
        self._email = email
        self._health_metrics: List[HealthMetric] = []
        self._alerts: List['Alert'] = []
        self._goals: List['HealthGoal'] = []

        # Validate inputs
        self._validate_user()

    def _validate_user(self):
        """Validate user data"""
        if not isinstance(self._age, int) or not (1 <= self._age <= 120):
            raise ValueError(f"Invalid age: {self._age}")
        if not self._email or '@' not in self._email:
            raise ValueError(f"Invalid email: {self._email}")

    # Getter methods (Encapsulation)
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def age(self) -> int:
        return self._age

    @property
    def gender(self) -> str:
        return self._gender

    @property
    def email(self) -> str:
        return self._email

    def add_metric(self, metric: HealthMetric):
        """Add a health metric with automatic alert checking"""
        self._health_metrics.append(metric)

        # Check for alerts if metric implements Alertable
        if isinstance(metric, Alertable):
            new_alerts = metric.check_for_alerts()
            self._alerts.extend(new_alerts)

    def get_metrics_by_type(self, metric_type: type) -> List[HealthMetric]:
        """Get metrics of specific type"""
        return [m for m in self._health_metrics if isinstance(m, metric_type)]

    def get_recent_metrics(self, n: int = 10) -> List[HealthMetric]:
        """Get recent health metrics"""
        sorted_metrics = sorted(self._health_metrics,
                                key=lambda x: x.timestamp,
                                reverse=True)
        return sorted_metrics[:n]

    def add_alert(self, alert: 'Alert'):
        """Add an alert"""
        self._alerts.append(alert)

    def get_unread_alerts(self) -> List['Alert']:
        """Get unread alerts"""
        return [alert for alert in self._alerts if not alert.is_read]

    def mark_alerts_read(self):
        """Mark all alerts as read"""
        for alert in self._alerts:
            alert.mark_read()

    def add_goal(self, goal: 'HealthGoal'):
        """Add a health goal"""
        self._goals.append(goal)

    def get_active_goals(self) -> List['HealthGoal']:
        """Get active (not completed) health goals"""
        return [goal for goal in self._goals if not goal.is_completed]

    def get_health_summary(self, time_range: Optional[TimeRange] = None) -> Dict:
        """Generate comprehensive health summary"""
        # Filter metrics by time range if provided
        metrics_in_range = self._health_metrics
        if time_range and time_range.is_valid():
            metrics_in_range = [
                m for m in self._health_metrics
                if time_range.start_date <= m.timestamp <= time_range.end_date
            ]

        summary = {
            "user_info": {
                "name": self._name,
                "age": self._age,
                "gender": self._gender
            },
            "time_period": {
                "start": time_range.start_date if time_range else None,
                "end": time_range.end_date if time_range else None,
                "days": time_range.duration_days() if time_range else None
            },
            "metrics_summary": {
                "total_metrics": len(metrics_in_range),
                "by_type": {},
                "normal_count": 0,
                "abnormal_count": 0
            },
            "alerts": {
                "total": len(self._alerts),
                "unread": len(self.get_unread_alerts()),
                "by_severity": {}
            },
            "goals": {
                "total": len(self._goals),
                "active": len(self.get_active_goals()),
                "completed": len([g for g in self._goals if g.is_completed])
            }
        }

        # Analyze metrics
        for metric in metrics_in_range:
            metric_type = metric.__class__.__name__
            if metric_type not in summary["metrics_summary"]["by_type"]:
                summary["metrics_summary"]["by_type"][metric_type] = 0
            summary["metrics_summary"]["by_type"][metric_type] += 1

            if metric.is_normal():
                summary["metrics_summary"]["normal_count"] += 1
            else:
                summary["metrics_summary"]["abnormal_count"] += 1

        # Analyze alerts by severity
        for alert in self._alerts:
            severity = alert.severity.value
            if severity not in summary["alerts"]["by_severity"]:
                summary["alerts"]["by_severity"][severity] = 0
            summary["alerts"]["by_severity"][severity] += 1

        return summary

    def calculate_trends(self, metric_type: type, days: int = 30) -> Dict:
        """Calculate trends for a specific metric type"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        metrics = [
            m for m in self.get_metrics_by_type(metric_type)
            if start_date <= m.timestamp <= end_date
        ]

        if not metrics:
            return {"error": f"No {metric_type.__name__} data found for last {days} days"}

        # Sort by date
        metrics.sort(key=lambda x: x.timestamp)

        # Calculate averages and changes
        if metric_type == BloodPressure:
            systolic_avg = sum(m.systolic for m in metrics) / len(metrics)
            diastolic_avg = sum(m.diastolic for m in metrics) / len(metrics)

            return {
                "metric_type": "Blood Pressure",
                "period_days": days,
                "readings_count": len(metrics),
                "average_systolic": round(systolic_avg, 1),
                "average_diastolic": round(diastolic_avg, 1),
                "trend": "Improving" if len(metrics) > 1 and metrics[-1].systolic < metrics[0].systolic else "Stable"
            }

        elif metric_type == GlucoseLevel:
            values = [m.value for m in metrics]
            avg = sum(values) / len(values)

            return {
                "metric_type": "Glucose",
                "period_days": days,
                "readings_count": len(metrics),
                "average_level": round(avg, 1),
                "min_level": min(values),
                "max_level": max(values),
                "variability": round(max(values) - min(values), 1)
            }

        elif metric_type == Weight:
            values = [m.value for m in metrics]
            avg = sum(values) / len(values)

            return {
                "metric_type": "Weight",
                "period_days": days,
                "readings_count": len(metrics),
                "average_weight": round(avg, 1),
                "weight_change": round(values[-1] - values[0], 1) if len(values) > 1 else 0,
                "bmi_trend": "Decreasing" if len(values) > 1 and values[-1] < values[0] else "Increasing"
            }

        return {"error": "Trend analysis not available for this metric type"}

    def __str__(self):
        return f"User: {self._name} (ID: {self._user_id}, Age: {self._age})"


# ==================== ALERT CLASS ====================

class Alert:
    """
    Alert/Notification class
    Demonstrates: Composition with User, Enum usage
    """

    def __init__(self, alert_type: str, message: str,
                 severity: Severity = Severity.MEDIUM):
        self._alert_type = alert_type
        self._message = message
        self._severity = severity
        self._timestamp = datetime.now()
        self._is_read = False
        self._resolved = False
        self._resolved_date = None

    @property
    def alert_type(self) -> str:
        return self._alert_type

    @property
    def message(self) -> str:
        return self._message

    @property
    def severity(self) -> Severity:
        return self._severity

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def is_read(self) -> bool:
        return self._is_read

    @property
    def resolved(self) -> bool:
        return self._resolved

    @property
    def resolved_date(self) -> Optional[datetime]:
        return self._resolved_date

    def mark_read(self):
        """Mark alert as read"""
        self._is_read = True

    def mark_resolved(self):
        """Mark alert as resolved"""
        self._resolved = True
        self._resolved_date = datetime.now()

    def get_priority(self) -> int:
        """Get numerical priority (lower = higher priority)"""
        priority_map = {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 3,
            Severity.LOW: 4
        }
        return priority_map.get(self._severity, 5)

    def __str__(self):
        status = "READ" if self._is_read else "UNREAD"
        resolved = "RESOLVED" if self._resolved else "PENDING"
        return f"[{self._severity.value}] {self._alert_type}: {self._message} ({status}, {resolved})"


# ==================== HEALTH GOAL CLASS ====================

class HealthGoal:
    """
    Health Goal class for tracking objectives
    Demonstrates: State management, Progress tracking
    """

    def __init__(self, goal_type: str, target_value: float,
                 current_value: float, start_date: date = None,
                 end_date: date = None, unit: str = ""):
        self._goal_type = goal_type
        self._target_value = target_value
        self._current_value = current_value
        self._start_date = start_date or date.today()
        self._end_date = end_date
        self._unit = unit
        self._is_completed = False
        self._completed_date = None

        self._validate_goal()

    def _validate_goal(self):
        """Validate goal parameters"""
        if self._target_value <= 0:
            raise ValueError("Target value must be positive")
        if self._end_date and self._end_date <= self._start_date:
            raise ValueError("End date must be after start date")

    @property
    def goal_type(self) -> str:
        return self._goal_type

    @property
    def target_value(self) -> float:
        return self._target_value

    @property
    def current_value(self) -> float:
        return self._current_value

    @current_value.setter
    def current_value(self, value: float):
        """Update current value and check if goal is achieved"""
        self._current_value = value
        self._check_completion()

    @property
    def progress(self) -> float:
        """Calculate progress percentage"""
        if self._target_value == 0:
            return 0
        progress = (self._current_value / self._target_value) * 100
        return min(progress, 100)  # Cap at 100%

    @property
    def is_completed(self) -> bool:
        return self._is_completed

    def _check_completion(self):
        """Check if goal has been achieved"""
        if self._current_value >= self._target_value and not self._is_completed:
            self._is_completed = True
            self._completed_date = date.today()

    def get_remaining(self) -> float:
        """Get remaining value to achieve goal"""
        return max(0, self._target_value - self._current_value)

    def get_days_remaining(self) -> Optional[int]:
        """Get days remaining until end date"""
        if not self._end_date:
            return None
        remaining = (self._end_date - date.today()).days
        return max(0, remaining)

    def __str__(self):
        status = "✓ Completed" if self._is_completed else f"⏳ {self.progress:.1f}%"
        remaining = self.get_remaining()
        return f"{self._goal_type}: {self._current_value}/{self._target_value} {self._unit} ({status})"


# ==================== HEALTH ANALYZER (Polymorphism) ====================

class HealthAnalyzer:
    """
    Health Analyzer class using polymorphism
    Demonstrates: Polymorphism, Strategy Pattern
    """

    @staticmethod
    def analyze_metrics(metrics: List[HealthMetric]) -> Dict:
        """
        Polymorphic method that works with any HealthMetric subclass
        """
        analysis = {
            "total_metrics": len(metrics),
            "normal_count": 0,
            "abnormal_count": 0,
            "metric_types": {},
            "category_distribution": {},
            "details": []
        }

        for metric in metrics:
            # Polymorphism in action - same method call, different behaviors
            is_normal = metric.is_normal()
            category = metric.get_category()
            metric_type = metric.__class__.__name__

            # Update counts
            if is_normal:
                analysis["normal_count"] += 1
            else:
                analysis["abnormal_count"] += 1

            # Update type distribution
            if metric_type not in analysis["metric_types"]:
                analysis["metric_types"][metric_type] = 0
            analysis["metric_types"][metric_type] += 1

            # Update category distribution
            if category not in analysis["category_distribution"]:
                analysis["category_distribution"][category] = 0
            analysis["category_distribution"][category] += 1

            # Add detailed analysis
            analysis["details"].append({
                "type": metric_type,
                "value": str(metric),
                "category": category,
                "is_normal": is_normal,
                "recommendation": metric.get_recommendation(),
                "timestamp": metric.timestamp
            })

        # Calculate percentages
        if analysis["total_metrics"] > 0:
            analysis["normal_percentage"] = (analysis["normal_count"] / analysis["total_metrics"]) * 100
            analysis["abnormal_percentage"] = (analysis["abnormal_count"] / analysis["total_metrics"]) * 100

        return analysis

    @staticmethod
    def analyze_trend(metrics: List[HealthMetric]) -> Dict:
        """Analyze trends over time for a series of metrics"""
        if len(metrics) < 2:
            return {"error": "Insufficient data for trend analysis"}

        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda x: x.timestamp)

        # Get first and last values
        first = sorted_metrics[0]
        last = sorted_metrics[-1]

        # Calculate days between
        days_diff = (last.timestamp - first.timestamp).days

        trend_analysis = {
            "period_days": days_diff,
            "readings_count": len(metrics),
            "first_reading": {
                "value": str(first),
                "timestamp": first.timestamp,
                "category": first.get_category()
            },
            "last_reading": {
                "value": str(last),
                "timestamp": last.timestamp,
                "category": last.get_category()
            }
        }

        # For numeric metrics, calculate change
        if hasattr(first, 'value') and hasattr(last, 'value'):
            value_change = last.value - first.value
            percent_change = (value_change / first.value * 100) if first.value != 0 else 0

            trend_analysis.update({
                "value_change": round(value_change, 2),
                "percent_change": round(percent_change, 2),
                "trend_direction": "Improving" if value_change < 0 else "Worsening" if value_change > 0 else "Stable"
            })

        return trend_analysis


# ==================== FACTORY PATTERN ====================

class HealthMetricFactory:
    """
    Factory class for creating health metrics
    Demonstrates: Factory Pattern, Error Handling
    """

    @staticmethod
    def create_metric(metric_type: str, **kwargs) -> HealthMetric:
        """Factory method to create health metrics"""
        try:
            if metric_type.lower() == 'blood_pressure' or metric_type == 'BP':
                systolic = kwargs.get('systolic')
                diastolic = kwargs.get('diastolic')
                if systolic is None or diastolic is None:
                    raise ValueError("Both systolic and diastolic values are required for BP")
                return BloodPressure(systolic, diastolic, kwargs.get('timestamp'))

            elif metric_type.lower() == 'glucose':
                level = kwargs.get('level')
                if level is None:
                    raise ValueError("Glucose level is required")
                is_fasting = kwargs.get('is_fasting', True)
                return GlucoseLevel(level, is_fasting, kwargs.get('timestamp'), kwargs.get('meal_time'))

            elif metric_type.lower() == 'weight':
                weight = kwargs.get('weight')
                height = kwargs.get('height')
                if weight is None or height is None:
                    raise ValueError("Both weight and height are required")
                return Weight(weight, height, kwargs.get('timestamp'))

            elif metric_type.lower() == 'exercise':
                minutes = kwargs.get('minutes')
                if minutes is None:
                    raise ValueError("Exercise minutes are required")
                return Exercise(minutes,
                                kwargs.get('activity_type', 'General'),
                                kwargs.get('intensity'),
                                kwargs.get('timestamp'))

            elif metric_type.lower() in ['heart_rate', 'heartrate']:
                rate = kwargs.get('rate')
                if rate is None:
                    raise ValueError("Heart rate is required")
                return HeartRate(rate,
                                 kwargs.get('age'),
                                 kwargs.get('condition', 'Resting'),
                                 kwargs.get('timestamp'))

            else:
                raise ValueError(f"Unknown metric type: {metric_type}")

        except Exception as e:
            # Enhanced error handling with context
            raise HealthMetricError(f"Failed to create {metric_type} metric: {str(e)}") from e

    @staticmethod
    def create_from_dict(data: Dict) -> HealthMetric:
        """Create metric from dictionary representation"""
        metric_type = data.get('type', '').lower()

        # Map type names to our metric classes
        type_mapping = {
            'bloodpressure': 'blood_pressure',
            'glucoselevel': 'glucose',
            'weight': 'weight',
            'exercise': 'exercise',
            'heartrate': 'heart_rate'
        }

        actual_type = type_mapping.get(metric_type, metric_type)

        # Remove type from data as it's not a constructor parameter
        data_copy = data.copy()
        if 'type' in data_copy:
            del data_copy['type']

        return HealthMetricFactory.create_metric(actual_type, **data_copy)


# ==================== SINGLETON PATTERN (Optional) ====================

class HealthMonitor:
    """
    Singleton class for managing health monitoring system
    Demonstrates:Singleton Pattern, System Management
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._users: Dict[int, User] = {}
            self._analyzers: List[HealthAnalyzer] = []
            self._initialized = True

    def register_user(self, user: User):
        """Register a new user"""
        if user.user_id in self._users:
            raise ValueError(f"User with ID {user.user_id} already exists")
        self._users[user.user_id] = user

    def get_user(self, user_id: int) -> User:
        """Get user by ID"""
        if user_id not in self._users:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return self._users[user_id]

    def get_all_alerts(self) -> List[Alert]:
        """Get all alerts from all users"""
        all_alerts = []
        for user in self._users.values():
            all_alerts.extend(user._alerts)
        return all_alerts

    def get_critical_alerts(self) -> List[Alert]:
        """Get all critical alerts (low or high)"""
        return [alert for alert in self.get_all_alerts()
                if alert.severity in [Severity.CRITICAL, Severity.HIGH]]

    def __str__(self):
        return f"HealthMonitor: {len(self._users)} users, {len(self.get_all_alerts())} total alerts"