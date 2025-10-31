import os

c = get_config()  # noqa: F821

# --- Core Hub config ---
c.JupyterHub.bind_url = "http://:8000"
c.JupyterHub.hub_ip = "hub"
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
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
network_name = os.environ.get("DOCKER_NETWORK_NAME", "jupyterhub-net")
c.DockerSpawner.network_name = network_name

# Use a public image by default to avoid local image missing errors during initial bring-up.
# Switch back to "local/jhub-singleuser:latest" after building your single-user image.
c.DockerSpawner.image = "quay.io/jupyter/datascience-notebook:latest"
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": "/home/jovyan"}

c.DockerSpawner.mem_limit = "4G"
c.DockerSpawner.cpu_limit = 2
c.DockerSpawner.remove = True
c.DockerSpawner.name_template = "jupyter-{username}-{servername}"

c.Spawner.default_url = "/lab"
c.Spawner.environment = {
    "GRANT_SUDO": "yes",
    "JUPYTERHUB_SINGLEUSER_APP": "jupyter_server.serverapp.ServerApp",
}

c.DockerSpawner.allowed_images = {
    "Full stack (Lab + VS Code + marimo)": "local/jhub-singleuser:latest",
    "Minimal (Python only)": "quay.io/jupyter/minimal-notebook:latest",
    "R notebook": "quay.io/jupyter/r-notebook:latest",
}

# --- OPTIONAL: ProfilesSpawner for image + resources ---
# Requires wrapspawner in hub image:
# from wrapspawner import ProfilesSpawner
# c.JupyterHub.spawner_class = "wrapspawner.ProfilesSpawner"
# c.ProfilesSpawner.profiles = [
#     ("Full stack - 4GB", "full-4g", "dockerspawner.DockerSpawner",
#      dict(image="local/jhub-singleuser:latest", mem_limit="4G", cpu_limit=2)),
#     ("R - 8GB", "r-8g", "dockerspawner.DockerSpawner",
#      dict(image="quay.io/jupyter/r-notebook:latest", mem_limit="8G", cpu_limit=4)),
# ]

# c.JupyterHub.trust_xheaders = True
