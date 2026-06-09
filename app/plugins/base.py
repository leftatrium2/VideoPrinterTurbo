"""Plugin abstraction layer — base classes, registry, and type enums.

Each pipeline stage is a separate *plugin type*. Concrete implementations
register themselves via PluginRegistry so the pipeline can discover them
by type and name, configured through config.toml.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class PluginType(str, Enum):
    """All supported plugin extension points."""
    DOWNLOADER = "downloader"
    TRANSCRIBER = "transcriber"
    LLM = "llm"
    MATERIAL = "material"
    PUBLISHER = "publisher"


class BasePlugin(ABC):
    """Abstract base for every plugin.

    Subclasses MUST set ``type`` and ``name`` as class attributes.

    Example::

        class YtDlpDownloader(BaseDownloader):
            type = PluginType.DOWNLOADER
            name = "yt-dlp"
    """

    type: PluginType
    name: str

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Auto-register subclasses when they define type and name
        if hasattr(cls, "type") and hasattr(cls, "name") and cls.type and cls.name:
            PluginRegistry.register(cls)

    @abstractmethod
    def validate_config(self) -> bool:
        """Verify the plugin's configuration is usable (e.g. API key set)."""
        ...


class PluginRegistry:
    """Global plugin registry — each plugin auto-registers on subclass creation.

    Usage:

        # Access a specific plugin by type + name
        dl = PluginRegistry.get(PluginType.DOWNLOADER, "yt-dlp")

        # Get the configured default for a plugin type
        dl = PluginRegistry.get_default(PluginType.DOWNLOADER)

        # List all available plugins of a type
        all_dl = PluginRegistry.list_plugins(PluginType.DOWNLOADER)
    """

    _plugins: dict[PluginType, dict[str, type[BasePlugin]]] = {}

    @classmethod
    def register(cls, plugin_cls: type[BasePlugin]) -> None:
        """Register a plugin class (called automatically on subclass creation)."""
        if plugin_cls.type not in cls._plugins:
            cls._plugins[plugin_cls.type] = {}
        cls._plugins[plugin_cls.type][plugin_cls.name] = plugin_cls

    @classmethod
    def get(cls, plugin_type: PluginType, name: str) -> type[BasePlugin] | None:
        """Look up a plugin class by type and name."""
        return cls._plugins.get(plugin_type, {}).get(name)

    @classmethod
    def get_default(cls, plugin_type: PluginType, default_name: str = "") -> type[BasePlugin] | None:
        """Get the default plugin for a type — uses ``default_name`` if provided,
        otherwise returns the first registered one."""
        plugins = cls._plugins.get(plugin_type, {})
        if not plugins:
            return None
        if default_name and default_name in plugins:
            return plugins[default_name]
        # Fall back to first available
        return next(iter(plugins.values()))

    @classmethod
    def list_plugins(cls, plugin_type: PluginType) -> list[str]:
        """List all registered plugin names for a type."""
        return list(cls._plugins.get(plugin_type, {}).keys())

    @classmethod
    def new(cls, plugin_type: PluginType, name: str, **kwargs) -> BasePlugin | None:
        """Instantiate a plugin by type and name, passing ``**kwargs``."""
        plugin_cls = cls.get(plugin_type, name)
        if plugin_cls is None:
            return None
        return plugin_cls(**kwargs)

    @classmethod
    def new_default(cls, plugin_type: PluginType, **kwargs) -> BasePlugin | None:
        """Instantiate the default plugin for a type."""
        plugin_cls = cls.get_default(plugin_type)
        if plugin_cls is None:
            return None
        return plugin_cls(**kwargs)
