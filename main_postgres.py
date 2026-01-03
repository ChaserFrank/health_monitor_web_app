"""
Main entry point for PostgreSQL Health Monitoring System
"""
import sys
from colorama import init

# Initialize colorama
init(autoreset=True)

from health_monitor_postgres import HealthMonitorAppPostgres


def main():
    """Main function to run the PostgreSQL application"""
    print("\n" + "=" * 60)
    print("   HEALTH MONITORING SYSTEM - PostgreSQL Edition")
    print("=" * 60)

    try:
        app = HealthMonitorAppPostgres()

        # Check database connection
        print("Checking database connection...")

        # Run the application
        app.run()

    except KeyboardInterrupt:
        print("\n\n⚠️  Application interrupted by user.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check your PostgreSQL installation and try again.")
    finally:
        print("\nThank you for using the Health Monitoring System.")


if __name__ == "__main__":
    # Check for required packages
    try:
        import psycopg2
        import colorama
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install required packages:")
        print("pip install -r requirements.txt")
        sys.exit(1)

    main()