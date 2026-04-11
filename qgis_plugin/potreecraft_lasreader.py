from __future__ import annotations

from pathlib import Path

import laspy
import numpy as np
import rasterio
from rasterio.transform import from_origin


GRID_SIZE = 1000


def _expand_degenerate_bounds(min_value: float, max_value: float, reference_span: float) -> tuple[float, float]:
    span = max_value - min_value
    if span > 0:
        return min_value, max_value

    if reference_span <= 0:
        raise ValueError("LAS/LAZ extent is degenerate in both X and Y; cannot build raster grid.")

    # Profile-like clouds can be valid while still having a zero-width axis.
    padding = max(reference_span / GRID_SIZE, 1e-9)
    half_padding = padding / 2.0
    center = min_value
    return center - half_padding, center + half_padding


class FlatLas:
    """Read a flat LAS/LAZ cloud, rasterize it, and save the result as GeoTIFF."""

    def __init__(self, input_path: Path, output_dir: Path, output_epsg: int, raster_mode: str):
        """Store source, destination, CRS, and rasterization mode settings."""
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.output_epsg = int(output_epsg)
        self.raster_mode = raster_mode.upper()

    def read_las(self) -> None:
        """Load LAS/LAZ coordinates and per-point attributes into memory."""
        suffix = self.input_path.suffix.lower()
        if suffix == ".las":
            las = laspy.read(self.input_path)
        elif suffix == ".laz":
            available_backends = laspy.LazBackend.detect_available()
            if not available_backends:
                raise ValueError(
                    "LAZ support is not available in this QGIS Python environment. "
                    "Install a laspy LAZ backend such as lazrs or laszip."
                )

            with laspy.open(self.input_path, laz_backend=available_backends) as laz_file:
                las = laz_file.read()
        else:
            raise ValueError(f"Not a .las or .laz file: {self.input_path}")

        self.x = las.x
        self.y = las.y
        self.z = las.z
        self.intensity = las.intensity

    def interpolate_las(self):
        """Aggregate point values onto a fixed grid and build its georeferencing."""
        raw_min_x = float(self.x.min())
        raw_max_x = float(self.x.max())
        raw_min_y = float(self.y.min())
        raw_max_y = float(self.y.max())

        if self.raster_mode == "INTENSITY":
            values = np.asarray(self.intensity, dtype=np.float32)
        else:
            values = np.asarray(self.z, dtype=np.float32)

        x_span = raw_max_x - raw_min_x
        y_span = raw_max_y - raw_min_y

        min_x, max_x = _expand_degenerate_bounds(raw_min_x, raw_max_x, y_span)
        min_y, max_y = _expand_degenerate_bounds(raw_min_y, raw_max_y, x_span)

        x_scale = (GRID_SIZE - 1) / (max_x - min_x)
        y_scale = (GRID_SIZE - 1) / (max_y - min_y)

        x_idx = np.clip(((self.x - min_x) * x_scale).astype(np.int32), 0, GRID_SIZE - 1)
        y_idx = np.clip(((self.y - min_y) * y_scale).astype(np.int32), 0, GRID_SIZE - 1)

        raster_sum = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)
        raster_count = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.uint32)

        np.add.at(raster_sum, (y_idx, x_idx), values)
        np.add.at(raster_count, (y_idx, x_idx), 1)

        zi = np.full((GRID_SIZE, GRID_SIZE), np.nan, dtype=np.float32)
        populated = raster_count > 0
        zi[populated] = (raster_sum[populated] / raster_count[populated]).astype(np.float32)

        transform = from_origin(
            min_x,
            max_y,
            (max_x - min_x) / zi.shape[1],
            (max_y - min_y) / zi.shape[0],
        )
        return transform, zi

    def output_path(self) -> Path:
        """Return the target GeoTIFF path derived from the current settings."""
        return self.output_dir / (
            f"{self.input_path.stem}_{self.output_epsg}_{self.raster_mode.lower()}.tif"
        )

    def save_tif(self, transform, zi) -> Path:
        """Write the rasterized grid to disk as a single-band GeoTIFF."""
        output_path = self.output_path()
        with rasterio.open(
            output_path,
            "w",
            driver="GTiff",
            height=zi.shape[0],
            width=zi.shape[1],
            count=1,
            dtype="float32",
            crs=f"EPSG:{self.output_epsg}",
            transform=transform,
            nodata=np.nan,
        ) as dst:
            dst.write(np.flipud(zi).astype("float32"), 1)
        return output_path


def convert_las_to_geotiff(input_path: Path, output_dir: Path, output_epsg: int, raster_mode: str) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    las_reader = FlatLas(input_path, output_dir, output_epsg, raster_mode)
    las_reader.read_las()
    transform, raster_data = las_reader.interpolate_las()
    return las_reader.save_tif(transform, raster_data)
