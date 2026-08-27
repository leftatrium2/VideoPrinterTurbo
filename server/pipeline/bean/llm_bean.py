from dataclasses import dataclass


@dataclass
class LLMBean:
    url: str = ""
    llm_text: str = ""
