# JupyterHub + DockerSpawner Platform — Product Requirements Document (PRD)

## 1) Overview

Build a self‑hosted JupyterHub deployment that spawns per‑user Docker containers. The single‑user image provides JupyterLab, VS Code (via `jupyter-vscode-proxy`), and **marimo** (proxied via `jupyter-server-proxy`). Users can choose between multiple images at spawn time (simple dropdown) or select a resource profile (via ProfilesSpawner).

## 2) Goals & Non‑Goals

**Goals**

* One‑command local deployment using Docker Compose.
* Per‑user containers with persistent home directories stored in named volumes.
* Default single‑user image with JupyterLab, VS Code, marimo; visible tiles in the Launcher.
* Simple local authentication (NativeAuthenticator) with optional self‑signup, easy admin elevation.
* Let users choose among multiple images at spawn time (built‑in dropdown) **or** via ProfilesSpawner for image + resources.
* Clean configuration, reproducible builds, documented ops routines.

**Non‑Goals**

* Kubernetes scaling (KubeSpawner) — out of scope for this phase.
* SSO/OAuth integration (GitHub/Google) — optional future enhancement.
* TLS termination and public reverse proxy setup — recommend Traefik/Nginx, but not part of this delivery.

## 3) Users & Use Cases

* **Data scientists / students**: need JupyterLab/VSCodium and marimo for exploratory work and apps.
* **Instructors**: consistent, shareable environments (nbgitpuller optional).
* **Admins**: manage user signups, assign admin role, control which images are allowed.

## 4) High‑Level Architecture

* **JupyterHub (Hub service)** in a Docker container on a dedicated Docker network.
* **DockerSpawner** launches **one container per user** from a chosen image.
* **Volumes**: per‑user named volume mounted to `/home/jovyan` for persistence.
* **Server Proxies**: `jupyter-server-proxy` exposes VS Code (`jupyter-vscode-proxy`) and marimo under the user server URL.

```
Browser ──> JupyterHub (hub) ──(spawn via docker.sock)──> User container(s)
                                                 └──> docker network: jupyterhub-net
```

## 5) Deliverables

1. **Working Docker Compose stack** with Hub and network configuration.
2. **Hub image** with JupyterHub + DockerSpawner + NativeAuthenticator; `jupyterhub_config.py` implementing:

   * Docker network wiring
   * Per‑user volumes
   * Default URL `/lab`
   * Image selection via `allowed_images` (and commented alternative using ProfilesSpawner)
3. **Single‑user image** with JupyterLab, jupyter‑server‑proxy, jupyter‑vscode‑proxy, marimo, and an added server proxy config for marimo.
4. **README snippets in this PRD** (Build/Run/Operate/Troubleshoot).
5. **Acceptance tests** section.
6. **Template scaffolding** under `templates/singleuser-uv/` for building uv-based single-user images (JupyterLab, code-server, marimo variants).

## 6) Repository Layout

```
jhub-docker/
├─ docker-compose.yml
├─ hub/
│  ├─ Dockerfile
│  └─ jupyterhub_config.py
└─ singleuser/
   ├─ Dockerfile
   └─ jupyter_server_config.d/
      └─ marimo-proxy.json
```

## 7) Implementation Details

### 7.1 `docker-compose.yml`

```yaml
version: "3.9"

networks:
  jupyterhub:
    name: jupyterhub-net

volumes:
  jupyterhub_data:

services:
  hub:
    build: ./hub
    image: local/jupyterhub-hub:latest
    container_name: jupyterhub-hub
    restart: unless-stopped
    networks:
      - jupyterhub
    ports:
      - "8000:8000"  # JupyterHub entry
    volumes:
      - jupyterhub_data:/srv/jupyterhub
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      DOCKER_HOST: unix:///var/run/docker.sock
      DOCKER_NETWORK_NAME: jupyterhub-net
      # Optional external host if behind reverse proxy
      # HUB_PUBLIC_HOST: hub.example.com
```

### 7.2 Hub image

**`hub/Dockerfile`**

```dockerfile
FROM jupyterhub/jupyterhub:latest

# DockerSpawner + local auth
RUN python3 -m pip install --no-cache-dir \
      dockerspawner \
      jupyterhub-nativeauthenticator

# Useful runtime bits
RUN python3 -m pip install --no-cache-dir \
      jupyterlab \
      jupyter-server-proxy

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
```

**`hub/jupyterhub_config.py`**

