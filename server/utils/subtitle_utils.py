import asyncio

from utils.config_utils import get_subtitle_font_list
import config.config as _config

g_font_list = []


def get_local_font() -> list:
    global g_font_list
    if len(g_font_list) == 0:
        g_font_list = asyncio.run(get_subtitle_font_list())
    return g_font_list


if __name__ == "__main__":
    _config.init_config()
    print(get_local_font())
