import pytest

pytest.importorskip("qgis.core")


def test_dialog_initializes_with_qgis(qgis_iface):
    from qgis_plugin.potreecraft_dialog import (
        CAMERA_MODE_CUSTOM,
        CAMERA_MODE_FIT_TO_SCREEN,
        POINTCLOUD_MODES,
        PotreeCraftDialog,
    )

    dialog = PotreeCraftDialog(qgis_iface)

    assert dialog.iface is qgis_iface
    assert dialog.pointcloud_mode_combo.count() == len(POINTCLOUD_MODES)
    assert dialog.raster_mode_combo.count() == len(POINTCLOUD_MODES)
    assert dialog.blast2dem_step_size_spinbox.value() == 1.0
    assert dialog.blast2dem_coloring_combo.currentText() == "Hillshade"
    assert [
        dialog.pointcloud_mode_combo.itemText(i)
        for i in range(dialog.pointcloud_mode_combo.count())
    ] == POINTCLOUD_MODES
    assert dialog.default_camera_mode_combo.currentData() == CAMERA_MODE_FIT_TO_SCREEN
    assert dialog.default_camera_mode_combo.itemData(1) == CAMERA_MODE_CUSTOM
    assert dialog.camera_position_x_edit.isEnabled() is False
    assert dialog.camera_target_z_edit.isEnabled() is False


def test_missing_laspy_disables_builtin_raster_backend(qgis_iface, monkeypatch):
    import qgis_plugin.potreecraft_dialog as dialog_module

    warnings = []
    monkeypatch.setattr(dialog_module, "LASPY_AVAILABLE", False)
    monkeypatch.setattr(
        dialog_module.QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(message),
    )

    dialog = dialog_module.PotreeCraftDialog(qgis_iface)
    actions = {
        action.data(): action for action in dialog._raster_backend_action_group.actions()
    }

    assert dialog._raster_backend == dialog_module.RASTER_BACKEND_BLAST2DEM
    assert not actions[dialog_module.RASTER_BACKEND_POTREECRAFT].isEnabled()
    assert actions[dialog_module.RASTER_BACKEND_BLAST2DEM].isChecked()
    assert "laspy" in warnings[0]


def test_missing_rasterio_disables_builtin_raster_backend(qgis_iface, monkeypatch):
    import qgis_plugin.potreecraft_dialog as dialog_module

    warnings = []
    monkeypatch.setattr(dialog_module, "LASPY_AVAILABLE", True)
    monkeypatch.setattr(dialog_module, "RASTERIO_AVAILABLE", False)
    monkeypatch.setattr(
        dialog_module.QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(message),
    )

    dialog = dialog_module.PotreeCraftDialog(qgis_iface)
    actions = {
        action.data(): action for action in dialog._raster_backend_action_group.actions()
    }

    assert dialog._raster_backend == dialog_module.RASTER_BACKEND_BLAST2DEM
    assert not actions[dialog_module.RASTER_BACKEND_POTREECRAFT].isEnabled()
    assert actions[dialog_module.RASTER_BACKEND_BLAST2DEM].isChecked()
    assert "rasterio" in warnings[0]


