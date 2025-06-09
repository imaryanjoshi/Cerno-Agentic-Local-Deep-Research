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

    click.echo(click.style(f"▶️ Running: '{command_str}' in '{cwd or os.getcwd()}'", fg="yellow"))

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
def setup():
    """
    Installs all dependencies and the project itself.
    """    # 2. Install the project in editable mode quietly
    click.echo(click.style("\nInstalling project and 'cerno' command...", fg="cyan"))
    run_command([sys.executable, "-m", "pip", "install", "-e", "."], quiet=True)

    # 3. Install Node.js dependencies quietly
    click.echo(click.style("\nInstalling Node.js dependencies...", fg="cyan"))
    run_command(["npm", "install"], cwd=FRONTEND_DIR, quiet=True)


@cli.command()
def migrate():
    """Runs Django database migrations."""
    click.echo(click.style("--- 🗃️ Running Database Migrations ---", bold=True))
    run_command([sys.executable, "manage.py", "makemigrations"])
    run_command([sys.executable, "manage.py", "migrate"])
    click.echo(click.style("✅  Migrations complete!", fg="green"))
    path = r"venv\Scripts\activate"
    click.echo("\nNext steps:")
    click.echo("\nFirst:")
    click.echo(f"  {click.style(f'Create a .env file from the .env.example template and add your API keys.', fg='yellow')}       - Activate the venv.")

    click.echo(f"  {click.style(f'run {path}', fg='yellow')}       - Activate the venv.")
    click.echo("Then:")

    click.echo(f"  {click.style('cerno start', fg='yellow')}       - Start the backend and frontend servers.")
    click.echo(f"  {click.style('cerno --help', fg='yellow')}      - See all available commands.")


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
    original_cwd = os.getcwd()  # Save the starting directory

    try:
        click.echo(click.style("🚀 Starting Django backend...", fg="cyan"))
        backend_proc = subprocess.Popen(backend_cmd)

        if not no_frontend:
            # --- THE FIX IS HERE ---
            # 1. Check if the frontend directory exists before trying to enter it.
            if not os.path.isdir(FRONTEND_DIR):
                click.echo(click.style(f"❌ Frontend directory '{FRONTEND_DIR}' not found.", fg="red"))
                sys.exit(1)

            click.echo(click.style("🚀 Starting Vite frontend...", fg="magenta"))

            # 2. Manually change the current working directory.
            os.chdir(FRONTEND_DIR)

            # 3. Run the command without the `cwd` argument, as we are already there.
            frontend_proc = subprocess.Popen(frontend_cmd, shell=IS_WINDOWS)

        click.echo(click.style("\n🎉 Servers are running! Press CTRL+C to stop.", fg="green", bold=True))
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        click.echo(click.style("\n🛑 CTRL+C detected, shutting down servers...", fg="yellow"))

    finally:
        # 4. CRUCIAL: Always change back to the original directory.
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