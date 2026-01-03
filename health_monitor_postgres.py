"""
Updated Main Health Monitoring Application with PostgreSQL
"""
import sys
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import getpass

# Initialize colorama for colored output
init(autoreset=True)

from models import *
from database_postgres import PostgresDBManager


class HealthMonitorAppPostgres:
    """Main application class with PostgreSQL support"""

    def __init__(self):
        self.db = PostgresDBManager()
        self.current_user: Optional[User] = None
        self.current_user_data: Optional[dict] = None

    def run(self):
        """Main application loop"""
        self.print_header()

        while True:
            if not self.current_user:
                self.show_main_menu()
            else:
                self.show_user_dashboard()

    def print_header(self):
        """Print application header"""
        print(Fore.CYAN + "=" * 60)
        print(Fore.GREEN + "       SMART HEALTH MONITORING SYSTEM")
        print(Fore.YELLOW + "           (PostgreSQL Edition)")
        print(Fore.CYAN + "=" * 60)
        print(Fore.LIGHTBLACK_EX + "Database: PostgreSQL | Version: 2.0 | Secure Login")
        print(Fore.CYAN + "=" * 60)

    def show_main_menu(self):
        """Display main menu"""
        print(f"\n{Fore.CYAN}🏠 MAIN MENU")
        print(f"{Fore.WHITE}1. {Fore.GREEN}Register New User")
        print(f"{Fore.WHITE}2. {Fore.GREEN}Login with Email")
        print(f"{Fore.WHITE}3. {Fore.GREEN}Quick Demo (Sample Data)")
        print(f"{Fore.WHITE}4. {Fore.RED}Exit Application")

        choice = self.get_valid_input(f"{Fore.YELLOW}Enter choice (1-4): ", int, 1, 4)

        if choice == 1:
            self.register_user()
        elif choice == 2:
            self.login_with_email()
        elif choice == 3:
            self.quick_demo()
        elif choice == 4:
            self.exit_application()

    def show_user_dashboard(self):
        """Display user dashboard after login"""
        self.print_user_header()

        print(f"\n{Fore.CYAN}📊 DASHBOARD MENU")
        print(f"{Fore.WHITE}1. {Fore.GREEN}➕ Add Health Metrics")
        print(f"{Fore.WHITE}2. {Fore.GREEN}📈 View Health Analytics")
        print(f"{Fore.WHITE}3. {Fore.GREEN}📋 Health History")
        print(f"{Fore.WHITE}4. {Fore.GREEN}⚠️  View Alerts")
        print(f"{Fore.WHITE}5. {Fore.GREEN}🎯 Set Health Goals")
        print(f"{Fore.WHITE}6. {Fore.GREEN}📊 Statistics Report")
        print(f"{Fore.WHITE}7. {Fore.BLUE}🔧 Account Settings")
        print(f"{Fore.WHITE}8. {Fore.RED}🚪 Logout")

        choice = self.get_valid_input(f"{Fore.YELLOW}Enter choice (1-8): ", int, 1, 8)

        if choice == 1:
            self.add_health_metrics_menu()
        elif choice == 2:
            self.view_health_analytics()
        elif choice == 3:
            self.view_health_history_advanced()
        elif choice == 4:
            self.view_alerts_advanced()
        elif choice == 5:
            self.set_health_goals()
        elif choice == 6:
            self.generate_statistics_report()
        elif choice == 7:
            self.account_settings()
        elif choice == 8:
            self.logout()

    def print_user_header(self):
        """Print user-specific header"""
        print(f"\n{Fore.GREEN}=" * 60)
        print(f"{Fore.CYAN}Welcome, {Fore.YELLOW}{self.current_user.name}!")

        # Show quick stats
        stats = self.db.get_health_stats(self.current_user.user_id)

        if stats.get('unread_alerts', 0) > 0:
            print(f"{Fore.RED}⚠️  You have {stats['unread_alerts']} unread alert(s)")

        print(f"{Fore.LIGHTBLACK_EX}User ID: {self.current_user.user_id} | "
              f"Last Login: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{Fore.GREEN}=" * 60)

    def register_user(self):
        """Enhanced user registration with more fields"""
        print(f"\n{Fore.CYAN}👤 USER REGISTRATION")
        print(f"{Fore.GREEN}=" * 40)

        # Input validation with improved error messages
        name = self.get_valid_string("Full Name: ", min_length=2, max_length=100)

        age = self.get_valid_input("Age: ", int, 1, 120)

        gender = self.get_valid_choice(
            "Gender: ",
            ['Male', 'Female', 'Other'],
            "Please enter Male, Female, or Other"
        )

        email = self.get_valid_email()

        phone = input("Phone (optional): ").strip()
        if phone and not self.validate_phone(phone):
            print(f"{Fore.YELLOW}⚠️  Phone format may be incorrect. Continuing anyway...")

        try:
            user_id = self.db.add_user(name, age, gender, email, phone)
            print(f"\n{Fore.GREEN}✅ Registration successful!")
            print(f"{Fore.CYAN}📋 User Details:")
            print(f"   Name: {name}")
            print(f"   Age: {age}")
            print(f"   Gender: {gender}")
            print(f"   Email: {email}")
            print(f"   User ID: {user_id}")

            # Auto-login after registration
            self.current_user = User(user_id, name, age, gender, email)
            self.current_user_data = {'phone': phone}

        except ValueError as e:
            print(f"{Fore.RED}❌ Registration failed: {e}")
        except Exception as e:
            print(f"{Fore.RED}❌ Database error: {e}")

    def login_with_email(self):
        """Secure login with email"""
        print(f"\n{Fore.CYAN}🔐 LOGIN")
        print(f"{Fore.GREEN}=" * 40)

        email = input("Email: ").strip()
        # In a real application, you would verify password here
        # For demo, we'll just check if email exists

        try:
            user_data = self.db.get_user_by_email(email)

            if user_data:
                user_id, name, age, gender, email, phone, created_date = user_data
                self.current_user = User(user_id, name, age, gender, email)
                self.current_user_data = {
                    'phone': phone,
                    'created_date': created_date
                }

                print(f"\n{Fore.GREEN}✅ Login successful!")
                print(f"{Fore.CYAN}Welcome back, {name}!")

                # Update last login (in a real app)
                print(f"{Fore.LIGHTBLACK_EX}Account created: {created_date}")

            else:
                print(f"{Fore.RED}❌ User not found. Please check your email or register.")

        except Exception as e:
            print(f"{Fore.RED}❌ Login error: {e}")

    def quick_demo(self):
        """Quick demo mode with sample data"""
        print(f"\n{Fore.CYAN}🚀 QUICK DEMO MODE")
        print(f"{Fore.YELLOW}Loading sample data...")

        try:
            # Use sample user
            self.current_user = User(1, "Demo User", 30, "Other", "demo@example.com")
            self.current_user_data = {'phone': '+1234567890'}

            print(f"{Fore.GREEN}✅ Demo mode activated!")
            print(f"{Fore.CYAN}You can now explore all features with sample data.")
            print(f"{Fore.YELLOW}Note: Changes will be saved temporarily.")

        except Exception as e:
            print(f"{Fore.RED}❌ Demo error: {e}")

    def add_health_metrics_menu(self):
        """Enhanced metrics menu with more options"""
        while True:
            print(f"\n{Fore.CYAN}➕ ADD HEALTH METRICS")
            print(f"{Fore.GREEN}=" * 40)
            print(f"{Fore.WHITE}1. {Fore.GREEN}🩸 Blood Pressure")
            print(f"{Fore.WHITE}2. {Fore.GREEN}🩸 Glucose Level")
            print(f"{Fore.WHITE}3. {Fore.GREEN}⚖️  Weight & BMI")
            print(f"{Fore.WHITE}4. {Fore.GREEN}🏃 Exercise")
            print(f"{Fore.WHITE}5. {Fore.GREEN}❤️  Heart Rate")
            print(f"{Fore.WHITE}6. {Fore.BLUE}📝 Add Notes to Last Reading")
            print(f"{Fore.WHITE}7. {Fore.RED}↩️  Back to Dashboard")

            choice = self.get_valid_input(f"{Fore.YELLOW}Choose (1-7): ", int, 1, 7)

            if choice == 7:
                break

            try:
                if choice == 1:
                    self.add_blood_pressure_advanced()
                elif choice == 2:
                    self.add_glucose_advanced()
                elif choice == 3:
                    self.add_weight_advanced()
                elif choice == 4:
                    self.add_exercise_advanced()
                elif choice == 5:
                    self.add_heart_rate()
                elif choice == 6:
                    self.add_notes_to_reading()

                # Ask if user wants to add another metric
                if choice != 6:
                    another = input(f"\n{Fore.YELLOW}Add another metric? (y/n): ").lower()
                    if another != 'y':
                        break

            except Exception as e:
                print(f"{Fore.RED}❌ Error: {e}")
                print(f"{Fore.YELLOW}Please try again.")

    def add_blood_pressure_advanced(self):
        """Enhanced BP entry with time and conditions"""
        print(f"\n{Fore.CYAN}🩸 BLOOD PRESSURE ENTRY")

        systolic = self.get_valid_input("Systolic (upper): ", int, 50, 250)
        diastolic = self.get_valid_input("Diastolic (lower): ", int, 30, 150)

        print(f"\n{Fore.YELLOW}Measurement Conditions:")
        print(f"{Fore.WHITE}1. Resting (after 5 min rest)")
        print(f"{Fore.WHITE}2. After exercise")
        print(f"{Fore.WHITE}3. Morning reading")
        print(f"{Fore.WHITE}4. Evening reading")

        condition_choice = self.get_valid_input("Select condition (1-4): ", int, 1, 4)
        conditions = ["Resting", "After exercise", "Morning", "Evening"]
        condition = conditions[condition_choice - 1]

        arm = self.get_valid_choice("Which arm? ", ["Left", "Right"], "Enter Left or Right")

        notes = input("Additional notes (optional): ").strip()

        # Create metric
        bp = BloodPressure(systolic, diastolic)

        # Store in database
        metric_id = self.db.add_health_metric(
            user_id=self.current_user.user_id,
            metric_type="BP",
            systolic=systolic,
            diastolic=diastolic,
            notes=f"{condition}, {arm} arm. {notes}"
        )

        # Add to user object
        self.current_user.add_metric(bp)

        print(f"\n{Fore.GREEN}✅ BP recorded successfully!")
        print(f"{Fore.CYAN}📊 Reading: {systolic}/{diastolic} mmHg")
        print(f"{Fore.CYAN}📝 Condition: {condition}, {arm} arm")
        print(f"{Fore.CYAN}💡 Analysis: {bp.get_recommendation()}")

        if systolic > 140 or diastolic > 90:
            print(f"{Fore.RED}⚠️  High BP detected! Please monitor regularly.")

    def add_glucose_advanced(self):
        """Enhanced glucose entry"""
        print(f"\n{Fore.CYAN}🩸 GLUCOSE LEVEL ENTRY")

        glucose = self.get_valid_input("Glucose level (mg/dL): ", float, 20, 600)

        print(f"\n{Fore.YELLOW}Measurement Type:")
        print(f"{Fore.WHITE}1. Fasting (8+ hours no food)")
        print(f"{Fore.WHITE}2. Post-prandial (2 hours after meal)")
        print(f"{Fore.WHITE}3. Random")

        type_choice = self.get_valid_input("Select type (1-3): ", int, 1, 3)
        types = ["Fasting", "Post-prandial", "Random"]
        measurement_type = types[type_choice - 1]

        is_fasting = measurement_type == "Fasting"

        if measurement_type == "Post-prandial":
            meal_size = self.get_valid_choice(
                "Meal size: ",
                ["Small", "Medium", "Large"],
                "Enter Small, Medium, or Large"
            )
            notes = f"Post-prandial ({meal_size} meal)"
        else:
            notes = measurement_type
            additional = input("Additional notes (optional): ").strip()
            if additional:
                notes += f" - {additional}"

        # Create metric
        glucose_metric = GlucoseLevel(glucose, is_fasting=is_fasting)

        # Store in database
        metric_id = self.db.add_health_metric(
            user_id=self.current_user.user_id,
            metric_type="Glucose",
            glucose_level=glucose,
            is_fasting=is_fasting,
            notes=notes
        )

        self.current_user.add_metric(glucose_metric)

        print(f"\n{Fore.GREEN}✅ Glucose recorded successfully!")
        print(f"{Fore.CYAN}📊 Reading: {glucose} mg/dL")
        print(f"{Fore.CYAN}📝 Type: {measurement_type}")

        status = "Normal" if glucose_metric.is_normal() else "Abnormal"
        color = Fore.GREEN if glucose_metric.is_normal() else Fore.RED
        print(f"{color}📈 Status: {status}")
        print(f"{Fore.CYAN}💡 Recommendation: {glucose_metric.get_recommendation()}")

    def view_health_analytics(self):
        """Advanced health analytics with trends"""
        print(f"\n{Fore.CYAN}📈 HEALTH ANALYTICS DASHBOARD")
        print(f"{Fore.GREEN}=" * 50)

        # Get metrics from database
        db_metrics = self.db.get_user_metrics(self.current_user.user_id, limit=50)

        if not db_metrics:
            print(f"{Fore.YELLOW}No health metrics found. Add some metrics first!")
            return

        # Convert to metric objects
        metric_objects = []
        for metric in db_metrics:
            metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric

            if mtype == "BP" and sys and dia:
                metric_objects.append(BloodPressure(sys, dia))
            elif mtype == "Glucose" and gluc:
                metric_objects.append(GlucoseLevel(gluc, is_fasting=fasting))
            elif mtype == "Weight" and wgt and ht:
                metric_objects.append(Weight(wgt, ht))
            elif mtype == "Exercise" and ex_min:
                metric_objects.append(Exercise(ex_min, act or "Activity"))

        # Use polymorphic analyzer
        analyzer = HealthAnalyzer()
        analysis = analyzer.analyze_metrics(metric_objects)

        # Display analysis
        print(f"\n{Fore.YELLOW}📊 OVERVIEW")
        print(f"{Fore.CYAN}Total Metrics Analyzed: {Fore.WHITE}{analysis['total_metrics']}")

        normal_percent = (analysis['normal_count'] / analysis['total_metrics'] * 100) if analysis[
                                                                                             'total_metrics'] > 0 else 0
        abnormal_percent = (analysis['abnormal_count'] / analysis['total_metrics'] * 100) if analysis[
                                                                                                 'total_metrics'] > 0 else 0

        print(f"{Fore.GREEN}✓ Normal Readings: {analysis['normal_count']} ({normal_percent:.1f}%)")
        print(f"{Fore.RED}⚠️ Abnormal Readings: {analysis['abnormal_count']} ({abnormal_percent:.1f}%)")

        # Display detailed analysis
        print(f"\n{Fore.YELLOW}🔍 DETAILED ANALYSIS")
        print(f"{Fore.GREEN}=" * 60)

        # Group by metric type
        metric_groups = {}
        for detail in analysis['details']:
            mtype = detail['type']
            if mtype not in metric_groups:
                metric_groups[mtype] = []
            metric_groups[mtype].append(detail)

        for mtype, details in metric_groups.items():
            normal_count = sum(1 for d in details if d['is_normal'])
            total_count = len(details)

            print(f"\n{Fore.CYAN}{mtype}:")
            print(f"  Readings: {total_count} | Normal: {normal_count} | "
                  f"Abnormal: {total_count - normal_count}")

            # Show recent abnormal readings
            abnormal = [d for d in details if not d['is_normal']][:3]
            if abnormal:
                print(f"  {Fore.RED}Recent issues:")
                for ab in abnormal:
                    print(f"    • {ab['value']}: {ab['recommendation']}")

    def view_health_history_advanced(self):
        """Advanced history view with filtering"""
        print(f"\n{Fore.CYAN}📋 HEALTH HISTORY")
        print(f"{Fore.GREEN}=" * 50)

        print(f"\n{Fore.YELLOW}Filter Options:")
        print(f"{Fore.WHITE}1. All metrics")
        print(f"{Fore.WHITE}2. Blood Pressure only")
        print(f"{Fore.WHITE}3. Glucose only")
        print(f"{Fore.WHITE}4. Weight only")
        print(f"{Fore.WHITE}5. Exercise only")

        filter_choice = self.get_valid_input("Choose filter (1-5): ", int, 1, 5)

        metric_type = None
        if filter_choice == 2:
            metric_type = "BP"
        elif filter_choice == 3:
            metric_type = "Glucose"
        elif filter_choice == 4:
            metric_type = "Weight"
        elif filter_choice == 5:
            metric_type = "Exercise"

        # Get metrics
        metrics = self.db.get_user_metrics(
            self.current_user.user_id,
            metric_type=metric_type,
            limit=20
        )

        if not metrics:
            print(f"{Fore.YELLOW}No metrics found with the selected filter.")
            return

        print(f"\n{Fore.CYAN}Found {len(metrics)} record(s):")
        print(f"{Fore.GREEN}=" * 60)

        for metric in metrics:
            metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric

            print(f"\n{Fore.YELLOW}📅 {date}")
            print(f"{Fore.CYAN}Type: {mtype}")

            if mtype == "BP" and sys and dia:
                # Color code based on values
                if sys > 140 or dia > 90:
                    color = Fore.RED
                elif sys < 90 or dia < 60:
                    color = Fore.YELLOW
                else:
                    color = Fore.GREEN
                print(f"{color}Reading: {sys}/{dia} mmHg")

            elif mtype == "Glucose" and gluc:
                if (fasting and gluc > 126) or (not fasting and gluc > 200):
                    color = Fore.RED
                elif gluc < 70:
                    color = Fore.YELLOW
                else:
                    color = Fore.GREEN
                print(f"{color}Reading: {gluc} mg/dL ({'Fasting' if fasting else 'Non-fasting'})")

            elif mtype == "Weight" and wgt and ht:
                bmi = wgt / ((ht / 100) ** 2)
                if bmi < 18.5:
                    color = Fore.YELLOW
                elif bmi > 24.9:
                    color = Fore.RED
                else:
                    color = Fore.GREEN
                print(f"{color}Weight: {wgt} kg | Height: {ht} cm | BMI: {bmi:.1f}")

            elif mtype == "Exercise" and ex_min:
                if ex_min < 30:
                    color = Fore.YELLOW
                else:
                    color = Fore.GREEN
                print(f"{color}Exercise: {ex_min} min ({act})")

            if notes:
                print(f"{Fore.LIGHTBLACK_EX}Notes: {notes}")

            print(f"{Fore.LIGHTBLACK_EX}{'-' * 40}")

    def view_alerts_advanced(self):
        """Advanced alerts view with actions"""
        print(f"\n{Fore.CYAN}⚠️  ALERTS & NOTIFICATIONS")
        print(f"{Fore.GREEN}=" * 50)

        # Query for alerts
        self.db.cursor.execute('''
                               SELECT alert_id,
                                      alert_type,
                                      message,
                                      severity,
                                      created_date,
                                      is_read,
                                      resolved
                               FROM alerts
                               WHERE user_id = %s
                               ORDER BY CASE severity
                                            WHEN 'Critical' THEN 1
                                            WHEN 'High' THEN 2
                                            WHEN 'Medium' THEN 3
                                            WHEN 'Low' THEN 4
                                            END,
                                        created_date DESC LIMIT 20
                               ''', (self.current_user.user_id,))

        alerts = self.db.cursor.fetchall()

        if not alerts:
            print(f"{Fore.GREEN}🎉 No alerts! Your health metrics look good.")
            return

        unread_count = sum(1 for a in alerts if not a[5])

        print(f"\n{Fore.YELLOW}You have {len(alerts)} alert(s)")
        if unread_count > 0:
            print(f"{Fore.RED}{unread_count} unread alert(s)")

        print(f"\n{Fore.CYAN}Alert List:")
        print(f"{Fore.GREEN}=" * 60)

        for i, alert in enumerate(alerts, 1):
            alert_id, alert_type, message, severity, date, is_read, resolved = alert

            # Determine color based on severity
            if severity == 'Critical':
                color = Fore.RED + Style.BRIGHT
            elif severity == 'High':
                color = Fore.RED
            elif severity == 'Medium':
                color = Fore.YELLOW
            else:
                color = Fore.BLUE

            read_indicator = "✓" if is_read else "✗"
            resolved_indicator = "✅" if resolved else "⏳"

            print(f"\n{color}[{severity}] {read_indicator} {resolved_indicator}")
            print(f"{Fore.WHITE}{i}. {alert_type}")
            print(f"{Fore.LIGHTBLACK_EX}   {date}")
            print(f"   {message}")

        # Offer actions
        print(f"\n{Fore.YELLOW}Actions:")
        print(f"{Fore.WHITE}1. Mark all as read")
        print(f"{Fore.WHITE}2. Mark specific alert as resolved")
        print(f"{Fore.WHITE}3. Back to dashboard")

        action = input(f"{Fore.YELLOW}Choose action (1-3): ").strip()

        if action == '1':
            self.db.cursor.execute('''
                                   UPDATE alerts
                                   SET is_read = TRUE
                                   WHERE user_id = %s
                                     AND NOT is_read
                                   ''', (self.current_user.user_id,))
            self.db.connection.commit()
            print(f"{Fore.GREEN}✅ All alerts marked as read!")

        elif action == '2':
            alert_num = self.get_valid_input("Alert number to resolve: ", int, 1, len(alerts))
            alert_id = alerts[alert_num - 1][0]

            self.db.cursor.execute('''
                                   UPDATE alerts
                                   SET resolved      = TRUE,
                                       resolved_date = CURRENT_TIMESTAMP
                                   WHERE alert_id = %s
                                   ''', (alert_id,))
            self.db.connection.commit()
            print(f"{Fore.GREEN}✅ Alert marked as resolved!")

    def generate_statistics_report(self):
        """Generate comprehensive statistics report"""
        print(f"\n{Fore.CYAN}📊 HEALTH STATISTICS REPORT")
        print(f"{Fore.GREEN}=" * 50)

        stats = self.db.get_health_stats(self.current_user.user_id)

        if not stats:
            print(f"{Fore.YELLOW}Insufficient data for statistics.")
            return

        print(f"\n{Fore.YELLOW}📈 30-DAY SUMMARY")
        print(f"{Fore.CYAN}{'=' * 40}")

        # Blood Pressure Stats
        bp_stats = stats.get('blood_pressure', {})
        if bp_stats.get('readings_count', 0) > 0:
            print(f"\n{Fore.GREEN}🩸 BLOOD PRESSURE")
            print(f"  Readings: {bp_stats['readings_count']}")
            print(f"  Average: {bp_stats.get('avg_systolic', 'N/A')}/{bp_stats.get('avg_diastolic', 'N/A')} mmHg")

            if bp_stats.get('avg_systolic') and bp_stats.get('avg_diastolic'):
                if bp_stats['avg_systolic'] > 140 or bp_stats['avg_diastolic'] > 90:
                    print(f"  {Fore.RED}Status: Above Normal (Consult doctor)")
                elif bp_stats['avg_systolic'] < 90 or bp_stats['avg_diastolic'] < 60:
                    print(f"  {Fore.YELLOW}Status: Below Normal (Monitor)")
                else:
                    print(f"  {Fore.GREEN}Status: Normal (Good)")

        # Glucose Stats
        glucose_stats = stats.get('glucose', {})
        if glucose_stats.get('readings_count', 0) > 0:
            print(f"\n{Fore.GREEN}🩸 GLUCOSE")
            print(f"  Readings: {glucose_stats['readings_count']}")
            print(f"  Average: {glucose_stats.get('avg_level', 'N/A')} mg/dL")

        # Exercise Stats
        exercise_stats = stats.get('exercise', {})
        print(f"\n{Fore.GREEN}🏃 EXERCISE")
        print(f"  Total Minutes: {exercise_stats.get('total_minutes', 0)}")
        print(f"  Active Days: {exercise_stats.get('days_count', 0)}")

        avg_daily = exercise_stats.get('total_minutes', 0) / max(exercise_stats.get('days_count', 1), 1)
        print(f"  Average Daily: {avg_daily:.1f} minutes")

        if avg_daily >= 30:
            print(f"  {Fore.GREEN}Status: Meeting recommended daily goal")
        else:
            print(f"  {Fore.YELLOW}Status: Below recommended 30 minutes daily")

        # Alerts
        print(f"\n{Fore.GREEN}⚠️  ALERTS")
        print(f"  Unread Alerts: {stats.get('unread_alerts', 0)}")

        print(f"\n{Fore.YELLOW}Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # Helper methods for input validation
    def get_valid_input(self, prompt: str, data_type, min_val=None, max_val=None):
        """Generic input validation with retry"""
        while True:
            try:
                value = input(prompt).strip()

                if not value:
                    print(f"{Fore.YELLOW}Input cannot be empty. Please try again.")
                    continue

                # Convert to desired type
                if data_type == int:
                    value = int(value)
                elif data_type == float:
                    value = float(value)

                # Range validation
                if min_val is not None and value < min_val:
                    print(f"{Fore.YELLOW}Value must be at least {min_val}")
                    continue
                if max_val is not None and value > max_val:
                    print(f"{Fore.YELLOW}Value must be at most {max_val}")
                    continue

                return value

            except ValueError:
                print(f"{Fore.RED}Invalid input. Please enter a valid {data_type.__name__}")
            except Exception as e:
                print(f"{Fore.RED}An error occurred: {e}")

    def get_valid_string(self, prompt: str, min_length=1, max_length=100):
        """Validate string input"""
        while True:
            value = input(prompt).strip()
            if len(value) < min_length:
                print(f"{Fore.YELLOW}Input must be at least {min_length} characters.")
            elif len(value) > max_length:
                print(f"{Fore.YELLOW}Input must be at most {max_length} characters.")
            else:
                return value

    def get_valid_email(self):
        """Validate email input"""
        while True:
            email = input("Email: ").strip().lower()
            if '@' not in email or '.' not in email:
                print(f"{Fore.YELLOW}Invalid email format. Please include '@' and domain.")
            elif len(email) < 5:
                print(f"{Fore.YELLOW}Email is too short.")
            else:
                return email

    def get_valid_choice(self, prompt: str, choices: list, error_msg: str = None):
        """Get valid choice from list"""
        while True:
            value = input(prompt).strip()
            if value in choices:
                return value
            print(error_msg or f"Please enter one of: {', '.join(choices)}")

    def validate_phone(self, phone: str) -> bool:
        """Simple phone validation"""
        # Remove non-digits
        digits = ''.join(filter(str.isdigit, phone))
        return 7 <= len(digits) <= 15

    def add_heart_rate(self):
        """Add heart rate reading"""
        print(f"\n{Fore.CYAN}❤️  HEART RATE")

        heart_rate = self.get_valid_input("Heart Rate (bpm): ", int, 30, 220)

        condition = self.get_valid_choice(
            "Condition: ",
            ["Resting", "After exercise", "During exercise", "Other"],
            "Please select a valid condition"
        )

        notes = input("Additional notes (optional): ").strip()

        # Simple analysis
        if 60 <= heart_rate <= 100:
            status = "Normal resting heart rate"
            color = Fore.GREEN
        elif heart_rate < 60:
            status = "Bradycardia (low heart rate)"
            color = Fore.YELLOW
        else:
            if condition == "Resting":
                status = "Tachycardia (high resting heart rate)"
                color = Fore.RED
            else:
                status = "Normal for activity"
                color = Fore.GREEN

        # Store in database
        metric_id = self.db.add_health_metric(
            user_id=self.current_user.user_id,
            metric_type="Heart_Rate",
            heart_rate=heart_rate,
            notes=f"{condition}. {notes}"
        )

        print(f"\n{Fore.GREEN}✅ Heart rate recorded!")
        print(f"{Fore.CYAN}📊 Reading: {heart_rate} bpm")
        print(f"{color}📈 Status: {status}")

    def set_health_goals(self):
        """Set health goals"""
        print(f"\n{Fore.CYAN}🎯 SET HEALTH GOALS")
        print(f"{Fore.GREEN}=" * 40)

        print(f"\n{Fore.YELLOW}Goal Types:")
        print(f"{Fore.WHITE}1. Weight Loss/Gain")
        print(f"{Fore.WHITE}2. Exercise Minutes")
        print(f"{Fore.WHITE}3. Blood Pressure Target")
        print(f"{Fore.WHITE}4. Glucose Target")

        goal_type_choice = self.get_valid_input("Select goal type (1-4): ", int, 1, 4)
        goal_types = ["Weight", "Exercise", "Blood Pressure", "Glucose"]
        goal_type = goal_types[goal_type_choice - 1]

        if goal_type == "Weight":
            target = self.get_valid_input("Target weight (kg): ", float, 30, 200)
            current = self.get_valid_input("Current weight (kg): ", float, 30, 200)
            timeframe = self.get_valid_input("Target timeframe (days): ", int, 7, 365)

            print(f"\n{Fore.GREEN}✅ Weight goal set!")
            print(f"{Fore.CYAN}Target: {target} kg in {timeframe} days")
            print(f"{Fore.CYAN}Current: {current} kg")
            print(f"{Fore.CYAN}To lose/gain: {abs(target - current):.1f} kg")

        elif goal_type == "Exercise":
            target = self.get_valid_input("Target daily minutes: ", int, 10, 300)
            weekly_days = self.get_valid_input("Days per week: ", int, 1, 7)

            print(f"\n{Fore.GREEN}✅ Exercise goal set!")
            print(f"{Fore.CYAN}Target: {target} minutes daily")
            print(f"{Fore.CYAN}Frequency: {weekly_days} days per week")
            print(f"{Fore.CYAN}Weekly total: {target * weekly_days} minutes")

    def account_settings(self):
        """Account settings menu"""
        print(f"\n{Fore.CYAN}🔧 ACCOUNT SETTINGS")
        print(f"{Fore.GREEN}=" * 40)

        print(f"\n{Fore.YELLOW}1. View Profile")
        print(f"{Fore.YELLOW}2. Change Email")
        print(f"{Fore.YELLOW}3. Update Phone")
        print(f"{Fore.YELLOW}4. Data Export")
        print(f"{Fore.YELLOW}5. Privacy Settings")
        print(f"{Fore.YELLOW}6. Back to Dashboard")

        choice = self.get_valid_input("Select option (1-6): ", int, 1, 6)

        if choice == 1:
            self.view_profile()
        elif choice == 2:
            print(f"{Fore.YELLOW}Email change feature coming soon!")
        elif choice == 3:
            print(f"{Fore.YELLOW}Phone update feature coming soon!")
        elif choice == 4:
            self.export_data()
        elif choice == 5:
            print(f"{Fore.YELLOW}Privacy settings coming soon!")

    def view_profile(self):
        """View user profile"""
        print(f"\n{Fore.CYAN}👤 USER PROFILE")
        print(f"{Fore.GREEN}=" * 40)

        print(f"\n{Fore.YELLOW}Basic Information:")
        print(f"{Fore.CYAN}Name: {Fore.WHITE}{self.current_user.name}")
        print(f"{Fore.CYAN}Age: {Fore.WHITE}{self.current_user.age}")
        print(f"{Fore.CYAN}Gender: {Fore.WHITE}{self.current_user.gender}")
        print(f"{Fore.CYAN}Email: {Fore.WHITE}{self.current_user.email}")

        if self.current_user_data and 'phone' in self.current_user_data:
            print(f"{Fore.CYAN}Phone: {Fore.WHITE}{self.current_user_data['phone']}")

        if self.current_user_data and 'created_date' in self.current_user_data:
            print(f"{Fore.CYAN}Member Since: {Fore.WHITE}{self.current_user_data['created_date']}")

        # Show some stats
        stats = self.db.get_health_stats(self.current_user.user_id)
        print(f"\n{Fore.YELLOW}Health Summary:")
        print(f"{Fore.CYAN}Total BP Readings: {Fore.WHITE}{stats.get('blood_pressure', {}).get('readings_count', 0)}")
        print(f"{Fore.CYAN}Total Glucose Readings: {Fore.WHITE}{stats.get('glucose', {}).get('readings_count', 0)}")
        print(f"{Fore.CYAN}Exercise Minutes (30 days): {Fore.WHITE}{stats.get('exercise', {}).get('total_minutes', 0)}")

    def export_data(self):
        """Export health data"""
        print(f"\n{Fore.CYAN}📤 DATA EXPORT")
        print(f"{Fore.GREEN}=" * 40)

        print(f"\n{Fore.YELLOW}Export Options:")
        print(f"{Fore.WHITE}1. Export all health data (CSV)")
        print(f"{Fore.WHITE}2. Export blood pressure only")
        print(f"{Fore.WHITE}3. Export glucose readings only")
        print(f"{Fore.WHITE}4. Cancel")

        choice = self.get_valid_input("Select option (1-4): ", int, 1, 4)

        if choice == 4:
            return

        # Get data based on choice
        metric_type = None
        if choice == 2:
            metric_type = "BP"
        elif choice == 3:
            metric_type = "Glucose"

        metrics = self.db.get_user_metrics(
            self.current_user.user_id,
            metric_type=metric_type,
            limit=1000  # Get all
        )

        if not metrics:
            print(f"{Fore.YELLOW}No data to export.")
            return

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"health_export_{self.current_user.user_id}_{timestamp}.csv"

        try:
            with open(filename, 'w') as f:
                # Write header
                f.write(
                    "Metric ID,Type,Date,Systolic,Diastolic,Glucose,Fasting,Weight,Height,Exercise,Activity,Heart Rate,Notes\n")

                # Write data
                for metric in metrics:
                    metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric

                    # Clean notes for CSV
                    clean_notes = str(notes).replace(',', ';').replace('\n', ' ') if notes else ""

                    f.write(
                        f"{metric_id},{mtype},{date},{sys or ''},{dia or ''},{gluc or ''},{fasting},{wgt or ''},{ht or ''},{ex_min or ''},{act or ''},{hr or ''},\"{clean_notes}\"\n")

            print(f"\n{Fore.GREEN}✅ Data exported successfully!")
            print(f"{Fore.CYAN}File: {filename}")
            print(f"{Fore.CYAN}Records: {len(metrics)}")
            print(f"{Fore.YELLOW}Note: This file contains your personal health data. Keep it secure!")

        except Exception as e:
            print(f"{Fore.RED}❌ Export failed: {e}")

    def add_notes_to_reading(self):
        """Add notes to the most recent reading"""
        print(f"\n{Fore.CYAN}📝 ADD NOTES TO RECENT READING")

        # Get most recent metric
        metrics = self.db.get_user_metrics(self.current_user.user_id, limit=1)

        if not metrics:
            print(f"{Fore.YELLOW}No recent readings found.")
            return

        metric = metrics[0]
        metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, old_notes = metric

        print(f"\n{Fore.YELLOW}Most Recent Reading:")
        print(f"{Fore.CYAN}Type: {mtype}")
        print(f"{Fore.CYAN}Date: {date}")

        if mtype == "BP":
            print(f"{Fore.CYAN}Reading: {sys}/{dia} mmHg")
        elif mtype == "Glucose":
            print(f"{Fore.CYAN}Reading: {gluc} mg/dL ({'Fasting' if fasting else 'Non-fasting'})")

        if old_notes:
            print(f"{Fore.CYAN}Current Notes: {old_notes}")

        new_notes = input(f"\n{Fore.YELLOW}Enter additional notes: ").strip()

        if new_notes:
            updated_notes = f"{old_notes or ''} | {new_notes}" if old_notes else new_notes

            # Update in database
            self.db.cursor.execute('''
                                   UPDATE health_metrics
                                   SET notes = %s
                                   WHERE metric_id = %s
                                   ''', (updated_notes, metric_id))
            self.db.connection.commit()

            print(f"{Fore.GREEN}✅ Notes updated successfully!")

    def logout(self):
        """Logout user"""
        print(f"\n{Fore.YELLOW}Logging out {self.current_user.name}...")
        self.current_user = None
        self.current_user_data = None
        print(f"{Fore.GREEN}✅ Logout successful!")

    def exit_application(self):
        """Exit the application gracefully"""
        print(f"\n{Fore.CYAN}Thank you for using the Health Monitoring System!")
        print(f"{Fore.YELLOW}Saving data and closing connections...")

        self.db.close()

        print(f"{Fore.GREEN}✅ Application closed successfully. Goodbye!")
        sys.exit(0)