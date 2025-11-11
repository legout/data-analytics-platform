# uv-based JupyterLab single-user image (nebula user, /home/jovyan persistence)

FROM ghcr.io/astral-sh/uv:python3.11-bookworm

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini sudo git curl ca-certificates bash \
    && rm -rf /var/lib/apt/lists/*

# Create 'nebula' with home /home/nebula for consistency across images
RUN useradd -m -d /home/nebula -s /bin/bash nebula \
    && echo "nebula ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nebula \
    && chmod 0440 /etc/sudoers.d/nebula

# Core packages for Jupyter Server + Lab + proxy
RUN uv pip install --system \
    jupyterhub \
    jupyter_server \
    jupyterlab \
    jupyter-server-proxy

# Ensure Jupyter config dir exists
RUN mkdir -p /usr/local/etc/jupyter/jupyter_server_config.d \
    && chown -R nebula:nebula /home/nebula

ENV JUPYTERHUB_SINGLEUSER_APP=jupyter_server.serverapp.ServerApp

ENTRYPOINT ["/usr/bin/tini", "-g", "--"]

USER nebula
WORKDIR /home/nebula
