# Ensure jupyter-server-proxy registers a named server at /marimo
c = get_config()  # type: ignore[name-defined]

c.ServerProxy.servers = getattr(c.ServerProxy, 'servers', {}) or {}
c.ServerProxy.servers.update({
    "marimo": {
    "command": [
        "marimo",
        "edit",
        "--host=127.0.0.1",
        "--port={port}"
    ],
        # Slightly generous timeout for first start
        "timeout": 30,
        "launcher_entry": {
            "title": "Marimo (uv)",
            "icon_path": ""
        },
        # Keep URLs relative to the Jupyter Server base_url (/user/<name>/)
        "absolute_url": False,
    }
})

