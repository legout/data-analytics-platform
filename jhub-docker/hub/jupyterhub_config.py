import os

c = get_config()  # noqa: F821

# --- Core Hub config ---
c.JupyterHub.bind_url = "http://:8000"
# Bind the Hub on all interfaces inside the container and
# explicitly advertise how singleuser containers should reach it.
c.JupyterHub.hub_ip = "0.0.0.0"
# Singleuser containers will contact the Hub's internal API on this URL
# over the docker network (service DNS name: "hub").
c.JupyterHub.hub_connect_url = "http://hub:8081"
c.JupyterHub.allow_named_servers = True
c.JupyterHub.admin_access = True
c.Application.log_level = "DEBUG"

# --- Authenticator ---
auth_strategy = os.environ.get("AUTH_STRATEGY", "native").lower()
if auth_strategy == "dummy":
    c.JupyterHub.authenticator_class = "dummyauthenticator.DummyAuthenticator"
    c.DummyAuthenticator.password = os.environ.get("DUMMY_PASSWORD", "")
elif auth_strategy == "native":
    c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"
    c.NativeAuthenticator.open_signup = True
    c.Authenticator.admin_users = {"admin"}
    # c.Authenticator.allowed_users = {"volker"}
    # For bootstrap: allow all users to login until admin approves them; remove after initial setup
    c.Authenticator.allow_all = True
    # c.Authenticator.request_otp = True

# always a good idea to limit to localhost when testing with an insecure config
# c.JupyterHub.ip = "127.0.0.1"

# c.DummyAuthenticator.password = os.environ.get("DUMMY_PASSWORD", "")
# else:
#     c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"
#     c.NativeAuthenticator.open_signup = True
#     c.Authenticator.admin_users = {"admin"}
# c.Authenticator.allowed_users = {"volker"}
# c.Authenticator.allow_all = True
# c.Authenticator.request_otp = True

# --- Spawner: DockerSpawner ---
# Switch to ProfilesSpawner to offer image + resource size selections
from wrapspawner import ProfilesSpawner  # type: ignore

c.JupyterHub.spawner_class = "wrapspawner.ProfilesSpawner"
network_name = os.environ.get("DOCKER_NETWORK_NAME", "jupyterhub-net")
c.DockerSpawner.network_name = network_name

# Default image (used if ProfilesSpawner is disabled). With ProfilesSpawner enabled below,
# the image will be selected per profile.
c.DockerSpawner.image = "local/uv-lab:latest"
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": "/home/nebula"}

c.DockerSpawner.mem_limit = "4G"
c.DockerSpawner.cpu_limit = 2
c.DockerSpawner.remove = True
c.DockerSpawner.name_template = "jupyter-{username}-{servername}"

c.Spawner.default_url = "/lab"
c.Spawner.environment = {
    "GRANT_SUDO": "yes",
    "JUPYTERHUB_SINGLEUSER_APP": "jupyter_server.serverapp.ServerApp",
}

# Ensure singleuser binds on all interfaces and expected port
c.Spawner.args = [
    "--ServerApp.ip=0.0.0.0",
    "--ServerApp.port=8888",
]

# Explicitly set the single-user server port expected inside containers.
# Without this, the Hub was waiting on port 80 (incorrect) which led to timeouts.
c.Spawner.port = 8888
c.DockerSpawner.container_port = 8888

# Give images a bit more time to become responsive on first start
# Allow more time for images to pull/start on first run and for the
# server to become responsive.
c.Spawner.start_timeout = int(os.environ.get("SPAWNER_START_TIMEOUT", "300"))
c.Spawner.http_timeout = 120

# If ProfilesSpawner is disabled, this image list will be used for a simple dropdown.
# Updated to uv-based images and removed minimal/r-notebook per request.
c.DockerSpawner.allowed_images = {
    "uv JupyterLab (nebula)": "local/uv-lab:latest",
    "uv VS Code (nebula)": "local/uv-vscode:latest",
    "uv Marimo (nebula)": "local/uv-marimo:latest",
}

# --- Profiles: image + resources (CPU/RAM) ---
# Define two sizes per image up to 4 CPU / 8GB RAM. Also set default_url where applicable.
c.ProfilesSpawner.profiles = [
    # uv JupyterLab
    (
        "uv Lab - 2 CPU / 4GB",
        "uv-lab-small",
        "dockerspawner.DockerSpawner",
        dict(
            image="local/uv-lab:latest", mem_limit="4G", cpu_limit=2, default_url="/lab"
        ),
    ),
    (
        "uv Lab - 4 CPU / 8GB",
        "uv-lab-large",
        "dockerspawner.DockerSpawner",
        dict(
            image="local/uv-lab:latest", mem_limit="8G", cpu_limit=4, default_url="/lab"
        ),
    ),
    # uv VS Code (no JupyterLab UI; uses jupyter-vscode-proxy)
    (
        "uv VS Code - 2 CPU / 4GB",
        "uv-vscode-small",
        "dockerspawner.DockerSpawner",
        dict(
            image="local/uv-vscode:latest",
            mem_limit="4G",
            cpu_limit=2,
            default_url="/vscode/",
        ),
    ),
    (
        "uv VS Code - 4 CPU / 8GB",
        "uv-vscode-large",
        "dockerspawner.DockerSpawner",
        dict(
            image="local/uv-vscode:latest",
            mem_limit="8G",
            cpu_limit=4,
            default_url="/vscode/",
        ),
    ),
    # uv Marimo
    (
        "uv Marimo - 1 CPU / 2GB",
        "uv-marimo-light",
        "dockerspawner.DockerSpawner",
        dict(
            image="local/uv-marimo:latest",
            mem_limit="2G",
            cpu_limit=1,
            # jupyter-server-proxy exposes named servers at /proxy/<name>/
            default_url="/proxy/marimo/",
        ),
    ),
    (
        "uv Marimo - 2 CPU / 4GB",
        "uv-marimo-medium",
        "dockerspawner.DockerSpawner",
        dict(
            image="local/uv-marimo:latest",
            mem_limit="4G",
            cpu_limit=2,
            default_url="/proxy/marimo/",
        ),
    ),
]

# c.JupyterHub.trust_xheaders = True
