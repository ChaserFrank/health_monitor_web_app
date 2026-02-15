# Smart Health Monitoring System

A full‑stack Flask web application that lets users track health metrics (blood pressure, glucose, weight/BMI, exercise, heart rate), visualize trends, and receive alert notifications for abnormal readings. The app uses PostgreSQL for persistence and provides both web pages and JSON API endpoints.


## Table of contents
- Project overview
- Features
- Tech stack
- Architecture and project structure
- Key modules and responsibilities
- Environment variables
- Setup and installation
- Database initialization and migrations
- Running the app
- Running tests
- API endpoints
- Security and production notes
- Troubleshooting
- Assumptions and non-goals


## Project overview
The Smart Health Monitoring System helps users build consistent health tracking habits by:
- Recording health metrics in a structured, queryable PostgreSQL database
- Detecting abnormal values and creating severity‑based alerts
- Visualizing history and trends with interactive charts
- Offering a simple JSON API for programmatic access


## Features
- User accounts (registration, login/logout) with session management
- Health metrics:
  - Blood Pressure (systolic/diastolic)
  - Glucose (fasting/non‑fasting)
  - Weight with BMI
  - Exercise (minutes, activity type)
  - Heart rate
- Alerts with severity levels (Low, Medium, High, Critical)
- Dashboard, metrics list, analytics charts (Plotly), alerts, profile pages
- Data export to CSV/JSON
- JSON API endpoints for metrics (list/add)
- Admin panel for user management


## Tech stack
- Backend: Python 3.11+ with Flask 3.x
  - Flask‑Login for sessions
  - Jinja2 templates
- Database: PostgreSQL (via psycopg2)
- Data/visualization: pandas, plotly
- Frontend: HTML, CSS (Bootstrap), JavaScript
- Config: dotenv‑based environment configuration
- Tests: pytest + unittest


## Architecture and project structure
Top‑level layout (key files only):

- app.py — Flask app factory, routes (web views + JSON APIs), login/session wiring
- config.py — configuration classes and environment variable loading
- database_postgres.py — PostgreSQL access layer (connection, DDL, queries)
- models.py — domain model classes (pure Python) for health metrics, alerts, goals, analysis
- templates/ — Jinja2 HTML templates for pages
- static/ — static assets (CSS, JS)
- tests/ — web, database, and model tests
- requirements.txt — Python dependencies
- setup_database.py — optional helper for DB setup (tables are also created automatically on app start)
- docs/ — additional documentation site artifacts (MkDocs), optional


## Key modules and responsibilities
- app.py
  - Initializes Flask, LoginManager, and database manager
  - Defines routes:
    - Authentication: /register, /login, /logout
    - UI pages: /, /dashboard, /metrics, /analytics, /alerts, /profile
    - Data export: /export_data/<format> (csv|json)
    - API: /api/metrics (GET), /api/add_metric (POST)
  - Uses db_manager (PostgresDBManager) for all persistence and queries
  - Generates Plotly charts for analytics

- config.py
  - Loads environment variables (.env supported via python‑dotenv)
  - Provides Config/DevelopmentConfig/ProductionConfig classes
  - Exposes DB_CONFIG for direct psycopg2 connections

- database_postgres.py
  - Creates/ensures database and all required tables (users, health_metrics, alerts, health_goals, user_auth)
  - Provides CRUD‑like methods:
    - add_user, get_user_by_email
    - add_health_metric (BP, Glucose, Weight, Exercise, Heart Rate)
    - get_user_metrics (with pagination and type filtering)
    - get_health_stats (aggregate stats over last 30 days)
  - Encapsulates alert creation for abnormal readings (on insert)

- models.py
  - Pure Python domain model classes with validation and analysis helpers:
    - HealthMetric base + BloodPressure, GlucoseLevel, Weight, Exercise, HeartRate
    - User, Alert, HealthGoal, HealthAnalyzer, HealthMetricFactory, TimeRange
  - These models are used by CLI or analytical flows; persistence is handled by database_postgres.py

- templates/
  - Jinja2 templates for pages (index, register, login, dashboard, metrics, analytics, alerts, profile)


