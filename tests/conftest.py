import os.path
import subprocess
import time

import pytest

pytest_plugins = 'pytester'

REPO_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "../"))


@pytest.fixture(autouse=True, scope="session")
def postgres_container(request):
    if request.config.getoption("database_url"):
        return  # Skip if --postgres-server option is given

    docker_ps_out = docker_compose("ps --services --filter status=running")
    if "db" in docker_ps_out:
        return  # Skip if container is already started through docker-compose

    docker_compose("up -d")
    time.sleep(3)
    request.addfinalizer(lambda: docker_compose("down"))
    return


def docker_compose(options: str) -> str:
    try:
        cmd = ["docker-compose", "--file", "docker-compose.yml"] + options.split()
        print(REPO_PATH)
        return subprocess.check_output(cmd, cwd=REPO_PATH).decode()
    except subprocess.CalledProcessError as exc:
        pytest.exit(f"Error calling docker-compose: {exc.stderr}", returncode=9)
