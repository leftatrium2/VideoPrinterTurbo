import asyncio
from pathlib import Path

from config.config import get_current_path
import config.config as _config


async def get_subtitle_font_list():
    fonts_path = Path(get_current_path()).resolve() / "server" / "resources" / "fonts"
    fonts = [p.name for p in fonts_path.iterdir() if p.suffix.lower() in (".ttf", ".ttc")]
    return fonts


if __name__ == "__main__":
    _config.init_config()
    print(asyncio.run(get_subtitle_font_list()))
