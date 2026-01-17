# Advanced Settings & Backend Integration

## Overview

BrowserOS includes comprehensive advanced settings that make working with local backends (Ollama, LM Studio, vLLM) seamless and powerful. This document covers all the advanced features including model discovery, system prompts, chat templates, sampling parameters, system monitoring, and ChatGPT API integration.

## Table of Contents

1. [Model Discovery](#model-discovery)
2. [System Prompt Presets](#system-prompt-presets)
3. [Chat Template Presets](#chat-template-presets)
4. [Advanced Sampling Parameters](#advanced-sampling-parameters)
5. [System Monitoring](#system-monitoring)
6. [ChatGPT Custom API](#chatgpt-custom-api)

---

## Model Discovery

### Problem Solved

Previously, users had to:
- Manually copy-paste model names from backend
- Go back and forth between backend UI and BrowserOS
- Guess model names without seeing what's available
- Deal with 3 hardcoded default models that might not exist

### Solution

**Automatic model discovery** from local backends with a single click!

### Supported Backends

| Backend | Default URL | Description |
|---------|------------|-------------|
| **Ollama** | `http://localhost:11434` | Popular local LLM runtime |
| **LM Studio** | `http://localhost:1234/v1` | User-friendly local LLM tool |
| **vLLM** | `http://localhost:8000/v1` | High-performance inference |
| **Text Generation WebUI** | `http://localhost:5000/v1` | Gradio-based interface |

### How to Use

1. **Enter Backend URL**
   ```
   http://localhost:11434  (for Ollama)
   http://localhost:1234/v1  (for LM Studio)
   ```

2. **Click "Discover Models"**
   - Automatically queries the backend
   - Lists all available models
   - Shows model metadata (size, quantization)

3. **Select a Model**
   - Click "Use Model" on any discovered model
   - Model ID is automatically filled in
   - Ready to use immediately!

### What You See

```
✓ Ollama (http://localhost:11434)
  Found 3 models:
    - llama3.1:8b (8B) [Q4_0]
    - mistral:7b (7B) [Q5_K_M]
    - codellama:13b (13B) [Q4_K_M]
```

### Python API

```python
from browseros.api import ModelDiscovery

async with ModelDiscovery(timeout=3.0) as discovery:
    # Discover from all default backends
    backends = await discovery.discover_all()

    for backend in backends:
        if backend.is_available:
            print(f"✓ {backend.name}")
            for model in backend.models:
                print(f"  - {model.model_id}")

    # Discover from custom backend
    custom_backends = [
        {"type": BackendType.OLLAMA, "url": "http://192.168.1.100:11434", "name": "Remote Ollama"}
    ]
    backends = await discovery.discover_all(custom_backends)
```

### Model Information

Each discovered model includes:
- **model_id**: Unique identifier
- **name**: Display name
- **size**: Model size (e.g., "8B", "13B")
- **quantization**: Quantization format (e.g., "Q4_0", "Q5_K_M")
- **family**: Model family (e.g., "llama", "mistral")
- **context_length**: Maximum context window
- **modified_at**: Last modification timestamp

---

## System Prompt Presets

### Overview

Pre-configured system prompts for common use cases. No more writing the same system prompt over and over!

### Available Presets

| Preset | Icon | Description | Use Case |
|--------|------|-------------|----------|
| **Default Assistant** | 💬 | Helpful, harmless, honest | General chat |
| **Code Expert** | 💻 | Expert programmer | Code review, debugging |
| **Python Specialist** | 🐍 | Python expert | Python development |
| **JavaScript Expert** | ⚡ | Modern JS/TS | Frontend development |
| **Creative Writer** | ✍️ | Storyteller | Creative writing |
| **Technical Writer** | 📝 | Documentation | Writing docs |
| **Patient Teacher** | 🎓 | Educational | Learning, teaching |
| **Research Assistant** | 🔬 | Thorough research | Research, analysis |
| **Brainstorming Partner** | 💡 | Idea generation | Brainstorming |
| **Debug Assistant** | 🐛 | Debugging expert | Troubleshooting |
| **Data Analyst** | 📊 | Data analysis | Data work |
| **DevOps Engineer** | ⚙️ | Infrastructure | DevOps, deployment |
| **Security Expert** | 🔒 | Cybersecurity | Security audits |
| **SQL Expert** | 🗄️ | Database | SQL queries |
| **CLI Expert** | ⚡ | Command-line | Shell scripts |
| **API Designer** | 🌐 | API design | API development |
| **Concise Mode** | ⚡ | Brief responses | Quick answers |
| **Detailed Mode** | 📖 | Comprehensive | Deep explanations |
| **ELI5** | 🧒 | Simple explanations | Beginners |
| **Socratic Method** | ❓ | Teaching via questions | Critical thinking |

### How to Use

1. **Select a Preset**
   - Click any preset card
   - System prompt is automatically loaded

2. **Customize**
   - Edit the system prompt text area
   - Add your own modifications

3. **Create Custom Presets**
   - Type directly in the text area
   - Save for future use

### Example Prompts

**Code Expert:**
```
You are an expert programmer and code reviewer. Provide clean,
well-documented code with best practices. Explain your reasoning
and suggest optimizations. Consider edge cases and potential
security issues.
```

**ELI5:**
```
Explain concepts using simple language, everyday analogies, and
relatable examples. Avoid jargon and break down complex ideas
into easy-to-understand pieces. Assume no prior knowledge.
```

### File Location

Presets are stored in:
```
packages/browseros/browseros/presets/system_prompts.json
```

Custom format:
```json
{
  "id": "your_preset",
  "name": "Your Preset Name",
  "description": "Short description",
  "icon": "🎯",
  "category": "custom",
  "prompt": "Your system prompt here..."
}
```

---

## Chat Template Presets

### Overview

Different LLM models use different chat formats. Choose the right template for your model to ensure proper formatting.

### Why This Matters

**Wrong template:**
```
User: Hello
Assistant: Hi there!
```

**Correct template (Llama 3):**
```
<|start_header_id|>user<|end_header_id|>

Hello<|eot_id|><|start_header_id|>assistant<|end_header_id|>

Hi there!<|eot_id|>
```

### Available Templates

| Template | Icon | Model Family | Format |
|----------|------|--------------|--------|
| **ChatML** | 💬 | GPT-3.5/4, Orca | `<\|im_start\|>...<\|im_end\|>` |
| **Llama 2** | 🦙 | Meta Llama 2 | `[INST] ... [/INST]` |
| **Llama 3** | 🦙 | Meta Llama 3 | `<\|start_header_id\|>...<\|eot_id\|>` |
| **Mistral** | 🌬️ | Mistral, Mixtral | `[INST] ... [/INST]` |
| **Alpaca** | 🦙 | Alpaca models | `### Instruction: ... ### Response:` |
| **Vicuna** | 🦙 | Vicuna models | `USER: ... ASSISTANT:` |
| **Gemma** | 💎 | Google Gemma | `<start_of_turn>user...<end_of_turn>` |
| **Phi-3** | Φ | Microsoft Phi | `<\|user\|>...<\|assistant\|>` |
| **Command R** | ⚡ | Cohere Command R | `<\|USER_TOKEN\|>...<\|CHATBOT_TOKEN\|>` |
| **Zephyr** | 💨 | HF Zephyr | `<\|user\|>...<\|assistant\|>` |
| **OpenChat** | 💬 | OpenChat | `GPT4 User: ... GPT4 Assistant:` |
| **DeepSeek** | 🔍 | DeepSeek | `User: ... Assistant:` |
| **Qwen** | 🐉 | Alibaba Qwen | `<\|im_start\|>user...<\|im_end\|>` |
| **Solar** | ☀️ | Upstage Solar | `### User: ... ### Assistant:` |
| **Custom** | ⚙️ | Your own | Define your own format |

### How to Use

1. **Select Template Matching Your Model**
   - Click the template card
   - Template is applied automatically

2. **For Custom Models**
   - Select "Custom Format"
   - Define your own tokens

### Template Structure

Each template defines:
```json
{
  "bos_token": "<|begin_of_text|>",
  "eos_token": "<|eot_id|>",
  "system_template": "<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>",
  "user_template": "<|start_header_id|>user<|end_header_id|>\n\n{message}<|eot_id|>",
  "assistant_template": "<|start_header_id|>assistant<|end_header_id|>\n\n{message}<|eot_id|>",
  "assistant_prefix": "<|start_header_id|>assistant<|end_header_id|>\n\n"
}
```

### File Location

Templates are stored in:
```
packages/browseros/browseros/presets/chat_templates.json
```

---

## Advanced Sampling Parameters

### Overview

Fine-tune the model's output generation behavior with precise control over sampling parameters.

### Parameters

#### Temperature (0.0 - 2.0)
**What it does:** Controls randomness in output

- **0.0**: Deterministic, always picks most likely token
- **0.7**: Balanced (default)
- **1.5**: Very creative, more random
- **2.0**: Maximum creativity

**Use cases:**
- **Low (0.1-0.3)**: Code generation, factual answers, math
- **Medium (0.6-0.9)**: General chat, balanced responses
- **High (1.2-2.0)**: Creative writing, brainstorming

**Example:**
```python
# Code generation
temperature = 0.2

# Creative story
temperature = 1.5
```

#### Top P - Nucleus Sampling (0.0 - 1.0)
**What it does:** Considers only top tokens with cumulative probability up to P

- **0.1**: Very narrow selection
- **0.9**: Balanced (default)
- **1.0**: Consider all tokens

**How it works:**
```
Tokens sorted by probability:
1. "hello" - 40%
2. "hi"    - 30%
3. "hey"   - 15%
4. "greetings" - 10%
5. "yo"    - 5%

Top P = 0.9:
  Cumulative: 40% + 30% + 15% + 10% = 95%
  ✓ Includes tokens 1-4
  ✗ Excludes token 5 ("yo")
```

#### Min P (0.0 - 1.0)
**What it does:** Minimum probability threshold for token selection

- **0.0**: No minimum (allow all)
- **0.05**: Standard (default)
- **0.2**: Stricter filtering

**Difference from Top P:**
- **Top P**: "Include tokens until cumulative reaches P"
- **Min P**: "Include only tokens above minimum probability"

**Example:**
```
Token probabilities:
- "the" - 0.40
- "a"   - 0.30
- "an"  - 0.20
- "this" - 0.08
- "that" - 0.02

Min P = 0.05:
  ✓ "the" (0.40)
  ✓ "a" (0.30)
  ✓ "an" (0.20)
  ✓ "this" (0.08)
  ✗ "that" (0.02) - Below threshold
```

#### Repeat Penalty (1.0 - 2.0)
**What it does:** Penalizes repeated tokens to reduce repetition

- **1.0**: No penalty
- **1.1**: Light penalty (default)
- **1.5**: Strong penalty

**How it works:**
```
Token appears in context:
  New probability = Original probability / Repeat penalty

Example with penalty 1.5:
  "hello" probability: 0.30
  If "hello" already used:
    New probability: 0.30 / 1.5 = 0.20
```

**Use cases:**
- **Low (1.0-1.1)**: Poems, code (repetition OK)
- **High (1.3-1.8)**: Avoid repetitive text

#### Maximum Response Length

**Tokens vs Words:**
- 1 token ≈ 0.75 words (English)
- 100 tokens ≈ 75 words
- 1000 tokens ≈ 750 words

**Common values:**
- **256**: Short answer
- **512**: Paragraph
- **2048**: Page (default)
- **4096**: Multiple pages
- **8192**: Long document

### Parameter Combinations

**Precise Code Generation:**
```
Temperature: 0.1
Top P: 0.9
Min P: 0.1
Repeat Penalty: 1.0
Max Tokens: 1024
```

**Balanced Chat:**
```
Temperature: 0.7
Top P: 0.9
Min P: 0.05
Repeat Penalty: 1.1
Max Tokens: 2048
```

**Creative Writing:**
```
Temperature: 1.3
Top P: 0.95
Min P: 0.02
Repeat Penalty: 1.2
Max Tokens: 4096
```

**Factual Q&A:**
```
Temperature: 0.3
Top P: 0.85
Min P: 0.1
Repeat Penalty: 1.0
Max Tokens: 512
```

---

## System Monitoring

### Overview

Real-time visualization of system resource usage during inference.

### Metrics Displayed

| Metric | Description | Warning Threshold |
|--------|-------------|-------------------|
| **CPU Usage** | CPU utilization % | > 80% |
| **RAM Usage** | Memory utilization % | > 80% |
| **GPU Usage** | GPU compute % | > 90% |
| **GPU Memory** | VRAM usage % | > 90% |

### Visual Indicators

- **Blue bar**: Normal usage (< 70%)
- **Orange bar**: High usage (70-90%)
- **Red bar**: Critical usage (> 90%)

### How It Works

**Native Integration:**
```python
# System stats are polled every 2 seconds
cpu_percent = psutil.cpu_percent(interval=1)
ram_percent = psutil.virtual_memory().percent

# GPU stats (if NVIDIA GPU present)
import pynvml
pynvml.nvmlInit()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
gpu_util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(handle).used / total * 100
```

**Browser Integration:**
```javascript
// Update monitor displays
function updateMonitor(type, percentage) {
  document.getElementById(`${type}Value`).textContent = `${percentage}%`;
  document.getElementById(`${type}Bar`).style.width = `${percentage}%`;
}

// Called every 2 seconds
setInterval(() => {
  fetch('/api/system/stats')
    .then(r => r.json())
    .then(stats => {
      updateMonitor('cpu', stats.cpu);
      updateMonitor('ram', stats.ram);
      updateMonitor('gpu', stats.gpu);
      updateMonitor('vram', stats.vram);
    });
}, 2000);
```

### Why This Matters

**Identify Bottlenecks:**
- High GPU usage → GPU bound
- High RAM usage → May need quantization
- High CPU usage → Pre/post-processing bottleneck

**Optimize Performance:**
```
If VRAM 95%:
  → Use smaller model
  → Use more aggressive quantization (Q4 instead of Q8)
  → Reduce context window

If CPU 90% but GPU 20%:
  → Bottleneck in tokenization
  → Consider batch processing
```

---

## ChatGPT Custom API

### Problem Solved

ChatGPT's API has specific requirements that differ from generic OpenAI-compatible APIs. Previously, users had to:
- Manually format requests correctly
- Handle authentication properly
- Deal with response parsing
- Manage errors and retries

### Solution

**Plug-and-play ChatGPT API handler** with proper OpenAI formatting!

### Features

- ✅ Proper authentication headers
- ✅ Correct message formatting
- ✅ Response parsing
- ✅ Error handling
- ✅ Streaming support (coming soon)
- ✅ Model listing
- ✅ Usage tracking

### Quick Start

```python
from browseros.api import ChatGPTHandler
import os

api_key = os.getenv("OPENAI_API_KEY")

async with ChatGPTHandler(api_key) as chatgpt:
    response = await chatgpt.simple_chat(
        prompt="What is the capital of France?",
        model="gpt-4o",
    )
    print(response)
    # Output: "The capital of France is Paris."
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| **gpt-4o** | 128K | Latest, most capable |
| **gpt-4o-mini** | 128K | Fast, cost-effective |
| **gpt-4-turbo** | 128K | Advanced reasoning |
| **gpt-4** | 8K | High quality |
| **gpt-3.5-turbo** | 16K | Fast, cheap |

### Advanced Usage

#### Multi-turn Conversation

```python
async with ChatGPTHandler(api_key) as chatgpt:
    # Start conversation
    messages = chatgpt.format_messages(
        user_prompt="Hello, I'd like to learn about Python",
        system_prompt="You are a patient Python teacher.",
    )

    # First response
    response1 = await chatgpt.chat(messages, model="gpt-4o")
    print(f"Assistant: {response1.get_message()}")

    # Continue conversation
    messages.append({"role": "assistant", "content": response1.get_message()})
    messages.append({"role": "user", "content": "Can you show me an example?"})

    response2 = await chatgpt.chat(messages, model="gpt-4o")
    print(f"Assistant: {response2.get_message()}")
```

#### With Custom Parameters

```python
response = await chatgpt.chat(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a poem about coding."}
    ],
    model="gpt-4o",
    temperature=1.2,          # More creative
    top_p=0.95,
    max_tokens=500,
    presence_penalty=0.6,     # Encourage new topics
    frequency_penalty=0.5,    # Reduce repetition
)
```

#### List Available Models

```python
async with ChatGPTHandler(api_key) as chatgpt:
    models = await chatgpt.list_models()

    print("Available models:")
    for model in models:
        print(f"  - {model['id']}")
```

#### Get Model Info

```python
model_info = await chatgpt.get_model_info("gpt-4o")
print(f"Model: {model_info['id']}")
print(f"Owner: {model_info['owned_by']}")
print(f"Created: {model_info['created']}")
```

### Response Object

```python
response = await chatgpt.chat(messages, model="gpt-4o")

# Get the message
message = response.get_message()

# Get finish reason
finish_reason = response.get_finish_reason()
# Values: "stop", "length", "content_filter"

# Get usage stats
usage = response.usage
print(f"Prompt tokens: {usage['prompt_tokens']}")
print(f"Completion tokens: {usage['completion_tokens']}")
print(f"Total tokens: {usage['total_tokens']}")
```

### Error Handling

```python
try:
    response = await chatgpt.chat(messages, model="gpt-4o")
except Exception as e:
    if "rate_limit" in str(e):
        print("Rate limit exceeded. Wait and retry.")
    elif "invalid_api_key" in str(e):
        print("Invalid API key. Check your key.")
    elif "context_length_exceeded" in str(e):
        print("Context too long. Reduce message history.")
    else:
        print(f"Error: {e}")
```

### Cost Optimization

```python
# Use cheaper model for simple tasks
simple_response = await chatgpt.simple_chat(
    prompt="What is 2+2?",
    model="gpt-4o-mini",  # Much cheaper
)

# Use gpt-4o for complex reasoning
complex_response = await chatgpt.simple_chat(
    prompt="Explain quantum entanglement",
    model="gpt-4o",  # Better quality
)
```

### Integration with BrowserOS

The ChatGPT handler is automatically used when you select "OpenAI" as your provider type in settings.

**Settings Configuration:**
```json
{
  "type": "openai",
  "name": "ChatGPT",
  "baseUrl": "https://api.openai.com/v1",
  "apiKey": "sk-...",
  "modelId": "gpt-4o"
}
```

---

## Complete Example

Here's a complete example using all features together:

```python
import asyncio
from browseros.api import (
    ModelDiscovery,
    ChatGPTHandler,
    EnhancedAPIClient
)

async def main():
    # 1. Discover local models
    async with ModelDiscovery() as discovery:
        backends = await discovery.discover_all()
        ollama_models = [
            model.model_id
            for backend in backends
            if backend.name == "Ollama" and backend.is_available
            for model in backend.models
        ]
        print(f"Found {len(ollama_models)} Ollama models")

    # 2. Use ChatGPT for planning
    async with ChatGPTHandler(api_key) as chatgpt:
        plan = await chatgpt.simple_chat(
            prompt="Create a plan for building a web app",
            system_prompt="You are a software architect.",
            model="gpt-4o",
            temperature=0.7,
        )
        print(f"Plan: {plan}")

    # 3. Use local model for implementation
    async with EnhancedAPIClient("http://localhost:11434") as client:
        # Ollama API call
        response = await client.post("/api/generate", data={
            "model": ollama_models[0],
            "prompt": f"Implement this plan:\n{plan}",
            "stream": False,
            "options": {
                "temperature": 0.3,  # More focused for code
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            }
        })
        print(f"Implementation: {response['response']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### Model Discovery Issues

**Problem:** No models found

**Solutions:**
1. Check backend is running: `curl http://localhost:11434/api/tags`
2. Verify URL is correct
3. Check firewall settings
4. Try different timeout (increase from 2s to 5s)

### ChatGPT API Errors

**Rate Limit Error:**
```python
# Implement exponential backoff
import time

for attempt in range(5):
    try:
        response = await chatgpt.chat(messages)
        break
    except Exception as e:
        if "rate_limit" in str(e):
            wait_time = 2 ** attempt
            print(f"Rate limited. Waiting {wait_time}s...")
            await asyncio.sleep(wait_time)
        else:
            raise
```

**Context Length Error:**
```python
# Truncate old messages
max_context = 4000
while sum(len(m['content']) for m in messages) > max_context:
    messages.pop(1)  # Remove oldest user message (keep system)
```

### System Monitoring Not Working

Check dependencies:
```bash
pip install psutil pynvml
```

For GPU monitoring (NVIDIA only):
```bash
# Install CUDA toolkit
# Then: pip install pynvml
```

---

## File Locations

```
packages/browseros/
├── browseros/
│   ├── api/
│   │   ├── model_discovery.py      # Model discovery
│   │   ├── chatgpt_handler.py      # ChatGPT API
│   │   └── enhanced_client.py      # HTTP client
│   └── presets/
│       ├── system_prompts.json     # System prompts
│       └── chat_templates.json     # Chat templates
└── resources/
    └── advanced_settings_panel.html # Settings UI
```

---

## Related Documentation

- [Enhanced API Client](./enhanced-api-client.md) - API performance features
- [Log Viewer](./log-viewer.md) - Debugging and monitoring
- [Voice Interaction](./voice-interaction.md) - Voice input
- [File Upload](./file-upload.md) - File and image uploads

---

## Changelog

### Version 1.1.0 (2026-01-16)

**New Features:**
- ✨ Model discovery for Ollama, LM Studio, vLLM, Text Generation WebUI
- ✨ 20 system prompt presets
- ✨ 15 chat template presets (Llama, Mistral, Gemma, etc.)
- ✨ Advanced sampling parameters (temperature, top_p, min_p, repeat penalty)
- ✨ Real-time system monitoring (CPU, RAM, GPU, VRAM)
- ✨ ChatGPT custom API handler with proper OpenAI formatting

**Improvements:**
- 🎯 No more manual model ID copy-paste
- 🎯 Automatic backend detection
- 🎯 Model metadata display (size, quantization)
- 🎯 Plug-and-play ChatGPT integration
- 🎯 Visual resource monitoring

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting)
2. Review example code
3. Submit issue on GitHub with:
   - Backend type and version
   - Error messages
   - Steps to reproduce
   - System info (OS, Python version)

---

**Note:** All features work with both local backends (Ollama, LM Studio) and cloud APIs (ChatGPT, Claude, Gemini). Choose what works best for your use case!
