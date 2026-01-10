"""
Database setup script for PostgreSQL
Run this once to initialize the database
"""
import sys

# Import after fixing the module
from database_postgres import PostgresDBManager

def setup_database():
    """Initialize the database with sample data"""
    print("=" * 50)
    print("   PostgreSQL Database Setup")
    print("=" * 50)

    try:
        # Create database manager (this will create DB if not exists)
        db = PostgresDBManager()

        print("\n✅ Database setup completed successfully!")

        # Add some sample data for testing
        print("\nAdding sample data...")

        # Add sample user
        user_id = db.add_user(
            name="John Doe",
            age=35,
            gender="Male",
            email="john@example.com",
            phone="+1234567890"
        )
        print(f"✅ Added sample user (ID: {user_id})")

        # Add sample health metrics
        print("\nAdding sample health metrics...")

        metrics = [
            ('BP', {'systolic': 120, 'diastolic': 80}),
            ('BP', {'systolic': 130, 'diastolic': 85}),
            ('Glucose', {'glucose_level': 95.5, 'is_fasting': True}),
            ('Glucose', {'glucose_level': 110.0, 'is_fasting': False}),
            ('Weight', {'weight': 75.5, 'height': 175}),
            ('Exercise', {'exercise_minutes': 45, 'activity_type': 'Running'}),
            ('Exercise', {'exercise_minutes': 20, 'activity_type': 'Walking'}),
        ]

        for metric_type, data in metrics:
            try:
                metric_id = db.add_health_metric(user_id, metric_type, **data)
                print(f"✅ Added {metric_type} metric (ID: {metric_id})")
            except Exception as e:
                print(f"⚠️  Could not add {metric_type} metric: {e}")

        # Get and display stats
        print("\n📊 Sample Statistics:")
        stats = db.get_health_stats(user_id)

        if stats:
            for category, data in stats.items():
                if isinstance(data, dict):
                    print(f"\n{category}:")
                    for key, value in data.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"{category}: {data}")
        else:
            print("No statistics available yet.")

        # Show all user metrics
        print("\n📋 Sample User Metrics:")
        user_metrics = db.get_user_metrics(user_id, limit=5)

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
        print("   Setup Complete! You can now run main_postgres.py")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    setup_database()