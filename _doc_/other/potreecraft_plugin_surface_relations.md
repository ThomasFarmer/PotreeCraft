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

## UML Sequence Diagrams

### 1. Plugin startup and dialog opening

```mermaid
sequenceDiagram
    actor User
    participant QGIS as QGIS Plugin Loader
    participant Init as __init__.py
    participant Main as potreecraft.py\nPotreeCraft
    participant Dialog as potreecraft_dialog.py\nPotreeCraftDialog
    participant Project as QgsProject

    QGIS->>Init: classFactory(iface)
    Init->>Main: PotreeCraft(iface)
    Main-->>QGIS: plugin instance
    QGIS->>Main: initGui()
    Main->>QGIS: add toolbar/menu action

    User->>QGIS: Click PotreeCraft action
    QGIS->>Main: run()
    alt First launch
        Main->>Dialog: create PotreeCraftDialog(iface)
        Dialog->>Project: read map layers + CRS
        Dialog->>Dialog: refresh_vector_layers()
        Dialog-->>Main: dialog ready
    else Reopen existing dialog
        Main->>Dialog: refresh_vector_layers()
    end
    Main->>Dialog: show()
    Main->>Dialog: exec_()
```

### 2. Vector export to GeoJSON

```mermaid
sequenceDiagram
    actor User
    participant Dialog as PotreeCraftDialog
    participant Project as QgsProject
    participant Writer as QgsVectorFileWriter
    participant FS as Output Folder
    participant Manifest as potreecraft_project_manifest.json

    User->>Dialog: Click "Convert Selected Vector Layers"
    Dialog->>Dialog: convert_selected_vectors()
    Dialog->>Dialog: _export_selected_vectors()
    Dialog->>Dialog: _validate_common_paths()
    Dialog->>Dialog: _selected_vector_layers()
    Dialog->>Project: transformContext()
    Dialog->>FS: create `vectors/cache/`
    Dialog->>FS: remove stale GeoJSON exports

    loop For each selected layer
        Dialog->>Writer: writeAsVectorFormatV3(layer, out_file, transform_context, options)
        Writer-->>Dialog: success/error
        alt Export succeeded
            Dialog->>FS: read GeoJSON
            Dialog->>FS: embed `potreecraft_style.color`
            Dialog->>FS: write updated GeoJSON
        else Export failed
            Dialog->>Dialog: collect error message
        end
    end

    Dialog->>Manifest: write layer manifest + defaults
    alt No blocking errors
        Dialog-->>User: success message
    else Some layers failed
        Dialog-->>User: warning with failed layer list
    end
```

### 3. LAS/LAZ to GeoTIFF conversion

```mermaid
sequenceDiagram
    actor User
    participant Dialog as PotreeCraftDialog
    participant Thread as QThread
    participant Worker as RasterConversionWorker
    participant LAS as potreecraft_lasreader.py
    participant Blast as blast2dem
    participant QGIS as QGIS iface

    User->>Dialog: Click "Run Raster Conversion"
    Dialog->>Dialog: run_las_to_tif_conversion()
    Dialog->>Dialog: validate LAS path + output folder + mode

    alt PotreeCraft backend
        Dialog->>Dialog: read project CRS EPSG code
        Dialog->>Thread: _start_raster_worker(worker)
        Thread->>Worker: run()
        Worker->>LAS: convert_las_to_geotiff(input_las, raster_dir, epsg, mode)
        LAS->>LAS: read LAS/LAZ with laspy
        LAS->>LAS: aggregate values into raster grid
        LAS->>LAS: write GeoTIFF with rasterio
        LAS-->>Worker: tif_out
    else blast2dem backend
        Dialog->>Thread: _start_raster_worker(worker)
        Thread->>Worker: run()
        Worker->>Blast: subprocess.run(blast2dem ...)
        Blast-->>Worker: returncode/stdout/stderr/tif_out
    end

    Worker-->>Dialog: finished(result)
    alt Conversion succeeded and raster exists
        Dialog->>QGIS: addRasterLayer(tif_out, layer_name)
        QGIS-->>Dialog: raster layer
        Dialog-->>User: success message
    else Conversion failed
        Dialog-->>User: warning message
    end
    Dialog->>Dialog: cleanup worker + re-enable UI
```

### 4. Full Potree project compilation

```mermaid
sequenceDiagram
    actor User
    participant Dialog as PotreeCraftDialog
    participant Thread as QThread
    participant CompileWorker as CompileProjectWorker
    participant Core as potreecraft_core.py
    participant Converter as PotreeConverter
    participant FS as Output Folder
    participant HTML as potreecraft_geojson_reader.py

    User->>Dialog: Click "Compile"
    Dialog->>Dialog: compile_project()
    Dialog->>Dialog: validate output folder, PotreeConverter path, LAS/LAZ path
    Dialog->>Dialog: _export_selected_vectors(show_messages=False)
    Dialog->>Dialog: resolve project name + CRS projection
    Dialog->>Thread: _start_compile_worker(worker)

    Thread->>CompileWorker: run()
    CompileWorker->>Core: compile_potree_project(...)
    Core->>FS: create output_dir
    Core->>Converter: run `PotreeConverter -i input -o output -p project`
    Converter-->>Core: stdout stream + exit code
    alt PotreeConverter failed
        Core-->>CompileWorker: raise RuntimeError
        CompileWorker-->>Dialog: failed(error)
        Dialog-->>User: compilation failed
    else PotreeConverter succeeded
        Core->>Core: verify output `libs/`
        Core->>FS: copy plugin runtime libs into `output/libs/`
        Core->>FS: copy exported GeoJSON files into `output/vectors/`
        Core->>Core: resolve pointcloud name from project/output
        Core->>HTML: generate_potree_html(vector_folder, project_name, ...)
        HTML->>FS: write `potree_main.html`
        HTML-->>Core: return code 0
        Core-->>CompileWorker: success
        CompileWorker-->>Dialog: finished(output_dir)
        Dialog-->>User: compilation completed
    end
```

## Diagram scope notes

- The diagrams model runtime behavior from the current `qgis_plugin/` implementation, not just packaging structure.
- `PotreeCraftDialog` is the main orchestrator for every user-triggered workflow.
- Both raster conversion and Potree compilation are pushed onto `QThread` workers so the dialog stays responsive.
- The compile flow includes an internal vector export step before `PotreeConverter` and HTML generation run.
天天中彩票♀♀♀♀♀♀assistant to=multi_tool_use.parallel კომენტary  天天中彩票大奖json
