from pathlib import Path

import yaml


# 加载 yaml 配置
def load_yaml_config(file_path: str = "config.yaml") -> dict:
    config_path = Path(file_path)
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_yaml_config()
