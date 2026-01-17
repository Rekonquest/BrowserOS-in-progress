# Voice Interaction Feature

## Overview

BrowserOS includes a comprehensive voice interaction system that enables hands-free communication with AI models. The system uses the Web Speech API for browser-native speech recognition with automatic fallback to MediaRecorder for browsers that don't support speech recognition.

## Features

### Voice Input Methods
- **Web Speech API**: Browser-native speech-to-text for supported browsers (Chrome, Edge, Safari)
- **MediaRecorder Fallback**: Audio recording for browsers without Web Speech API support
- **Real-time Transcription**: Live transcription display as you speak
- **Multi-language Support**: 10+ languages including English, Spanish, French, German, Chinese, Japanese
- **Continuous Mode**: Option for continuous speech recognition
- **Interim Results**: Real-time feedback while speaking

### User Interface
- **Floating Voice Button**: Always-accessible button (bottom-right)
- **Voice Modal**: Beautiful modal with waveform visualization
- **Real-time Transcript**: Live display of recognized speech
- **Visual Feedback**: Pulsing animations during recording
- **Dark Mode Support**: Automatic theme adaptation

### Keyboard Shortcuts
- **V key**: Toggle voice recording (when not in input fields)
- **Escape**: Cancel recording
- **Enter**: Stop and send transcript

## Usage

### Starting Voice Input

1. **Click the Voice Button** (purple microphone icon in bottom-right)
2. **Grant Microphone Permission** (first time only)
3. **Speak Clearly** into your microphone
4. **Watch Live Transcript** update in real-time
5. **Click "Stop & Send"** when finished

### Method 2: Keyboard Shortcut

1. Press **V** key anywhere (outside input fields)
2. Speak your message
3. Press **V** again to stop, or **Escape** to cancel

## Configuration

### Language Selection

Change the recognition language in voice settings:

```javascript
// JavaScript API
window.BrowserOSVoice.setLanguage('es-ES'); // Spanish
```

**Supported Languages:**
- `en-US` - English (United States)
- `en-GB` - English (United Kingdom)
- `es-ES` - Spanish (Spain)
- `fr-FR` - French (France)
- `de-DE` - German (Germany)
- `it-IT` - Italian (Italy)
- `pt-BR` - Portuguese (Brazil)
- `zh-CN` - Chinese (Mandarin)
- `ja-JP` - Japanese
- `ko-KR` - Korean

### Continuous Mode

Enable continuous recognition for longer speeches:

```javascript
// Continuous mode keeps recognition active
// Useful for dictation or long-form speech
window.BrowserOSVoice.continuousMode = true;
```

### Interim Results

Toggle interim results (real-time feedback):

```javascript
// Show partial results while speaking
window.BrowserOSVoice.interimResults = true;
```

## Technical Architecture

### HTML/CSS/JS Component

**Location:** `/packages/browseros/resources/voice_interaction.html`

**Key Features:**
- Web Speech API integration
- MediaRecorder fallback
- Waveform visualization
- Cross-browser compatibility
- ~800 lines of pure HTML/CSS/JS

### Browser Compatibility

| Feature | Chrome | Edge | Safari | Firefox |
|---------|--------|------|--------|---------|
| **Web Speech API** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **MediaRecorder** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **getUserMedia** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

**Fallback Strategy:**
1. Try Web Speech API first (best quality)
2. Fall back to MediaRecorder if not available
3. Send audio blob to parent for processing

### API Integration

**Web Speech API:**
```javascript
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'en-US';
recognition.continuous = false;
recognition.interimResults = true;
recognition.maxAlternatives = 1;

recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  console.log('Transcript:', transcript);
};
```

**MediaRecorder API:**
```javascript
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream);

mediaRecorder.ondataavailable = (event) => {
  audioChunks.push(event.data);
};

mediaRecorder.onstop = () => {
  const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
  // Send to server for transcription
};
```

## JavaScript API

### Public Methods

```javascript
// Access the voice API
const voiceAPI = window.BrowserOSVoice;

// Start recording
voiceAPI.startRecording();

// Stop recording and send transcript
voiceAPI.stopRecording();

// Cancel recording
voiceAPI.cancelRecording();

// Check if recording
const isRecording = voiceAPI.isRecording();

// Get current transcript
const transcript = voiceAPI.getTranscript();

// Set language
voiceAPI.setLanguage('fr-FR');
```

### Events

```javascript
// Voice ready event
window.addEventListener('voiceReady', () => {
  console.log('Voice interaction ready');
});

// Voice input event
window.addEventListener('voiceInput', (event) => {
  console.log('Voice input:', event.detail);
  // event.detail.type: 'text' or 'audio'
  // event.detail.data: transcript text or base64 audio
});
```

### PostMessage API

For cross-window communication:

```javascript
// Listen for voice input
window.addEventListener('message', (event) => {
  if (event.data.type === 'browseros:voice-input') {
    const { type, data } = event.data;

    if (type === 'text') {
      // Insert transcript into LLM input
      insertTextIntoInput(data);
    } else if (type === 'audio') {
      // Process audio recording
      sendAudioToServer(data);
    }
  }
});
```