```python
import os

c = get_config()  # noqa

# --- Core Hub config ---
c.JupyterHub.bind_url = "http://:8000"
c.JupyterHub.hub_ip = "hub"           # service name on the docker network
c.JupyterHub.allow_named_servers = True
c.JupyterHub.admin_access = True

# --- Auth: simple local accounts ---
c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"
c.NativeAuthenticator.open_signup = True
c.Authenticator.admin_users = {"admin"}

# --- Spawner: DockerSpawner ---
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
network_name = os.environ.get("DOCKER_NETWORK_NAME", "jupyterhub-net")
c.DockerSpawner.network_name = network_name

# Default single-user image (fallback)
c.DockerSpawner.image = "local/jhub-singleuser:latest"

# Per-user named volumes for /home/jovyan
c.DockerSpawner.volumes = {
    "jupyterhub-user-{username}": "/home/jovyan"
}

# Resource limits (tune for your host)
c.DockerSpawner.mem_limit = "4G"
c.DockerSpawner.cpu_limit = 2

# Cleanup stopped containers
c.DockerSpawner.remove = True

# Naming template (debug friendly)
c.DockerSpawner.name_template = "jupyter-{username}-{servername}"

# Default UI: JupyterLab
c.Spawner.default_url = "/lab"

# Environment into user containers
c.Spawner.environment = {
    "GRANT_SUDO": "yes",
    "JUPYTERHUB_SINGLEUSER_APP": "jupyter_server.serverapp.ServerApp"
}

# --- Allow users to choose from multiple images (simple dropdown) ---
c.DockerSpawner.allowed_images = {
    "Full stack (Lab + VS Code + marimo)": "local/jhub-singleuser:latest",
    "Minimal (Python only)": "quay.io/jupyter/minimal-notebook:latest",
    "R notebook": "quay.io/jupyter/r-notebook:latest",
}

# --- OPTIONAL: ProfilesSpawner for image + resources (replace spawner_class above) ---
# Requires: pip install wrapspawner (in hub image)
# from wrapspawner import ProfilesSpawner
# c.JupyterHub.spawner_class = "wrapspawner.ProfilesSpawner"
# c.ProfilesSpawner.profiles = [
#     ("Full stack - 4GB", "full-4g", "dockerspawner.DockerSpawner",
#      dict(image="local/jhub-singleuser:latest", mem_limit="4G", cpu_limit=2)),
#     ("R - 8GB", "r-8g", "dockerspawner.DockerSpawner",
#      dict(image="quay.io/jupyter/r-notebook:latest", mem_limit="8G", cpu_limit=4)),
# ]

# If behind a reverse proxy, consider:
# c.JupyterHub.trust_xheaders = True
```

### 7.3 Single‑user image (Lab + VS Code + marimo)

**`singleuser/Dockerfile`**

```dockerfile
# Rich base with conda, JupyterLab, etc.
FROM quay.io/jupyter/datascience-notebook:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl tini && \
    rm -rf /var/lib/apt/lists/*

USER ${NB_UID}

# Core pieces
RUN mamba install -y -c conda-forge \
    jupyterhub jupyter_server jupyterlab \
    && mamba clean -afy

RUN pip install --no-cache-dir \
    jupyter-server-proxy \
    jupyter-vscode-proxy \
    marimo \
    nbgitpuller

# Default to Jupyter Server (Lab UI)
ENV JUPYTERHUB_SINGLEUSER_APP=jupyter_server.serverapp.ServerApp

# Server-proxy definition for marimo (Launcher tile + /marimo)
COPY jupyter_server_config.d/marimo-proxy.json /opt/conda/etc/jupyter/jupyter_server_config.d/marimo-proxy.json
```

**`singleuser/jupyter_server_config.d/marimo-proxy.json`**

```json
{
  "ServerProxy": {
    "servers": {
      "marimo": {
        "command": [
          "bash",
          "-lc",
          "marimo",
          "--host=127.0.0.1",
          "--port={port}"
        ],
        "timeout": 20,
        "launcher_entry": {
          "title": "Marimo",
          "icon_path": ""
        }
      }
    }
  }
}
```

> To open a specific project dir by default, change command to: `cd /home/jovyan && marimo --host=127.0.0.1 --port={port}`.

### 7.4 Custom uv-based single-user templates

To support bespoke Python stacks while keeping images small, the repository ships a template bundle under `templates/singleuser-uv/`. It targets the `ghcr.io/astral-sh/uv` base image and creates a non-root `ewn` user so containers match local development expectations.

