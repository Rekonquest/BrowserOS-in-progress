# File Upload Feature

## Overview

BrowserOS includes a universal file and image upload system that works seamlessly across all LLM providers (ChatGPT, Claude, Gemini, Copilot, Perplexity, and others). The file upload bar provides an intuitive interface for uploading images, PDFs, documents, and code files to AI models.

## Features

### Visual Upload Bar
- **Always-accessible upload bar** at the bottom of the screen
- **Drag-and-drop support** for quick file uploads
- **Image preview** for uploaded images
- **File information display** showing name, type, and size
- **Multiple file support** with clear visual organization
- **Toggle button** to show/hide the upload bar
- **Dark mode support** with automatic theme detection

### Supported File Types

#### Images
- PNG, JPG, JPEG, GIF, WebP, SVG
- Automatic image preview generation
- Base64 encoding for seamless injection

#### Documents
- PDF files
- Text files (.txt, .md)
- JSON, XML, CSV, YAML files
- Microsoft Office (.doc, .docx, .xls, .xlsx)

#### Code Files
- Python (.py)
- JavaScript/TypeScript (.js, .ts)
- Java (.java)
- C/C++ (.c, .cpp, .h)
- Go (.go), Rust (.rs), Ruby (.rb)
- PHP, Shell scripts (.sh)
- CSS, HTML

## Usage

### Method 1: Click to Upload

1. Click the **"Upload Files"** button in the upload bar
2. Select one or more files from your file system
3. Files appear in the upload bar with previews (for images)
4. Files are automatically prepared for injection into the LLM

### Method 2: Drag and Drop

1. Drag files from your file manager
2. Drop them anywhere on the BrowserOS window
3. A visual drop zone appears to guide you
4. Files are added to the upload bar automatically

### Method 3: Paste from Clipboard

1. Copy an image to your clipboard (Cmd+C / Ctrl+C)
2. Use the clipboard integration to paste into the upload bar
3. (Note: Direct paste support depends on browser capabilities)

## File Management

### Viewing Uploaded Files

The upload bar displays all uploaded files with:
- **File icon** indicating the type (image, document, code, PDF)
- **File name** (truncated with ellipsis if too long)
- **File size** in human-readable format (KB, MB, GB)
- **Image preview** for image files (60x60px thumbnail)

### Removing Files

- Click the **X button** on any file to remove it
- Click **"Clear All"** to remove all files at once

### Toggling the Upload Bar

- Click the **floating toggle button** (bottom-right) to show/hide the bar
- The bar slides in/out smoothly with animation
- Files remain in memory even when the bar is hidden

## Integration with LLM Providers

### Automatic Provider Detection

BrowserOS automatically detects the LLM provider based on the URL:

| Provider | Detection Pattern |
|----------|------------------|
| ChatGPT | `chatgpt.com`, `openai.com` |
| Claude | `claude.ai`, `anthropic.com` |
| Gemini | `gemini.google.com`, `bard.google.com` |
| Copilot | `copilot.microsoft.com`, `bing.com/chat` |
| Perplexity | `perplexity.ai` |
| Generic | Any other LLM provider |

### File Injection Methods

#### For Images
1. Converts image to Data URL (base64)
2. Creates a File object from the data URL
3. Injects into the provider's file input element
4. Triggers the change event to activate the upload

**Example injection code:**
```javascript
const dataUrl = 'data:image/png;base64,...';
const file = new File([blob], 'image.png', { type: 'image/png' });
const dataTransfer = new DataTransfer();
dataTransfer.items.add(file);
fileInput.files = dataTransfer.files;
fileInput.dispatchEvent(new Event('change', { bubbles: true }));
```

#### For Text/Code Files
1. Reads file content as plain text
2. Formats with file name markers
3. Inserts into the text input or contenteditable div
4. Triggers input event for reactivity

**Example injection format:**
```
--- File: example.py ---
def hello_world():
    print("Hello, World!")
--- End of file ---
```

## Technical Architecture

### HTML/CSS/JS Component

**Location:** `/packages/browseros/resources/file_upload_bar.html`

**Key Features:**
- Pure HTML/CSS/JS implementation (no dependencies)
- Works in any WebView or iframe
- CSS animations for smooth interactions
- Responsive design for different screen sizes
- ~1000 lines of code with comprehensive functionality

