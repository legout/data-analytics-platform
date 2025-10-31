# syntax=docker/dockerfile:1
FROM quay.io/jupyter/datascience-notebook:latest

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://code-server.dev/install.sh | sh

USER ${NB_UID}

RUN mamba install -y -c conda-forge \
    jupyterhub \
    jupyter_server \
    jupyterlab \
    && mamba clean -afy

RUN pip install --no-cache-dir \
    jupyter-server-proxy \
    jupyter-vscode-proxy \
    marimo \
    nbgitpuller

ENV JUPYTERHUB_SINGLEUSER_APP=jupyter_server.serverapp.ServerApp

COPY jupyter_server_config.d/marimo-proxy.json /opt/conda/etc/jupyter/jupyter_server_config.d/marimo-proxy.json
