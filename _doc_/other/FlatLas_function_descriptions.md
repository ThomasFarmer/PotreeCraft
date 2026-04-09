# FlatLas Function Descriptions

## Class Summary

`FlatLas` reads a LAS/LAZ point cloud, converts the selected value channel into a regular raster grid, and writes that grid to a GeoTIFF file.

## Methods

### `__init__(self, input_path, output_dir, output_epsg, raster_mode)`

- Purpose: Store source file, output location, target CRS, and rasterization mode.
- Inputs:
  - `input_path`: Path to the input LAS or LAZ file.
  - `output_dir`: Directory where the GeoTIFF should be written.
  - `output_epsg`: EPSG code to embed in the output GeoTIFF.
  - `raster_mode`: Requested raster mode, for example `intensity` or `elevation`.
- Output:
  - None.

### `read_las(self)`

- Purpose: Load the point-cloud coordinates and supported attributes into memory.
- Inputs:
  - None directly. Uses `self.input_path`.
- Output:
  - None.
- Notes:
  - Supports `.las` directly.
  - Supports `.laz` when a compatible laspy backend is available.
  - Populates `self.x`, `self.y`, `self.z`, and `self.intensity`.

### `interpolate_las(self)`

- Purpose: Aggregate point values onto a fixed-size raster grid and compute its affine transform.
- Inputs:
  - None directly. Uses loaded point-cloud arrays from `read_las()`.
- Output:
  - Tuple `(transform, zi)` where:
    - `transform`: Raster affine transform created with `rasterio.transform.from_origin`.
    - `zi`: `numpy` array containing the rasterized values.

### `output_path(self)`

- Purpose: Build the destination GeoTIFF filename from the current settings.
- Inputs:
  - None.
- Output:
  - `Path` to the target `.tif` file.

### `save_tif(self, transform, zi)`

- Purpose: Write the raster array to disk as a GeoTIFF.
- Inputs:
  - `transform`: Affine transform describing raster georeferencing.
  - `zi`: Raster data array to save.
- Output:
  - `Path` to the written GeoTIFF file.
