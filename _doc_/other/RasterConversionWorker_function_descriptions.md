# RasterConversionWorker Function Descriptions

## Class Summary

`RasterConversionWorker` runs LAS/LAZ to GeoTIFF conversion in a background thread so the QGIS dialog stays responsive.

## Signals

### `finished`

- Purpose: Emits a result dictionary after a successful conversion.
- Output:
  - `dict` containing conversion details such as backend, output path, return code, and captured command output where applicable.

### `failed`

- Purpose: Emits an error message if conversion fails.
- Output:
  - `str` containing the failure message.

## Methods

### `__init__(self, backend, input_las, mode, script_path_raw, output_dir=None, output_epsg=None)`

- Purpose: Store all conversion settings needed by the worker thread.
- Inputs:
  - `backend`: Raster backend key, for example `potreecraft` or `blast2dem`.
  - `input_las`: Path to the source `.las` or `.laz` file.
  - `mode`: Raster display/value mode such as `rgb`, `intensity`, or `elevation`.
  - `script_path_raw`: Optional raw path string to an external backend executable.
  - `output_dir`: Optional project output directory.
  - `output_epsg`: Optional EPSG code used by the built-in converter.
- Output:
  - None.

### `run(self)`

- Purpose: Execute the selected backend and emit either `finished` or `failed`.
- Inputs:
  - None.
- Output:
  - None directly.
- Notes:
  - Calls `_run_blast2dem()` for the legacy backend.
  - Calls `_run_potreecraft()` for the built-in backend.

### `_run_blast2dem(self)`

- Purpose: Run the external `blast2dem` executable and package the result.
- Inputs:
  - None directly. Uses worker state set in `__init__`.
- Output:
  - `dict` with:
    - `backend`: Backend identifier.
    - `command`: Command list passed to `subprocess.run`.
    - `stdout`: Captured standard output.
    - `stderr`: Captured standard error.
    - `returncode`: Process exit code.
    - `tif_out`: Output GeoTIFF path as a string.

### `_run_potreecraft(self)`

- Purpose: Run PotreeCraft's built-in LAS raster conversion logic.
- Inputs:
  - None directly. Uses worker state set in `__init__`.
- Output:
  - `dict` with:
    - `backend`: Backend identifier.
    - `command`: `None`, because no external command is executed.
    - `stdout`: Empty string.
    - `stderr`: Empty string.
    - `returncode`: `0` on success.
    - `tif_out`: Output GeoTIFF path as a string.
