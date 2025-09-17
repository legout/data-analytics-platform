FROM jupyterhub/jupyterhub:latest

RUN apt-get update && apt-get install -y curl git && apt-get clean

# Install uv for Python venv management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Create Python virtual environment
RUN uv venv /opt/venv

# Install required Python packages
RUN /opt/venv/bin/pip install --upgrade pip
RUN /opt/venv/bin/pip install polars duckdb pyiceberg ducklake delta-rs ibis boring-semantic-layer datafusion fsspec-utils flowerpower flowerpower-io

# Install Code Server
RUN curl -fsSL https://code-server.dev/install.sh | sh

# Install Jupyter server proxy extensions
RUN /opt/venv/bin/pip install jupyter-server-proxy jupyterlab-codeserver jupyter-marimo-proxy

CMD ["jupyterhub", "--ip", "0.0.0.0", "--port", "8000"]
