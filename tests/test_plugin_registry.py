import pytest
from app.plugins.base import BasePlugin, PluginRegistry, PluginType


def test_subclass_auto_registers(isolated_registry):
    class _Stub(BasePlugin):
        type = PluginType.DOWNLOADER
        name = "stub-auto"
        def validate_config(self): return True

    assert PluginRegistry.get(PluginType.DOWNLOADER, "stub-auto") is _Stub


def test_get_returns_correct_plugin(isolated_registry):
    class _A(BasePlugin):
        type = PluginType.LLM
        name = "llm-a"
        def validate_config(self): return True

    class _B(BasePlugin):
        type = PluginType.LLM
        name = "llm-b"
        def validate_config(self): return True

    assert PluginRegistry.get(PluginType.LLM, "llm-a") is _A
    assert PluginRegistry.get(PluginType.LLM, "llm-b") is _B


def test_get_default_with_name(isolated_registry):
    class _X(BasePlugin):
        type = PluginType.MATERIAL
        name = "mat-x"
        def validate_config(self): return True

    class _Y(BasePlugin):
        type = PluginType.MATERIAL
        name = "mat-y"
        def validate_config(self): return True

    result = PluginRegistry.get_default(PluginType.MATERIAL, "mat-y")
    assert result is _Y


def test_get_default_without_name_returns_first(isolated_registry):
    PluginRegistry._plugins[PluginType.TRANSCRIBER] = {}

    class _First(BasePlugin):
        type = PluginType.TRANSCRIBER
        name = "first"
        def validate_config(self): return True

    class _Second(BasePlugin):
        type = PluginType.TRANSCRIBER
        name = "second"
        def validate_config(self): return True

    result = PluginRegistry.get_default(PluginType.TRANSCRIBER, "")
    assert result is _First


def test_list_plugins(isolated_registry):
    PluginRegistry._plugins[PluginType.PUBLISHER] = {}

    class _P1(BasePlugin):
        type = PluginType.PUBLISHER
        name = "pub-1"
        def validate_config(self): return True

    class _P2(BasePlugin):
        type = PluginType.PUBLISHER
        name = "pub-2"
        def validate_config(self): return True

    names = PluginRegistry.list_plugins(PluginType.PUBLISHER)
    assert set(names) == {"pub-1", "pub-2"}


def test_get_nonexistent_plugin_returns_none(isolated_registry):
    result = PluginRegistry.get(PluginType.DOWNLOADER, "does-not-exist")
    assert result is None
