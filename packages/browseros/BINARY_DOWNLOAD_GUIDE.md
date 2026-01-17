# NexusOS Binary Download Build System

**Following Brave/Vivaldi's Approach: Download Pre-Built Chromium Instead of Compiling**

This guide explains how to use NexusOS's binary download approach, which **eliminates the need** for:
- ❌ 100+ GB Chromium source code
- ❌ 4-8 hour compilation time
- ❌ Complex build toolchains (depot_tools, GN, Ninja)

Instead, you:
- ✅ Download pre-built Chromium binaries (~500 MB)
- ✅ Apply NexusOS branding and customizations
- ✅ Package and distribute in minutes

---

## Quick Start

### Option 1: Use Your Own R2-Hosted Binaries (Recommended)

This is the most flexible approach - you control the Chromium versions and can ensure they match your needs exactly.

```bash
# 1. Set R2 credentials (one-time setup)
export R2_ACCOUNT_ID="your_account_id"
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"
export R2_BUCKET_NAME="nexusos-binaries"

# 2. Upload pre-built Chromium to R2 (see "Preparing Chromium Binaries" below)
# binaries/chromium/chromium-137.0.7151.69-linux-x64.tar.xz

# 3. Build NexusOS using downloaded Chromium
export CHROMIUM_BINARY_SOURCE=r2
cd packages/browseros
uv run python -m build.browseros build \
  --modules chromium_download,resources,package_linux

# 4. Find your package
# dist/NexusOS_v0.36.3_x64.AppImage
```

**Build time:** 5-10 minutes vs 4-8 hours!

### Option 2: Use Local Chromium Binary (Testing)

For quick testing with a Chromium binary you already have:

```bash
# Point to local Chromium archive
export CHROMIUM_BINARY_SOURCE=local
export CHROMIUM_BINARY_PATH=/path/to/chromium-linux-x64.tar.xz

# Build
uv run python -m build.browseros build \
  --modules chromium_download,resources,package_linux
```

### Option 3: Official Chromium Snapshots (Experimental)

Download from Google's official Chromium snapshot repository:

```bash
export CHROMIUM_BINARY_SOURCE=official

# Build
uv run python -m build.browseros build \
  --modules chromium_download,resources,package_linux
```

**Note:** This requires mapping Chromium versions to build numbers. See "Version Mapping" section.

---

## How It Works

### Traditional Build (git_setup + compile):
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Clone 100GB │ ──▶ │ Compile      │ ──▶ │ Package     │
│ Chromium    │     │ 4-8 hours    │     │ NexusOS     │
└─────────────┘     └──────────────┘     └─────────────┘
```

### New Binary Download (chromium_download):
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Download    │ ──▶ │ Apply        │ ──▶ │ Package     │
│ 500MB       │     │ Branding     │     │ NexusOS     │
│ 5 minutes   │     │ 2 minutes    │     │ 3 minutes   │
└─────────────┘     └──────────────┘     └─────────────┘
```

### What Gets Applied to Downloaded Binary:

Even though you're using a pre-built Chromium binary, the build system still applies all NexusOS customizations:

1. **Branding Resources** (resources module)
   - Icons and logos
   - About pages
   - Default settings

2. **String Replacements** (string_replaces module)
   - "Chromium" → "NexusOS"
   - Copyright notices
   - Localization strings

3. **File Replacements** (chromium_replace module)
   - Custom UI components
   - Modified configuration files

4. **Extensions** (bundled_extensions module)
   - NexusOS AI agent
   - Custom developer tools

5. **Signing** (sign_* modules)
   - Code signing certificates
   - Platform-specific signing

6. **Packaging** (package_* modules)
   - Windows .exe installer
   - Linux AppImage + .deb
   - macOS .dmg

---

## Preparing Chromium Binaries

### Where to Get Pre-Built Chromium

**Option A: Download from Google's Official Snapshots**

Google provides pre-built Chromium binaries for all platforms:

```bash
# Find the latest build number for your version
# Visit: https://chromiumdash.appspot.com/releases

# Download for Linux x64
wget https://commondatastorage.googleapis.com/chromium-browser-snapshots/Linux_x64/1384803/chrome-linux.zip

# Download for macOS ARM64
wget https://commondatastorage.googleapis.com/chromium-browser-snapshots/Mac_Arm/1384803/chrome-mac.zip

# Download for Windows x64
wget https://commondatastorage.googleapis.com/chromium-browser-snapshots/Win_x64/1384803/chrome-win.zip
```

**Option B: Build Your Own (One-Time)**

If you need specific patches or modifications:

