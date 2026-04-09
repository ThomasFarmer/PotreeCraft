# simple_geojson_reader Function Descriptions

## Class Summary

`simple_geojson_reader` reads a GeoJSON file, stores lightweight metadata, and extracts geometry data into the global Potree overlay feature collections used during HTML generation.

## Methods

### `__init__(self, filepath)`

- Purpose: Load a GeoJSON file and cache basic metadata about it.
- Inputs:
  - `filepath`: Path to the GeoJSON file.
- Output:
  - None.
- Notes:
  - Populates `name`, `crs`, `geomtype`, `feature_count`, and an initially empty `feature_list`.

### `print_metadata(self)`

- Purpose: Write a short metadata summary to the log.
- Inputs:
  - None.
- Output:
  - None.

### `extract_coordinates(self)`

- Purpose: Walk through the GeoJSON features and flatten supported geometry types into Potree-friendly coordinate structures.
- Inputs:
  - None directly. Uses the GeoJSON file referenced by `self.filepath`.
- Output:
  - None directly.
- Notes:
  - Appends normalized line features to `lns_gjs_feature_list`.
  - Appends normalized point features to `pts_gjs_feature_list`.
  - Appends normalized polygon features to `ply_gjs_feature_list`.
