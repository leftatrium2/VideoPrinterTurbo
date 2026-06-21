import json
import os.path
from pathlib import Path

import yaml

# 模块级全局变量，调用 init_config() 后生效
config: dict = {}
downloader_config: dict | None = None


# 加载 yaml 配置
def load_yaml_config(file_path: str = "config.yaml") -> dict:
    config_path = Path(file_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json_config(file_path: str = None) -> dict or None:
    if file_path is None:
        file_path = Path(__file__).parent.parent / "downloader.json"
    else:
        file_path = Path(file_path)
    if not file_path.exists():
        return None
    content = file_path.read_text(encoding="utf-8")
    return json.loads(content)


def init_config():
    global config
    config = load_yaml_config()
    global downloader_config
    downloader_config = load_json_config()
    print(downloader_config)