```bash
# 1. Clone Chromium (one-time, keep for future builds)
git clone --depth 1 https://chromium.googlesource.com/chromium/src chromium_src

# 2. Build once (takes 4-8 hours)
cd chromium_src
gn gen out/Default --args='is_component_build=false is_official_build=true'
autoninja -C out/Default chrome

# 3. Archive the build
tar -cJf chromium-137.0.7151.69-linux-x64.tar.xz -C out/Default .

# 4. Upload to R2 (now you can delete the 100GB source!)
```

### Uploading to R2

```bash
# Install AWS CLI (works with R2)
pip install awscli

# Configure for R2
aws configure set aws_access_key_id $R2_ACCESS_KEY_ID
aws configure set aws_secret_access_key $R2_SECRET_ACCESS_KEY

# Upload Chromium binary
aws s3 cp \
  chromium-137.0.7151.69-linux-x64.tar.xz \
  s3://nexusos-binaries/binaries/chromium/ \
  --endpoint-url https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com

# Verify upload
aws s3 ls s3://nexusos-binaries/binaries/chromium/ \
  --endpoint-url https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com
```

### R2 Directory Structure

```
nexusos-binaries/
├── binaries/
│   ├── chromium/
│   │   ├── chromium-137.0.7151.69-linux-x64.tar.xz
│   │   ├── chromium-137.0.7151.69-linux-arm64.tar.xz
│   │   ├── chromium-137.0.7151.69-macos-x64.tar.xz
│   │   ├── chromium-137.0.7151.69-macos-arm64.tar.xz
│   │   ├── chromium-137.0.7151.69-windows-x64.zip
│   │   └── checksums.txt
│   └── browseros-server/
│       └── ... (existing server binaries)
```

---

## Build Pipeline Comparison

### Old Pipeline (Source-Based)

```bash
browseros build \
  --modules git_setup,compile,resources,sign_linux,package_linux
```

Modules executed:
1. `git_setup` - Checkout Chromium source (requires 100GB already cloned)
2. `compile` - Compile from source (4-8 hours)
3. `resources` - Apply branding
4. `sign_linux` - Sign binaries
5. `package_linux` - Create AppImage + .deb

**Total time:** 4-8 hours
**Disk space:** 100+ GB

### New Pipeline (Binary-Based)

```bash
export CHROMIUM_BINARY_SOURCE=r2

browseros build \
  --modules chromium_download,resources,sign_linux,package_linux
```

Modules executed:
1. `chromium_download` - Download pre-built binary (5 minutes)
2. `resources` - Apply branding (2 minutes)
3. `sign_linux` - Sign binaries (1 minute)
4. `package_linux` - Create AppImage + .deb (2 minutes)

**Total time:** 10 minutes
**Disk space:** 2-3 GB

---

## Configuration

### Environment Variables

```bash
# Required for R2 downloads
export R2_ACCOUNT_ID="your_account_id"
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"
export R2_BUCKET_NAME="nexusos-binaries"

# Binary download source
export CHROMIUM_BINARY_SOURCE="r2"  # Options: r2, official, ungoogled, local

# For local testing
export CHROMIUM_BINARY_PATH="/path/to/chromium.tar.xz"

# Chromium version
export CHROMIUM_VERSION="137.0.7151.69"

# Chromium destination
export CHROMIUM_SRC="$(pwd)/chromium_bin"  # Much smaller than source!
```

### YAML Configuration

You can also create a config file for binary-based builds:

```yaml
# build/config/release.binary.linux.yaml
chromium_src: "chromium_bin"  # Different from source builds
chromium_version: "137.0.7151.69"
build_type: "release"

required_envs:
  - R2_ACCOUNT_ID
  - R2_ACCESS_KEY_ID
  - R2_SECRET_ACCESS_KEY
  - CHROMIUM_BINARY_SOURCE

modules:
  - chromium_download  # Instead of git_setup
  - resources
  - bundled_extensions
  - chromium_replace
  - string_replaces
  # - compile  # SKIP compilation!
  - sign_linux
  - package_linux
  - upload
```

Usage:
```bash
browseros build --config release.binary.linux.yaml
```

---

## Version Mapping (Official Snapshots)

When using `CHROMIUM_BINARY_SOURCE=official`, you need to map Chromium versions to build numbers.

### How to Find Build Numbers

