import asyncio
import os.path

from openai import OpenAI

from config.config import init_config
from pipeline.llm.base import BaseLLMProvider
from pipeline.llm.llm_utils import LLMUtils
from pipeline.llm.subtitle_utils import SubTitleUtils
from utils.file_utils import get_subtitle_path, get_llm_rewrite_path


class OpenAIProvider(BaseLLMProvider):
    __base_url = None
    __api_key = None
    __model = None

    def config(self, api_key: str, base_url: str, model: str):
        self.__base_url = base_url
        self.__api_key = api_key
        self.__model = model

    def rewrite(self, text: str, src_path: str, dst_path: str):
        client = OpenAI(
            api_key=self.__api_key,
            base_url=self.__base_url,
        )
        subtitles = SubTitleUtils.parse_srt(src_path)
        #  batch_size 怎么定
        # 太大容易超 context 或者模型漏译/漏返回；
        # 太小请求次数多、成本高。
        # 中文字幕一般每批 30~80 条比较稳，长字幕（每条很多字）适当调小。
        dst_subtitles = LLMUtils.rewrite_srt(
            client, model, subtitles, text, batch_size=50
        )
        SubTitleUtils.write_srt(dst_subtitles, dst_path)


if __name__ == "__main__":
    init_config()
    llm_path = asyncio.run(get_llm_rewrite_path())
    apikey = "sk-ab80cf21b3884471aa20ce8613fcbd7b"
    baseurl = "https://api.deepseek.com"
    model = "deepseek-v4-pro"
    subtitle_path = asyncio.run(get_subtitle_path())
    src_path = os.path.join(subtitle_path, "gSNFJbgoaHI.cs.srt")
    llm: BaseLLMProvider = OpenAIProvider()
    llm.config(apikey, baseurl, model)
    llm_path = os.path.join(llm_path, "gSNFJbgoaHI.cn.srt")
    llm.rewrite("将当前的字幕翻译为中文", src_path, llm_path)
    print(llm_path)
