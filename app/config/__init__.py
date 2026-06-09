"""Configuration module - loads config.toml into a global config object."""
from app.config.config import Config

config = Config.load()