**JavaScript API:**
```javascript
// Public API exposed as window.BrowserOSFileUpload
BrowserOSFileUpload.addFiles(filesArray)      // Add files programmatically
BrowserOSFileUpload.removeFile(fileId)        // Remove specific file
BrowserOSFileUpload.clearAllFiles()           // Clear all files
BrowserOSFileUpload.getFiles()                // Get array of file objects
BrowserOSFileUpload.getFileCount()            // Get number of files
BrowserOSFileUpload.toggleBar()               // Toggle bar visibility
BrowserOSFileUpload.showBar()                 // Show the bar
BrowserOSFileUpload.hideBar()                 // Hide the bar
```

**Events:**
```javascript
// Custom events dispatched by the component
window.addEventListener('fileUploadReady', (e) => {
  console.log('File upload component is ready');
});

window.addEventListener('filesChanged', (e) => {
  console.log('Files changed:', e.detail.files, e.detail.count);
});

// PostMessage API for cross-window communication
window.parent.postMessage({
  type: 'browseros:files-changed',
  files: [...],
  count: 3
}, '*');
```

### C++ Integration

**Location:**
- `/packages/browseros/chromium_patches/chrome/browser/ui/views/file_upload_overlay.h`
- `/packages/browseros/chromium_patches/chrome/browser/ui/views/file_upload_overlay.cc`

**Class:** `FileUploadOverlay`

**Key Methods:**
```cpp
// Set the target WebContents where files will be injected
void SetTargetWebContents(content::WebContents* target_web_contents);

// Show/hide/toggle the upload bar
void ShowUploadBar();
void HideUploadBar();
void ToggleUploadBar();

// File management
const std::vector<UploadedFile>& GetUploadedFiles() const;
void ClearAllFiles();
void AddFiles(const std::vector<base::FilePath>& file_paths);

// Inject files into the target LLM provider
void InjectFilesIntoLLM();
```

**Integration Example:**
```cpp
// In your coordinator or view class
auto* file_upload_overlay = AddChildView(std::make_unique<FileUploadOverlay>());
file_upload_overlay->SetBounds(0, 0, width(), height());
file_upload_overlay->SetTargetWebContents(llm_provider_web_contents_);

// Files are automatically handled by the overlay
```

## User Experience

### Visual Design

#### Upload Bar
- **Position:** Fixed at the bottom of the screen
- **Background:** Frosted glass effect (backdrop-filter: blur)
- **Height:** 80px (auto-adjusts based on content)
- **Border:** Subtle top border with shadow
- **Transition:** Smooth slide-in/out animation (0.3s)

