# potree_html_generator Function Descriptions

## Class Summary

`potree_html_generator` writes the final `potree_main.html` file used to visualize the converted point cloud and vector overlays.

## Methods

### `write_potree_html(cls, pointcloud_name, pointcloud_display_mode="rgb", point_radius=5.0, fallback_projection="", cesium_map=False, cesium_map_sea_level=0.0, output_dir=None)`

- Purpose: Generate the Potree HTML entry file using either the default template or the Cesium-enabled template.
- Inputs:
  - `pointcloud_name`: Name of the point cloud project to load in the viewer.
  - `pointcloud_display_mode`: Default point-cloud attribute mode, such as `rgb`, `intensity`, or `elevation`.
  - `point_radius`: Radius used for rendered point-vector overlays.
  - `fallback_projection`: Projection string used by the Cesium template when needed.
  - `cesium_map`: Whether Cesium map support should be enabled.
  - `cesium_map_sea_level`: Elevation offset applied in the Cesium template.
  - `output_dir`: Optional output directory where `potree_main.html` will be written.
- Output:
  - None directly.
- Notes:
  - Writes `potree_main.html` into `output_dir`.
  - Appends the generated vector class and data payload to the HTML.
  - Falls back to the non-Cesium template if the Cesium runtime is not present.
