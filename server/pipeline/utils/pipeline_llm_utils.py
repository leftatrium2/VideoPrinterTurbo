import asyncio
import os.path
from pathlib import Path

import config.config as _config
from pipeline.llm.base import BaseLLMProvider
from pipeline.llm.openai_provider import OpenAIProvider
from pipeline.utils.pipeline_video_downloader_utils import init_downloader
from utils.file_utils import get_llm_rewrite_path


def llm_rewrite(prompt: str, src_path: str, dst_path: str,
                **args) -> bool:
    api_key = args.get("api_key")
    base_url = args.get("base_url")
    model = args.get("model")
    llm: BaseLLMProvider = OpenAIProvider(
        api_key, base_url, model
    )
    return llm.rewrite(prompt, src_path, dst_path)


if __name__ == "__main__":
    _config.init_config()
    init_downloader()
    src_path = "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/storage/video_to_text/20260720215545133997.srt"
    src = Path(src_path).expanduser().resolve()
    dst_path = asyncio.run(get_llm_rewrite_path())
    dst_path = os.path.join(dst_path, src.name)

    llm_rewrite(
        prompt="翻译为中文",
        src_path=src_path,
        dst_path=dst_path,
        api_key="",
        base_url="https://api.deepseek.com",
        model="deepseek-flash"
    )
