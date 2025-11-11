# uv-based single-user image that boots Jupyter Server but lands users in marimo.
# Includes helper scripts to manage multiple persistent uv virtualenvs per user.

FROM ghcr.io/astral-sh/uv:python3.11-bookworm

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini sudo git curl ca-certificates bash \
    && rm -rf /var/lib/apt/lists/*

# Create a cool user named 'nebula' with home at /home/nebula
RUN useradd -m -d /home/nebula -s /bin/bash nebula \
    && echo "nebula ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nebula \
    && chmod 0440 /etc/sudoers.d/nebula

# Install the minimal pieces for JupyterHub single-user + marimo + proxy
# Use uv's fast installer. `--system` installs into the base environment.
RUN uv pip install --system \
    jupyterhub \
    jupyter_server \
    jupyter-server-proxy \
    marimo \
    jupyter-marimo-proxy
    #jhsingle-native-proxy

# Prepare persistent uv venv directory and helper activation
RUN mkdir -p /home/nebula/.uv/venvs \
    && mkdir -p /usr/local/etc/jupyter/jupyter_server_config.d \
    && chown -R nebula:nebula /home/nebula

# Copy helper scripts and proxy config
COPY singleuser/uv-helpers/uv-venv /usr/local/bin/uv-venv
COPY singleuser/uv-helpers/activate.sh /home/nebula/.uv/activate


RUN chmod +x /usr/local/bin/uv-venv \
    && chown -R nebula:nebula /home/nebula

# Set explicit config dir env for guaranteed discovery
#ENV JUPYTER_CONFIG_DIR=/usr/local/etc/jupyter

# Make sure the JupyterHub single-user app is the Jupyter Server
ENV JUPYTERHUB_SINGLEUSER_APP=jupyter_server.serverapp.ServerApp

# Good init for signal handling
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]

# Switch to non-root and default to home
USER nebula
WORKDIR /home/nebula
