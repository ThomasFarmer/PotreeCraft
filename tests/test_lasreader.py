import numpy as np
import pytest

pytest.importorskip("laspy")
pytest.importorskip("rasterio")

from qgis_plugin.potreecraft_lasreader import FlatLas, GRID_SIZE


def _make_reader():
    reader = FlatLas(input_path="dummy.las", output_dir=".", output_epsg=4326, raster_mode="elevation")
    reader.intensity = np.array([0, 0, 0], dtype=np.uint16)
    return reader


def test_interpolate_las_accepts_constant_y_extent():
    reader = _make_reader()
    reader.x = np.array([19.04, 19.045, 19.05], dtype=np.float64)
    reader.y = np.array([47.66, 47.66, 47.66], dtype=np.float64)
    reader.z = np.array([8.08, 11.0, 21.76], dtype=np.float32)

    transform, raster = reader.interpolate_las()

    assert raster.shape == (GRID_SIZE, GRID_SIZE)
    assert np.isfinite(transform.e)
    assert transform.e < 0
    assert np.count_nonzero(~np.isnan(raster)) == 3


def test_interpolate_las_rejects_fully_degenerate_extent():
    reader = _make_reader()
    reader.x = np.array([19.04, 19.04, 19.04], dtype=np.float64)
    reader.y = np.array([47.66, 47.66, 47.66], dtype=np.float64)
    reader.z = np.array([8.08, 11.0, 21.76], dtype=np.float32)

    with pytest.raises(ValueError, match="degenerate in both X and Y"):
        reader.interpolate_las()