#### Upload Button
- **Color:** Google Blue (#4285f4)
- **Style:** Rounded corners (8px), shadow on hover
- **Icon:** Plus sign (+) with "Upload Files" label
- **Hover Effect:** Darker blue, lifts slightly

#### File Items
- **Layout:** Horizontal scrollable list
- **Style:** White cards with subtle shadow
- **Image Preview:** 60x60px rounded thumbnail
- **Remove Button:** X icon on hover (top-right)

#### Drop Zone Overlay
- **Appearance:** Full-screen overlay with blue tint
- **Center Content:** Dashed border box with upload icon
- **Text:** "Drop files here" + file type hints
- **Animation:** Smooth fade-in/out

### Accessibility

- **Keyboard Navigation:** Tab through files, Enter to remove
- **Screen Reader Support:** ARIA labels on all buttons
- **High Contrast Mode:** Border and focus indicators
- **Reduced Motion:** Respects `prefers-reduced-motion` media query

### Performance

- **File Reading:** Asynchronous with FileReader API
- **Base64 Encoding:** Efficient for images < 10MB
- **Memory Management:** Files cleared when bar is hidden
- **Lazy Loading:** Preview generation on-demand
- **Scroll Performance:** Virtual scrolling for many files

## Configuration

### Customization Options

#### Accepted File Types
Modify the `accept` attribute on the file input:
```html
<input type="file" accept="image/*,.pdf,.txt,.md">
```

#### Upload Bar Height
Adjust the CSS variable:
```css
.upload-bar {
  padding: 12px 16px; /* Adjust padding to change height */
}
```

#### Color Scheme
Override the primary color:
```css
.upload-button {
  background: #your-color;
}
```

### Advanced Settings

#### Maximum File Size
Add validation in the JavaScript:
```javascript
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

async function addFiles(newFiles) {
  for (const file of filesArray) {
    if (file.size > MAX_FILE_SIZE) {
      alert(`File too large: ${file.name}`);
      continue;
    }
    // ... rest of the code
  }
}
```

#### Custom Injection Logic
Override the `GetInjectionJavaScript` method in C++:
```cpp
std::string FileUploadOverlay::GetInjectionJavaScript(
    const std::string& provider,
    const UploadedFile& file) const {
  // Your custom injection logic here
}
```

## Troubleshooting

### Files Not Appearing in LLM Provider

**Problem:** Files are uploaded to the bar but don't appear in ChatGPT/Claude.

**Solution:**
1. Check that the LLM provider's page is fully loaded
2. Verify the provider has native file upload support
3. Check browser console for JavaScript errors
4. Try manually clicking the provider's upload button first

### Image Preview Not Showing

**Problem:** Uploaded images don't show thumbnails.

**Solution:**
1. Ensure the file is a valid image format
2. Check file size (very large images may take time to preview)
3. Verify FileReader API is available in your browser

### Drag-and-Drop Not Working

**Problem:** Files can't be dragged onto the window.

**Solution:**
1. Ensure JavaScript is enabled
2. Check that the page has focus (click the window first)
3. Try dragging to the drop zone instead of the bar
4. Verify file permissions (some files may be protected)

### Upload Bar Hidden

**Problem:** Upload bar disappeared and can't be found.

**Solution:**
1. Look for the floating toggle button (bottom-right corner)
2. Click the toggle button to show the bar
3. If button is missing, refresh the page

## Security Considerations

### File Content Handling
- **No Server Upload:** Files are processed entirely client-side
- **Base64 Encoding:** Images are encoded before injection
- **Sandboxing:** Upload UI runs in isolated WebView
- **XSS Prevention:** Content is escaped before injection

### Privacy
- **Local Processing:** Files never leave your machine
- **No Tracking:** No analytics or telemetry on uploaded files
- **Temporary Storage:** Files are cleared when tab is closed

### Permissions
- **File System Access:** Requires user interaction (click/drag)
- **Clipboard Access:** Requires explicit user permission
- **Cross-Origin:** Upload UI is isolated from provider pages

## Examples

### Example 1: Uploading Code for Review

1. Click "Upload Files"
2. Select `main.py` from your project
3. File appears in the upload bar
4. BrowserOS injects the code into ChatGPT with markers:
   ```
   --- File: main.py ---
   [your code here]
   --- End of file ---
   ```
5. Ask: "Can you review this code and suggest improvements?"

### Example 2: Analyzing Multiple Images

1. Drag 3 images from Finder/Explorer onto BrowserOS
2. All 3 images appear in the upload bar with previews
3. BrowserOS injects them into Claude
4. Ask: "Compare these designs and tell me which is better"

### Example 3: Uploading a PDF Document

1. Click "Upload Files"
2. Select `report.pdf`
3. PDF icon appears in the upload bar
4. BrowserOS attempts to extract text or upload via provider's native mechanism
5. Ask: "Summarize this report"

## Future Enhancements

### Planned Features
- [ ] **OCR Support:** Extract text from images
- [ ] **PDF Text Extraction:** Read PDF content before upload
- [ ] **Batch Upload:** Upload entire folders
- [ ] **Cloud Integration:** Import from Google Drive, Dropbox
- [ ] **File Compression:** Auto-compress large files
- [ ] **Upload History:** Remember recently uploaded files
- [ ] **Annotation Tools:** Draw on images before uploading

### Experimental Features
- **Voice Recording:** Record audio and upload as file
- **Screenshot Tool:** Capture screen and upload directly
- **Video Upload:** Support for video files
- **Archive Extraction:** Auto-extract ZIP files

## Related Documentation

- [Tool Usage Indicator](./tool-usage-indicator.md) - Visual feedback when models use tools
- [JSON MCP Transport](./json-mcp-transport.md) - JSON-RPC protocol for model communication
- [Clash of GPTs](../architecture/clash-of-gpts.md) - Multi-pane LLM comparison interface

## Changelog

### Version 1.0.0 (2026-01-16)
- Initial release of file upload feature
- Support for images, PDFs, documents, and code files
- Drag-and-drop functionality
- Image preview capability
- Multi-file upload support
- Automatic LLM provider detection
- Dark mode support

## Support

For issues or questions about the file upload feature:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review the [GitHub Issues](https://github.com/Rekonquest/BrowserOS/issues)
3. Submit a new issue with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Browser and OS version
   - Screenshots if applicable
