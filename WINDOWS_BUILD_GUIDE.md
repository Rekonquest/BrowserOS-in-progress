# NexusOS Windows Build Guide

Complete guide for building NexusOS browser for Windows with `.exe` installer and portable `.zip` packages.

---

## 🎯 Quick Start (Windows Users)

### Prerequisites

1. **Windows 10/11** (64-bit)
2. **Python 3.12+** ([Download](https://www.python.org/downloads/))
3. **Git for Windows** ([Download](https://git-scm.com/download/win))
4. **Internet connection** (for downloading Chromium)

### Build NexusOS in 3 Commands

```powershell
# 1. Clone repository
git clone https://github.com/Rekonquest/BrowserOS-in-progress.git
cd BrowserOS-in-progress\packages\browseros

# 2. Install dependencies
pip install uv
uv sync

# 3. Build NexusOS (downloads Chromium automatically)
$env:CHROMIUM_BINARY_SOURCE="official"
uv run python -m build.browseros build --modules chromium_download,resources,package_windows

# 4. Find your installer
dir releases\*\*.exe
```

**Build time:** 10-15 minutes
**Output:**
- `NexusOS_vX.X.X_x64.exe` - Windows installer
- `NexusOS_vX.X.X_x64.zip` - Portable version

---

## 📦 What Gets Created

### 1. Windows Installer (.exe)

**File:** `NexusOS_v0.37.0_x64.exe`

Features:
- ✅ Single-click installation
- ✅ Desktop shortcut creation
- ✅ Start menu integration
- ✅ Automatic uninstaller
- ✅ Code-signed (if certificates configured)

Based on Chromium's `mini_installer.exe` - the same installer used by Chrome, Edge, Brave.

### 2. Portable ZIP (.zip)

**File:** `NexusOS_v0.37.0_x64.zip`

Features:
- ✅ No installation required
- ✅ Run from USB drive
- ✅ No registry changes
- ✅ Self-contained with all dependencies

Perfect for:
- Testing without installation
- Portable use on multiple PCs
- Corporate environments with restricted permissions

---

## 🔧 Detailed Build Instructions

### Step 1: Set Up Environment

```powershell
# Open PowerShell as Administrator (not required but recommended)

# Navigate to project
cd BrowserOS-in-progress\packages\browseros

# Create virtual environment (optional)
python -m venv env
.\env\Scripts\Activate.ps1

# Install dependencies
pip install uv
uv sync
```

### Step 2: Configure Build

```powershell
# Set Chromium download source
$env:CHROMIUM_BINARY_SOURCE="official"  # Downloads from Google

# OR use local Chromium archive
$env:CHROMIUM_BINARY_SOURCE="local"
$env:CHROMIUM_BINARY_PATH="C:\Downloads\chromium-win-x64.zip"

# OR use R2 storage
$env:CHROMIUM_BINARY_SOURCE="r2"
$env:R2_ACCOUNT_ID="your_account_id"
$env:R2_ACCESS_KEY_ID="your_access_key"
$env:R2_SECRET_ACCESS_KEY="your_secret_key"

# Set architecture (default is x64)
$env:ARCH="x64"  # or "arm64" for Windows ARM
```

### Step 3: Build NexusOS

```powershell
# Full build (download + package)
uv run python -m build.browseros build `
  --modules chromium_download,resources,package_windows

# Just package (if Chromium already downloaded)
uv run python -m build.browseros build `
  --modules resources,package_windows

# With code signing (requires certificates)
$env:ESIGNER_USERNAME="your_email@example.com"
$env:ESIGNER_PASSWORD="your_password"
$env:ESIGNER_TOTP_SECRET="your_2fa_secret"

uv run python -m build.browseros build `
  --modules chromium_download,resources,sign_windows,package_windows
```

### Step 4: Find Your Packages

```powershell
# List all built packages
dir releases\*\*.exe
dir releases\*\*.zip

# Example output:
# releases\0.37.0\NexusOS_v0.37.0_x64.exe   (150 MB)
# releases\0.37.0\NexusOS_v0.37.0_x64.zip   (180 MB)
```

---

## 🏗️ Build System Architecture

### Windows Packaging Module

**Location:** `build/modules/package/windows.py`

What it does:
1. **Locates compiled Chromium** in `chromium_bin/out/Default_x64/`
2. **Builds mini_installer.exe** using Chromium's installer framework
3. **Creates portable ZIP** with all necessary files
4. **Applies branding** (NexusOS icons, strings, settings)
5. **Code signs** (if certificates configured)

### Build Pipeline

```
┌─────────────────┐
│ chromium_       │  Downloads Chromium from:
│ download        │  - Google snapshots
│                 │  - Or your R2 storage
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ resources       │  Applies NexusOS branding:
│                 │  - Icons and logos
│                 │  - String replacements
│                 │  - Default settings
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ sign_windows    │  Code signs (optional):
│ (optional)      │  - chrome.exe
│                 │  - mini_installer.exe
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ package_        │  Creates packages:
│ windows         │  - .exe installer
│                 │  - .zip portable
└────────┬────────┘
         │
         ▼
     Installers ready!
```

---

## 💾 Manual Chromium Download (Alternative)

If automatic download fails, manually download Chromium:

### Option 1: Download from Google

1. Visit: https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html
2. Navigate to: `Win_x64` → `LATEST`
3. Download: `chrome-win.zip`
4. Extract to: `chromium_bin\`

```powershell
# Then build
$env:CHROMIUM_SRC="$(pwd)\chromium_bin"
uv run python -m build.browseros build --modules package_windows
```

### Option 2: Download Specific Version

```powershell
# Find build number for your version at:
# https://chromiumdash.appspot.com/releases

# Download specific build
$BuildNumber = "1400000"  # Example
$Url = "https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/$BuildNumber/chrome-win.zip"

# Download and extract
Invoke-WebRequest -Uri $Url -OutFile chrome-win.zip
Expand-Archive chrome-win.zip -DestinationPath chromium_bin
```

---

## 🔐 Code Signing (Optional)

For distributing to end users, code signing is recommended.

### Using SSL.com CodeSignTool

```powershell
# 1. Install CodeSignTool
# Download from: https://www.ssl.com/how-to/esigner-codesigntool-command-guide/

# 2. Set environment variables
$env:CODE_SIGN_TOOL_PATH="C:\CodeSignTool"
$env:ESIGNER_USERNAME="your_email@ssl.com"
$env:ESIGNER_PASSWORD="your_password"
$env:ESIGNER_TOTP_SECRET="your_2fa_secret"
$env:ESIGNER_CREDENTIAL_ID="your_credential_id"  # Optional

# 3. Build with signing
uv run python -m build.browseros build `
  --modules chromium_download,sign_windows,package_windows
```

### What Gets Signed

- `chrome.exe` - Main browser executable
- `browseros_server.exe` - NexusOS server component
- `mini_installer.exe` - Final installer
- Other executables in the package

### Verification

```powershell
# Verify signature
Get-AuthenticodeSignature "releases\0.37.0\NexusOS_v0.37.0_x64.exe"

# Should show:
# SignerCertificate      : [your certificate details]
# Status                 : Valid
```

---

## 🧪 Testing Your Build

### Test the Installer

```powershell
# Run installer (elevated permissions required)
.\releases\0.37.0\NexusOS_v0.37.0_x64.exe

# Installer will:
# 1. Extract files to %LOCALAPPDATA%\NexusOS\
# 2. Create desktop shortcut
# 3. Add to Start menu
# 4. Register uninstaller
```

### Test the Portable ZIP

```powershell
# Extract ZIP
Expand-Archive releases\0.37.0\NexusOS_v0.37.0_x64.zip -DestinationPath NexusOS

# Run directly (no installation)
.\NexusOS\chrome.exe
```

### Verify Installation

```powershell
# Check installed location
dir "$env:LOCALAPPDATA\NexusOS\Application"

# Check Start Menu
dir "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\NexusOS"

# Check uninstaller
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\NexusOS"
```

---

## 🚀 CI/CD Build (GitHub Actions)

### Automated Windows Build

```yaml
# .github/workflows/build-windows.yml
name: Build NexusOS for Windows

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          cd packages/browseros
          uv sync

      - name: Build NexusOS
        env:
          CHROMIUM_BINARY_SOURCE: official
        run: |
          cd packages/browseros
          uv run python -m build.browseros build `
            --modules chromium_download,resources,package_windows

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: nexusos-windows
          path: |
            packages/browseros/releases/**/*.exe
            packages/browseros/releases/**/*.zip
```

---

## 📊 Build Output Examples

### Successful Build Output

```
🚀 BrowserOS Build System
======================================================================
Platform: Windows
Architecture: x64
Pipeline: chromium_download → resources → package_windows
======================================================================

🔧 Running module: chromium_download
======================================================================
Chromium Binary Download
Fetching latest build number...
✅ Latest build number: 1400523
Download URL: https://...Win_x64/1400523/chrome-win.zip
Downloading Chromium... (this may take a few minutes)
  Downloaded: 10MB / 180MB (5.6%)
  Downloaded: 20MB / 180MB (11.1%)
  ...
  Downloaded: 180MB / 180MB (100.0%)
✅ Download complete: chrome-win.zip
✅ Chromium binary validation passed

🔧 Running module: resources
======================================================================
Applying NexusOS branding...
✅ Copied icons
✅ Applied string replacements
✅ Updated default settings

🔧 Running module: package_windows
======================================================================
📦 Packaging NexusOS for Windows (x64)
Building mini_installer.exe...
✅ Created: NexusOS_v0.37.0_x64.exe (150 MB)
Creating portable ZIP...
✅ Created: NexusOS_v0.37.0_x64.zip (180 MB)

======================================================================
✅ Pipeline completed successfully in 12m 34s
======================================================================

📦 Packages created:
  releases\0.37.0\NexusOS_v0.37.0_x64.exe
  releases\0.37.0\NexusOS_v0.37.0_x64.zip
```

---

## 🐛 Troubleshooting

### "mini_installer.exe not found"

**Problem:** Chromium wasn't compiled with installer target.

**Solution:**
```powershell
# Ensure you have the complete Chromium download
$env:CHROMIUM_BINARY_SOURCE="official"
uv run python -m build.browseros build --modules chromium_download
```

### "CodeSignTool not found"

**Problem:** Code signing tool not installed or not in PATH.

**Solution:**
```powershell
# Skip signing for testing
uv run python -m build.browseros build `
  --modules chromium_download,resources,package_windows

# Or install CodeSignTool from SSL.com
```

### "Access denied" during build

**Problem:** Antivirus blocking build tools or files in use.

**Solution:**
```powershell
# 1. Close NexusOS if running
Get-Process | Where-Object {$_.ProcessName -like "*nexusos*"} | Stop-Process

# 2. Add build directory to antivirus exclusions
# 3. Run PowerShell as Administrator
```

### Download fails with network error

**Problem:** Proxy, firewall, or network restrictions.

**Solution:**
```powershell
# Use manual download
# Download from: https://download-chromium.appspot.com/
# Extract to chromium_bin\

# Then build without download step
uv run python -m build.browseros build --modules package_windows
```

---

## 📦 Distribution

### Share Your Build

#### Upload to GitHub Releases

```powershell
# Using GitHub CLI
gh release create v0.37.0 `
  releases\0.37.0\NexusOS_v0.37.0_x64.exe `
  releases\0.37.0\NexusOS_v0.37.0_x64.zip `
  --title "NexusOS v0.37.0" `
  --notes "Windows release of NexusOS browser"
```

#### Host on Website

Upload to your web server or CDN:
```
https://yoursite.com/downloads/
  ├── NexusOS_v0.37.0_x64.exe      (Windows installer)
  ├── NexusOS_v0.37.0_x64.zip      (Windows portable)
  └── checksums.txt                (SHA256 hashes)
```

#### Create Checksums

```powershell
# Generate SHA256 checksums
Get-FileHash releases\0.37.0\*.exe, releases\0.37.0\*.zip | `
  Select-Object Hash, Path | `
  Out-File -FilePath checksums.txt
```

---

## 🎯 Next Steps

1. **Test your build:**
   - Install the .exe on a clean Windows machine
   - Run the portable version from USB
   - Verify all features work

2. **Customize branding:**
   - Update icons in `resources/icons/`
   - Modify strings in `build/modules/resources/string_replaces.py`
   - Change default settings

3. **Set up auto-updates:**
   - Configure update server
   - See: `build/modules/updates/` for update system

4. **Create installer customizations:**
   - Modify installer UI
   - Add custom installation options
   - See: `build/config/installer.yaml`

---

## 📚 Additional Resources

- **Chromium Downloads:** https://download-chromium.appspot.com/
- **Build System Docs:** [BINARY_DOWNLOAD_GUIDE.md](packages/browseros/BINARY_DOWNLOAD_GUIDE.md)
- **Code Signing Guide:** https://www.ssl.com/guide/esigner-codesigntool/
- **Windows Installer Docs:** https://www.chromium.org/developers/design-documents/installer/

---

## ✅ Quick Reference

| Command | Description |
|---------|-------------|
| `uv run python -m build.browseros build --list` | List all build modules |
| `uv run python -m build.browseros build --modules chromium_download,package_windows` | Build Windows packages |
| `$env:CHROMIUM_BINARY_SOURCE="official"` | Use official Chromium |
| `$env:CHROMIUM_BINARY_SOURCE="local"` | Use local Chromium |
| `Get-FileHash *.exe` | Verify file integrity |
| `.\NexusOS_v0.37.0_x64.exe` | Install NexusOS |

---

**Status:** ✅ Ready to build on Windows
**Build Time:** 10-15 minutes
**Output:** .exe installer + .zip portable
**Size:** ~150-180 MB