Template highlights:

* **Variants**: `Dockerfile.jupyterlab` (full workspace with proxies), `Dockerfile.codeserver` (no JupyterLab; launches code-server through `jhsingle-native-proxy`), and `Dockerfile.marimo` (marimo-only with `jhsingle-native-proxy`).
* **Shared dependencies**: drop package pins into `requirements.txt`; each Dockerfile installs them with `uv pip install --system`.
* **Optional tooling**: both marimo and VS Code proxy JSON snippets are provided; delete what you do not need.
* **Entrypoints**: helper scripts (`start-code-server.sh`, `start-marimo.sh`) bridge non-Jupyter apps back to the Hub by wrapping them with `jhsingle-native-proxy`.

Workflow:

1. Copy `templates/singleuser-uv/` to a new folder (e.g. `singleuser/uv-analytics`) and pick one of the Dockerfile flavors.
2. Rename the chosen Dockerfile or pass `-f` during `docker build`.
3. Customize `requirements.txt` and optional build steps (`build.sh`) for per-project tooling.
4. Build and tag the image, then map it into `c.DockerSpawner.allowed_images`.
5. For resource-bound offerings, add ProfilesSpawner entries combining the image tag with CPU / RAM limits:

   ```python
   c.JupyterHub.spawner_class = "wrapspawner.ProfilesSpawner"
   c.ProfilesSpawner.profiles = [
       ("uv Lab - 2 CPU / 4GB", "uv-lab-small", "dockerspawner.DockerSpawner",
        dict(image="local/uv-lab:latest", mem_limit="4G", cpu_limit=2)),
       ("code-server - 4 CPU / 8GB", "uv-code-medium", "dockerspawner.DockerSpawner",
        dict(image="local/uv-code:latest", mem_limit="8G", cpu_limit=4)),
       ("marimo - 1 CPU / 2GB", "uv-marimo-light", "dockerspawner.DockerSpawner",
        dict(image="local/uv-marimo:latest", mem_limit="2G", cpu_limit=1))
   ]
   ```

   *(Set `default_url` within each profile if you want to land users on a proxy endpoint such as `/proxy/code-server/` or `/marimo/`.)*

## 8) Build, Run, Operate

**Build & start**

```bash
# from repo root
docker compose build
docker compose up -d
# open http://localhost:8000
```

**First admin**

Bootstrap options:

- NativeAuthenticator (default): visit `/hub/signup`, create `admin` with a strong password (8+ chars), then log in and approve other users in the Admin UI.
- If sign-in is blocked during bootstrap, switch to Dummy auth temporarily: set `AUTH_STRATEGY=dummy` (and optionally `DUMMY_PASSWORD=…`) in the Hub environment, restart the stack, log in as `admin`, approve users, then switch back to native.

**Using multiple images**

* Stop your running server, then Start again to see the image dropdown.
* For ProfilesSpawner, switch `spawner_class` and rebuild hub; choices include RAM/CPU limits.

## 9) Security & Hardening

* **Restrict images** with `allowed_images` (do not allow arbitrary user‑provided names).
* Run the Hub behind **Traefik/Nginx** with TLS and proper headers (`X-Forwarded-*` + `trust_xheaders=True`).
* Pin specific image digests for reproducibility in production.
* Consider enabling an **idle culler** service to stop inactive servers.

## 10) Troubleshooting

* **Users can’t reach Hub from containers**: both hub and user containers must share `jupyterhub-net`; verify `c.JupyterHub.hub_ip = "hub"`.
* **VS Code tile missing**: ensure `jupyter-vscode-proxy` is installed in the **single‑user** image; rebuild.
* **Marimo tile/URL not working**: confirm CLI supports `--host/--port`; check proxy JSON path; rebuild image.
* **Spawn fails**: check Docker permissions (`/var/run/docker.sock` mount) and resource limits.

## 11) Acceptance Criteria

* `docker compose up -d` brings up a reachable Hub at `http://localhost:8000`.
* New user can sign up, start a server, and see **JupyterLab**, **VS Code** tile, and **Marimo** tile.
* Selecting different images via dropdown launches the correct image (verify different package sets).
* User home persists across server restarts via per‑user named volumes.
* Admin can view and stop user servers via Admin panel.

## 12) Future Enhancements (Optional)

