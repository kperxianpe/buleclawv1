#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 客户端 - 统一封装 OpenAI/Claude/Kimi
"""
import os
import json
import urllib.request
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    KIMI = "kimi"


@dataclass
class Message:
    role: str
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: Optional[str]


class LLMClient:
    """
    Unified LLM Client
    
    Supports OpenAI, Anthropic (Claude), and Kimi (Moonshot)
    """
    
    def __init__(
        self,
        provider: ModelProvider = None,
        model: str = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        # Auto-detect provider from env
        if provider is None:
            if os.getenv('KIMI_API_KEY'):
                provider = ModelProvider.KIMI
                model = model or 'moonshot-v1-8k'
            elif os.getenv('OPENAI_API_KEY'):
                provider = ModelProvider.OPENAI
                model = model or 'gpt-4'
            else:
                provider = ModelProvider.KIMI
                model = model or 'moonshot-v1-8k'
        
        self.provider = provider
        self.model = model or 'moonshot-v1-8k'
        self.api_key = api_key or self._get_api_key()
        self.base_url = base_url or self._get_base_url()
    
    def _get_api_key(self) -> str:
        if self.provider == ModelProvider.KIMI:
            return os.getenv('KIMI_API_KEY', '')
        elif self.provider == ModelProvider.OPENAI:
            return os.getenv('OPENAI_API_KEY', '')
        elif self.provider == ModelProvider.ANTHROPIC:
            return os.getenv('ANTHROPIC_API_KEY', '')
        return ''
    
    def _get_base_url(self) -> str:
        if self.provider == ModelProvider.KIMI:
            return os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
        elif self.provider == ModelProvider.OPENAI:
            return 'https://api.openai.com/v1'
        elif self.provider == ModelProvider.ANTHROPIC:
            return 'https://api.anthropic.com/v1'
        return ''
    
    def chat_completion(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> LLMResponse:
        """
        Synchronous chat completion
        
        For async, wrap with asyncio.to_thread
        """
        if self.provider == ModelProvider.KIMI:
            return self._kimi_completion(messages, temperature, max_tokens)
        elif self.provider == ModelProvider.OPENAI:
            return self._openai_completion(messages, temperature, max_tokens)
        else:
            raise NotImplementedError(f"Provider {self.provider} not implemented")
    
    def _kimi_completion(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """Kimi API call"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    finish_reason=data["choices"][0].get("finish_reason")
                )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"Kimi API error: {error_body}")
    
    def _openai_completion(
        self,
        messages: List[Message],
        temperature: float,
        max_tokens: int
    ) -> LLMResponse:
        """OpenAI API call"""
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                return LLMResponse(
                    content=data["choices"][0]["message"]["content"],
                    model=data.get("model", self.model),
                    usage=data.get("usage", {}),
                    finish_reason=data["choices"][0].get("finish_reason")
                )
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"OpenAI API error: {error_body}")


# Global client instance
llm_client = LLMClient()
