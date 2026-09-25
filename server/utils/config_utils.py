import asyncio
from pathlib import Path

import config.config as _config
from utils.file_utils import get_resource_font_path


async def get_subtitle_font_list():
    fonts_path = Path(get_resource_font_path())
    fonts = [p.name for p in fonts_path.iterdir() if p.suffix.lower() in (".ttf", ".ttc")]
    return fonts


if __name__ == "__main__":
    _config.init_config()
    print(asyncio.run(get_subtitle_font_list()))
