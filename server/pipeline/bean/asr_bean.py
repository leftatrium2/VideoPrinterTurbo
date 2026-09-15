from utils import const


class AsrBean:
    """ 当前选择的ASR类型 """
    audio_rewrite_type: int = const.PIPELINE_ERR_ASR_UNKNOWN

    """ 生成的字幕文件，绝对地址 """
    subtitle_path: str = ""
