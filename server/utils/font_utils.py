from pathlib import Path
from typing import Optional

from fontTools.ttLib import TTFont
import config.config as _config


def get_font_params(font_path: str) -> Optional[tuple[str, Optional[str]]]:
    """
    从字体路径中获取字体名称和字体类型
    """
    font_full_path = Path(font_path).expanduser().resolve()
    if not font_full_path.is_file():
        return None
    font_full_dir = str(font_full_path.parent)
    font = TTFont(str(font_full_path))
    font_name = font['name'].getDebugName(1)
    font.close()
    return font_full_dir, font_name


if __name__ == "__main__":
    _config.init_config()
    print(get_font_params(
        "/Users/sunxiao5/opensource/agent/VideoPrinterTurbo/server/resources/fonts/NotoSansSC-Regular.ttf"))
