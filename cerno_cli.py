# cerno_cli.py
import subprocess
import sys
import time
import os
import click

# --- Configuration ---
IS_WINDOWS = os.name == 'nt'
FRONTEND_DIR = "frontend"
NULL_DEVICE = "NUL" if IS_WINDOWS else "/dev/null"
REPO_URL = "\n https://github.com/divagr18/Cerno-Agentic-Local-Deep-Research"


# --- Helper Function for Running Commands ---
def run_command(command, cwd=None, quiet=False, error_message="Command failed"):
    """
    Runs a command and checks for errors.
    This version manually changes directory if 'cwd' is provided, which is more robust on Windows.
    """
    if IS_WINDOWS and isinstance(command, list):
        command_str = subprocess.list2cmdline(command)
    elif isinstance(command, list):
        command_str = " ".join(command)
    else:
        command_str = command

    click.echo(click.style(f"▶️  Running: '{command_str}' in '{cwd or os.getcwd()}'", fg="yellow"))

    original_cwd = os.getcwd()
    stdout_dest = None
    try:
        if cwd:
            os.chdir(cwd)
        stdout_dest = open(NULL_DEVICE, 'w') if quiet else None
        stderr_dest = subprocess.STDOUT if quiet else None

        subprocess.run(
            command,
            check=True,
            shell=True,
            stdout=stdout_dest,
            stderr=stderr_dest
        )
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"❌ {error_message}", fg="red"))

        click.echo(f"   The command failed with exit code {e.returncode}.")
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(
            click.style(f"❌ Command not found: {command[0] if isinstance(command, list) else command.split()[0]}",
                        fg="red"))
        sys.exit(1)
    finally:
        if cwd:
            os.chdir(original_cwd)
        # Close the file handle if we opened one
        if stdout_dest:
            stdout_dest.close()


# --- CLI Command Definitions ---

@click.group()
def cli():
    """Cerno AI Workspace CLI - Your one-stop tool for managing the project."""
    pass


@cli.command()
@click.option('--verbose', is_flag=True, default=False, help="Show detailed output from pip and npm.")
def setup(verbose):
    """
    Installs all dependencies and the project itself.
    """
    quiet_mode = not verbose

    click.echo(f" ")
    click.echo(click.style("🚧 Cerno is new and under active development!", fg="cyan"))
    click.echo(f" ")
    click.echo(f"🎉 If you encounter any issues, please report them at:  {REPO_URL}/issues")
    click.echo(f" ")
    click.echo(f"👉 If you find Cerno helpful please ⭐ star the repo here:   {REPO_URL}")
    click.echo(f" ")

    # 2. Install the project in editable mode
    click.echo(click.style("\nInstalling project in editable mode (pip install -e .)...", fg="cyan"))
    run_command([sys.executable, "-m", "pip", "install", "-e", "."], quiet=quiet_mode,
                error_message="Failed to install project in editable mode.")

    # 3. Install Node.js dependencies
    click.echo(click.style("\nInstalling Node.js dependencies (npm install)...", fg="cyan"))
    run_command(["npm", "install"], cwd=FRONTEND_DIR, quiet=quiet_mode,
                error_message="Failed to install Node.js dependencies. Is Node.js/npm installed and in your PATH?")

    click.echo(click.style("\n✅ Setup complete!", fg="green"))


@cli.command()
@click.option('--verbose', is_flag=True, default=False, help="Show detailed output from migration commands.")
def migrate(verbose):
    """Runs Django database migrations."""
    quiet_mode = not verbose

    click.echo(click.style("--- 🗃️  Running Database Migrations ---", bold=True))
    click.echo(f" ")

    run_command([sys.executable, "manage.py", "makemigrations"], quiet=quiet_mode)
    click.echo(f" ")

    run_command([sys.executable, "manage.py", "migrate"], quiet=quiet_mode)
    click.echo(f" ")

    click.echo(click.style("✅  Migrations complete!", fg="green"))
    path = "source venv/bin/activate" if not IS_WINDOWS else r"venv\Scripts\activate"
    click.echo("\nNext steps:")
    click.echo(
        f"  1. {click.style('Create a .env file from the .env.example template and add your API keys.', fg='yellow')}")
    click.echo(f"  2. {click.style(f'Activate the virtual environment: `{path}`', fg='yellow')}")
    click.echo(f"  3. {click.style('Start the servers: `cerno start`', fg='yellow')}")
    click.echo(f"\nSee all commands with {click.style('cerno --help', fg='yellow')}")
    click.echo(f" ")
    click.echo(f"🎉 If you encounter any issues, please report them at:  {REPO_URL}/issues")


@cli.command(help="Launch both backend and frontend servers concurrently.")
@click.option('--no-frontend', is_flag=True, default=False, help="Launch only the backend server.")
def start(no_frontend):
    """Launch backend and frontend servers concurrently."""
    click.echo(click.style("--- ✨ Launching Cerno Workspace ---", bold=True))

    backend_cmd = [sys.executable, "-m", "uvicorn", "core.asgi:application", "--reload"]

    if IS_WINDOWS:
        frontend_cmd = "npm run dev --open"
    else:
        frontend_cmd = ["npm", "run", "dev", "--", "--open"]

    backend_proc = None
    frontend_proc = None
    original_cwd = os.getcwd()

    try:
        click.echo(click.style("🚀 Starting Django backend...", fg="cyan"))
        backend_proc = subprocess.Popen(backend_cmd)

        if not no_frontend:
            if not os.path.isdir(FRONTEND_DIR):
                click.echo(click.style(f"❌ Frontend directory '{FRONTEND_DIR}' not found.", fg="red"))
                sys.exit(1)

            click.echo(click.style("🚀 Starting Vite frontend...", fg="magenta"))
            os.chdir(FRONTEND_DIR)
            frontend_proc = subprocess.Popen(frontend_cmd, shell=IS_WINDOWS)

        time.sleep(1.2)
        click.echo(click.style("\n🎉 Servers are running! Press CTRL+C to stop.", fg="green", bold=True))
        click.echo(f" ")
        click.echo(f"🎉 If you encounter any issues, please report them at:  {REPO_URL}/issues")
        click.echo(f" ")
        click.echo(f"👉 If you find Cerno helpful please ⭐ star the repo here:   {REPO_URL}")
        click.echo(f" ")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        click.echo(click.style("\n🛑 CTRL+C detected, shutting down servers...", fg="yellow"))

    finally:
        os.chdir(original_cwd)
        if frontend_proc and frontend_proc.poll() is None:
            click.echo("   - Stopping frontend server...")
            if IS_WINDOWS:
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(frontend_proc.pid)])
            else:
                frontend_proc.terminate()
            frontend_proc.wait()
        if backend_proc and backend_proc.poll() is None:
            click.echo("   - Stopping backend server...")
            backend_proc.terminate()
            backend_proc.wait()
        click.echo(click.style("✅ Servers stopped.", fg="green"))


if __name__ == '__main__':
    cli()