1. Visit [Chromium Dash](https://chromiumdash.appspot.com/releases)
2. Search for your version (e.g., "137.0.7151.69")
3. Note the build number (e.g., "1384803")

### Automated Mapping (TODO)

The build system could maintain a version mapping file:

```json
// build/config/chromium_versions.json
{
  "137.0.7151.69": {
    "linux-x64": "1384803",
    "linux-arm64": "1384810",
    "macos-x64": "1384803",
    "macos-arm64": "1384810",
    "windows-x64": "1384803"
  }
}
```

This would enable automatic lookups without manual version checking.

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build NexusOS (Binary Download)

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
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
          R2_ACCOUNT_ID: ${{ secrets.R2_ACCOUNT_ID }}
          R2_ACCESS_KEY_ID: ${{ secrets.R2_ACCESS_KEY_ID }}
          R2_SECRET_ACCESS_KEY: ${{ secrets.R2_SECRET_ACCESS_KEY }}
          R2_BUCKET_NAME: nexusos-binaries
          CHROMIUM_BINARY_SOURCE: r2
        run: |
          cd packages/browseros
          uv run python -m build.browseros build \
            --modules chromium_download,resources,package_linux

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: nexusos-linux
          path: packages/browseros/dist/*.AppImage
```

**Build time on GitHub Actions:** ~10 minutes vs hours!

---

## Comparison with Other Browsers

### Brave Browser

Brave uses a hybrid approach:
1. Downloads official Chromium release
2. Applies Brave-specific patches (C++ code)
3. Compiles ONLY the patched components
4. Links with unmodified Chromium base

**NexusOS approach is similar but simpler:**
- No C++ patches needed (Python-based customization)
- No partial recompilation
- Just branding and packaging

### Vivaldi Browser

Vivaldi:
1. Uses proprietary UI layer (closed source)
2. Links against Chromium library
3. Bundles as a single package

**NexusOS approach:**
- Open source
- Uses Chromium's UI with customization
- Lighter weight

### Microsoft Edge

Edge:
1. Microsoft builds Chromium internally
2. Applies proprietary features
3. Signs and distributes

**NexusOS approach:**
- Use public Chromium builds
- Add open-source features
- Community-driven

---

## Troubleshooting

### "Failed to download Chromium binary from R2"

**Solution:** Make sure you've uploaded the binary to R2:

```bash
# Check what's in your bucket
aws s3 ls s3://nexusos-binaries/binaries/chromium/ \
  --endpoint-url https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com

# Upload if missing
aws s3 cp chromium-*.tar.xz s3://nexusos-binaries/binaries/chromium/ \
  --endpoint-url https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com
```

### "Chromium binary validation failed"

**Solution:** The downloaded binary is incomplete or corrupted.

```bash
# Verify archive integrity
tar -tJf chromium-linux-x64.tar.xz | head

# Should contain files like:
# chrome
# chrome_sandbox
# locales/
# resources/
```

### "CHROMIUM_BINARY_SOURCE environment variable not set"

**Solution:** Set the binary source:

```bash
export CHROMIUM_BINARY_SOURCE=r2  # or: official, local, ungoogled
```

### "Build number mapping needed for version"

**Solution:** When using official snapshots, you need to manually specify the build number. For now, use R2 or local sources instead.

---

## Benefits Summary

| Aspect | Source Build | Binary Download |
|--------|--------------|-----------------|
| **Disk Space** | 100+ GB | 2-3 GB |
| **Build Time** | 4-8 hours | 5-10 minutes |
| **Setup** | Complex (depot_tools, GN, Ninja) | Simple (Python, R2) |
| **CI/CD** | Expensive (high-CPU runners) | Cheap (standard runners) |
| **Iteration** | Slow (recompile each time) | Fast (download once) |
| **Flexibility** | Full C++ customization | Branding & packaging |
| **Maintenance** | Track Chromium source changes | Track binary releases |

---

## Next Steps

1. **Upload your first Chromium binary to R2**
   - Download from official snapshots or build once
   - Upload with version naming convention

2. **Test the binary download build**
   ```bash
   export CHROMIUM_BINARY_SOURCE=r2
   uv run python -m build.browseros build --modules chromium_download,resources,package_linux
   ```

3. **Set up CI/CD with binary downloads**
   - Add R2 secrets to GitHub
   - Configure workflow to use chromium_download

4. **Document your Chromium version strategy**
   - Which versions do you support?
   - How often do you update?
   - Security patch policy?

---

## See Also

- [BrowserOS Build System Documentation](BUILD_SYSTEM_MODERNIZATION.md)
- [Chromium Download Snapshots](https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html)
- [Chromium Dash (Version Tracking)](https://chromiumdash.appspot.com/releases)
- [Brave Browser Build Process](https://github.com/brave/brave-browser/wiki/Brave-Release-Schedule)
- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)

---

**Status:** ✅ Binary download module implemented and ready to use!

**Contact:** See CONTRIBUTING.md for questions or contributions.
