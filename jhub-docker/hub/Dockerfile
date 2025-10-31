FROM jupyterhub/jupyterhub:latest

RUN python3 -m pip install --no-cache-dir \
    dockerspawner \
    jupyterhub-nativeauthenticator \
    jupyterhub-dummyauthenticator \
    wrapspawner

RUN python3 -m pip install --no-cache-dir \
    jupyterlab \
    jupyter-server-proxy

COPY jupyterhub_config.py /srv/jupyterhub/jupyterhub_config.py
