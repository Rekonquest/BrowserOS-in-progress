# Tool Usage Indicator

Visual feedback system that shows when AI models are actively using tools or browsing the web.

## Overview

The Tool Usage Indicator provides a **glowing, pulsing blue border** around the browser viewport when AI assistants are using tools, similar to the visual feedback in Gemini and Comet apps. This gives users immediate visual awareness of tool activity without interrupting their workflow.

## Features

- **Glowing Border Effect** - Smooth, pulsing animation around the viewport
- **Color-Coded Tool Types** - Different colors for different tool categories
- **Tool Info Badge** - Displays current tool name and type
- **Auto-Hide Support** - Optional automatic hiding after a timeout
- **Non-Intrusive** - Overlay doesn't block user interaction
- **Theme Support** - Works in both light and dark modes

## Visual Design

### Tool Type Colors

| Tool Type | Color | Use Case |
|-----------|-------|----------|
| Browser | Blue (#4285F4) | Web browsing, navigation |
| Filesystem | Green (#34A853) | File operations, reading/writing |
| Terminal | Yellow (#FBBC05) | Command execution, shell |
| API | Red (#EA4335) | API calls, external services |

### Animation

The border uses a 2-second pulsing animation that oscillates between:
- Minimum opacity: 65% with 10px glow
- Maximum opacity: 100% with 40px glow

## Usage

### Integration Methods

#### 1. HTML Iframe Integration

```html
<!-- Include the tool indicator in your page -->
<iframe
  src="/resources/tool_usage_indicator.html"
  style="position: fixed; top: 0; left: 0; width: 100%; height: 100%;
         pointer-events: none; border: none; z-index: 999999;">
</iframe>
```

#### 2. JavaScript API

```javascript
// Show indicator when tool starts
window.showToolUsage('Web Browser', 'browser');

// Update tool name during execution
window.updateToolName('Reading webpage...');

// Hide indicator when tool completes
window.hideToolUsage();

// Check if indicator is showing
const isActive = window.isShowingToolUsage();

// Auto-hide after 5 seconds
window.showToolUsage('File System', 'filesystem', 5000);
```

#### 3. Cross-Window Communication

```javascript
// From parent window - send message to indicator iframe
const indicatorFrame = document.getElementById('toolIndicator');
indicatorFrame.contentWindow.postMessage({
  type: 'show-tool-usage',
  toolName: 'Terminal',
  toolType: 'terminal',
  autoHideMs: 0  // Don't auto-hide
}, '*');

// Hide the indicator
indicatorFrame.contentWindow.postMessage({
  type: 'hide-tool-usage'
}, '*');

// Listen for tool usage events
window.addEventListener('message', (event) => {
  if (event.data.type === 'tool-usage-started') {
    console.log('Tool started:', event.data.toolName);
  } else if (event.data.type === 'tool-usage-ended') {
    console.log('Tool completed');
  }
});
```

## Implementation in BrowserOS

### Clash of GPTs Integration

The tool indicator is integrated into the Clash of GPTs side panel:

```cpp
// In clash_of_gpts_view.cc
void ClashOfGptsView::ShowToolUsageIndicator(
    const std::string& tool_name,
    const std::string& tool_type) {
  // Post message to indicator frame
  std::string script = base::StringPrintf(
      "window.showToolUsage('%s', '%s');",
      tool_name.c_str(),
      tool_type.c_str());

  tool_indicator_web_view_->GetWebContents()->ExecuteJavaScript(
      base::UTF8ToUTF16(script));
}
```

### MCP Server Integration

The MCP server automatically triggers the indicator when tools are executed:

```python
# In MCP server tool handler
def browser_tool_handler(params):
    # Notify frontend to show indicator
    notify_tool_usage_start("Web Browser", "browser")

    try:
        result = execute_browser_tool(params)
        return result
    finally:
        # Hide indicator when done
        notify_tool_usage_end()
```

## Configuration

### Settings

Users can configure the tool indicator in BrowserOS settings:

1. Navigate to `chrome://browseros/settings`
2. Go to **Tools & Features** section
3. Toggle **Show Tool Usage Indicator**
4. Customize:
   - Enable/disable indicator
   - Adjust glow intensity (0.0 to 1.0)
   - Set auto-hide duration
   - Choose border thickness

### Preferences

```cpp
// In browseros_prefs.h
extern const char kShowToolUsageIndicator[];
extern const char kToolIndicatorGlowIntensity[];
extern const char kToolIndicatorAutoHideMs[];
```

## Testing

### Manual Test Mode

Open the indicator page with test mode:

```
/resources/tool_usage_indicator.html?test=true
```

This will automatically show the indicator after 1 second for visual verification.

### Automated Tests

```javascript
// Test showing indicator
window.showToolUsage('Test Tool', 'browser');
assert(window.isShowingToolUsage() === true);

// Test auto-hide
window.showToolUsage('Test Tool', 'browser', 1000);
setTimeout(() => {
  assert(window.isShowingToolUsage() === false);
}, 1500);

// Test color variants
['browser', 'filesystem', 'terminal', 'api'].forEach(type => {
  window.showToolUsage(`Test ${type}`, type);
  // Visual verification
  window.hideToolUsage();
});
```

## Browser Compatibility

- Chrome/Chromium: Full support
- Edge: Full support
- Firefox: Full support
- Safari: Full support (WebKit animations)

## Performance

- **CPU Usage:** < 1% during animation
- **Memory:** ~2MB for indicator frame
- **GPU:** Uses hardware acceleration for animations
- **Battery Impact:** Minimal (efficient CSS animations)

## Accessibility

- **Screen Readers:** Announces tool usage via ARIA live regions
- **Keyboard Navigation:** Close button is keyboard accessible
- **High Contrast Mode:** Adapts colors for visibility
- **Reduced Motion:** Respects `prefers-reduced-motion` media query

## Examples

### Basic Usage

```javascript
// Show browser tool indicator
window.showToolUsage('Web Browser', 'browser');

// Wait for tool to complete
await performBrowserAction();

// Hide indicator
window.hideToolUsage();
```

### Multiple Tools Sequence

```javascript
// Filesystem tool
window.showToolUsage('Reading files...', 'filesystem');
await readFiles();

// Switch to terminal tool
window.showToolUsage('Running command...', 'terminal');
await runCommand();

// Switch to API tool
window.showToolUsage('Fetching data...', 'api');
await fetchData();

// Hide when all done
window.hideToolUsage();
```

### With Error Handling

```javascript
try {
  window.showToolUsage('Web Browser', 'browser');
  await navigateToPage();
} catch (error) {
  console.error('Tool failed:', error);
} finally {
  window.hideToolUsage();
}
```

## Future Enhancements

- [ ] Multiple simultaneous tool indicators
- [ ] Progress bar for long-running tools
- [ ] Tool history/timeline
- [ ] Custom tool type definitions
- [ ] Animated tool transitions
- [ ] Sound effects (optional)

## See Also

- [MCP JSON Transport](json-mcp-transport.md)
- [BrowserOS Settings](../settings/browseros-settings.md)
- [Clash of GPTs](clash-of-gpts.md)
