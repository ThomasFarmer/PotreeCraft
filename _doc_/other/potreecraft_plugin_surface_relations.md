# PotreeCraft Plugin Surface Relations

This is a surface-level file interaction map for the QGIS plugin package in `qgis_plugin/`.

```mermaid
flowchart TD
    QGIS[QGIS plugin loader] --> INIT["qgis_plugin/__init__.py<br/>classFactory(iface)"]
    INIT --> MAIN["qgis_plugin/potreecraft.py<br/>PotreeCraft"]

    MAIN --> RESPY["qgis_plugin/resources.py<br/>compiled Qt resources"]
    RESPY -. generated from .-> RESQRC["qgis_plugin/resources.qrc"]
    RESQRC --> ICON["qgis_plugin/pc_icon_24.png"]

    MAIN --> DIALOG["qgis_plugin/potreecraft_dialog.py<br/>PotreeCraftDialog"]
    DIALOG --> UI["qgis_plugin/potreecraft_dialog_base.ui<br/>Qt Designer layout"]

    DIALOG --> QGISAPI["QGIS API<br/>layers, CRS, export, widgets"]
    DIALOG --> CORE["qgis_plugin/potreecraft_core.py<br/>compile_potree_project()"]
    DIALOG --> LAS["qgis_plugin/potreecraft_lasreader.py<br/>built-in LAS to GeoTIFF"]
    DIALOG --> BLAST["blast2dem<br/>optional external raster backend"]

    CORE --> GEO["qgis_plugin/potreecraft_geojson_reader.py<br/>generate_potree_html()"]
    CORE --> JSLIBS["qgis_plugin/jslibs/<br/>runtime web libraries copied to output"]
    CORE --> CONVERTER["PotreeConverter<br/>external executable"]

    PB["qgis_plugin/pb_tool.cfg<br/>deployment manifest"] --> INIT
    PB --> MAIN
    PB --> DIALOG
    PB --> LAS
    PB --> CORE
    PB --> GEO
    PB --> UI
    PB --> RESQRC
    PB --> META["qgis_plugin/metadata.txt<br/>plugin metadata"]
    PB --> JSLIBS
    PB --> ICON
```

## Quick reading notes

- `__init__.py` is the QGIS entry point and hands control to `potreecraft.py`.
- `potreecraft.py` wires the toolbar/menu action and opens `potreecraft_dialog.py`.
- `potreecraft_dialog.py` is the main coordinator. It talks to QGIS, launches vector export, starts project compilation through `potreecraft_core.py`, and can run raster generation through `potreecraft_lasreader.py` or external `blast2dem`.
- `potreecraft_core.py` is the build pipeline. It runs external `PotreeConverter`, copies `jslibs/`, and calls `potreecraft_geojson_reader.py` to produce the final Potree HTML.
- `resources.py` is not edited by hand in normal workflow; it is the compiled Python form of `resources.qrc`, which includes the plugin icon path used by `potreecraft.py`.
- `pb_tool.cfg` is the packaging/deployment map. It declares which plugin files are shipped together, so it is important even though it is not part of runtime execution.
天天中彩票♀♀♀♀♀♀assistant to=multi_tool_use.parallel კომენტary  天天中彩票大奖json
