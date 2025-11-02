FROM jupyterhub/jupyterhub:latest

RUN python3 -m pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-nativeauthenticator \
    jupyterhub-dummyauthenticator \
    wrapspawner

RUN python3 -m pip install --no-cache-dir \
    jupyterlab \
    jupyter-server-proxy

# Place config outside the persisted /srv/jupyterhub volume so it never gets shadowed
RUN mkdir -p /etc/jupyterhub
COPY jupyterhub_config.py /etc/jupyterhub/jupyterhub_config.py
