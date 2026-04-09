# PotreeCraftDialog Function Descriptions

## Class Summary

`PotreeCraftDialog` is the main QGIS dialog for the plugin. It manages user interaction for vector export, raster conversion, Potree project compilation, logging, and UI state updates.

## Core Methods

### `__init__(self, iface, parent=None)`

- Purpose: Build the dialog UI, connect signals, initialize controls, and load the current project state.
- Inputs:
  - `iface`: Active QGIS interface instance.
  - `parent`: Optional parent Qt widget.
- Output:
  - None.

### `log(self, message)`

- Purpose: Append a message to the dialog log and QGIS message log.
- Inputs:
  - `message`: Text to record.
- Output:
  - None.

### `_log_qgis_message(self, message, level=Qgis.Info)`

- Purpose: Send a message to the QGIS message log under the `PotreeCraft` tag.
- Inputs:
  - `message`: Text to record.
  - `level`: QGIS log severity level.
- Output:
  - None.

### `_show_warning(self, message)`

- Purpose: Log a warning and show it in a message box.
- Inputs:
  - `message`: Warning text.
- Output:
  - None.

## Progress Dialog Methods

### `_show_conversion_progress_dialog(self)`

- Purpose: Create and show the modal progress dialog for raster conversion.
- Inputs:
  - None.
- Output:
  - A `QProgressDialog` instance.

### `_show_compile_progress_dialog(self)`

- Purpose: Create and show the modal progress dialog for project compilation.
- Inputs:
  - None.
- Output:
  - A `QProgressDialog` instance.

## Cesium UI Methods

### `_on_cesium_map_toggled(self, checked)`

- Purpose: Enable or disable Cesium-related controls and log the new state.
- Inputs:
  - `checked`: Boolean checkbox state.
- Output:
  - None.

### `_on_cesium_slider_changed(self, value)`

- Purpose: Synchronize the Cesium elevation spin box from the slider.
- Inputs:
  - `value`: Integer slider value.
- Output:
  - None.

### `_on_cesium_spinbox_changed(self, value)`

- Purpose: Synchronize the Cesium elevation slider from the spin box.
- Inputs:
  - `value`: Floating-point elevation value.
- Output:
  - None.

## Worker Lifecycle Methods

### `_set_raster_conversion_ui_busy(self, busy)`

- Purpose: Enable or disable raster-conversion controls while work is running.
- Inputs:
  - `busy`: Boolean busy state.
- Output:
  - None.

### `_cleanup_raster_worker(self)`

- Purpose: Close progress UI, stop the worker thread, and clear raster-worker references.
- Inputs:
  - None.
- Output:
  - None.

### `_set_compile_ui_busy(self, busy)`

- Purpose: Enable or disable compile-related controls while compilation is running.
- Inputs:
  - `busy`: Boolean busy state.
- Output:
  - None.

### `_cleanup_compile_worker(self)`

- Purpose: Close progress UI, stop the compile thread, and clear worker references.
- Inputs:
  - None.
- Output:
  - None.

### `_start_compile_worker(self, worker)`

- Purpose: Move a compile worker into a `QThread`, connect signals, and start it.
- Inputs:
  - `worker`: A configured `CompileProjectWorker` instance.
- Output:
  - None.

### `_start_raster_worker(self, worker)`

- Purpose: Move a raster worker into a `QThread`, connect signals, and start it.
- Inputs:
  - `worker`: A configured `RasterConversionWorker` instance.
- Output:
  - None.

### `_on_raster_conversion_finished(self, result)`

- Purpose: Handle a successful raster conversion, load the output raster into QGIS, and notify the user.
- Inputs:
  - `result`: Result dictionary emitted by the raster worker.
- Output:
  - None.

### `_on_raster_conversion_failed(self, error_message)`

- Purpose: Handle raster conversion errors and restore the dialog state.
- Inputs:
  - `error_message`: Readable failure message.
- Output:
  - None.

### `_on_compile_finished(self, result)`

- Purpose: Handle successful project compilation and inform the user.
- Inputs:
  - `result`: Result dictionary emitted by the compile worker.
- Output:
  - None.

### `_on_compile_failed(self, error_message)`

- Purpose: Handle compilation failure and restore the dialog state.
- Inputs:
  - `error_message`: Readable failure message.
- Output:
  - None.

## Path and Status Methods

### `_update_python_status(self)`

- Purpose: Show the active QGIS Python version, executable path, and install root in the dialog.
- Inputs:
  - None.
- Output:
  - None.

### `_copy_python_path(self)`

- Purpose: Copy the active QGIS Python executable path to the clipboard.
- Inputs:
  - None.
- Output:
  - None.

### `_browse_las_input(self)`

- Purpose: Let the user pick a LAS/LAZ input file and fill the project name if empty.
- Inputs:
  - None.
- Output:
  - None.

### `_browse_output_folder(self)`

- Purpose: Let the user pick the project output folder.
- Inputs:
  - None.
- Output:
  - None.

### `_load_potreeconverter_path(self)`

- Purpose: Load the saved PotreeConverter path from QGIS settings into the dialog.
- Inputs:
  - None.
