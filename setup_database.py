"""
Database setup script for PostgreSQL
Run this once to initialize the database
"""
from database_postgres import PostgresDBManager
import sys


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
        metrics = [
            ('BP', {'systolic': 120, 'diastolic': 80}),
            ('Glucose', {'glucose_level': 95.5, 'is_fasting': True}),
            ('Weight', {'weight': 75.5, 'height': 175}),
            ('Exercise', {'exercise_minutes': 45, 'activity_type': 'Running'})
        ]

        for metric_type, data in metrics:
            metric_id = db.add_health_metric(user_id, metric_type, **data)
            print(f"✅ Added {metric_type} metric (ID: {metric_id})")

        # Get and display stats
        print("\n📊 Sample Statistics:")
        stats = db.get_health_stats(user_id)
        for category, data in stats.items():
            print(f"{category}: {data}")

        db.close()

        print("\n" + "=" * 50)
        print("   Setup Complete! You can now run main.py")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    setup_database()