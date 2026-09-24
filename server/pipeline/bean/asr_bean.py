from pipeline.transcriber.subtitle.subtitle_transcriber import SubTitleTranscriber
from utils import const


class AsrBean:
    """ 当前选择的ASR类型 """
    audio_rewrite_type: int = const.TASK_CONFIG_ASR_FROM_NONE
    task_url: str = ""
    lang: int = 0

    """ 生成的字幕文件，绝对地址 """
    subtitle_full_path: str = ""

    def __convert_asr_type_to_str(self, asr_type: int) -> str:
        if asr_type == const.TASK_CONFIG_ASR_FROM_LOCAL_WHISPER:
            return "LOCAL WHISPER"
        elif asr_type == const.TASK_CONFIG_ASR_FROM_REMOTE_WHISPER:
            return "REMOTE WHISPER"
        elif asr_type == const.TASK_CONFIG_ASR_FROM_TENCENT_CLOUD:
            return "TENCENT CLOUD"
        elif asr_type == const.TASK_CONFIG_ASR_FROM_XF_YUN:
            return "XF YUN"
        elif asr_type == const.TASK_CONFIG_ASR_FROM_OPENAI:
            return "OPENAI"
        elif asr_type == const.TASK_CONFIG_ASR_FROM_AZURE:
            return "AZURE"
        elif asr_type == const.TASK_CONFIG_ASR_FROM_BYTEDANCE:
            return "BYTEDANCE"
        return "UNKNOWN"

    def __get_subtitle_lang(self, lang: int):
        return SubTitleTranscriber.get_subtitle_lang(lang)

    def __str__(self) -> str:
        return f"""
        AsrBean(
            audio_rewrite_type: {self.__convert_asr_type_to_str(self.audio_rewrite_type)}, 
            task_url: {self.task_url}, 
            lang: {self.__get_subtitle_lang(self.lang)}, 
            subtitle_path: {self.subtitle_full_path})
        """
