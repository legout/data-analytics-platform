# Custom Single-User Image Template (uv base)

This template shows how to build JupyterHub-compatible single-user images from the lightweight `ghcr.io/astral-sh/uv` base image. All variants:

* Create a non-root user named `ewn` (UID 1000 by default).
* Install shared Python dependencies declared in `requirements.txt`.
* Support optional extras (JupyterLab, VS Code proxy, marimo) through small build-time toggles.

## Usage

1. Copy this directory to a new folder (e.g. `singleuser/custom-analytics`).
2. Decide which entrypoint you want:
   * `Dockerfile.jupyterlab` — JupyterLab + server proxies for VS Code and marimo.
   * `Dockerfile.codeserver` — boots code-server directly, no JupyterLab.
   * `Dockerfile.marimo` — boots marimo directly, no JupyterLab.
3. Rename your chosen Dockerfile to `Dockerfile` or point Docker to it with `docker build -f`.
4. Add Python dependencies to `requirements.txt`.
5. (Optional) Add extra build steps or tooling to `build.sh`.
6. Build your image:

   ```bash
   # from repo root
    docker build -t local/custom-analytics -f singleuser/custom-analytics/Dockerfile .
   ```

7. Register the image with JupyterHub either via `c.DockerSpawner.allowed_images` or ProfilesSpawner (examples in the PRD).

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile.jupyterlab` | Full JupyterLab workspace with Jupyter server proxies for VS Code and marimo. |
| `Dockerfile.codeserver` | Code-server focused image (no JupyterLab); uses `jhsingle-native-proxy` for Hub integration. |
| `Dockerfile.marimo` | Lightweight marimo-only image (no JupyterLab); exposes marimo via `jhsingle-native-proxy`. |
| `requirements.txt` | Shared Python dependencies installed with uv. |
| `build.sh` | Example helper script to pin uv version / run additional steps. |
| `marimo-proxy.json` | ServerProxy snippet to expose marimo within JupyterLab (if enabled). |
| `vscode-proxy.json` | ServerProxy snippet for VS Code when running the JupyterLab flavor. |
| `start-code-server.sh` | Launch wrapper to run code-server through `jhsingle-native-proxy`. |
| `start-marimo.sh` | Launch wrapper to run marimo through `jhsingle-native-proxy`. |

## Customizing

* **User / permissions**: the Dockerfiles create `/home/ewn` and set ownership. Adjust UID/GID with `--build-arg`.
* **Python packages**: edit `requirements.txt` or add extra `uv pip install` lines.
* **System packages**: extend the `apt-get` step inside each Dockerfile.
* **Marimo / VS Code**: comment or remove the related sections (and environment variables) if you do not need them.
* **c.DockerSpawner.allowed_images**: add a descriptive label (e.g. `"Analytics (uv + Lab)"`) mapped to your built image tag.
* **ProfilesSpawner resources**: combine image + CPU/RAM caps for different sizes (see Hub config example).
