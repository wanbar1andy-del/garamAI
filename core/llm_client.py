"""
GARAM LLM Client - GPT-OSS 로컬 모델 통신 래퍼

GPT-OSS (로컬 LLM)와의 통신을 단일 인터페이스로 추상화.
모델 변경 시 이 파일만 수정하면 전체 시스템에 반영됨.

지원 백엔드:
- Ollama (http://localhost:11434/api/generate)
- LM Studio (http://localhost:1234/v1/chat/completions)
- 기타 OpenAI 호환 API
"""

import requests
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class LLMClient:
    """
    로컬 LLM 통신 클라이언트
    
    장중 사용 시 타임아웃을 짧게 설정하여
    의사결정 지연을 최소화합니다.
    """
    
    def __init__(
        self,
        endpoint: str = "http://localhost:11434/api/generate",
        model: str = "llama3.2:1b",
        timeout: float = 5.0,
        backend: str = "ollama"
    ):
        """
        Args:
            endpoint: LLM API 엔드포인트
            model: 모델 이름
            timeout: 타임아웃 (초) - 장중용은 짧게 (5초)
            backend: 백엔드 타입 ("ollama", "lmstudio", "openai")
        """
        self.endpoint = endpoint
        self.model = model
        self.timeout = timeout
        self.backend = backend
        
        logger.info(f"LLMClient initialized: {backend} @ {endpoint}, model={model}, timeout={timeout}s")
    
    def ask_gpt_oss(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        GPT-OSS에게 질문하고 응답 받기
        
        Args:
            prompt: 사용자 프롬프트
            max_tokens: 최대 토큰 수
            temperature: 온도 (0.0 ~ 1.0, 낮을수록 결정적)
            system_prompt: 시스템 프롬프트 (선택)
        
        Returns:
            LLM 응답 텍스트
        
        Raises:
            TimeoutError: 타임아웃 발생
            ConnectionError: 연결 실패
        """
        try:
            if self.backend == "ollama":
                return self._ask_ollama(prompt, max_tokens, temperature, system_prompt)
            elif self.backend == "lmstudio":
                return self._ask_lmstudio(prompt, max_tokens, temperature, system_prompt)
            elif self.backend == "openai":
                return self._ask_openai_compatible(prompt, max_tokens, temperature, system_prompt)
            else:
                raise ValueError(f"Unsupported backend: {self.backend}")
        
        except requests.Timeout:
            logger.error(f"LLM request timeout ({self.timeout}s)")
            raise TimeoutError(f"LLM request timeout after {self.timeout}s")
        
        except requests.ConnectionError as e:
            logger.error(f"LLM connection error: {e}")
            raise ConnectionError(f"Failed to connect to LLM at {self.endpoint}")
        
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    def _ask_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """Ollama API 호출"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        return result.get("response", "")
    
    def _ask_lmstudio(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """LM Studio (OpenAI 호환) API 호출"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            self.endpoint,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _ask_openai_compatible(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        system_prompt: Optional[str]
    ) -> str:
        """OpenAI 호환 API 호출 (일반)"""
        return self._ask_lmstudio(prompt, max_tokens, temperature, system_prompt)
    
    def health_check(self) -> bool:
        """
        LLM 서버 헬스 체크
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = self.ask_gpt_oss(
                "Hello",
                max_tokens=10,
                temperature=0.0
            )
            logger.info(f"LLM health check OK: {response[:50]}")
            return True
        
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False


# 전역 LLM 클라이언트 인스턴스 (싱글톤 패턴)
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    전역 LLM 클라이언트 인스턴스 반환
    
    설정은 config.py 또는 환경변수에서 로드
    """
    global _llm_client
    
    if _llm_client is None:
        # TODO: config.py에서 설정 로드
        _llm_client = LLMClient(
            endpoint="http://localhost:11434/api/generate",
            model="llama3.2:1b",  # 기본값 (장중용 경량 모델)
            timeout=5.0,
            backend="ollama"
        )
    
    return _llm_client


# 편의 함수
def ask_gpt_oss(prompt: str, max_tokens: int = 512, temperature: float = 0.3) -> str:
    """
    GPT-OSS에게 질문 (전역 클라이언트 사용)
    
    Args:
        prompt: 프롬프트
        max_tokens: 최대 토큰
        temperature: 온도
    
    Returns:
        LLM 응답
    """
    client = get_llm_client()
    return client.ask_gpt_oss(prompt, max_tokens, temperature)


# 사용 예시
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 헬스 체크
    client = get_llm_client()
    if client.health_check():
        print("✅ LLM is healthy")
        
        # 테스트 질문
        response = ask_gpt_oss("What is 2+2?", max_tokens=50)
        print(f"Response: {response}")
    else:
        print("❌ LLM is not available")
