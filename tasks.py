# tasks.py
import os
from invoke import task, Context

# --- Configuration ---
# Determines if we are on Windows or a Unix-like system (Linux, macOS)
IS_WINDOWS = os.name == 'nt'
# The command to activate the virtual environment
VENV_ACTIVATE = "source venv/bin/activate" if not IS_WINDOWS else "venv\\Scripts\\activate"


@task
def setup(c: Context):
    """
    Install all Python and Node.js dependencies.
    """
    print("--- Installing Python dependencies from requirements.txt ---")
    c.run("pip install -r requirements.txt")

    print("\n--- Installing Node.js dependencies from frontend/package.json ---")
    with c.cd("frontend"):
        c.run("npm install")

    print("\n✅ Setup complete!")
    print("Next steps:")
    print("1. Create a '.env' file from the '.env.example' template and add your API keys.")
    print("2. Run 'invoke migrate' to set up your database.")
    print("3. Run 'invoke start' to launch the app.")


@task
def migrate(c: Context):
    """
    Runs Django's 'makemigrations' and 'migrate' commands.
    """
    print("--- Running Django database migrations ---")
    c.run("python manage.py makemigrations")
    c.run("python manage.py migrate")
    print("✅ Migrations complete.")


@task
def start_backend(c: Context):
    """
    Starts the Django development server.
    """
    print("🚀 Starting Django backend server on http://127.0.0.1:8000")
    c.run("python manage.py runserver", pty=not IS_WINDOWS)


@task
def start_frontend(c: Context):
    """
    Starts the Vite React development server.
    """
    print("🚀 Starting Vite frontend server on http://localhost:5173")
    with c.cd("frontend"):
        c.run("npm run dev", pty=not IS_WINDOWS)


@task(help={'no-frontend': "Launch only the backend server."})
def start(c: Context, no_frontend=False):
    """
    Launch both backend and frontend servers simultaneously.
    """
    print("--- Launching AI Agent Workspace ---")

    # Run backend asynchronously
    backend_promise = c.run("invoke start-backend", asynchronous=True, pty=not IS_WINDOWS)

    if not no_frontend:
        # Run frontend asynchronously
        frontend_promise = c.run("invoke start-frontend", asynchronous=True, pty=not IS_WINDOWS)

    print("\n🎉 Both servers are running! Press CTRL+C to stop.")
    # You can add more logic here if needed, but for now, we just let them run.
    # The promises can be joined if you need to wait for them to finish,
    # but for servers, we want them to run indefinitely.