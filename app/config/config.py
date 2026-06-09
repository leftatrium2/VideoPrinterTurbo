"""Configuration loader — reads config.toml and exposes typed settings."""

import os
import shutil
import socket
from dataclasses import dataclass, field
from typing import Any

import toml
from loguru import logger


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
config_file = f"{root_dir}/config.toml"


@dataclass
class AppConfig:
    """Application-level settings from [app] section."""

    listen_host: str = "0.0.0.0"
    listen_port: int = 8080
    log_level: str = "DEBUG"
    project_name: str = "VideoPrinterTurbo"
    project_version: str = "0.1.0"

    # LLM provider
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model_name: str = "gpt-4o-mini"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model_name: str = "deepseek-chat"
    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-2.5-flash"

    # Video downloader
    downloader_provider: str = "yt-dlp"
    downloads_dir: str = ""

    # Transcriber
    transcriber_provider: str = "whisper"

    # Subtitle
    subtitle_provider: str = "edge"

    # Material search
    material_provider: str = "pexels"
    pexels_api_keys: list[str] = field(default_factory=list)
    pixabay_api_keys: list[str] = field(default_factory=list)
    tls_verify: bool = True

    # TTS
    edge_tts_timeout: int = 30

    # Publisher
    upload_post_enabled: bool = False
    upload_post_api_key: str = ""
    upload_post_username: str = ""
    upload_post_platforms: list[str] = field(default_factory=lambda: ["tiktok", "instagram"])
    upload_post_auto_upload: bool = False

    # Redis (optional)
    enable_redis: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # Task queue
    max_concurrent_tasks: int = 5
    max_queued_tasks: int = 100

    # Endpoint for generated file URLs
    endpoint: str = ""

    # Raw dict for dynamic access
    _raw: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self._raw.get(key, default)


@dataclass
class WhisperConfig:
    model_size: str = "large-v3"
    device: str = "cpu"
    compute_type: str = "int8"


@dataclass
class ProxyConfig:
    http: str = ""
    https: str = ""


@dataclass
class UIConfig:
    hide_log: bool = False
    subtitle_position: str = "bottom"
    custom_position: float = 70.0
    language: str = ""


class Config:
    """Global configuration — loaded once from config.toml."""

    app: AppConfig
    whisper: WhisperConfig
    proxy: ProxyConfig
    ui: UIConfig

    def __init__(self, data: dict):
        self.app = AppConfig(**{k: v for k, v in data.get("app", {}).items() if k != "_raw"})
        self.app._raw = data.get("app", {})
        # Override from top-level keys (legacy support)
        self.app.listen_host = data.get("listen_host", self.app.listen_host)
        self.app.listen_port = data.get("listen_port", self.app.listen_port)
        self.app.log_level = data.get("log_level", self.app.log_level)
        self.app.project_name = data.get("project_name", self.app.project_name)
        self.app.project_version = data.get("project_version", self.app.project_version)

        self.whisper = WhisperConfig(**data.get("whisper", {}))
        self.proxy = ProxyConfig(**data.get("proxy", {}))
        self.ui = UIConfig(**data.get("ui", {}))

        # Apply env overrides
        self.app.redis_host = os.getenv(
            "VPT_REDIS_HOST",
            os.getenv("REDIS_HOST", self.app.redis_host),
        )

        logger.info(f"{self.app.project_name} v{self.app.project_version}")

    @classmethod
    def load(cls) -> "Config":
        if os.path.isdir(config_file):
            shutil.rmtree(config_file)

        if not os.path.isfile(config_file):
            example_file = f"{root_dir}/config.example.toml"
            if os.path.isfile(example_file):
                shutil.copyfile(example_file, config_file)
                logger.info("copied config.example.toml → config.toml")

        logger.info(f"load config from: {config_file}")
        try:
            data = toml.load(config_file)
        except Exception as e:
            logger.warning(f"load config failed: {e}, trying utf-8-sig")
            with open(config_file, encoding="utf-8-sig") as fp:
                data = toml.loads(fp.read())

        return cls(data)
