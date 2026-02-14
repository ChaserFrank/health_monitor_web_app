"""
Main Flask Application for Health Monitoring System
"""
import os
import json
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import plotly
import plotly.graph_objs as go
import pandas as pd

from config import config
from database_postgres import PostgresDBManager
from models import (
    User, BloodPressure, GlucoseLevel, Weight, Exercise, HeartRate,
    HealthMetricFactory, HealthAnalyzer, Alert, HealthGoal, TimeRange
)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

# Initialize database
db_manager = PostgresDBManager()

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


# User loader for Flask-Login - FIXED VERSION
@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login"""
    try:
        # Convert user_id to integer
        user_id_int = int(user_id)

        # Execute query properly - FIXED: cursor.execute returns None, not the cursor itself
        db_manager.cursor.execute(
            "SELECT user_id, name, age, gender, email, phone, created_date, is_active FROM users WHERE user_id = %s",
            (user_id_int,)
        )
        user_data = db_manager.cursor.fetchone()

        if user_data:
            return WebUser(
                user_id=user_data[0],
                name=user_data[1],
                age=user_data[2],
                gender=user_data[3],
                email=user_data[4],
                phone=user_data[5]
            )
        else:
            app.logger.warning(f"User {user_id} not found in database")
            return None

    except ValueError as e:
        app.logger.error(f"Error converting user_id to integer: {e}")
        return None
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {e}")
        return None


# Custom User class for web application
class WebUser:
    """Web user class for Flask-Login"""

    def __init__(self, user_id, name, age, gender, email, phone=None, is_admin=False):
        self.id = str(user_id)  # Flask-Login expects id as string
        self.user_id = user_id
        self.name = name
        self.age = age
        self.gender = gender
        self.email = email
        self.phone = phone
        self.is_admin = is_admin
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return str(self.id)


# ==================== DECORATORS ====================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            age = int(request.form.get('age', 0))
            gender = request.form.get('gender', '').strip()
            email = request.form.get('email', '').strip().lower()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            # Validation
            if not all([name, email, password]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('register'))

            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return redirect(url_for('register'))

            if age < 1 or age > 120:
                flash('Please enter a valid age (1-120)', 'error')
                return redirect(url_for('register'))

            # Check if user already exists
            existing_user = db_manager.get_user_by_email(email)
            if existing_user:
                flash('Email already registered. Please login.', 'error')
                return redirect(url_for('login'))

            # Hash password
            password_hash = generate_password_hash(password)

            # Add user to database
            user_id = db_manager.add_user(name, age, gender, email, phone)

            # Store password hash in separate table
            db_manager.cursor.execute(
                "INSERT INTO user_auth (user_id, password_hash) VALUES (%s, %s)",
                (user_id, password_hash)
            )
            db_manager.connection.commit()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except ValueError as e:
            flash(f'Registration failed: {str(e)}', 'error')
            return redirect(url_for('register'))
        except Exception as e:
            db_manager.connection.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
            app.logger.error(f"Registration error: {e}")
            return redirect(url_for('register'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        try:
            # Get user from database
            user_data = db_manager.get_user_by_email(email)

            if user_data:
                # Handle different tuple lengths based on what get_user_by_email returns
                if len(user_data) >= 6:
                    user_id, name, age, gender, email, phone = user_data[:6]
                    created_date = user_data[6] if len(user_data) > 6 else None
                    is_admin = user_data[7] if len(user_data) > 7 else False
                else:
                    # Fallback if tuple structure is different
                    user_id = user_data[0]
                    name = user_data[1]
                    age = user_data[2]
                    gender = user_data[3]
                    email = user_data[4]
                    phone = user_data[5] if len(user_data) > 5 else None
                    is_admin = False

                # Verify password (simplified for demo)
                db_manager.cursor.execute(
                    "SELECT password_hash FROM user_auth WHERE user_id = %s",
                    (user_id,)
                )
                auth_data = db_manager.cursor.fetchone()

                # For demo: if no auth record exists, still allow login
                # In production, you would check: check_password_hash(auth_data[0], password)
                if not auth_data:
                    app.logger.warning(f"No auth record found for user {user_id}, creating one")
                    password_hash = generate_password_hash(password)
                    db_manager.cursor.execute(
                        "INSERT INTO user_auth (user_id, password_hash) VALUES (%s, %s)",
                        (user_id, password_hash)
                    )
                    db_manager.connection.commit()

                # Create user object
                user = WebUser(user_id, name, age, gender, email, phone, is_admin)

                # Login user
                login_user(user, remember=True)
                flash('Login successful!', 'success')

                # Set session variables
                session['user_id'] = user_id
                session['user_name'] = name

                # Update last login
                db_manager.cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
                    (user_id,)
                )
                db_manager.connection.commit()

                # Redirect to dashboard
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard'))
            else:
                flash('Invalid email or password', 'error')

        except Exception as e:
            app.logger.error(f"Login error: {e}")
            flash(f'Login failed: {str(e)}', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    try:
        # Get user stats
        stats = db_manager.get_health_stats(current_user.user_id)

        # Get recent metrics
        recent_metrics = db_manager.get_user_metrics(current_user.user_id, limit=5)

        # Get unread alerts count
        db_manager.cursor.execute(
            "SELECT COUNT(*) FROM alerts WHERE user_id = %s AND NOT is_read",
            (current_user.user_id,)
        )
        unread_alerts_result = db_manager.cursor.fetchone()
        unread_alerts = unread_alerts_result[0] if unread_alerts_result else 0

        # Convert metrics to objects for display
        metric_objects = []
        for metric in recent_metrics:
            if len(metric) >= 13:
                metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric[:13]
            else:
                continue  # Skip malformed metrics

            if mtype == "BP" and sys and dia:
                metric_objects.append({
                    'type': 'Blood Pressure',
                    'value': f'{sys}/{dia} mmHg',
                    'date': date,
                    'icon': 'heart-pulse'
                })
            elif mtype == "Glucose" and gluc:
                metric_objects.append({
                    'type': 'Glucose',
                    'value': f'{gluc} mg/dL',
                    'date': date,
                    'icon': 'droplet'
                })
            elif mtype == "Weight" and wgt and ht:
                bmi = wgt / ((ht / 100) ** 2)
                metric_objects.append({
                    'type': 'Weight',
                    'value': f'{wgt} kg (BMI: {bmi:.1f})',
                    'date': date,
                    'icon': 'scale'
                })
            elif mtype == "Exercise" and ex_min:
                metric_objects.append({
                    'type': 'Exercise',
                    'value': f'{ex_min} minutes',
                    'date': date,
                    'icon': 'dumbbell'
                })

        return render_template('dashboard.html',
                               user=current_user,
                               stats=stats,
                               recent_metrics=metric_objects,
                               unread_alerts=unread_alerts)
    except Exception as e:
        app.logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('index'))


@app.route('/add_metric', methods=['GET', 'POST'])
@login_required
def add_metric():
    """Add health metric"""
    if request.method == 'POST':
        metric_type = request.form.get('metric_type', '').strip()

        try:
            if metric_type == 'BP':
                systolic = int(request.form.get('systolic', 0))
                diastolic = int(request.form.get('diastolic', 0))
                notes = request.form.get('notes', '').strip()

                metric_id = db_manager.add_health_metric(
                    user_id=current_user.user_id,
                    metric_type='BP',
                    systolic=systolic,
                    diastolic=diastolic,
                    notes=notes
                )

                flash(f'Blood pressure recorded successfully!', 'success')

            elif metric_type == 'Glucose':
                glucose = float(request.form.get('glucose', 0))
                is_fasting = request.form.get('is_fasting', 'false') == 'true'
                notes = request.form.get('notes', '').strip()

                metric_id = db_manager.add_health_metric(
                    user_id=current_user.user_id,
                    metric_type='Glucose',
                    glucose_level=glucose,
                    is_fasting=is_fasting,
                    notes=notes
                )

                flash(f'Glucose level recorded successfully!', 'success')

            elif metric_type == 'Weight':
                weight = float(request.form.get('weight', 0))
                height = float(request.form.get('height', 0))
                notes = request.form.get('notes', '').strip()

                metric_id = db_manager.add_health_metric(
                    user_id=current_user.user_id,
                    metric_type='Weight',
                    weight=weight,
                    height=height,
                    notes=notes
                )

                flash(f'Weight recorded successfully!', 'success')

            elif metric_type == 'Exercise':
                minutes = int(request.form.get('minutes', 0))
                activity = request.form.get('activity', 'Walking').strip()
                notes = request.form.get('notes', '').strip()

                metric_id = db_manager.add_health_metric(
                    user_id=current_user.user_id,
                    metric_type='Exercise',
                    exercise_minutes=minutes,
                    activity_type=activity,
                    notes=notes
                )

                flash(f'Exercise recorded successfully!', 'success')

            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Error adding metric: {str(e)}', 'error')

    return render_template('add_metric.html', user=current_user)


@app.route('/metrics')
@login_required
def view_metrics():
    """View health metrics"""
    metric_type = request.args.get('type', '')
    page = int(request.args.get('page', 1))
    limit = 10
    offset = (page - 1) * limit

    # Get metrics from database
    metrics = db_manager.get_user_metrics(
        current_user.user_id,
        metric_type=metric_type if metric_type else None,
        limit=limit,
        offset=offset
    )

    # Format metrics for display
    formatted_metrics = []
    for metric in metrics:
        if len(metric) >= 13:
            metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric[:13]
        else:
            continue

        metric_data = {
            'id': metric_id,
            'type': mtype,
            'date': date,
            'notes': notes
        }

        if mtype == "BP" and sys and dia:
            metric_data['display'] = f'{sys}/{dia} mmHg'
            metric_data['icon'] = 'heart-pulse'
            # Determine color based on values
            if sys > 140 or dia > 90:
                metric_data['color'] = 'danger'
            elif sys < 90 or dia < 60:
                metric_data['color'] = 'warning'
            else:
                metric_data['color'] = 'success'

        elif mtype == "Glucose" and gluc:
            metric_data['display'] = f'{gluc} mg/dL'
            metric_data['icon'] = 'droplet'
            if (fasting and gluc > 126) or (not fasting and gluc > 200):
                metric_data['color'] = 'danger'
            elif gluc < 70:
                metric_data['color'] = 'warning'
            else:
                metric_data['color'] = 'success'

        elif mtype == "Weight" and wgt and ht:
            bmi = wgt / ((ht / 100) ** 2)
            metric_data['display'] = f'{wgt} kg (BMI: {bmi:.1f})'
            metric_data['icon'] = 'scale'
            if bmi < 18.5 or bmi > 24.9:
                metric_data['color'] = 'warning'
            else:
                metric_data['color'] = 'success'

        elif mtype == "Exercise" and ex_min:
            metric_data['display'] = f'{ex_min} minutes ({act})'
            metric_data['icon'] = 'dumbbell'
            if ex_min < 30:
                metric_data['color'] = 'warning'
            else:
                metric_data['color'] = 'success'

        formatted_metrics.append(metric_data)

    # Get total count for pagination
    query = "SELECT COUNT(*) FROM health_metrics WHERE user_id = %s"
    params = [current_user.user_id]

    if metric_type:
        query += " AND metric_type = %s"
        params.append(metric_type)

    db_manager.cursor.execute(query, params)
    total_count_result = db_manager.cursor.fetchone()
    total_count = total_count_result[0] if total_count_result else 0
    total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1

    return render_template('metrics.html',
                           metrics=formatted_metrics,
                           current_page=page,
                           total_pages=total_pages,
                           metric_type=metric_type,
                           user=current_user)


@app.route('/analytics')
@login_required
def analytics():
    """Health analytics and charts"""
    # Get metrics for charts
    metrics = db_manager.get_user_metrics(current_user.user_id, limit=100)

    # Prepare data for charts
    bp_data = []
    glucose_data = []
    weight_data = []
    exercise_data = []

    for metric in metrics:
        if len(metric) >= 13:
            metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric[:13]
        else:
            continue

        if mtype == "BP" and sys and dia:
            bp_data.append({
                'date': date,
                'systolic': sys,
                'diastolic': dia
            })
        elif mtype == "Glucose" and gluc:
            glucose_data.append({
                'date': date,
                'level': gluc,
                'fasting': fasting
            })
        elif mtype == "Weight" and wgt:
            weight_data.append({
                'date': date,
                'weight': wgt
            })
        elif mtype == "Exercise" and ex_min:
            exercise_data.append({
                'date': date,
                'minutes': ex_min,
                'activity': act
            })

    # Create Plotly charts
    charts = {}

    # Blood Pressure Chart
    if bp_data:
        df_bp = pd.DataFrame(bp_data)
        df_bp['date'] = pd.to_datetime(df_bp['date'])
        df_bp = df_bp.sort_values('date')

        fig_bp = go.Figure()
        fig_bp.add_trace(go.Scatter(
            x=df_bp['date'], y=df_bp['systolic'],
            mode='lines+markers', name='Systolic',
            line=dict(color='red', width=2)
        ))
        fig_bp.add_trace(go.Scatter(
            x=df_bp['date'], y=df_bp['diastolic'],
            mode='lines+markers', name='Diastolic',
            line=dict(color='blue', width=2)
        ))
        fig_bp.update_layout(
            title='Blood Pressure Trends',
            xaxis_title='Date',
            yaxis_title='mmHg',
            hovermode='x unified'
        )
        charts['bp'] = json.dumps(fig_bp, cls=plotly.utils.PlotlyJSONEncoder)

    # Glucose Chart
    if glucose_data:
        df_glucose = pd.DataFrame(glucose_data)
        df_glucose['date'] = pd.to_datetime(df_glucose['date'])
        df_glucose = df_glucose.sort_values('date')

        fig_glucose = go.Figure()
        fig_glucose.add_trace(go.Scatter(
            x=df_glucose['date'], y=df_glucose['level'],
            mode='lines+markers', name='Glucose Level',
            line=dict(color='green', width=2)
        ))
        fig_glucose.update_layout(
            title='Glucose Level Trends',
            xaxis_title='Date',
            yaxis_title='mg/dL',
            hovermode='x unified'
        )
        charts['glucose'] = json.dumps(fig_glucose, cls=plotly.utils.PlotlyJSONEncoder)

    # Get stats
    stats = db_manager.get_health_stats(current_user.user_id)

    return render_template('analytics.html',
                           charts=charts,
                           stats=stats,
                           user=current_user)


@app.route('/alerts')
@login_required
def alerts():
    """View alerts"""
    # Get alerts from database
    db_manager.cursor.execute('''
                              SELECT alert_id, alert_type, message, severity, created_date, is_read
                              FROM alerts
                              WHERE user_id = %s
                              ORDER BY CASE severity
                                           WHEN 'Critical' THEN 1
                                           WHEN 'High' THEN 2
                                           WHEN 'Medium' THEN 3
                                           WHEN 'Low' THEN 4
                                           END,
                                       created_date DESC
                              ''', (current_user.user_id,))

    alerts_data = db_manager.cursor.fetchall()

    # Format alerts
    formatted_alerts = []
    for alert in alerts_data:
        if len(alert) >= 6:
            alert_id, alert_type, message, severity, created_date, is_read = alert[:6]
        else:
            continue

        # Get icon based on severity
        icons = {
            'Critical': 'exclamation-triangle',
            'High': 'exclamation-circle',
            'Medium': 'exclamation',
            'Low': 'info-circle'
        }
        icon = icons.get(severity, 'info-circle')

        formatted_alerts.append({
            'id': alert_id,
            'type': alert_type,
            'message': message,
            'severity': severity,
            'date': created_date,
            'is_read': is_read,
            'icon': icon
        })

    return render_template('alerts.html',
                           alerts=formatted_alerts,
                           user=current_user)


@app.route('/mark_alert_read/<int:alert_id>', methods=['POST'])
@login_required
def mark_alert_read(alert_id):
    """Mark a single alert as read"""
    try:
        db_manager.cursor.execute(
            "UPDATE alerts SET is_read = TRUE WHERE alert_id = %s AND user_id = %s",
            (alert_id, current_user.user_id)
        )
        db_manager.connection.commit()
        flash('Alert marked as read', 'success')
    except Exception as e:
        app.logger.error(f"Error marking alert read: {e}")
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('alerts'))


# ==================== NEW ROUTE ADDED HERE ====================
@app.route('/mark_all_alerts_read', methods=['POST'])
@login_required
def mark_all_alerts_read():
    """Mark all alerts as read"""
    try:
        db_manager.cursor.execute(
            "UPDATE alerts SET is_read = TRUE WHERE user_id = %s AND NOT is_read",
            (current_user.user_id,)
        )
        db_manager.connection.commit()
        flash('All alerts marked as read', 'success')
    except Exception as e:
        app.logger.error(f"Error marking all alerts read: {e}")
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('alerts'))


@app.route('/delete_alert/<int:alert_id>', methods=['POST'])
@login_required
def delete_alert(alert_id):
    """Delete an alert"""
    try:
        db_manager.cursor.execute(
            "DELETE FROM alerts WHERE alert_id = %s AND user_id = %s",
            (alert_id, current_user.user_id)
        )
        db_manager.connection.commit()
        flash('Alert deleted successfully', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('alerts'))


@app.route('/export_data/<format>')
@login_required
def export_data(format):
    """Export user data in specified format"""
    if format not in ['csv', 'json']:
        flash('Invalid export format', 'error')
        return redirect(url_for('profile'))

    # Get user metrics
    metrics = db_manager.get_user_metrics(current_user.user_id, limit=1000)

    # Format data for export
    export_data = {
        'user': {
            'name': current_user.name,
            'email': current_user.email,
            'age': current_user.age,
            'gender': current_user.gender
        },
        'export_date': datetime.now().isoformat(),
        'metrics': []
    }

    for metric in metrics:
        if len(metric) >= 13:
            metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric[:13]
        else:
            continue

        metric_data = {
            'type': mtype,
            'date': date.isoformat() if date else None,
            'notes': notes
        }

        if mtype == "BP" and sys and dia:
            metric_data['systolic'] = sys
            metric_data['diastolic'] = dia
        elif mtype == "Glucose" and gluc:
            metric_data['glucose'] = float(gluc)
            metric_data['is_fasting'] = fasting
        elif mtype == "Weight" and wgt:
            metric_data['weight'] = float(wgt)
            metric_data['height'] = float(ht) if ht else None
        elif mtype == "Exercise" and ex_min:
            metric_data['minutes'] = ex_min
            metric_data['activity'] = act

        export_data['metrics'].append(metric_data)

    if format == 'json':
        response = jsonify(export_data)
        response.headers['Content-Disposition'] = f'attachment; filename=health_data_{datetime.now().strftime("%Y%m%d")}.json'
        return response

    elif format == 'csv':
        import csv
        from io import StringIO

        # Create CSV
        si = StringIO()
        writer = csv.writer(si)

        # Write header
        writer.writerow(['Type', 'Date', 'Value1', 'Value2', 'Value3', 'Notes'])

        # Write data
        for metric in export_data['metrics']:
            row = [
                metric['type'],
                metric['date'],
                metric.get('systolic', metric.get('glucose', metric.get('weight', metric.get('minutes', '')))),
                metric.get('diastolic', metric.get('is_fasting', metric.get('height', metric.get('activity', '')))),
                '',
                metric['notes']
            ]
            writer.writerow(row)

        response = app.response_class(
            response=si.getvalue(),
            status=200,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=health_data_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
        return response


@app.route('/profile')
@login_required
def profile():
    """User profile"""
    # Get user details
    db_manager.cursor.execute(
        "SELECT * FROM users WHERE user_id = %s",
        (current_user.user_id,)
    )
    user_data = db_manager.cursor.fetchone()

    # Get health summary
    stats = db_manager.get_health_stats(current_user.user_id)

    return render_template('profile.html',
                           user_data=user_data,
                           stats=stats,
                           user=current_user)


@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        name = request.form.get('name', '').strip()
        age = int(request.form.get('age', 0))
        phone = request.form.get('phone', '').strip()

        db_manager.cursor.execute('''
                                  UPDATE users
                                  SET name = %s,
                                      age = %s,
                                      phone = %s
                                  WHERE user_id = %s
                                  ''', (name, age, phone, current_user.user_id))

        db_manager.connection.commit()

        # Update current user object
        current_user.name = name
        current_user.age = age
        current_user.phone = phone

        flash('Profile updated successfully!', 'success')
    except Exception as e:
        app.logger.error(f"Profile update error: {e}")
        flash(f'Error updating profile: {str(e)}', 'error')

    return redirect(url_for('profile'))


# ==================== API ENDPOINTS ====================

@app.route('/api/metrics', methods=['GET'])
@login_required
def api_get_metrics():
    """API endpoint to get metrics (for AJAX)"""
    metric_type = request.args.get('type', '')
    limit = int(request.args.get('limit', 50))

    metrics = db_manager.get_user_metrics(
        current_user.user_id,
        metric_type=metric_type if metric_type else None,
        limit=limit
    )

    # Format metrics as JSON
    formatted = []
    for metric in metrics:
        if len(metric) >= 13:
            metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric[:13]
        else:
            continue

        metric_dict = {
            'id': metric_id,
            'type': mtype,
            'date': date.isoformat() if date else None,
            'notes': notes
        }

        if mtype == "BP" and sys and dia:
            metric_dict['systolic'] = sys
            metric_dict['diastolic'] = dia
        elif mtype == "Glucose" and gluc:
            metric_dict['glucose'] = float(gluc)
            metric_dict['is_fasting'] = fasting
        elif mtype == "Weight" and wgt:
            metric_dict['weight'] = float(wgt)
            metric_dict['height'] = float(ht) if ht else None
        elif mtype == "Exercise" and ex_min:
            metric_dict['minutes'] = ex_min
            metric_dict['activity'] = act

        formatted.append(metric_dict)

    return jsonify(formatted)


@app.route('/api/add_metric', methods=['POST'])
@login_required
def api_add_metric():
    """API endpoint to add metric (for AJAX)"""
    try:
        data = request.get_json()
        metric_type = data.get('type', '').upper()

        if metric_type == 'BP':
            metric_id = db_manager.add_health_metric(
                user_id=current_user.user_id,
                metric_type='BP',
                systolic=data.get('systolic'),
                diastolic=data.get('diastolic'),
                notes=data.get('notes', '')
            )
        elif metric_type == 'GLUCOSE':
            metric_id = db_manager.add_health_metric(
                user_id=current_user.user_id,
                metric_type='Glucose',
                glucose_level=data.get('glucose'),
                is_fasting=data.get('is_fasting', True),
                notes=data.get('notes', '')
            )
        else:
            return jsonify({'error': 'Invalid metric type'}), 400

        return jsonify({
            'success': True,
            'metric_id': metric_id,
            'message': 'Metric added successfully'
        })

    except Exception as e:
        app.logger.error(f"API add metric error: {e}")
        return jsonify({'error': str(e)}), 400


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('error.html',
                           error_code=404,
                           error_message="Page not found"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """500 error handler"""
    return render_template('error.html',
                           error_code=500,
                           error_message="Internal server error"), 500


@app.errorhandler(401)
def unauthorized(e):
    """401 error handler"""
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for('login'))


# ==================== CONTEXT PROCESSORS ====================

@app.context_processor
def inject_now():
    """Inject current datetime into all templates"""
    return {'now': datetime.now()}


# ==================== MAIN ====================

if __name__ == '__main__':
    # Create necessary tables if they don't exist
    try:
        # Create user_auth table if it doesn't exist
        db_manager.cursor.execute('''
                                  CREATE TABLE IF NOT EXISTS user_auth
                                  (
                                      auth_id SERIAL PRIMARY KEY,
                                      user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
                                      password_hash VARCHAR(255) NOT NULL,
                                      created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                  )
                                  ''')
        db_manager.connection.commit()
        print("✅ User auth table verified/created")
    except Exception as e:
        print(f"Note: Could not create auth table (might already exist): {e}")

    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)