## Environment variables
Put these in a .env file in the project root, or pass them via your environment:
- DB_HOST — PostgreSQL host (e.g., localhost)
- DB_NAME — PostgreSQL database name
- DB_USER — PostgreSQL username
- DB_PASSWORD — PostgreSQL password
- DB_PORT — PostgreSQL port (default 5432)
- SECRET_KEY — Flask secret key (set to a long random string in production)
- DATABASE_URL — Optional full SQLAlchemy/DB URL; used for the SQLALCHEMY_DATABASE_URI config
- SESSION_COOKIE_SECURE — true/false; enable true in production over HTTPS

Example .env (do not commit real secrets):

DB_HOST=localhost
DB_NAME=health_monitor_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_PORT=5432
SECRET_KEY=dev-secret-key-change
SESSION_COOKIE_SECURE=False


## Setup and installation
1) Prerequisites
- Python 3.11+ (3.12 supported)
- PostgreSQL running and reachable

2) Create and activate a virtual environment
- Windows (PowerShell):
  - python -m venv .venv
  - .\.venv\Scripts\Activate.ps1

3) Install dependencies
- pip install -r requirements.txt

4) Configure environment
- Create a .env file as shown above


## Database initialization and migrations
- On startup, PostgresDBManager will:
  - Ensure the target database exists (connecting to the default postgres DB first)
  - Create all required tables and indexes if they do not exist
- There is no Alembic/Flask‑Migrate in this repository. For schema changes, consider introducing Alembic later. For now, the built‑in DDL will create/verify tables.

Optional: setup_database.py is provided; however, the application auto‑creates tables, so running the app is usually sufficient.


## Running the app
- Ensure PostgreSQL is running and environment variables are set
- Start the Flask app:
  - python app.py
- The server runs on http://0.0.0.0:5000 by default

Default pages:
- / — Home
- /register — Create account
- /login — Login (demo logic; see Security notes)
- /dashboard — Dashboard (requires login)
- /metrics — Metrics list with pagination
- /analytics — Plotly charts
- /alerts — Alerts list
- /profile — Profile and stats


## Running tests
- Run all tests with pytest:
  - pytest -q

Tests live under tests/ and cover web routes, auth flows, metrics workflows, APIs, and error handling.


## API endpoints
Simple JSON endpoints (no Django REST Framework):

- GET /api/metrics
  - Query params:
    - type (optional): BP | Glucose | Weight | Exercise | Heart_Rate
    - limit (optional): integer, default 50
  - Auth: requires login session
  - Response: JSON list of metric objects with type‑specific fields

- POST /api/add_metric
  - Body: application/json
  - Example (Blood Pressure):
    {
      "type": "BP",
      "systolic": 120,
      "diastolic": 80,
      "notes": "optional"
    }
  - Example (Glucose):
    {
      "type": "GLUCOSE",
      "glucose": 95.0,
      "is_fasting": true,
      "notes": "optional"
    }
  - Auth: requires login session
  - Response: { success: true, metric_id: <int>, message: "..." }

- GET /export_data/csv and GET /export_data/json
  - Downloads metrics for the current user in CSV or JSON format


## Security and production notes
- The current /login implementation in app.py is demo‑oriented and does not validate a password hash from the user_auth table. Do not use as‑is for production. Integrate proper password verification (check_password_hash) and CSRF protection for forms before deploying.
- Set SECRET_KEY and SESSION_COOKIE_SECURE appropriately in production.
- Restrict and validate all user inputs on server side; client‑side validation is not sufficient.


## Troubleshooting
- Cannot connect to DB: verify DB_HOST/DB_PORT, credentials, and that PostgreSQL is running.
- Tables missing: the app creates tables on startup; check logs/console for DDL errors.
- Plotly/pandas errors: ensure dependencies installed with correct versions for your Python runtime.


## Assumptions and non‑goals
- This project uses Flask (not Django). There are no Django apps, urls.py, serializers.py, forms.py, or admin.py files. Where the original request referenced Django, we documented the closest Flask equivalents.
- Domain models in models.py are plain Python classes; persistence uses explicit SQL/psycopg2 in database_postgres.py.
- Migrations are not managed by Alembic in this repo; schema is created/verified at runtime.
