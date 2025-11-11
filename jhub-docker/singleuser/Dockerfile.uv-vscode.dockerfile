# uv-based VS Code (code-server) single-user image without JupyterLab UI.

FROM ghcr.io/astral-sh/uv:python3.11-bookworm

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini sudo git curl ca-certificates bash \
    && rm -rf /var/lib/apt/lists/*

# Create 'nebula' with home /home/nebula for consistency
RUN useradd -m -d /home/nebula -s /bin/bash nebula \
    && echo "nebula ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nebula \
    && chmod 0440 /etc/sudoers.d/nebula

# Install Jupyter Server (no Lab) and VS Code proxy
# jupyter-vscode-proxy brings code-server and wires it via server-proxy at /vscode/
RUN uv pip install --system \
    jupyterhub \
    jupyter_server \
    jupyter-server-proxy \
    jupyter-vscode-proxy

# Install code-server (required by jupyter-vscode-proxy)
RUN curl -fsSL https://code-server.dev/install.sh | sh

RUN mkdir -p /usr/local/etc/jupyter/jupyter_server_config.d \
    && chown -R nebula:nebula /home/nebula

ENV JUPYTERHUB_SINGLEUSER_APP=jupyter_server.serverapp.ServerApp

ENTRYPOINT ["/usr/bin/tini", "-g", "--"]

USER nebula
WORKDIR /home/nebula
