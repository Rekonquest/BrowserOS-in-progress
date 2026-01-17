"""
ChatGPT Custom API Handler

Provides plug-and-play ChatGPT API support with proper OpenAI API formatting.
Handles all the OpenAI-specific requirements that differ from generic OpenAI-compatible APIs.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class ChatGPTModel(Enum):
    """Available ChatGPT models"""
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4 = "gpt-4"
    GPT_4_32K = "gpt-4-32k"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    # Latest models
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"


@dataclass
class ChatMessage:
    """Chat message format"""
    role: str  # "system", "user", or "assistant"
    content: str
    name: Optional[str] = None


@dataclass
class ChatGPTRequest:
    """ChatGPT API request format"""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    top_p: float = 0.9
    n: int = 1
    stream: bool = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request dict"""
        data = {
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "n": self.n,
            "stream": self.stream,
            "presence_penalty": self.presence_penalty,
            "frequency_penalty": self.frequency_penalty,
        }

        if self.stop:
            data["stop"] = self.stop
        if self.max_tokens:
            data["max_tokens"] = self.max_tokens
        if self.logit_bias:
            data["logit_bias"] = self.logit_bias
        if self.user:
            data["user"] = self.user

        return data


@dataclass
class ChatGPTResponse:
    """ChatGPT API response format"""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatGPTResponse':
        """Create from API response dict"""
        return cls(
            id=data.get("id", ""),
            object=data.get("object", ""),
            created=data.get("created", 0),
            model=data.get("model", ""),
            choices=data.get("choices", []),
            usage=data.get("usage", {}),
        )

    def get_message(self) -> str:
        """Extract the assistant's message"""
        if self.choices and len(self.choices) > 0:
            return self.choices[0].get("message", {}).get("content", "")
        return ""

    def get_finish_reason(self) -> str:
        """Get the finish reason"""
        if self.choices and len(self.choices) > 0:
            return self.choices[0].get("finish_reason", "")
        return ""


class ChatGPTHandler:
    """
    Handler for ChatGPT API with proper OpenAI formatting
    """

    BASE_URL = "https://api.openai.com/v1"

    def __init__(self, api_key: str, timeout: float = 60.0, debug: bool = False):
        """
        Initialize ChatGPT handler

        Args:
            api_key: OpenAI API key
            timeout: Request timeout in seconds
            debug: Enable debug logging
        """
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")

        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.timeout = timeout
        self.debug = debug
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def start(self):
        """Start the HTTP session"""
        if self.session is None:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            )

    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o",
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: Optional[int] = None,
        presence_penalty: float = 0.0,
        frequency_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
        stream: bool = False,
    ) -> ChatGPTResponse:
        """
        Send a chat completion request to ChatGPT

        Args:
            messages: List of chat messages
            model: Model to use (gpt-4o, gpt-4, gpt-3.5-turbo, etc.)
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Nucleus sampling parameter (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            presence_penalty: Presence penalty (-2.0 to 2.0)
            frequency_penalty: Frequency penalty (-2.0 to 2.0)
            stop: Stop sequences
            stream: Enable streaming (not yet implemented)

        Returns:
            ChatGPTResponse object
        """
        if not self.session:
            await self.start()

        request = ChatGPTRequest(
            model=model,
            messages=messages,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            presence_penalty=presence_penalty,
            frequency_penalty=frequency_penalty,
            stop=stop,
            stream=stream,
        )

        if self.debug:
            print(f"[ChatGPT] Request: {json.dumps(request.to_dict(), indent=2)}")

        try:
            async with self.session.post(
                f"{self.BASE_URL}/chat/completions",
                json=request.to_dict(),
            ) as response:
                response.raise_for_status()
                data = await response.json()

                if self.debug:
                    print(f"[ChatGPT] Response: {json.dumps(data, indent=2)}")

                return ChatGPTResponse.from_dict(data)

        except aiohttp.ClientError as e:
            raise Exception(f"ChatGPT API error: {str(e)}")

    async def simple_chat(
        self,
        prompt: str,
        model: str = "gpt-4o",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Simple chat interface (single prompt, single response)

        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for chat()

        Returns:
            Assistant's response as string
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await self.chat(messages, model=model, **kwargs)
        return response.get_message()

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models

        Returns:
            List of model information
        """
        if not self.session:
            await self.start()

        try:
            async with self.session.get(f"{self.BASE_URL}/models") as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("data", [])

        except aiohttp.ClientError as e:
            raise Exception(f"ChatGPT API error: {str(e)}")

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get information about a specific model

        Args:
            model_id: Model ID (e.g., "gpt-4")

        Returns:
            Model information dict
        """
        if not self.session:
            await self.start()

        try:
            async with self.session.get(f"{self.BASE_URL}/models/{model_id}") as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as e:
            raise Exception(f"ChatGPT API error: {str(e)}")

    def format_messages(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> List[Dict[str, str]]:
        """
        Format messages for ChatGPT API

        Args:
            user_prompt: Current user prompt
            system_prompt: Optional system prompt
            conversation_history: Optional conversation history

        Returns:
            Formatted messages list
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_prompt})

        return messages


# Example usage
async def main():
    """Example usage of ChatGPT handler"""
    import os

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    async with ChatGPTHandler(api_key, debug=True) as chatgpt:
        # Simple chat
        response = await chatgpt.simple_chat(
            prompt="What is the capital of France?",
            system_prompt="You are a helpful geography teacher.",
            model="gpt-4o",
        )
        print(f"Response: {response}")

        # Multi-turn conversation
        messages = chatgpt.format_messages(
            user_prompt="Hello, I'd like to learn about Python",
            system_prompt="You are a patient Python teacher.",
        )

        response1 = await chatgpt.chat(messages, model="gpt-4o")
        print(f"\nAssistant: {response1.get_message()}")

        messages.append({"role": "assistant", "content": response1.get_message()})
        messages.append({"role": "user", "content": "Can you show me a simple example?"})

        response2 = await chatgpt.chat(messages, model="gpt-4o")
        print(f"\nAssistant: {response2.get_message()}")

        # List models
        models = await chatgpt.list_models()
        print(f"\nAvailable models: {len(models)}")
        for model in models[:5]:
            print(f"  - {model.get('id')}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
