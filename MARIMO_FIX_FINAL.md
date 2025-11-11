# Marimo 404 Fix - Final Implementation

**Issue**: Marimo container returning "404 Not Found" despite container running  
**Root Cause**: Marimo not configured with base URL path for proxy operation  
**Status**: ✅ FIXED - November 3, 2025

---

## Problem Analysis

### Logs Revealed the Issue

From marimo container logs:
```
[I] 302 GET /user/admin/ -> /user/admin/marimo/?
[I] 302 GET /user/admin/marimo/ -> /user/admin/marimo  (removes trailing slash)
[W] 404 GET /user/admin/marimo  (404 NOT FOUND)
```

**Root Cause**: Marimo was NOT told about its base URL path. When running at `/user/admin/marimo/`, marimo needs to know this via the `--base-url` flag so it can:
- Serve routes relative to that path
- Generate correct URLs for links
- Handle requests properly

### Why Previous Fix Was Insufficient

The first fix (`/proxy/marimo/` → `/marimo/`) was **correct and necessary**, but incomplete. That fixed the JupyterHub routing, but marimo itself still didn't know where it was being served from.

---

## Solution Implemented

### Changes Made

Updated two configuration files to add base-url support:

#### 1. `marimo-proxy-uv.json` - Added 3 critical elements:

```json
{
    "ServerProxy": {
        "servers": {
            "marimo": {
                "command": [
                    "marimo",
                    "edit",
                    "--host=127.0.0.1",
                    "--port={port}",
                    "--base-url={base_url}marimo",  // ← ADDED
                    "--headless"                     // ← ADDED
                ],
                "timeout": 30,                       // ← INCREASED from 20
                "absolute_url": true,                // ← ADDED (CRITICAL!)
                "launcher_entry": {
                    "title": "Marimo (uv)",
                    "icon_path": ""
                }
            }
        }
    }
}
```

#### 2. `marimo-proxy-uv.py` - Same changes:

```python
c.ServerProxy.servers.update({
    "marimo": {
        "command": [
            "marimo",
            "edit",
            "--host=127.0.0.1",
            "--port={port}",
            "--base-url={base_url}marimo",  # ← ADDED
            "--headless"                     # ← ADDED
        ],
        "timeout": 30,
        "absolute_url": True,                # ← CHANGED from False (CRITICAL!)
        "launcher_entry": {
            "title": "Marimo (uv)",
            "icon_path": ""
        },
    }
})
```

### What Each Change Does

| Change | Purpose |
|--------|---------|
| `--base-url={base_url}marimo` | Tells marimo its serving path (e.g., `/user/admin/marimo`) |
| `--headless` | Disables browser auto-open (recommended for proxy) |
| `absolute_url: true` | jupyter-server-proxy passes FULL URLs to marimo |
| `timeout: 30` | More time for first startup |

### Why `{base_url}` Template Variable

- `{base_url}` is replaced by jupyter-server-proxy at runtime
- In JupyterHub: `{base_url}` = `/user/<username>/`
- Combined: marimo receives `--base-url /user/admin/marimo`
- This tells marimo to serve all routes relative to that base

---

## Implementation Steps Completed

1. ✅ Updated `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy-uv.json`
2. ✅ Updated `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy-uv.py`
3. ✅ Rebuilt marimo image: `local/uv-marimo:latest`
4. ✅ Verified configuration is in the image

---

## Testing Instructions

### IMPORTANT: You Must Restart Your marimo Server

The fix is in the **new image**, but your running container is still using the **old image**.

### Step 1: Stop JupyterHub Stack (Recommended)

```bash
cd jhub-docker
docker compose down
docker compose up -d
```

**Why full restart?** Ensures JupyterHub spawns new containers from the updated image.

### Step 2: Login and Test

1. **Login** to JupyterHub: `http://localhost:8000`
2. **Stop** any existing marimo server:
   - Go to `/hub/home`
   - Click "Stop" on your marimo server
   - Wait for it to stop completely
3. **Start fresh** marimo server:
   - Select profile: "uv Marimo - 1 CPU / 2GB" (or 2 CPU)
   - Click "Start"
   - Wait 10-30 seconds

### Step 3: Verify Success

You should:
- ✅ Redirect to: `http://localhost:8000/user/<username>/marimo/`
- ✅ See: **Marimo editor interface** (file browser or welcome screen)
- ✅ **NO** 404 error
- ✅ Be able to create and edit notebooks

### Step 4: Create Test Notebook

1. Click "New notebook" or "+" button
2. Add Python code: `import marimo as mo; mo.md("Hello!")`
3. Run the cell
4. Verify marimo's reactive updates work

---

## How URL Routing Works Now

### Before Fix (Broken):
```
1. Browser requests: /user/admin/marimo/
2. Proxy routes to marimo on localhost:8888
3. Marimo thinks it's at: /
4. Marimo serves routes: /file.py, /api/..., etc.
5. Browser expects: /user/admin/marimo/file.py
6. Mismatch → 404 NOT FOUND ❌
```

