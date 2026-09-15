from dataclasses import dataclass


@dataclass
class LLMBean:
    llm_text: str = ""
    llm_path: str = ""
