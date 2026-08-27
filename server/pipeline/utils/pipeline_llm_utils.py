from pipeline.llm.base import BaseLLMProvider
from pipeline.llm.openai_provider import OpenAIProvider


def llm_rewrite(text: str, src_path: str, dst_path: str,
                config: dict) -> bool:
    if 'api_key' not in config or 'base_url' not in config or 'model' not in config:
        return False
    llm: BaseLLMProvider = OpenAIProvider()
    api_key = config['api_key']
    base_url = config['base_url']
    model = config['model']
    llm.config(api_key, base_url, model)
    llm.rewrite(text, src_path, dst_path)
    return True
