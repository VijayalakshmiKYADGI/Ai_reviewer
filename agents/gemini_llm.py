import os
from typing import Any, List, Optional, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
import google.generativeai as genai
from pydantic import Field
import structlog

logger = structlog.get_logger()

class GeminiLLM(BaseChatModel):
    """Custom wrapper for Google Gemini API to satisfy CrewAI/LangChain interface."""
    
    model_name: str = "gemini-1.5-pro"
    temperature: float = 0.1
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.api_key:
            genai.configure(api_key=self.api_key)
            
    @property
    def _llm_type(self) -> str:
        return "gemini-custom"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        try:
            model = genai.GenerativeModel(self.model_name)
            
            # Simple prompt construction
            # Ideally we map messages to Gemini history, but simple string prompt works for agents usually
            prompt_parts = []
            
            for m in messages:
                if isinstance(m, SystemMessage):
                    prompt_parts.append(f"System: {m.content}\n")
                elif isinstance(m, HumanMessage):
                    prompt_parts.append(f"User: {m.content}\n")
                elif isinstance(m, AIMessage):
                    prompt_parts.append(f"Model: {m.content}\n")
                else:
                    prompt_parts.append(f"{m.content}\n")
            
            full_prompt = "\n".join(prompt_parts)
            
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                stop_sequences=stop if stop else []
            )
            
            response = model.generate_content(full_prompt, generation_config=generation_config)
            
            # handle safety blocks or empty response
            text = response.text if response.parts else ""
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=text))])
            
        except Exception as e:
            logger.error("gemini_generation_failed", error=str(e))
            # Return empty or error message to avoid crash
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"Error: {str(e)}"))])

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}