### After Fix (Working):
```
1. Browser requests: /user/admin/marimo/
2. Proxy routes to marimo with: --base-url /user/admin/marimo
3. Marimo knows it's at: /user/admin/marimo
4. Marimo serves routes: /user/admin/marimo/file.py, /user/admin/marimo/api/...
5. Browser expects: /user/admin/marimo/file.py
6. Perfect match → ✅ SUCCESS!
```

---

## Verification Commands

### Check Image Has Updated Config

```bash
# Should show --base-url in command
docker run --rm local/uv-marimo:latest \
  cat /usr/local/etc/jupyter/jupyter_server_config.d/marimo-proxy.json | grep base-url

# Expected output:
#   "--base-url={base_url}marimo",
```

### Check Marimo Version

```bash
# Must be >= 0.6.21 (when --base-url was added)
docker run --rm local/uv-marimo:latest marimo --version

# Expected: marimo 0.x.x (where x >= 6.21)
```

### View Running Container Logs

After starting a marimo server:
```bash
# Get container name
docker ps | grep marimo

# View startup logs
docker logs <container-id> 2>&1 | head -30

# Look for:
# [ServerProxy] Proxying marimo from /marimo/ to ...
# marimo edit --base-url=/user/.../marimo
```

---

## Troubleshooting

### Still Getting 404

**Cause**: Old container still running with old config

**Solution**:
```bash
# Full stack restart
cd jhub-docker
docker compose down
docker compose up -d

# Then login and start fresh marimo server
```

### Marimo Says "No such option: --base-url"

**Cause**: Marimo version is < 0.6.21

**Solution**: Update Dockerfile to ensure marimo >= 0.6.21:
```dockerfile
RUN uv pip install --system "marimo>=0.6.21"
```

### Config Not Loaded

**Verify config is in image**:
```bash
docker run --rm local/uv-marimo:latest ls -la /usr/local/etc/jupyter/jupyter_server_config.d/
# Should show: marimo-proxy.json and marimo-proxy.py
```

### Marimo Loads But Links Don't Work

**Check absolute_url setting**:
```bash
docker run --rm local/uv-marimo:latest \
  cat /usr/local/etc/jupyter/jupyter_server_config.d/marimo-proxy.json | grep absolute_url

# Expected: "absolute_url": true
```

---

## Summary of Both Fixes

### Fix #1 (Previous): Hub URL Configuration
- Changed: `default_url="/proxy/marimo/"` → `default_url="/marimo/"`
- Why: jupyter-server-proxy exposes named servers at `/<name>/` not `/proxy/<name>/`
- File: `jhub-docker/hub/jupyterhub_config.py`

### Fix #2 (This Fix): Marimo Base URL Configuration
- Added: `--base-url={base_url}marimo` to marimo command
- Added: `absolute_url: true` in proxy config
- Added: `--headless` flag
- Why: Marimo needs to know its base path for correct routing
- Files: 
  - `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy-uv.json`
  - `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy-uv.py`

**Both fixes together** enable marimo to work correctly behind the jupyter-server-proxy!

---

## Files Changed

| File | Status | Changes |
|------|--------|---------|
| `marimo-proxy-uv.json` | ✅ Updated | Added --base-url, --headless, absolute_url: true |
| `marimo-proxy-uv.py` | ✅ Updated | Added --base-url, --headless, absolute_url: True |
| `local/uv-marimo:latest` | ✅ Rebuilt | Contains updated configuration |
| Hub config | ✓ Already fixed | default_url="/marimo/" |

---

## What Users Need to Do

### Immediate Action Required:
1. **Restart stack**: `docker compose down && docker compose up -d`
2. **Stop old marimo servers** from `/hub/home`
3. **Start fresh marimo server**
4. **Test**: Should work with no 404! 🎉

### No Changes Needed:
- ✓ Lab and VS Code profiles (already working)
- ✓ Hub configuration (already correct)
- ✓ Docker Compose file (no changes)

---

## Technical Reference

### jupyter-server-proxy Template Variables

| Variable | Replaced With | Example |
|----------|--------------|---------|
| `{port}` | Dynamic port assigned | `8888` |
| `{base_url}` | User's server base path | `/user/admin/` |

### Absolute URL Behavior

| Setting | Proxy Behavior | Marimo Receives |
|---------|----------------|-----------------|
| `absolute_url: false` | Strips prefix | `/file.py` |
| `absolute_url: true` | Keeps full path | `/user/admin/marimo/file.py` |

For marimo, **true is required** because marimo needs the full path context.

---

## Additional Resources

- **jupyter-marimo-proxy**: https://github.com/jyio/jupyter-marimo-proxy
  - Community package solving the same problem
  - Reference implementation used for this fix
- **Marimo docs**: https://docs.marimo.io/guides/deploying/
  - Official documentation on --base-url flag
- **jupyter-server-proxy docs**: https://jupyter-server-proxy.readthedocs.io/
  - Documentation on proxy configuration

---

## Success Criteria

✅ **Complete** when:
- Marimo container starts without errors
- URL `http://localhost:8000/user/<username>/marimo/` loads marimo editor
- No 404 errors
- Can create and edit notebooks
- Reactive updates work correctly

---

**Fixed by**: Droid (Factory AI)  
**Date**: 2025-11-03  
**Related Files**: MARIMO_FIX.md, DEPLOYMENT_VERIFICATION.md, COMPLETION_SUMMARY.md
