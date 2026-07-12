import json
import os.path
from pathlib import Path

import yaml

from utils.file_utils import get_current_path

# Module-level global variables, effective after calling init_config()
config: dict = {}
downloader_config: dict | None = None
i18n_config: dict | None = None


# Load yaml configuration
def load_yaml_config(file_path: str) -> dict:
    config_path = Path(file_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json_config(file_path: str) -> dict or None:
    file_path = Path(file_path)
    if not file_path.exists():
        return None
    content = file_path.read_text(encoding="utf-8")
    return json.loads(content)


def init_config():
    global config
    config_path = os.path.join(get_current_path(), "config.yaml")
    config = load_yaml_config(config_path)
    global downloader_config
    downloader_config_path = os.path.join(get_current_path(), "downloader.json")
    downloader_config = load_json_config(downloader_config_path)
    global i18n_config
    i18n_config_path = os.path.join(get_current_path(), "i18n.json")
    i18n_config = load_json_config(i18n_config_path)
