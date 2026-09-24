from dataclasses import dataclass


@dataclass
class LLMBean:
    llm_text: str = ""
    llm_full_path: str = ""

    def __str__(self) -> str:
        return f"""
        LLMBean(
            llm_text: {self.llm_text}, 
            llm_full_path: {self.llm_full_path}
        )
        """