- Output:
  - None.

### `_save_potreeconverter_path(self, path)`

- Purpose: Save the PotreeConverter executable path into QGIS settings.
- Inputs:
  - `path`: Path string to persist.
- Output:
  - None.

### `_persist_potreeconverter_path(self)`

- Purpose: Save the currently typed PotreeConverter path after editing finishes.
- Inputs:
  - None.
- Output:
  - None.

### `_browse_potreeconverter_path(self)`

- Purpose: Let the user pick the PotreeConverter executable path.
- Inputs:
  - None.
- Output:
  - None.

### `_browse_raster_script(self)`

- Purpose: Let the user pick an optional external raster backend executable.
- Inputs:
  - None.
- Output:
  - None.

### `_init_raster_backend_menu(self)`

- Purpose: Build the raster backend selection menu and connect its actions.
- Inputs:
  - None.
- Output:
  - None.

### `_on_raster_backend_action_triggered(self, action)`

- Purpose: Switch the active raster backend after a menu selection.
- Inputs:
  - `action`: Triggered Qt action carrying the backend key.
- Output:
  - None.

### `_update_raster_backend_ui(self)`

- Purpose: Refresh labels, placeholders, and enabled states based on the selected raster backend.
- Inputs:
  - None.
- Output:
  - None.

## Vector Layer Table Methods

### `refresh_vector_layers(self)`

- Purpose: Reload vector layers from the current QGIS project into the export table.
- Inputs:
  - None.
- Output:
  - None.

### `_update_project_crs_label(self)`

- Purpose: Show the current project CRS in a readable label.
- Inputs:
  - None.
- Output:
  - None.

### `_add_vector_layer_row(self, layer)`

- Purpose: Add one layer row to the table with export, color, and annotation controls.
- Inputs:
  - `layer`: QGIS vector layer instance.
- Output:
  - None.

### `_layer_from_row(self, row)`

- Purpose: Resolve the QGIS layer represented by a table row.
- Inputs:
  - `row`: Table row index.
- Output:
  - The matching layer object, or `None` if the row cannot be resolved.

### `_geometry_label(layer)`

- Purpose: Convert a QGIS geometry type into a human-readable label.
- Inputs:
  - `layer`: QGIS vector layer instance.
- Output:
  - `str`, such as `Point`, `LineString`, `Polygon`, or `Unknown`.

### `_layer_color_hex(layer)`

- Purpose: Extract the layer's renderer color as a hex string.
- Inputs:
  - `layer`: QGIS vector layer instance.
- Output:
  - `str` hex color, defaulting to `#808080` if unavailable.

### `_selected_vector_layers(self)`

- Purpose: Collect all layers currently checked for export.
- Inputs:
  - None.
- Output:
  - `List` of `(row, layer)` tuples.

### `_sanitized_layer_filename(layer_name)`

- Purpose: Convert a layer name into a file-friendly GeoJSON base name.
- Inputs:
  - `layer_name`: Original layer name string.
- Output:
  - `str` with spaces replaced by underscores.

### `_clear_previous_vector_exports(self, vector_out_dir, selected_layers)`

- Purpose: Remove stale GeoJSON exports that no longer correspond to selected layers.
- Inputs:
  - `vector_out_dir`: Export directory containing `.geojson` files.
  - `selected_layers`: List of currently selected layer tuples.
- Output:
  - None.

### `_embed_layer_style_metadata(self, geojson_path, color_hex)`

- Purpose: Write PotreeCraft color metadata into an exported GeoJSON file.
- Inputs:
  - `geojson_path`: Path to the exported GeoJSON file.
  - `color_hex`: Layer color encoded as a hex string.
- Output:
  - None.

### `_validate_common_paths(self)`

- Purpose: Validate and create the project output folder used by export and compilation.
- Inputs:
  - None.
- Output:
  - `Path` for the output directory, or `None` if validation fails.

### `_write_manifest(self, manifest_path, vector_export_dir)`

- Purpose: Write the project manifest describing exported layers and viewer defaults.
- Inputs:
  - `manifest_path`: Output path for the manifest JSON file.
  - `vector_export_dir`: Directory containing exported vector GeoJSON files.
- Output:
  - None.

### `_export_selected_vectors(self, show_messages=True)`

- Purpose: Export the selected vector layers to GeoJSON, attach style metadata, and write the manifest.
- Inputs:
  - `show_messages`: Whether to show user-facing success or warning dialogs.
- Output:
  - `Path` to the vector export directory, or `None` if export cannot proceed.

### `convert_selected_vectors(self)`

- Purpose: Trigger a manual vector export from the dialog button.
- Inputs:
  - None.
- Output:
  - None.

## Conversion and Compilation Methods

### `run_las_to_tif_conversion(self)`

- Purpose: Validate raster-conversion inputs and start the background conversion worker.
- Inputs:
  - None.
- Output:
  - None.

### `compile_project(self)`

- Purpose: Validate inputs, export vectors, and start full Potree project compilation.
- Inputs:
  - None.
- Output:
  - None.
