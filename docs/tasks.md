# JupyterHub DockerSpawner PRD Task List

## Core Setup
- [x] Create repository skeleton `jhub-docker/` with `hub/` and `singleuser/` directories.

## Docker Compose
- [x] Add `jupyterhub-net` network and `jupyterhub_data` named volume to `docker-compose.yml`.
- [x] Configure the `hub` service build context, image tag, port mapping, docker socket mount, and environment values in `docker-compose.yml`.
- [ ] Ensure Hub state persists by mounting `jupyterhub_data:/srv/jupyterhub` under `hub.volumes` in `docker-compose.yml`.

## Hub Image
- [x] Write `hub/Dockerfile` installing `dockerspawner`, `jupyterhub-nativeauthenticator`, `jupyterlab`, and `jupyter-server-proxy`.
- [x] Implement core Hub settings in `hub/jupyterhub_config.py` (bind URL, hub IP, authenticator, admin settings).
- [x] Add DockerSpawner configuration in `hub/jupyterhub_config.py` covering network, default image, per-user volumes, resource limits, environment, and allowed images dropdown.
- [x] Comment optional ProfilesSpawner configuration in `hub/jupyterhub_config.py` using `wrapspawner` for future resource profiles.
- [ ] Harden authentication defaults in `hub/jupyterhub_config.py` (disable `c.Authenticator.allow_all` and `c.Authenticator.request_otp` unless explicitly required).

## Single-User Image
- [x] Write `singleuser/Dockerfile` based on `quay.io/jupyter/datascience-notebook` with required apt packages and Python dependencies.
- [x] Add `singleuser/jupyter_server_config.d/marimo-proxy.json` defining the marimo server proxy launcher entry.
- [x] Create `templates/singleuser-uv/` scaffolding with uv-based Dockerfile variants (JupyterLab, code-server, marimo) and helper scripts.
- [x] Write `templates/singleuser-uv/README.md` guiding engineers through copying and customizing uv images.
- [ ] Update Hub configuration to register uv-based images via `c.DockerSpawner.allowed_images`.

## Resource Profiles
- [ ] Configure ProfilesSpawner entries pairing uv image flavors with CPU/RAM limits.
- [x] Document how to adjust `default_url` per profile for code-server and marimo-first experiences.
- [ ] Enable ProfilesSpawner in Hub (`c.JupyterHub.spawner_class = "wrapspawner.ProfilesSpawner"`) when profiles are ready.

## Documentation
- [x] Extend the PRD/README with build and startup instructions (`docker compose build` / `docker compose up -d`).
- [x] Document first-admin flow and how to manage admin privileges.
- [x] Document troubleshooting guidance for networking, missing VS Code tile, marimo proxy issues, and spawn failures.
- [x] Document security and hardening recommendations (restrict images, reverse proxy, image pinning, idle culler).

## Verification
- [x] Draft acceptance test checklist covering signup, server launch UI tiles, image selection verification, volume persistence, and admin controls.
- [ ] Run `docker compose up -d` locally to confirm the Hub is reachable at `http://localhost:8000`.
- [ ] Verify per-user containers start with `/lab` default URL and receive expected environment variables.
- [ ] Confirm allowed images dropdown launches each specified image.
- [ ] Build at least one uv image variant and add it to `allowed_images`; verify it appears in the spawn UI and launches successfully.
- [ ] Validate per-user volume persistence across server restarts.

## Optional Reverse Proxy
- [ ] Add `nginx` service definition to `docker-compose.yml` for TLS termination when needed.
- [ ] Write Nginx configuration files (`nginx/nginx.conf`, `nginx/conf.d/jupyterhub.conf`) mirroring the PRD guidance.
- [x] Document steps to generate self-signed certificates and optional DH params for local testing.
- [ ] When enabling Nginx, set `c.JupyterHub.trust_xheaders = True` and keep Hub binding internal to the Docker network.
