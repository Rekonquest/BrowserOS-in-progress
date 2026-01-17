# NexusOS

<div align="center">

[![License: Polyform Noncommercial](https://img.shields.io/badge/License-Polyform%20Noncommercial-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Built with Chromium](https://img.shields.io/badge/Built%20with-Chromium-4285F4?logo=googlechrome&logoColor=white)](https://www.chromium.org/)

**A privacy-focused Chromium-based browser with native AI agent integration**

</div>

---

## 🎯 Overview

NexusOS is an open-source Chromium fork designed for developers and power users who want:
- **Local-first AI agents** - Run automation on your machine, not in the cloud
- **Privacy by design** - Bring your own API keys or use local models (Ollama, LMStudio)
- **Full control** - Open source, auditable, forkable
- **Chrome compatibility** - Works with all your existing extensions and workflows

## 🚀 Features

### Core Capabilities
- 🤖 **Native AI Agent Runtime** - Execute automation tasks directly in the browser
- 🔐 **Privacy-First Architecture** - Your data never leaves your machine
- 🔌 **MCP Server Support** - Control the browser from external tools via Model Context Protocol
- 🎨 **Chromium Base** - Full compatibility with Chrome extensions and web standards
- 🛡️ **Enhanced Privacy** - Integrated privacy patches from ungoogled-chromium

### AI Integration
- **Multi-Provider Support** - OpenAI, Anthropic, Google, local models (Ollama/LMStudio)
- **Bring Your Own Keys** - Use your own API credentials
- **Local Model Support** - Run completely offline with local LLMs
- **Agent Automation** - Automate web tasks with AI assistance

## ⚡ Quick Build (Recommended)

**Following Brave/Vivaldi's approach:** Download pre-built Chromium binaries instead of compiling from source!

### Why Binary Download?
- ✅ **10 minutes** instead of 4-8 hours
- ✅ **2 GB disk space** instead of 100+ GB
- ✅ **Simple setup** - no complex build toolchains
- ✅ **Same result** - full NexusOS browser with all features

### Quick Start (Binary Download)
```bash
# 1. Clone repository
git clone https://github.com/Rekonquest/BrowserOS-in-progress.git
cd BrowserOS-in-progress/packages/browseros

# 2. Install Python dependencies
pip install uv
uv sync

# 3. Set up R2 credentials (for downloading pre-built Chromium)
export R2_ACCOUNT_ID="your_account_id"
export R2_ACCESS_KEY_ID="your_access_key"
export R2_SECRET_ACCESS_KEY="your_secret_key"
export CHROMIUM_BINARY_SOURCE=r2

# 4. Build NexusOS (downloads Chromium, applies branding, packages)
uv run python -m build.browseros build \
  --modules chromium_download,resources,package_linux

# 5. Find your package
ls -lh dist/NexusOS*.AppImage
```

**Total time:** ~10 minutes | **Disk space:** ~2 GB

📖 **See [BINARY_DOWNLOAD_GUIDE.md](packages/browseros/BINARY_DOWNLOAD_GUIDE.md) for complete instructions**

---

## 🏗️ Building from Source (Advanced)

**Note:** Most users should use the [binary download approach](#-quick-build-recommended) above.
Only build from source if you need custom C++ patches or are contributing to Chromium itself.

### Prerequisites
- Python 3.12 or higher
- Git with submodule support
- **100+ GB disk space** for Chromium source
- **4-8 hours** for compilation
- Platform-specific build tools (depot_tools, GN, Ninja)

### Quick Start
```bash
# Clone the repository
git clone --recursive https://github.com/Rekonquest/BrowserOS-in-progress.git
cd BrowserOS-in-progress

# Set up Python environment
cd packages/browseros
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run build system
browseros build --help
```

### Development
```bash
# Initialize submodules (if not cloned with --recursive)
git submodule update --init --recursive

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run demo application
python demo_app.py
```

## 📚 Documentation

### Build System
- **[Binary Download Guide](packages/browseros/BINARY_DOWNLOAD_GUIDE.md)** ⭐ **Recommended** - 10-minute builds
- [Build System Modernization](packages/browseros/BUILD_SYSTEM_MODERNIZATION.md) - Advanced source builds
- [Migration Guide](packages/browseros/MIGRATION_GUIDE.md) - Upgrading from older versions
- [Package Info](PACKAGE_INFO.md) - Demo application and packaging details

### Testing
- [Test Documentation](packages/browseros/tests/README.md) - Running the test suite
- [Test Coverage Reports](packages/browseros/htmlcov/) - Available after running `make test-coverage`

### Platform-Specific
- [Windows Build Assessment](WINDOWS_BUILD_ASSESSMENT.md) - Windows-specific information

## 🤝 Contributing

Contributions are welcome! This is an independent open-source project.

### How to Contribute
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow Python 3.12+ best practices
- Maintain test coverage
- Update documentation for new features
- Security fixes are always welcome

## 🔒 Security

- **Security-hardened dependencies** - All known CVEs patched (see requirements.txt)
- **Regular audits** - Automated pip-audit scans via GitHub Actions
- **Vulnerability reporting** - See [SECURITY.md](.github/SECURITY.md)

## 📦 Project Structure

```
.
├── packages/
│   └── browseros/          # Main build system and Python code
│       ├── build/          # Build modules and CLI
│       ├── chromium_patches/ # Patches applied to Chromium
│       ├── resources/      # Browser resources and UI
│       ├── tests/          # Test suite
│       └── demo_app.py     # Demo application
├── docs/                   # Documentation
└── .github/                # GitHub workflows and configurations
```

## 📄 License

NexusOS is licensed under the [Polyform Noncommercial License 1.0.0](LICENSE).

**TL;DR:**
- ✅ Free for personal use, research, and learning
- ✅ Free for non-profits, schools, and research organizations
- ✅ View, modify, and share the code
- ✅ Fork it and make it your own
- ❌ No commercial use without a commercial license

**Need it for business?** Contact the repository owner for a commercial license.

## 🙏 Credits

This project builds upon excellent open-source work:

- **[The Chromium Project](https://www.chromium.org/)** - The foundation that makes this possible
- **[ungoogled-chromium](https://github.com/ungoogled-software/ungoogled-chromium)** - Privacy patches and inspiration
- **All contributors** - Thank you for making this project better

---

## ⚙️ Technical Details

### Python Build System
- **Modern tooling** - Built with Python 3.12+, pytest, ruff, pyright
- **Type safety** - Pydantic-based configuration
- **Comprehensive testing** - Unit, integration, and dynamic tests
- **Artifact management** - Automated build artifact tracking

### Browser Features
- **Chromium 142.0** base (version may vary, check build)
- **Cross-platform** - macOS, Windows, Linux support
- **Extension compatible** - Full Chrome Web Store compatibility
- **Developer-friendly** - Built by developers, for developers

---

<div align="center">

**Built for privacy, designed for productivity**

[Report Bug](https://github.com/Rekonquest/BrowserOS-in-progress/issues) ·
[Request Feature](https://github.com/Rekonquest/BrowserOS-in-progress/issues)

</div>
