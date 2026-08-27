from dataclasses import dataclass


@dataclass
class AsrBean:
    url: str = ""
    """ 生成的字幕文件，绝对地址 """
    subtitle_path: str = ""
