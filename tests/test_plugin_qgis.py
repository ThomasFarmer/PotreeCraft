def test_dialog_initializes_with_qgis(qgis_iface):
    from qgis_plugin.potreecraft_dialog import POINTCLOUD_MODES, PotreeCraftDialog

    dialog = PotreeCraftDialog(qgis_iface)

    assert dialog.iface is qgis_iface
    assert dialog.pointcloud_mode_combo.count() == len(POINTCLOUD_MODES)
    assert dialog.raster_mode_combo.count() == len(POINTCLOUD_MODES)
    assert [
        dialog.pointcloud_mode_combo.itemText(i)
        for i in range(dialog.pointcloud_mode_combo.count())
    ] == POINTCLOUD_MODES


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
