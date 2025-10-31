# JupyterHub DockerSpawner PRD Task List

## Core Setup
- [ ] Create repository skeleton `jhub-docker/` with `hub/` and `singleuser/` directories.

## Docker Compose
- [ ] Add `jupyterhub-net` network and `jupyterhub_data` named volume to `docker-compose.yml`.
- [ ] Configure the `hub` service build context, image tag, port mapping, docker socket mount, and environment values in `docker-compose.yml`.

## Hub Image
- [ ] Write `hub/Dockerfile` installing `dockerspawner`, `jupyterhub-nativeauthenticator`, `jupyterlab`, and `jupyter-server-proxy`.
- [ ] Implement core Hub settings in `hub/jupyterhub_config.py` (bind URL, hub IP, authenticator, admin settings).
- [ ] Add DockerSpawner configuration in `hub/jupyterhub_config.py` covering network, default image, per-user volumes, resource limits, environment, and allowed images dropdown.
- [ ] Comment optional ProfilesSpawner configuration in `hub/jupyterhub_config.py` using `wrapspawner` for future resource profiles.

## Single-User Image
- [ ] Write `singleuser/Dockerfile` based on `quay.io/jupyter/datascience-notebook` with required apt packages and Python dependencies.
- [ ] Add `singleuser/jupyter_server_config.d/marimo-proxy.json` defining the marimo server proxy launcher entry.
- [ ] Create `templates/singleuser-uv/` scaffolding with uv-based Dockerfile variants (JupyterLab, code-server, marimo) and helper scripts.
- [ ] Write `templates/singleuser-uv/README.md` guiding engineers through copying and customizing uv images.
- [ ] Update Hub configuration to register uv-based images via `c.DockerSpawner.allowed_images`.

## Resource Profiles
- [ ] Configure ProfilesSpawner entries pairing uv image flavors with CPU/RAM limits.
- [ ] Document how to adjust `default_url` per profile for code-server and marimo-first experiences.

## Documentation
- [ ] Extend the PRD/README with build and startup instructions (`docker compose build` / `docker compose up -d`).
- [ ] Document first-admin flow and how to manage admin privileges.
- [ ] Document troubleshooting guidance for networking, missing VS Code tile, marimo proxy issues, and spawn failures.
- [ ] Document security and hardening recommendations (restrict images, reverse proxy, image pinning, idle culler).

## Verification
- [ ] Draft acceptance test checklist covering signup, server launch UI tiles, image selection verification, volume persistence, and admin controls.
- [ ] Run `docker compose up -d` locally to confirm the Hub is reachable at `http://localhost:8000`.
- [ ] Verify per-user containers start with `/lab` default URL and receive expected environment variables.
- [ ] Confirm allowed images dropdown launches each specified image.

## Optional Reverse Proxy
- [ ] Add `nginx` service definition to `docker-compose.yml` for TLS termination when needed.
- [ ] Write Nginx configuration files (`nginx/nginx.conf`, `nginx/conf.d/jupyterhub.conf`) mirroring the PRD guidance.
- [ ] Document steps to generate self-signed certificates and optional DH params for local testing.