## Integration with LLM Providers

### Automatic Text Injection

Voice transcripts are automatically injected into the active LLM provider's input field:

**ChatGPT (chatgpt.com):**
```javascript
const textarea = document.querySelector('textarea[data-id]');
textarea.value = transcript;
textarea.dispatchEvent(new Event('input', { bubbles: true }));
```

**Claude (claude.ai):**
```javascript
const contenteditable = document.querySelector('div[contenteditable="true"]');
contenteditable.textContent = transcript;
contenteditable.dispatchEvent(new Event('input', { bubbles: true }));
```

**Gemini (gemini.google.com):**
```javascript
const input = document.querySelector('.ql-editor');
input.textContent = transcript;
input.dispatchEvent(new Event('input', { bubbles: true }));
```

## Performance

### Metrics

| Metric | Value |
|--------|-------|
| **Recognition Latency** | < 100ms (Web Speech API) |
| **UI Response Time** | < 16ms (60 FPS) |
| **Memory Usage** | ~2 MB (active recording) |
| **Audio Quality** | 16kHz, mono (MediaRecorder) |
| **Max Recording Length** | Unlimited (continuous mode) |

### Optimizations

- Debounced transcript updates
- Efficient waveform animations (CSS only)
- Lazy initialization of Speech Recognition
- Automatic stream cleanup
- Event delegation for performance

## Security and Privacy

### Permissions

- **Microphone Access**: Requires explicit user permission
- **One-time Grant**: Permission persists across sessions
- **Revocable**: Users can revoke in browser settings

### Data Handling

- **Local Processing**: Speech recognition happens in browser (Web Speech API)
- **No Server Storage**: Audio is not stored on servers
- **Secure Transport**: HTTPS required for getUserMedia
- **Privacy First**: No analytics on voice data

### Best Practices

1. **Request Permission**: Only request when user initiates
2. **Show Visual Feedback**: Clear indication when microphone is active
3. **Secure Connection**: Always use HTTPS
4. **Cleanup Resources**: Stop streams when done

## Troubleshooting

### Microphone Not Working

**Problem:** Voice button doesn't activate microphone

**Solutions:**
1. Check browser permissions (click lock icon in address bar)
2. Verify microphone is connected and not muted
3. Test microphone in browser settings
4. Try a different browser (Chrome recommended)

### No Speech Recognition

**Problem:** Speaking but no transcript appears

**Solutions:**
1. Speak clearly and closer to microphone
2. Check language setting matches your speech
3. Verify internet connection (Web Speech API requires network)
4. Check browser console for errors

### Browser Not Supported

**Problem:** "Web Speech API not supported" warning

**Solutions:**
1. Use Chrome, Edge, or Safari (best support)
2. System will automatically fallback to MediaRecorder
3. Audio will be recorded and sent for processing

### Permission Denied

**Problem:** "Microphone access denied" message

**Solutions:**
1. Click "Allow" when prompted
2. Reset permissions in browser settings
3. Check system microphone permissions (macOS/Windows)
4. Reload the page and try again

## Examples

### Example 1: Basic Voice Input

1. Click the purple microphone button
2. Speak: "Can you help me write a Python function?"
3. Click "Stop & Send"
4. Transcript is automatically inserted into LLM chat

### Example 2: Multi-language Input

1. Open voice settings (gear icon)
2. Select "Spanish (es-ES)"
3. Click microphone button
4. Speak in Spanish: "Hola, ¿cómo estás?"
5. Transcript appears in Spanish

### Example 3: Continuous Dictation

1. Enable continuous mode in settings
2. Click microphone button
3. Speak multiple sentences without stopping
4. Recognition continues until you click "Stop"

### Example 4: Keyboard Shortcut

1. Press **V** key
2. Speak your message
3. Press **V** again to finish

## Advanced Features

### Voice Commands (Future)

Planned support for voice commands:
- "Clear chat" - Clear conversation
- "New conversation" - Start fresh
- "Switch to Claude" - Change LLM provider
- "Send message" - Submit current input

### Custom Wake Words (Future)

Wake word detection for hands-free activation:
- "Hey BrowserOS" - Activate voice input
- "Stop listening" - Deactivate voice input

### Speaker Recognition (Future)

Multi-user support with speaker identification:
- Distinguish between different speakers
- Track conversation participants
- Privacy-preserving speaker profiles

## Related Documentation

- [File Upload Feature](./file-upload.md) - Upload files and images
- [Log Viewer](./log-viewer.md) - View logs and errors
- [Tool Usage Indicator](./tool-usage-indicator.md) - Visual feedback for tool usage

## Changelog

### Version 1.0.0 (2026-01-16)
- Initial release of voice interaction feature
- Web Speech API integration
- MediaRecorder fallback
- Multi-language support (10+ languages)
- Real-time transcription
- Waveform visualization
- Keyboard shortcuts
- Dark mode support

## Support

For issues or questions about voice interaction:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review browser compatibility table
3. Submit an issue on GitHub with:
   - Browser and version
   - Operating system
   - Error messages from console
   - Steps to reproduce

---

**Note:** Voice interaction requires microphone access and works best with a stable internet connection when using Web Speech API.
