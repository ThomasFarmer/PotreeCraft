import sys
from types import ModuleType


def test_class_factory_returns_plugin_instance(monkeypatch):
    import qgis_plugin

    fake_module = ModuleType("qgis_plugin.potreecraft")

    class FakePlugin:
        def __init__(self, iface):
            self.iface = iface

    fake_module.PotreeCraft = FakePlugin
    monkeypatch.setitem(sys.modules, "qgis_plugin.potreecraft", fake_module)

    iface = object()
    plugin = qgis_plugin.classFactory(iface)

    assert isinstance(plugin, FakePlugin)
    assert plugin.iface is iface
