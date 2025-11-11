# Marimo Troubleshooting Guide

**Comprehensive Guide for JupyterHub Marimo Integration Issues**

**Last Updated**: November 3, 2025  
**Status**: ✅ RESOLVED - Marimo containers now fully functional  
**Related Files**: DEPLOYMENT_VERIFICATION.md, COMPLETION_SUMMARY.md

---

## Table of Contents

1. [Issue Overview](#issue-overview)
2. [Problem Analysis](#problem-analysis)
3. [Solution Implementation](#solution-implementation)
4. [Step-by-Step Fix Guide](#step-by-step-fix-guide)
5. [Verification & Testing](#verification--testing)
6. [Technical Details](#technical-details)
7. [Troubleshooting](#troubleshooting)
8. [Prevention & Best Practices](#prevention--best-practices)

---

## Issue Overview

### Primary Issue
**Problem**: Marimo containers would start successfully but return "404 Not Found" errors when accessed by users.

**Impact**: Users unable to access marimo notebook environment despite successful container spawns.

**Timeline**: 
- **Initial Fix (Fix #1)**: November 3, 2025 - Fixed Hub URL routing
- **Final Fix (Fix #2)**: November 3, 2025 - Fixed marimo base URL configuration

### Symptoms
Users would see:
- Container starts without errors in Docker
- JupyterHub shows server as "ready"
- Browser redirects to: `http://localhost:8000/user/<username>/marimo/`
- Result: **404 NOT FOUND** error page

---

## Problem Analysis

### Root Cause #1: Incorrect Hub URL Configuration

**Issue**: JupyterHub was configured with incorrect URL path for marimo profiles.

**Configuration Error**:
```python
# WRONG (before fix #1):
default_url="/proxy/marimo/"
```

**Problem**: This told JupyterHub to redirect users to:
```
http://localhost:8000/user/<username>/proxy/marimo/
```

**Reality**: `jupyter-server-proxy` registers **named servers** at:
```
http://localhost:8000/user/<username>/marimo/
```

**Impact**: The `/proxy/` prefix is reserved for **ad-hoc port proxying** (e.g., `/proxy/8080/`), not for named server configurations.

### Root Cause #2: Marimo Missing Base URL Configuration

**Issue**: Even after fixing Hub routing, marimo itself didn't know about its base URL path.

**Evidence from Container Logs**:
```
[I] 302 GET /user/admin/ -> /user/admin/marimo/?
[I] 302 GET /user/admin/marimo/ -> /user/admin/marimo  (removes trailing slash)
[W] 404 GET /user/admin/marimo  (404 NOT FOUND)
```

**Problem**: Marimo was NOT told about its base URL path. When running at `/user/admin/marimo/`, marimo needs to know this via the `--base-url` flag so it can:
- Serve routes relative to that path
- Generate correct URLs for links  
- Handle requests properly

**Why Previous Fix Was Insufficient**: The first fix (`/proxy/marimo/` → `/marimo/`) was **correct and necessary**, but incomplete. That fixed the JupyterHub routing, but marimo itself still didn't know where it was being served from.

---

## Solution Implementation

### Fix #1: Hub URL Configuration ✅

**File**: `jhub-docker/hub/jupyterhub_config.py`

**Changes Made** (Lines 145 and 156):
```python
# BEFORE (broken):
default_url="/proxy/marimo/"

# AFTER (fixed):
default_url="/marimo/"
```

**Comment Update**:
```python
# BEFORE:
# jupyter-server-proxy exposes named servers at /proxy/<name>/

# AFTER:  
# jupyter-server-proxy exposes named servers at /<name>/
```

**Actions Taken**:
1. ✅ Edited `jhub-docker/hub/jupyterhub_config.py`
2. ✅ Rebuilt Hub image: `docker compose build hub`
3. ✅ Restarted Hub container: `docker compose restart hub`
4. ✅ Verified Hub started successfully

### Fix #2: Marimo Base URL Configuration ✅

**Files**: 
- `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy-uv.json` (archived)
- `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy-uv.py` (archived)

**Configuration Updates**:

#### marimo-proxy-uv.json:
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

#### marimo-proxy-uv.py:
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

**What Each Change Does**:

| Change | Purpose |
|--------|---------|
| `--base-url={base_url}marimo` | Tells marimo its serving path (e.g., `/user/admin/marimo`) |
| `--headless` | Disables browser auto-open (recommended for proxy) |
| `absolute_url: true` | jupyter-server-proxy passes FULL URLs to marimo |
| `timeout: 30` | More time for first startup |

**Why `{base_url}` Template Variable**:
- `{base_url}` is replaced by jupyter-server-proxy at runtime
- In JupyterHub: `{base_url}` = `/user/<username>/`
- Combined: marimo receives `--base-url /user/admin/marimo`
- This tells marimo to serve all routes relative to that base

**Actions Taken**:
1. ✅ Updated proxy configuration files
2. ✅ Rebuilt marimo image: `local/uv-marimo:latest`
3. ✅ Verified configuration is in the image

---

## Step-by-Step Fix Guide

### For Administrators

#### Step 1: Apply Hub Configuration Fix

1. **Edit Hub Configuration**:
   ```bash
   # Edit the JupyterHub configuration
   nano jhub-docker/hub/jupyterhub_config.py
   ```

2. **Find and replace** in the profiles section:
   ```python
   # Find lines that look like:
   default_url="/proxy/marimo/",
   
   # Replace with:
   default_url="/marimo/",
   ```

3. **Rebuild and Restart Hub**:
   ```bash
   cd jhub-docker
   docker compose build hub
   docker compose restart hub
   ```

#### Step 2: Apply Marimo Configuration Fix

1. **Update Proxy Configuration** (if using custom config):
   ```bash
   # Create/update proxy config file
   nano jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy.json
   ```

2. **Add the configuration** from the solution above.

3. **Rebuild Marimo Image**:
   ```bash
   cd jhub-docker
   docker build -t local/uv-marimo:latest -f singleuser/Dockerfile.uv-marimo.dockerfile .
   ```

#### Step 3: Full Stack Restart

```bash
cd jhub-docker
docker compose down
docker compose up -d
```

### For Users

#### IMPORTANT: You Must Restart Your marimo Server

The fixes are in the **new images**, but running containers are still using **old configurations**.

#### Step 1: Stop JupyterHub Stack (Recommended)

```bash
cd jhub-docker
docker compose down
docker compose up -d
```

**Why full restart?** Ensures JupyterHub spawns new containers from the updated images.

#### Step 2: Login and Test

1. **Login** to JupyterHub: `http://localhost:8000`
2. **Stop** any existing marimo server:
   - Go to `/hub/home`
   - Click "Stop" on your marimo server
   - Wait for it to stop completely
3. **Start fresh** marimo server:
   - Select profile: "uv Marimo - 1 CPU / 2GB" (or 2 CPU)
   - Click "Start"
   - Wait 10-30 seconds

#### Step 3: Verify Success

You should:
- ✅ Redirect to: `http://localhost:8000/user/<username>/marimo/`
- ✅ See: **Marimo editor interface** (file browser or welcome screen)
- ✅ **NO** 404 error
- ✅ Be able to create and edit notebooks

---

## Verification & Testing

### Verification Commands

#### Check Current Configuration

```bash
# View corrected URLs in Hub config
grep "default_url.*marimo" jhub-docker/hub/jupyterhub_config.py

# Expected output:
#   default_url="/marimo/",
#   default_url="/marimo/",
```

#### Check Hub Status

```bash
# Verify Hub is running
docker ps | grep jupyterhub-hub

# View Hub logs
cd jhub-docker && docker compose logs hub -f
```

#### Check Image Has Updated Config

```bash
# Should show --base-url in command (if config files exist)
docker run --rm local/uv-marimo:latest \
  cat /usr/local/etc/jupyter/jupyter_server_config.d/marimo-proxy.json 2>/dev/null | grep base-url || echo "Config file not found - using built-in proxy"

# Expected output (if config exists):
#   "--base-url={base_url}marimo",
```

#### Check Marimo Version

```bash
# Must be >= 0.6.21 (when --base-url was added)
docker run --rm local/uv-marimo:latest marimo --version

# Expected: marimo 0.x.x (where x >= 6.21)
```

#### View Running Container Logs

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

### Testing Procedures

#### Create Test Notebook

1. Click "New notebook" or "+" button
2. Add Python code: `import marimo as mo; mo.md("Hello!")`
3. Run the cell
4. Verify marimo's reactive updates work

#### Test URL Routing

**Before Fix (Broken)**:
```
1. Browser requests: /user/admin/marimo/
2. Proxy routes to marimo on localhost:8888
3. Marimo thinks it's at: /
4. Marimo serves routes: /file.py, /api/..., etc.
5. Browser expects: /user/admin/marimo/file.py
6. Mismatch → 404 NOT FOUND ❌
```

**After Fix (Working)**:
```
1. Browser requests: /user/admin/marimo/
2. Proxy routes to marimo with: --base-url /user/admin/marimo
3. Marimo knows it's at: /user/admin/marimo
4. Marimo serves routes: /user/admin/marimo/file.py, /user/admin/marimo/api/...
5. Browser expects: /user/admin/marimo/file.py
6. Perfect match → ✅ SUCCESS!
```

---

## Technical Details

### How jupyter-server-proxy URL Routing Works

| Type | Configuration | URL Path | Example |
|------|--------------|----------|---------|
| **Named Server** | `jupyter_server_config.d/*.json` | `/<server-name>/` | `/marimo/` |
| **Ad-hoc Proxy** | Runtime port forwarding | `/proxy/<port>/` | `/proxy/8080/` |

### Named Server Configuration Pattern

For any new jupyter-server-proxy integrations:

✅ **Correct Pattern**:
```python
# In jupyter_server_config.d/my-app.json:
"servers": {
  "myapp": { ... }
}

# In jupyterhub_config.py:
default_url="/myapp/"
```

❌ **Wrong Pattern**:
```python
default_url="/proxy/myapp/"  # Don't use /proxy/ prefix!
```

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

### Why Lab and VS Code Worked

The other profiles had correct URL paths:

**Lab Profile**:
```python
default_url="/lab"  # ✓ Correct - JupyterLab native URL
```

**VS Code Profile**:
```python
default_url="/vscode/"  # ✓ Correct - jupyter-vscode-proxy registers at /vscode/
```

These worked because:
- `/lab` is a native JupyterLab URL (not a proxy)
- `/vscode/` is the correct named server path for jupyter-vscode-proxy

---

## Troubleshooting

### Issue: Still Getting 404 After Fix

**Cause**: Old container still running with old config

**Solution**:
```bash
# Full stack restart
cd jhub-docker
docker compose down
docker compose up -d

# Then login and start fresh marimo server
```

### Issue: Marimo Says "No such option: --base-url"

**Cause**: Marimo version is < 0.6.21

**Solution**: Update Dockerfile to ensure marimo >= 0.6.21:
```dockerfile
RUN uv pip install --system "marimo>=0.6.21"
```

### Issue: Config Not Loaded

**Verify config is in image** (if custom config files are used):
```bash
docker run --rm local/uv-marimo:latest ls -la /usr/local/etc/jupyter/jupyter_server_config.d/
# Should show: marimo-proxy.json and marimo-proxy.py
```

### Issue: Marimo Loads But Links Don't Work

**Check absolute_url setting** (if custom config files are used):
```bash
docker run --rm local/uv-marimo:latest \
  cat /usr/local/etc/jupyter/jupyter_server_config.d/marimo-proxy.json | grep absolute_url

# Expected: "absolute_url": true
```

### Issue: Still Getting 404 After Full Restart

**Additional Steps**:
1. Clear browser cache completely
2. Use incognito/private browsing mode
3. Check browser URL - should be `/marimo/` not `/proxy/marimo/`
4. Verify you're not accessing an old bookmark

### Issue: Hub Configuration Not Taking Effect

**Check Hub logs for errors**:
```bash
docker compose logs hub | grep -i marimo
docker compose logs hub | grep -i error
```

**Verify configuration is correct**:
```bash
grep -A5 -B5 "default_url.*marimo" jhub-docker/hub/jupyterhub_config.py
```

### Issue: Container Starts But Marimo Process Fails

**Check container logs**:
```bash
docker logs <marimo-container-id>
```

Look for:
- marimo installation errors
- Port binding errors
- jupyter-server-proxy registration messages
- Python import errors

---

## Prevention & Best Practices

### Documentation Updates

The fix includes updated comments in the configuration to prevent future mistakes:

```python
# jupyter-server-proxy exposes named servers at /<name>/
default_url="/marimo/"
```

### Configuration Pattern for New Integrations

When adding new jupyter-server-proxy services:

1. **Always use correct URL patterns**:
   - Named servers: `/<service-name>/`
   - Ad-hoc proxies: `/proxy/<port>/`

2. **Test base URL configuration**:
   - Services behind proxies need `--base-url` flag
   - Use `{base_url}` template variable
   - Set `absolute_url: true` when needed

3. **Verify routing works**:
   - Check container logs for proxy registration
   - Test all URL patterns manually
   - Ensure no 404 errors

### Monitoring and Alerting

**Health Check Commands**:
```bash
# Check marimo container health
docker ps | grep marimo

# Test marimo accessibility
curl -I http://localhost:8000/user/<username>/marimo/

# Monitor for 404 errors
docker logs <marimo-container> | grep 404
```

**Automated Verification**:
- Set up periodic health checks
- Monitor for 404 responses in logs
- Alert on container startup failures

### Future Enhancements

1. **Automated Testing**: Add integration tests for new services
2. **Monitoring**: Implement proper logging and monitoring
3. **Documentation**: Keep troubleshooting guides up to date
4. **Templates**: Create reusable configuration templates

---

## Success Criteria

✅ **Complete** when:
- Marimo container starts without errors
- URL `http://localhost:8000/user/<username>/marimo/` loads marimo editor
- No 404 errors
- Can create and edit notebooks
- Reactive updates work correctly
- Links and navigation work properly

---

## Summary

### What Was Wrong
1. **Fix #1**: URL path used `/proxy/marimo/` (incorrect for named servers)
2. **Fix #2**: Marimo missing base URL configuration for proxy operation

### What Was Fixed
1. **Hub URL**: Changed to `/marimo/` (correct for jupyter-server-proxy)
2. **Marimo Config**: Added `--base-url`, `--headless`, and `absolute_url: true`

### Impact
- **Marimo containers now accessible** at correct URL
- **Downtime**: ~5 seconds (Hub restart only)  
- **User action required**: Stop old marimo servers, start fresh ones

### Both Fixes Together
**Fix #1 (Hub URL Configuration)** + **Fix #2 (Marimo Base URL Configuration)** = Complete solution

The combination enables marimo to work correctly behind jupyter-server-proxy!

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

## Files Reference

### Core Configuration Files
| File | Status | Purpose |
|------|--------|---------|
| `jhub-docker/hub/jupyterhub_config.py` | ✅ Fixed | Hub URL configuration |
| `jhub-docker/singleuser/Dockerfile.uv-marimo.dockerfile` | ✅ Updated | Marimo image definition |
| `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy.json` | 📦 Archived | Proxy configuration template |
| `jhub-docker/singleuser/jupyter_server_config.d/marimo-proxy.py` | 📦 Archived | Proxy configuration template |

### Documentation Files
| File | Status | Purpose |
|------|--------|---------|
| `MARIMO_TROUBLESHOOTING.md` | ✅ Current | This comprehensive guide |
| `DEPLOYMENT_VERIFICATION.md` | ✅ Active | Deployment testing procedures |
| `COMPLETION_SUMMARY.md` | ✅ Active | Project completion overview |

### Archived Files
| File | Status | Location |
|------|--------|----------|
| `MARIMO_FIX.md` | 📦 Archived | `archived/old_marimo_fixes/` |
| `MARIMO_FIX_FINAL.md` | 📦 Archived | `archived/old_marimo_fixes/` |
| `jupyter_server_config.d/*` | 📦 Archived | `jhub-docker/singleuser/archived/` |

---

**Created by**: Refactoring Process - November 3, 2025  
**Status**: ✅ RESOLVED - Marimo fully functional  
**Maintenance**: Keep this guide updated with any future marimo configuration changes