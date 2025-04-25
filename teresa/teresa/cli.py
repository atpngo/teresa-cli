# teresa/cli.py

import typer
import docker
import os
import shutil
import subprocess

app = typer.Typer()
REPO_URL = "https://github.com/Elegant-Mind-Club/teresa-docker.git"
CONTAINER_NAME = "teresa_dev_env"


def git_installed():
    git_path = shutil.which("git")
    if git_path:
        return True
    else:
        return False


def docker_daemon_is_running():
    try:
        client = docker.from_env()
        return client.ping()
    except Exception as e:
        print(
            f"Docker daemon is not running. Please check if docker is installed or start the Docker daemon."
        )
        return False


def get_os_install_dir():
    home_dir = os.path.expanduser("~")
    if os.name == "nt":  # Windows
        install_dir = os.path.join(home_dir, "AppData", "Local", "teresa")
    elif os.name == "posix":
        if "darwin" in os.uname().sysname.lower():  # macOS
            install_dir = os.path.join(home_dir, "Documents", "teresa")
        else:  # Linux
            install_dir = os.path.join(home_dir, ".teresa")
    else:
        typer.echo("Unsupported platform.")
        raise SystemExit(1)

    return install_dir


def install_and_sync_repo(install_dir):
    if not os.path.exists(install_dir):
        typer.echo(f"Setting up environment in {install_dir}...")
        os.makedirs(install_dir, exist_ok=True)
        try:
            if git_installed():
                typer.echo(f"Cloning Dockerfiles into {install_dir}...")
                subprocess.run(
                    ["git", "clone", REPO_URL, install_dir],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            else:
                typer.echo("Git is not installed. Please install Git and try again.")
                raise SystemExit(1)
        except Exception as e:
            typer.echo(f"Failed to clone the repository: {e}")
            raise SystemExit(1)
    else:
        typer.echo(f"Found existing files at {install_dir}")
        typer.echo(f"Pulling latest changes...")
        res = subprocess.run(
            ["git", "pull"],
            cwd=install_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        typer.echo(f"{res.stdout}")


def container_is_running():
    client = docker.from_env()
    try:
        container = client.containers.get(CONTAINER_NAME)
        if container.status == "running":
            return True
        else:
            return False
    except docker.errors.NotFound:
        return False
    except Exception as e:
        typer.echo(f"Error checking container status: {e}")
        return False


def count_interactive_shells():
    client = docker.from_env()
    try:
        container = client.containers.get(CONTAINER_NAME)
        if container.status == "running":
            exec_processes = container.top()["Processes"]
            shell_count = sum(
                1
                for process in exec_processes
                if "sh" in process[-1] or "bash" in process[-1]
            )
            return shell_count
        else:
            return 0
    except docker.errors.NotFound:
        return 0
    except Exception as e:
        typer.echo(f"Error counting interactive shells: {e}")
        return 0


def stop_all_containers():
    typer.echo("Stopping any container instances...")
    install_dir = get_os_install_dir()
    if count_interactive_shells():
        subprocess.call(["docker", "compose", "down"], cwd=install_dir)


def purge():
    install_dir = get_os_install_dir()

    # Check if the container is still running and stop it
    stop_all_containers()
    # Delete the container
    typer.echo("Deleting the container and cache...")
    subprocess.run(
        ["docker", "compose", "down", "--volumes", "--rmi", "all"], cwd=install_dir
    )
    # Prune all dangling containers
    typer.echo("Removing dangling images...")
    res = subprocess.run(
        ["docker", "image", "prune", "-f"],
        capture_output=True,
        text=True,
    )
    typer.echo(res.stdout)

    # Then remove install files (needs to work across any OS)
    if os.path.exists(install_dir):
        try:
            shutil.rmtree(install_dir)
            typer.echo(f"Deleted all install files in {install_dir}")
        except Exception as e:
            typer.echo(f"Failed to delete install files: {e}")


@app.command()
def start():
    """Start the development environment."""
    if not (docker_daemon_is_running() and git_installed()):
        return

    install_dir = get_os_install_dir()
    install_and_sync_repo(install_dir)

    # If container is not running
    num_shells = count_interactive_shells()
    if num_shells == 0:
        subprocess.run(
            ["docker", "compose", "up", "-d", "--build"],
            cwd=install_dir,
        )
    subprocess.run(["docker", "exec", "-it", CONTAINER_NAME, "bash"])

    # Once we exit, we count the number of open shells and if it's 0 then we stop the container
    num_shells = count_interactive_shells()
    if num_shells == 1:
        subprocess.call(["docker", "compose", "down"], cwd=install_dir)


@app.command()
def stop():
    """Check if container is running and then stop it"""
    stop_all_containers()


@app.command()
def restart():
    """Rebuild the dev container from scratch."""
    # stop all containers, delete them, and then pull latest Dockerfiles, rebuild
    purge()
    install_dir = get_os_install_dir()
    install_and_sync_repo(install_dir)


@app.command()
def cleanup():
    """Delete all install files"""
    purge()


if __name__ == "__main__":
    app()
