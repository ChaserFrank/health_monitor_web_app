"""
Database setup script for PostgreSQL
Run this once to initialize the database
"""
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database_postgres import PostgresDBManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure database_postgres.py exists in the same directory")
    sys.exit(1)

def setup_database():
    """Initialize the database with sample data"""
    print("=" * 50)
    print("   PostgreSQL Database Setup")
    print("=" * 50)

    try:
        # Create database manager
        db = PostgresDBManager()

        print("\n✅ Database setup completed successfully!")

        # Add some sample data for testing
        print("\nAdding sample data...")

        # Check if sample user already exists
        existing_user = db.get_user_by_email("john@example.com")

        if existing_user:
            user_id = existing_user[0]
            print(f"✅ Sample user already exists (ID: {user_id})")

            # Get existing metrics count
            existing_metrics = db.get_user_metrics(user_id, limit=1)
            if existing_metrics:
                print("✅ Sample metrics already exist")
            else:
                # Add sample metrics if they don't exist
                print("Adding sample health metrics...")
                metrics = [
                    ('BP', {'systolic': 120, 'diastolic': 80, 'notes': 'Morning reading'}),
                    ('BP', {'systolic': 130, 'diastolic': 85, 'notes': 'Evening reading'}),
                    ('Glucose', {'glucose_level': 95.5, 'is_fasting': True, 'notes': 'Fasting glucose'}),
                    ('Glucose', {'glucose_level': 110.0, 'is_fasting': False, 'notes': 'After meal'}),
                    ('Weight', {'weight': 75.5, 'height': 175, 'notes': 'Morning weight'}),
                    ('Exercise', {'exercise_minutes': 45, 'activity_type': 'Running', 'notes': 'Morning run'}),
                    ('Exercise', {'exercise_minutes': 20, 'activity_type': 'Walking', 'notes': 'Evening walk'}),
                ]

                for metric_type, data in metrics:
                    try:
                        metric_id = db.add_health_metric(user_id, metric_type, **data)
                        print(f"✅ Added {metric_type} metric (ID: {metric_id})")
                    except Exception as e:
                        print(f"⚠️  Could not add {metric_type} metric: {e}")
        else:
            # Add sample user
            try:
                user_id = db.add_user(
                    name="John Doe",
                    age=35,
                    gender="Male",
                    email="john@example.com",
                    phone="+1234567890"
                )
                print(f"✅ Added sample user (ID: {user_id})")

                # Add sample password (for demo only)
                db.cursor.execute(
                    "INSERT INTO user_auth (user_id, password_hash) VALUES (%s, %s)",
                    (user_id, 'demo_password_hash')
                )
                db.connection.commit()
                print("✅ Added demo password")

                # Add sample health metrics
                print("\nAdding sample health metrics...")
                metrics = [
                    ('BP', {'systolic': 120, 'diastolic': 80, 'notes': 'Morning reading'}),
                    ('BP', {'systolic': 130, 'diastolic': 85, 'notes': 'Evening reading'}),
                    ('Glucose', {'glucose_level': 95.5, 'is_fasting': True, 'notes': 'Fasting glucose'}),
                    ('Glucose', {'glucose_level': 110.0, 'is_fasting': False, 'notes': 'After meal'}),
                    ('Weight', {'weight': 75.5, 'height': 175, 'notes': 'Morning weight'}),
                    ('Exercise', {'exercise_minutes': 45, 'activity_type': 'Running', 'notes': 'Morning run'}),
                    ('Exercise', {'exercise_minutes': 20, 'activity_type': 'Walking', 'notes': 'Evening walk'}),
                ]

                for metric_type, data in metrics:
                    try:
                        metric_id = db.add_health_metric(user_id, metric_type, **data)
                        print(f"✅ Added {metric_type} metric (ID: {metric_id})")
                    except Exception as e:
                        print(f"⚠️  Could not add {metric_type} metric: {e}")

            except ValueError as e:
                print(f"⚠️  User already exists or error: {e}")

        # Get and display stats
        print("\n📊 Sample Statistics:")
        stats_user_id = user_id if 'user_id' in locals() else existing_user[0] if existing_user else None

        if stats_user_id:
            stats = db.get_health_stats(stats_user_id)

            if stats:
                print(f"\nBlood Pressure:")
                print(f"  Readings: {stats['blood_pressure']['readings_count']}")
                print(f"  Average: {stats['blood_pressure']['avg_systolic'] or 'N/A'}/{stats['blood_pressure']['avg_diastolic'] or 'N/A'} mmHg")

                print(f"\nGlucose:")
                print(f"  Readings: {stats['glucose']['readings_count']}")
                print(f"  Average: {stats['glucose']['avg_level'] or 'N/A'} mg/dL")

                print(f"\nExercise:")
                print(f"  Total Minutes: {stats['exercise']['total_minutes']}")
                print(f"  Active Days: {stats['exercise']['days_count']}")

                print(f"\nAlerts:")
                print(f"  Unread: {stats['unread_alerts']}")
            else:
                print("No statistics available yet.")
        else:
            print("No user found for statistics.")

        # Show user metrics
        print("\n📋 Sample User Metrics:")
        if stats_user_id:
            user_metrics = db.get_user_metrics(stats_user_id, limit=5)

            if user_metrics:
                for metric in user_metrics:
                    metric_id, mtype, sys, dia, gluc, fasting, wgt, ht, ex_min, act, hr, date, notes = metric
                    print(f"\n📅 {date} - {mtype}:")
                    if mtype == 'BP' and sys and dia:
                        print(f"  Reading: {sys}/{dia} mmHg")
                    elif mtype == 'Glucose' and gluc:
                        print(f"  Reading: {gluc} mg/dL ({'Fasting' if fasting else 'Non-fasting'})")
                    elif mtype == 'Weight' and wgt and ht:
                        bmi = wgt / ((ht/100) ** 2)
                        print(f"  Weight: {wgt} kg, Height: {ht} cm, BMI: {bmi:.1f}")
                    elif mtype == 'Exercise' and ex_min:
                        print(f"  Exercise: {ex_min} minutes ({act})")
            else:
                print("No metrics found.")

        db.close()

        print("\n" + "=" * 50)
        print("   Setup Complete! You can now run app.py")
        print("=" * 50)
        print("\nDemo Login:")
        print("  Email: john@example.com")
        print("  Password: any password (validation simplified for demo)")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_database()