def test_blast2dem_worker_includes_step_size_and_coloring(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import qgis_plugin.potreecraft_dialog as dialog_module

    executable = tmp_path / "blast2dem.exe"
    executable.touch()
    input_las = tmp_path / "cloud.las"
    input_las.touch()
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    monkeypatch.setattr(dialog_module.subprocess, "run", fake_run)
    worker = dialog_module.RasterConversionWorker(
        backend=dialog_module.RASTER_BACKEND_BLAST2DEM,
        input_las=input_las,
        mode="elevation",
        script_path_raw=str(executable),
        output_dir=tmp_path,
        blast2dem_step_size=1.0,
        blast2dem_coloring="Hillshade",
    )

    worker._run_blast2dem()

    assert captured["command"][-5:] == [
        "-step",
        "1",
        "-v",
        "-elevation",
        "-hillshade",
    ]
    assert captured["kwargs"] == {
        "capture_output": True,
        "text": True,
        "shell": False,
    }


def test_clear_previous_vector_exports_removes_unchecked_layer_outputs(qgis_iface, tmp_path):
    from types import SimpleNamespace

    from qgis_plugin.potreecraft_dialog import PotreeCraftDialog

    dialog = PotreeCraftDialog(qgis_iface)
    vector_out_dir = tmp_path / "vectors_geojson"
    vector_out_dir.mkdir()

    keep_file = vector_out_dir / "roads.geojson"
    stale_file = vector_out_dir / "buildings.geojson"
    keep_file.write_text("{}", encoding="utf-8")
    stale_file.write_text("{}", encoding="utf-8")

    selected = [(0, SimpleNamespace(name=lambda: "roads"))]
    dialog._clear_previous_vector_exports(vector_out_dir, selected)

    assert keep_file.exists()
    assert not stale_file.exists()


def test_vector_layer_functions_follow_geometry_and_annotation_state(qgis_iface):
    from qgis.PyQt.QtCore import QVariant
    from qgis.core import QgsField, QgsProject, QgsVectorLayer

    from qgis_plugin.potreecraft_dialog import PotreeCraftDialog

    project = QgsProject.instance()
    project.removeAllMapLayers()

    point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "points", "memory")
    line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "lines", "memory")
    polygon_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "polygons", "memory")

    point_provider = point_layer.dataProvider()
    point_provider.addAttributes(
        [QgsField("title", QVariant.String), QgsField("description", QVariant.String)]
    )
    point_layer.updateFields()

    project.addMapLayer(point_layer)
    project.addMapLayer(line_layer)
    project.addMapLayer(polygon_layer)

    try:
        dialog = PotreeCraftDialog(qgis_iface)

        def row_for_layer(layer_name):
            for row in range(dialog.layers_table.rowCount()):
                item = dialog.layers_table.item(row, 1)
                if item and item.text() == layer_name:
                    return row
            raise AssertionError(f"Layer row not found: {layer_name}")

        point_row = row_for_layer("points")
        line_row = row_for_layer("lines")
        polygon_row = row_for_layer("polygons")

        point_functions = dialog._function_boxes[point_row]
        line_functions = dialog._function_boxes[line_row]
        polygon_functions = dialog._function_boxes[polygon_row]

        assert [
            point_functions.itemText(i) for i in range(point_functions.count())
        ] == [
            "point (circle)",
            "point (mesh sphere)",
            "point (mesh disc)",
            "annotation",
            "coordinates (measurement)",
        ]
        assert [line_functions.itemText(i) for i in range(line_functions.count())] == [
            "linestring",
            "distance (measurement)",
            "height (measurement)",
            "height (profile)",
        ]
        assert [
            polygon_functions.itemText(i) for i in range(polygon_functions.count())
        ] == [
            "polygon (outline)",
            "polygon (filled)",
            "area (measurement)",
        ]
        assert polygon_functions.currentText() == "polygon (outline)"

        point_title = dialog._annotation_title_boxes[point_row]
        point_desc = dialog._annotation_desc_boxes[point_row]

        assert not point_title.isEnabled()
        assert not point_desc.isEnabled()
        assert [point_title.itemText(i) for i in range(point_title.count())] == [
            "(none)",
            "title",
            "description",
        ]

        point_functions.setCurrentText("annotation")

        assert point_title.isEnabled()
        assert point_desc.isEnabled()

        point_title.setCurrentText("title")
        point_desc.setCurrentText("description")
        point_functions.setCurrentText("point (mesh sphere)")

        assert not point_title.isEnabled()
        assert not point_desc.isEnabled()
        assert point_title.currentText() == "(none)"
        assert point_desc.currentText() == "(none)"

        point_provider.addAttributes([QgsField("notes", QVariant.String)])
        point_layer.updateFields()
        dialog.refresh_vector_layers()

        point_row = row_for_layer("points")
        point_functions = dialog._function_boxes[point_row]
        point_title = dialog._annotation_title_boxes[point_row]
        point_desc = dialog._annotation_desc_boxes[point_row]

        point_functions.setCurrentText("annotation")

        assert [point_title.itemText(i) for i in range(point_title.count())] == [
            "(none)",
            "title",
            "description",
            "notes",
        ]
        assert [point_desc.itemText(i) for i in range(point_desc.count())] == [
            "(none)",
            "title",
            "description",
            "notes",
        ]
    finally:
        project.removeAllMapLayers()