* OAuth (GitHub/Google/GitLab) via OAuthenticator.
* GPU profiles (CUDA‑enabled images) with resource quotas.
* Course distribution with `nbgitpuller` links.
* Kubernetes migration (KubeSpawner) for scaling.

## 13) Definition of Done

* Repo contains all files exactly as specified.
* README section in this PRD is sufficient for a new engineer to bring up the stack on a clean Docker host.
* Manual QA run-through passes all acceptance criteria above.

## 14) Nginx reverse proxy (self‑signed TLS)

This section adds an **Nginx** reverse proxy terminating TLS with your **self‑signed certificates** and forwarding to the Hub over the internal Docker network.

### 14.1 Compose changes (add `nginx` service)

```yaml
# docker-compose.yml (add alongside the existing hub service)
services:
  hub:
    # ... (unchanged except remove published port)
    ports: []  # Hub is internal only now; exposed via nginx

  nginx:
    image: nginx:alpine
    container_name: jupyterhub-nginx
    restart: unless-stopped
    depends_on:
      - hub
    networks:
      - jupyterhub
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/certs:/etc/nginx/certs:ro
```

### 14.2 Hub tweaks

```python
# hub/jupyterhub_config.py
# ... existing config ...
c.JupyterHub.trust_xheaders = True
# Keep Hub binding internal (docker network)
c.JupyterHub.bind_url = "http://:8000"
# Optional: advertise an external hostname if you have one
# c.JupyterHub.base_url = "/"  # default; adjust if you terminate under a subpath
```

### 14.3 Nginx config files

**`nginx/nginx.conf`**

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events { worker_connections 1024; }

http {
  include       /etc/nginx/mime.types;
  default_type  application/octet-stream;
  log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
  access_log  /var/log/nginx/access.log  main;

  sendfile        on;
  tcp_nopush      on;
  tcp_nodelay     on;
  keepalive_timeout  65;
  types_hash_max_size 4096;

  # WebSocket upgrade mapping
  map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
  }

  include /etc/nginx/conf.d/*.conf;
}
```

**`nginx/conf.d/jupyterhub.conf`**

```nginx
# Redirect all HTTP to HTTPS
server {
  listen 80;
  listen [::]:80;
  server_name _;
  return 301 https://$host$request_uri;
}

server {
  listen 443 ssl http2;
  listen [::]:443 ssl http2;
  server_name _;

  # Self-signed certs
  ssl_certificate     /etc/nginx/certs/fullchain.pem;
  ssl_certificate_key /etc/nginx/certs/privkey.pem;
  # Optional: stronger key exchange (generate dhparam.pem ~ few minutes)
  ssl_dhparam         /etc/nginx/certs/dhparam.pem;

  # Reasonable TLS defaults
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:10m;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers on;

  # DO NOT set HSTS for self-signed in development; browsers will pin and complain.
  # add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

  # Max upload size (adjust as needed)
  client_max_body_size 64m;

  # Proxy to the Hub (internal service name `hub` on docker network)
  location / {
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;

    # WebSocket support
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    proxy_read_timeout 86400;  # long-lived kernels/terminals
    proxy_send_timeout 86400;

    proxy_pass http://hub:8000/;
  }
}
```

### 14.4 Self-signed certificate generation

Create the certs once on the host and mount them into the container under `nginx/certs/`.

```bash
mkdir -p nginx/certs
# 1) Private key
openssl genrsa -out nginx/certs/privkey.pem 4096
# 2) Self-signed cert (CN=your host; use your IP/host for CN and add SANs if desired)
openssl req -new -x509 -key nginx/certs/privkey.pem -out nginx/certs/fullchain.pem -days 825 \
  -subj "/CN=localhost"
# 3) (Optional) Stronger DH params (takes a while)
openssl dhparam -out nginx/certs/dhparam.pem 2048
```

**Trusting the cert**: Because it’s self‑signed, users’ browsers will warn. To suppress locally, import `fullchain.pem` into the system/browser trust store. For production, use a real CA (e.g., Let’s Encrypt via Certbot/Traefik).

### 14.5 Run

```bash
docker compose up -d --build
# Visit https://localhost (accept the warning for self‑signed)
```

### 14.6 Notes

* If you deploy behind another reverse proxy/load balancer, ensure only one layer terminates TLS or forward TLS with `proxy_protocol` + `real_ip` handling.
* If hosting under a sub‑path (e.g., `/hub/`), set `c.JupyterHub.base_url = "/hub/"` and update `proxy_pass http://hub:8000/hub/` in Nginx.
