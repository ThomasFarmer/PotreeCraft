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
