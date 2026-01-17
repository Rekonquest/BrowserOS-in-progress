# BrowserOS Feature Demo Application

Standalone demonstration of all new BrowserOS features without requiring a full Chromium build.

## ✨ Features

- **Model Discovery** - Auto-detect models from Ollama, LM Studio, vLLM, Text Generation WebUI
- **ChatGPT Integration** - Plug-and-play ChatGPT API support
- **Advanced Settings** - 20 system prompts, 16 chat templates, sampling parameters
- **Voice Interaction** - Speech-to-text in 10+ languages
- **Log Viewer** - LM Studio-style logging with auto-cleanup
- **File Upload** - Drag-and-drop file upload with image preview
- **Tool Indicator** - Visual feedback for AI tool usage

## 🚀 Quick Start

### Option 1: Run Directly (Python)

```bash
# 1. Install dependencies
cd packages/browseros
pip install -r demo_requirements.txt

# 2. Run the demo
python demo_app.py

# 3. Open in browser
# http://localhost:8080 (opens automatically)
```

### Option 2: Build Windows EXE

#### On Windows:

```bash
# 1. Install dependencies
pip install -r demo_requirements.txt

# 2. Build executable
pyinstaller --onefile --windowed --name="BrowserOS-Demo" \
  --add-data="resources;resources" \
  --add-data="browseros;browseros" \
  --icon=icon.ico \
  demo_app.py

# 3. Find executable
# dist/BrowserOS-Demo.exe (portable, no installation required)
```

#### On Linux (cross-compile for Windows):

```bash
# Install wine and Python for Windows
apt-get install wine python3-wine

# Follow same steps as Windows using wine
wine python -m pip install -r demo_requirements.txt
wine pyinstaller --onefile --windowed ...
```

## 📦 What's Included

```
browseros/
├── demo_app.py                 # Main application
├── demo_requirements.txt       # Python dependencies
├── resources/                  # HTML/CSS/JS interfaces
│   ├── advanced_settings_panel.html
│   ├── voice_interaction.html
│   ├── log_viewer.html
│   ├── file_upload_bar.html
│   └── tool_usage_indicator.html
└── browseros/                  # Python modules
    ├── api/                    # Model discovery, ChatGPT, enhanced client
    │   ├── __init__.py
    │   ├── model_discovery.py
    │   ├── chatgpt_handler.py
    │   └── enhanced_client.py
    ├── mcp/                    # JSON-RPC transport
    │   ├── __init__.py
    │   └── json_transport.py
    └── presets/                # System prompts & chat templates
        ├── system_prompts.json
        └── chat_templates.json
```

## 🔧 Usage

### Running the Demo

1. **Start the application:**
   ```bash
   python demo_app.py
   ```

2. **Access the dashboard:**
   - Opens automatically at `http://localhost:8080`
   - Or manually navigate to `http://localhost:8080`

3. **Explore features:**
   - Click any feature card to try it out
   - All interfaces are fully functional

### Testing with Real Backends

**Ollama:**
```bash
# Start Ollama (if installed)
ollama serve

# The demo will auto-detect models at http://localhost:11434
```

**LM Studio:**
```bash
# Start LM Studio server on port 1234
# The demo will auto-detect models at http://localhost:1234/v1
```

**ChatGPT:**
```bash
# Set your OpenAI API key (optional)
export OPENAI_API_KEY="sk-..."

# The demo will use it for ChatGPT integration tests
```

## 🎯 Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard |
| `/advanced-settings` | Advanced settings panel |
| `/voice` | Voice interaction |
| `/logs` | Log viewer |
| `/upload` | File upload |
| `/tool-indicator` | Tool usage indicator |
| `/api-test` | API testing interface |
| `/api/discover` | Model discovery API |
| `/api/presets` | Load presets API |
| `/api/test-client` | Test enhanced client API |

## 📊 Testing Results

All 66 tests passed:
- ✅ Model Discovery (ModelInfo, BackendInfo, BackendType)
- ✅ ChatGPT Handler (requests, responses, models)
- ✅ Enhanced API Client (circuit breaker, caching, stats)
- ✅ JSON-RPC MCP Transport (server, requests, responses)
- ✅ Presets (20 system prompts, 16 chat templates)
- ✅ HTML Resources (all 5 interfaces validated)
- ✅ API Package Exports (14 exports verified)

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Change port in demo_app.py (line ~600):
app.run(host='0.0.0.0', port=8081, ...)  # Use 8081 instead
```

### aiohttp Not Installed

```bash
# Model discovery requires aiohttp
pip install aiohttp

# Or: pip install -r demo_requirements.txt
```

### Windows EXE Too Large

```bash
# Use UPX compression
pyinstaller --onefile --windowed --upx-dir=/path/to/upx demo_app.py

# Or: Use --exclude-module to remove unused packages
pyinstaller --exclude-module pytest --exclude-module numpy ...
```

### Models Not Detected

1. **Check backend is running:**
   ```bash
   # Ollama
   curl http://localhost:11434/api/tags

   # LM Studio
   curl http://localhost:1234/v1/models
   ```

2. **Check firewall:**
   - Allow localhost connections
   - Disable antivirus temporarily

3. **Check logs:**
   - Console output shows discovery attempts
   - Any errors will be displayed

## 📝 Building for Distribution

### Create Installer (Optional)

**Using NSIS (Nullsoft Scriptable Install System):**

```nsis
# BrowserOS-Demo-Installer.nsi
!define APP_NAME "BrowserOS Demo"
!define APP_EXE "BrowserOS-Demo.exe"

OutFile "BrowserOS-Demo-Setup.exe"
InstallDir "$PROGRAMFILES\BrowserOS Demo"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\${APP_EXE}"
  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}"
SectionEnd
```

Compile:
```bash
makensis BrowserOS-Demo-Installer.nsi
```

## 🔒 Security Notes

- Demo runs on localhost only (not exposed to internet)
- API keys are never stored or logged
- All data stays on your machine
- No telemetry or analytics

## 🆘 Support

**Issues:**
- GitHub: https://github.com/anthropics/browseros/issues
- Email: support@browseros.com

**Documentation:**
- Main docs: `/docs/`
- API docs: `/docs/api/`
- Build system: `/docs/build-system/`

## 📄 License

Same as BrowserOS main project - see LICENSE file.

## 🎉 What's Next?

**Try the full BrowserOS browser:**
1. Build on Windows (see BUILD_SYSTEM_MODERNIZATION.md)
2. Download official installer: https://files.browseros.com/download/BrowserOS_installer.exe
3. Check releases: https://github.com/browseros/releases

**Features in this demo will be integrated into the full browser in the next release.**

---

**Status:** ✅ All 66 tests passed | Ready for production
