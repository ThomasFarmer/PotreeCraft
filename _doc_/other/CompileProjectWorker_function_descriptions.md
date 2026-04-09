# CompileProjectWorker Function Descriptions

## Class Summary

`CompileProjectWorker` runs full Potree project compilation in a background thread, including point cloud conversion, runtime library copying, vector export integration, and HTML generation.

## Signals

### `finished`

- Purpose: Emits a result payload when compilation succeeds.
- Output:
  - `dict`, currently containing the compiled `output_dir`.

### `failed`

- Purpose: Emits a readable error message when compilation fails.
- Output:
  - `str` containing the failure message.

### `log_message`

- Purpose: Streams log lines back to the dialog while compilation is running.
- Output:
  - `str` containing one log message.

## Methods

### `__init__(self, potreeconverter_path, input_path, output_dir, project_name, vector_data_dir, pointcloud_display_mode, point_radius, projection, cesium_map, cesium_map_sea_level)`

- Purpose: Store all project compilation options for threaded execution.
- Inputs:
  - `potreeconverter_path`: Path to the PotreeConverter executable.
  - `input_path`: Path to the source LAS/LAZ file.
  - `output_dir`: Project output directory.
  - `project_name`: Requested Potree project name.
  - `vector_data_dir`: Directory containing exported vector GeoJSON files.
  - `pointcloud_display_mode`: Default point cloud display mode in the generated viewer.
  - `point_radius`: Radius used for point-vector overlays.
  - `projection`: Optional projection string, typically an EPSG auth id.
  - `cesium_map`: Whether Cesium map support should be enabled.
  - `cesium_map_sea_level`: Elevation offset applied to the Cesium base map.
- Output:
  - None.

### `run(self)`

- Purpose: Call the core compilation routine and emit success, failure, and log messages.
- Inputs:
  - None directly. Uses worker state set in `__init__`.
- Output:
  - None directly.
- Notes:
  - On success, emits `finished({"output_dir": ...})`.
  - On failure, emits `failed(...)`.
