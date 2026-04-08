# -*- coding: utf-8 -*-
"""Main PotreeCraft dialog implementation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import QObject, QSettings, Qt, QThread, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QActionGroup,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QTableWidgetItem,
)
from qgis.core import Qgis, QgsMapLayerType, QgsMessageLog, QgsProject, QgsVectorFileWriter, QgsWkbTypes

from .potreecraft_core import compile_potree_project

FORM_CLASS, _ = uic.loadUiType(
    str(Path(__file__).resolve().with_name("potreecraft_dialog_base.ui"))
)


POINTCLOUD_MODES = ["intensity", "elevation", "rgb"]
RASTER_BACKEND_POTREECRAFT = "potreecraft"
RASTER_BACKEND_BLAST2DEM = "blast2dem"
RASTER_BACKEND_LABELS = {
    RASTER_BACKEND_POTREECRAFT: "PotreeCraft (rasterio + numpy)",
    RASTER_BACKEND_BLAST2DEM: "Legacy blast2dem (LASTools v1.0)",
}
LEGACY_RASTER_MODE_FLAGS = {
    "rgb": "-rgb",
    "intensity": "-intensity",
    "elevation": "-elevation",
}
POTREECONVERTER_SETTINGS_KEY = "PotreeCraft/potreeconverter_path"


class RasterConversionWorker(QObject):
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(
        self,
        backend: str,
        input_las: Path,
        mode: str,
        script_path_raw: str,
        output_dir: Optional[Path] = None,
        output_epsg: Optional[int] = None,
    ):
        super().__init__()
        self.backend = backend
        self.input_las = input_las
        self.mode = mode
        self.script_path_raw = script_path_raw
        self.output_dir = output_dir
        self.output_epsg = output_epsg

    def run(self) -> None:
        try:
            if self.backend == RASTER_BACKEND_BLAST2DEM:
                self.finished.emit(self._run_blast2dem())
                return

            self.finished.emit(self._run_potreecraft())
        except Exception as exc:
            self.failed.emit(str(exc))

    def _run_blast2dem(self) -> dict:
        if self.output_dir is None:
            raise ValueError("Output directory is required for blast2dem conversion.")

        raster_dir = self.output_dir / "raster"
        raster_dir.mkdir(parents=True, exist_ok=True)
        tif_out = raster_dir / f"{self.input_las.stem}_{self.mode}.tif"
        blast2dem_path = self.script_path_raw or "blast2dem"
        if self.script_path_raw:
            blast2dem_executable = Path(self.script_path_raw).expanduser()
            if not blast2dem_executable.exists():
                raise FileNotFoundError(f"blast2dem executable not found:\n{blast2dem_executable}")
            blast2dem_path = str(blast2dem_executable)

        legacy_flag = LEGACY_RASTER_MODE_FLAGS.get(self.mode)
        if not legacy_flag:
            raise ValueError(
                f"Raster mode '{self.mode}' is not supported by the legacy blast2dem backend."
            )

        command = [
            blast2dem_path,
            "-i",
            str(self.input_las),
            "-o",
            str(tif_out),
            "-otif",
            "-v",
            legacy_flag,
        ]

        process = subprocess.run(command, capture_output=True, text=True)
        return {
            "backend": self.backend,
            "command": command,
            "stdout": process.stdout or "",
            "stderr": process.stderr or "",
            "returncode": process.returncode,
            "tif_out": str(tif_out),
        }

    def _run_potreecraft(self) -> dict:
        if self.output_epsg is None:
            raise ValueError("Output EPSG is required for PotreeCraft conversion.")

        try:
            from .potreecraft_lasreader import convert_las_to_geotiff
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Built-in raster conversion is not available in the deployed plugin copy. "
                "Redeploy or reload the plugin so potreecraft_lasreader.py is included."
            ) from exc

        if self.output_dir is None:
            raise ValueError("Project folder is required for PotreeCraft conversion.")

        raster_dir = self.output_dir / "raster"
        tif_out = convert_las_to_geotiff(self.input_las, raster_dir, self.output_epsg, self.mode)
        return {
            "backend": self.backend,
            "command": None,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
            "tif_out": str(tif_out),
        }


class CompileProjectWorker(QObject):
    finished = pyqtSignal(dict)
    failed = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(
        self,
        potreeconverter_path: Path,
        input_path: Path,
        output_dir: Path,
        project_name: str,
        vector_data_dir: Path,
        pointcloud_display_mode: str,
        point_radius: float,
        projection: str,
        cesium_map: bool,
        cesium_map_sea_level: float,
    ):
        super().__init__()
        self.potreeconverter_path = potreeconverter_path
        self.input_path = input_path
        self.output_dir = output_dir
        self.project_name = project_name
        self.vector_data_dir = vector_data_dir
        self.pointcloud_display_mode = pointcloud_display_mode
        self.point_radius = point_radius
        self.projection = projection
        self.cesium_map = cesium_map
        self.cesium_map_sea_level = cesium_map_sea_level

    def run(self) -> None:
        try:
            compile_potree_project(
                potreeconverter_path=self.potreeconverter_path,
                input_path=self.input_path,
                output_dir=self.output_dir,
                project_name=self.project_name,
                vector_data_dir=self.vector_data_dir,
                pointcloud_display_mode=self.pointcloud_display_mode,
                point_radius=self.point_radius,
                projection=self.projection,
                cesium_map=self.cesium_map,
                cesium_map_sea_level=self.cesium_map_sea_level,
                log_callback=self.log_message.emit,
            )
            self.finished.emit({"output_dir": str(self.output_dir)})
        except Exception as exc:
            self.failed.emit(str(exc))


class PotreeCraftDialog(QDialog, FORM_CLASS):
    """PotreeCraft UI for vector export and project compilation."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self._python_executable_path = sys.executable
        self._raster_backend = RASTER_BACKEND_POTREECRAFT

        self._annotation_checks: Dict[int, QCheckBox] = {}
        self._annotation_title_boxes: Dict[int, QComboBox] = {}
        self._annotation_desc_boxes: Dict[int, QComboBox] = {}
        self._raster_worker_thread: Optional[QThread] = None
        self._raster_worker: Optional[RasterConversionWorker] = None
        self._raster_progress_dialog: Optional[QProgressDialog] = None
        self._compile_worker_thread: Optional[QThread] = None
        self._compile_worker: Optional[CompileProjectWorker] = None
        self._compile_progress_dialog: Optional[QProgressDialog] = None

        self.refresh_layers_button.clicked.connect(self.refresh_vector_layers)
        self.las_browse_button.clicked.connect(self._browse_las_input)
        self.output_browse_button.clicked.connect(self._browse_output_folder)
        self.potreeconverter_browse_button.clicked.connect(self._browse_potreeconverter_path)
        self.potreeconverter_path_edit.editingFinished.connect(self._persist_potreeconverter_path)
        self.raster_script_browse_button.clicked.connect(self._browse_raster_script)
        self.run_raster_conversion_button.clicked.connect(self.run_las_to_tif_conversion)
        self.convert_vectors_button.clicked.connect(self.convert_selected_vectors)
        self.compile_button.clicked.connect(self.compile_project)
        self.copy_python_path_button.clicked.connect(self._copy_python_path)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)
        QgsProject.instance().crsChanged.connect(self._update_project_crs_label)

        self.pointcloud_mode_combo.clear()
        self.pointcloud_mode_combo.addItems(POINTCLOUD_MODES)
        self.point_radius_spinbox.setDecimals(3)
        self.point_radius_spinbox.setMinimum(0.001)
        self.point_radius_spinbox.setMaximum(1_000_000.0)
        self.point_radius_spinbox.setSingleStep(0.5)
        self.point_radius_spinbox.setValue(5.0)
        self.point_radius_spinbox.setToolTip(
            "Radius used for point vector overlays in the generated Potree HTML."
        )
        self.cesium_elevation_slider.setValue(0)
        self.cesium_elevation_spinbox.setValue(0.0)
        self.cesium_map_checkbox.toggled.connect(self._on_cesium_map_toggled)
        self.cesium_elevation_slider.valueChanged.connect(self._on_cesium_slider_changed)
        self.cesium_elevation_spinbox.valueChanged.connect(self._on_cesium_spinbox_changed)
        self.raster_mode_combo.clear()
        self.raster_mode_combo.addItems(POINTCLOUD_MODES)
        self.raster_backend_status_edit.setMinimumWidth(120)
        self._init_raster_backend_menu()

        self.layers_table.setColumnCount(7)
        self.layers_table.setHorizontalHeaderLabels(
            [
                "Use",
                "Layer",
                "Geometry",
                "Color",
                "Annotation",
                "Title Field",
                "Description Field",
            ]
        )
        self.layers_table.verticalHeader().setVisible(False)
        self.layers_table.horizontalHeader().setStretchLastSection(True)
        self.layers_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.layers_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.copy_python_path_button.setMaximumWidth(90)

        self._update_python_status()
        self._load_potreeconverter_path()
        self._update_project_crs_label()

        self.refresh_vector_layers()

    def log(self, message: str) -> None:
        self.log_box.appendPlainText(message)
        self._log_qgis_message(message, Qgis.Info)

    def _log_qgis_message(self, message: str, level=Qgis.Info) -> None:
        QgsMessageLog.logMessage(message, "PotreeCraft", level)

    def _show_warning(self, message: str) -> None:
        self.log(message)
        self._log_qgis_message(message, Qgis.Warning)
        QMessageBox.warning(self, "PotreeCraft", message)

    def _show_conversion_progress_dialog(self) -> QProgressDialog:
        progress = QProgressDialog(
            "Converting pointcloud, this may take a few moments...",
            "",
            0,
            0,
            self,
        )
        progress.setWindowTitle("PotreeCraft")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        progress.raise_()
        progress.activateWindow()
        return progress

    def _on_cesium_map_toggled(self, checked: bool) -> None:
        self.cesium_elevation_slider.setEnabled(checked)
        self.cesium_elevation_spinbox.setEnabled(checked)
        state = "enabled" if checked else "disabled"
        self.log(f"Cesium base map {state}.")
        if checked:
            self.log(
                f"Cesium map elevation set to {self.cesium_elevation_spinbox.value():.1f} m."
            )

    def _on_cesium_slider_changed(self, value: int) -> None:
        spinbox_value = value / 10.0
        if self.cesium_elevation_spinbox.value() != spinbox_value:
            self.cesium_elevation_spinbox.blockSignals(True)
            self.cesium_elevation_spinbox.setValue(spinbox_value)
            self.cesium_elevation_spinbox.blockSignals(False)

    def _on_cesium_spinbox_changed(self, value: float) -> None:
        slider_value = int(round(value * 10))
        if self.cesium_elevation_slider.value() != slider_value:
            self.cesium_elevation_slider.blockSignals(True)
            self.cesium_elevation_slider.setValue(slider_value)
            self.cesium_elevation_slider.blockSignals(False)

    def _show_compile_progress_dialog(self) -> QProgressDialog:
        progress = QProgressDialog(
            "Compiling Potree project, this may take a few moments...",
            "",
            0,
            0,
            self,
        )
        progress.setWindowTitle("PotreeCraft")
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.show()
        progress.raise_()
        progress.activateWindow()
        return progress

    def _set_raster_conversion_ui_busy(self, busy: bool) -> None:
        self.run_raster_conversion_button.setEnabled(not busy)
        self.raster_backend_button.setEnabled(not busy)
        self.raster_mode_combo.setEnabled(not busy)
        self.las_browse_button.setEnabled(not busy)
        self.output_browse_button.setEnabled(not busy)
        self.raster_script_browse_button.setEnabled(not busy and self._raster_backend == RASTER_BACKEND_BLAST2DEM)

    def _cleanup_raster_worker(self) -> None:
        if self._raster_progress_dialog is not None:
            self._raster_progress_dialog.close()
            self._raster_progress_dialog.deleteLater()
            self._raster_progress_dialog = None

        self._set_raster_conversion_ui_busy(False)

        if self._raster_worker_thread is not None:
            self._raster_worker_thread.quit()
            self._raster_worker_thread.wait()
            self._raster_worker_thread.deleteLater()
            self._raster_worker_thread = None

        self._raster_worker = None

    def _set_compile_ui_busy(self, busy: bool) -> None:
        self.compile_button.setEnabled(not busy)
        self.convert_vectors_button.setEnabled(not busy)
        self.refresh_layers_button.setEnabled(not busy)
        self.point_radius_spinbox.setEnabled(not busy)
        self.las_browse_button.setEnabled(not busy)
        self.output_browse_button.setEnabled(not busy)
        self.potreeconverter_browse_button.setEnabled(not busy)
        self.potreeconverter_path_edit.setEnabled(not busy)
        self.project_name_edit.setEnabled(not busy)
        self.pointcloud_mode_combo.setEnabled(not busy)
        self.cesium_map_checkbox.setEnabled(not busy)
        cesium_controls_enabled = (not busy) and self.cesium_map_checkbox.isChecked()
        self.cesium_elevation_slider.setEnabled(cesium_controls_enabled)
        self.cesium_elevation_spinbox.setEnabled(cesium_controls_enabled)

    def _cleanup_compile_worker(self) -> None:
        if self._compile_progress_dialog is not None:
            self._compile_progress_dialog.close()
            self._compile_progress_dialog.deleteLater()
            self._compile_progress_dialog = None

        self._set_compile_ui_busy(False)

        if self._compile_worker_thread is not None:
            self._compile_worker_thread.quit()
            self._compile_worker_thread.wait()
            self._compile_worker_thread.deleteLater()
            self._compile_worker_thread = None

        self._compile_worker = None

    def _start_compile_worker(self, worker: CompileProjectWorker) -> None:
        self._cleanup_compile_worker()
        self._set_compile_ui_busy(True)
        self._compile_progress_dialog = self._show_compile_progress_dialog()

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.log_message.connect(self.log)
        worker.finished.connect(self._on_compile_finished)
        worker.failed.connect(self._on_compile_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)

        self._compile_worker = worker
        self._compile_worker_thread = thread
        thread.start()

    def _start_raster_worker(self, worker: RasterConversionWorker) -> None:
        self._cleanup_raster_worker()
        self._set_raster_conversion_ui_busy(True)
        self._raster_progress_dialog = self._show_conversion_progress_dialog()

        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_raster_conversion_finished)
        worker.failed.connect(self._on_raster_conversion_failed)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)

        self._raster_worker = worker
        self._raster_worker_thread = thread
        thread.start()

    def _on_raster_conversion_finished(self, result: dict) -> None:
        try:
            backend = result["backend"]
            tif_out = Path(result["tif_out"])

            if backend == RASTER_BACKEND_BLAST2DEM:
                command = result.get("command") or []
                self.log("Running LAS->GeoTIFF conversion:")
                self.log(f"Selected backend: {RASTER_BACKEND_LABELS[backend]}")
                self.log(" ".join(command))
                if result.get("stdout"):
                    self.log(result["stdout"].rstrip())
                if result.get("stderr"):
                    self.log(result["stderr"].rstrip())

                if result.get("returncode") != 0:
                    self._show_warning(
                        f"{RASTER_BACKEND_LABELS[backend]} failed with code {result.get('returncode')}."
                    )
                    return

                if not tif_out.exists():
                    self._show_warning(f"Script finished but output raster was not found:\n{tif_out}")
                    return
            else:
                self.log(f"Created GeoTIFF next to source LAS/LAZ: {tif_out}")

            layer_name = tif_out.stem
            raster = self.iface.addRasterLayer(str(tif_out), layer_name)
            if not raster:
                self._show_warning("GeoTIFF created, but QGIS failed to load raster layer.")
                return

            self.log(f"Raster layer added: {tif_out}")
            QMessageBox.information(
                self, "PotreeCraft", "LAS->GeoTIFF conversion complete and raster layer loaded."
            )
        finally:
            self._cleanup_raster_worker()

    def _on_raster_conversion_failed(self, error_message: str) -> None:
        try:
            if self._raster_backend == RASTER_BACKEND_POTREECRAFT:
                error_message = f"PotreeCraft (rasterio + numpy) failed: {error_message}"
            self._show_warning(error_message)
        finally:
            self._cleanup_raster_worker()

    def _on_compile_finished(self, result: dict) -> None:
        try:
            output_dir = result.get("output_dir")
            if output_dir:
                self.log(f"Compilation completed successfully: {output_dir}")
            QMessageBox.information(self, "PotreeCraft", "Compilation completed successfully.")
        finally:
            self._cleanup_compile_worker()

    def _on_compile_failed(self, error_message: str) -> None:
        try:
            self._show_warning(f"Compilation failed. Check the log for details.\n{error_message}")
        finally:
            self._cleanup_compile_worker()

    def _update_python_status(self) -> None:
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        install_root = Path(sys.executable).resolve().parent.parent
        self.python_status_label.setText(
            f"QGIS Python: {version} | Executable: {sys.executable} | Install root: {install_root}"
        )
        self.python_status_label.setToolTip(sys.executable)

    def _copy_python_path(self) -> None:
        QApplication.clipboard().setText(self._python_executable_path)
        self.log(f"Copied Python executable path: {self._python_executable_path}")

    def _browse_las_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select LAS/LAZ File", "", "LAS/LAZ (*.las *.laz);;All files (*.*)"
        )
        if path:
            self.las_input_edit.setText(path)
            if not self.project_name_edit.text().strip():
                self.project_name_edit.setText(Path(path).stem)

    def _browse_output_folder(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Project Folder", "")
        if path:
            self.output_folder_edit.setText(path)
            self.log(f"Selected project folder: {path}")

    def _load_potreeconverter_path(self) -> None:
        settings = QSettings()
        saved_path = settings.value(POTREECONVERTER_SETTINGS_KEY, "", type=str)
        if saved_path:
            self.potreeconverter_path_edit.setText(saved_path)

    def _save_potreeconverter_path(self, path: str) -> None:
        QSettings().setValue(POTREECONVERTER_SETTINGS_KEY, path)

    def _persist_potreeconverter_path(self) -> None:
        path = self.potreeconverter_path_edit.text().strip()
        self._save_potreeconverter_path(path)
        if path:
            self.log(f"PotreeConverter executable path set: {path}")

    def _browse_potreeconverter_path(self) -> None:
        if sys.platform.startswith("win"):
            file_filter = "Executables (*.exe);;All files (*.*)"
        else:
            file_filter = "All files (*);;Executables (*)"

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select PotreeConverter Executable",
            self.potreeconverter_path_edit.text().strip(),
            file_filter,
        )
        if path:
            self.potreeconverter_path_edit.setText(path)
            self._save_potreeconverter_path(path)
            self.log(f"Selected PotreeConverter executable: {path}")

    def _browse_raster_script(self) -> None:
        if self._raster_backend == RASTER_BACKEND_BLAST2DEM:
            title = "Select blast2dem Executable"
            file_filter = "Executables (*.exe *.bat *.cmd);;All files (*.*)"
        else:
            title = "Select LAS Conversion Script"
            file_filter = "Python (*.py);;All files (*.*)"

        path, _ = QFileDialog.getOpenFileName(self, title, "", file_filter)
        if path:
            self.raster_script_edit.setText(path)

    def _init_raster_backend_menu(self) -> None:
        menu = QMenu(self)
        action_group = QActionGroup(self)
        action_group.setExclusive(True)

        for backend_key in (RASTER_BACKEND_POTREECRAFT, RASTER_BACKEND_BLAST2DEM):
            action = menu.addAction(RASTER_BACKEND_LABELS[backend_key])
            action.setCheckable(True)
            action.setData(backend_key)
            action_group.addAction(action)
            if backend_key == self._raster_backend:
                action.setChecked(True)

        action_group.triggered.connect(self._on_raster_backend_action_triggered)
        self._raster_backend_action_group = action_group
        self.raster_backend_button.setMenu(menu)
        self._update_raster_backend_ui()

    def _on_raster_backend_action_triggered(self, action) -> None:
        backend_key = action.data()
        if backend_key:
            self._raster_backend = backend_key
            self._update_raster_backend_ui()
            self.log(f"Selected raster backend: {RASTER_BACKEND_LABELS[self._raster_backend]}")

    def _update_raster_backend_ui(self) -> None:
        self.raster_backend_status_edit.setText(RASTER_BACKEND_LABELS[self._raster_backend])

        if self._raster_backend == RASTER_BACKEND_BLAST2DEM:
            self.label_raster_script.setText("blast2dem Executable")
            self.raster_script_edit.setEnabled(True)
            self.raster_script_browse_button.setEnabled(True)
            self.raster_script_edit.setPlaceholderText(
                "Optional. Leave empty to use blast2dem from PATH."
            )
            self.raster_script_edit.setToolTip(
                "Path to blast2dem. Leave blank to run blast2dem from the system PATH."
            )
        else:
            self.label_raster_script.setText("Built-in Converter")
            self.raster_script_edit.clear()
            self.raster_script_edit.setEnabled(False)
            self.raster_script_browse_button.setEnabled(False)
            self.raster_script_edit.setPlaceholderText(
                "Built-in PotreeCraft conversion uses qgis_plugin/potreecraft_lasreader.py."
            )
            self.raster_script_edit.setToolTip(
                "PotreeCraft mode uses the built-in LAS reader and writes the GeoTIFF next to the LAS/LAZ file."
            )

    def refresh_vector_layers(self) -> None:
        self.log("Refreshing vector layers from current project...")
        self._update_project_crs_label()
        self.layers_table.setRowCount(0)
        self._annotation_checks.clear()
        self._annotation_title_boxes.clear()
        self._annotation_desc_boxes.clear()

        vector_layers = [
            lyr
            for lyr in QgsProject.instance().mapLayers().values()
            if lyr.type() == QgsMapLayerType.VectorLayer
        ]

        for layer in vector_layers:
            self._add_vector_layer_row(layer)

        self.log(f"Loaded {len(vector_layers)} vector layer(s) from current project.")

    def _update_project_crs_label(self) -> None:
        project_crs = QgsProject.instance().crs()
        authid = project_crs.authid().strip()
        description = project_crs.description().strip()

        if authid and description:
            label_text = f"Project CRS: {authid} ({description})"
        elif authid:
            label_text = f"Project CRS: {authid}"
        elif description:
            label_text = f"Project CRS: {description}"
        else:
            label_text = "Project CRS: not set"

        self.project_crs_label.setText(label_text)

    def _add_vector_layer_row(self, layer) -> None:
        row = self.layers_table.rowCount()
        self.layers_table.insertRow(row)

        use_item = QTableWidgetItem()
        use_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        use_item.setCheckState(Qt.Checked)
        self.layers_table.setItem(row, 0, use_item)

        layer_item = QTableWidgetItem(layer.name())
        layer_item.setData(Qt.UserRole, layer.id())
        self.layers_table.setItem(row, 1, layer_item)

        geom_label = self._geometry_label(layer)
        self.layers_table.setItem(row, 2, QTableWidgetItem(geom_label))

        color_hex = self._layer_color_hex(layer)
        color_item = QTableWidgetItem(color_hex)
        color_item.setBackground(QColor(color_hex))
        self.layers_table.setItem(row, 3, color_item)

        fields = [field.name() for field in layer.fields()]
        point_layer = QgsWkbTypes.geometryType(layer.wkbType()) == QgsWkbTypes.PointGeometry

        ann_check = QCheckBox()
        ann_check.setEnabled(point_layer)
        ann_check.setChecked(False)
        self.layers_table.setCellWidget(row, 4, ann_check)

        title_combo = QComboBox()
        title_combo.addItem("(none)")
        title_combo.addItems(fields)
        title_combo.setEnabled(False)
        self.layers_table.setCellWidget(row, 5, title_combo)

        desc_combo = QComboBox()
        desc_combo.addItem("(none)")
        desc_combo.addItems(fields)
        desc_combo.setEnabled(False)
        self.layers_table.setCellWidget(row, 6, desc_combo)

        ann_check.toggled.connect(title_combo.setEnabled)
        ann_check.toggled.connect(desc_combo.setEnabled)

        self._annotation_checks[row] = ann_check
        self._annotation_title_boxes[row] = title_combo
        self._annotation_desc_boxes[row] = desc_combo

    def _layer_from_row(self, row: int):
        item = self.layers_table.item(row, 1)
        if item is None:
            return None
        layer_id = item.data(Qt.UserRole)
        if not layer_id:
            return None
        return QgsProject.instance().mapLayer(layer_id)

    @staticmethod
    def _geometry_label(layer) -> str:
        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        if geom_type == QgsWkbTypes.PointGeometry:
            return "Point"
        if geom_type == QgsWkbTypes.LineGeometry:
            return "LineString"
        if geom_type == QgsWkbTypes.PolygonGeometry:
            return "Polygon"
        return "Unknown"

    @staticmethod
    def _layer_color_hex(layer) -> str:
        try:
            symbol = layer.renderer().symbol()
            if symbol and symbol.color().isValid():
                return symbol.color().name(QColor.HexRgb)
        except Exception:
            pass
        return "#808080"

    def _selected_vector_layers(self) -> List:
        selected = []
        for row in range(self.layers_table.rowCount()):
            use_item = self.layers_table.item(row, 0)
            if use_item and use_item.checkState() == Qt.Checked:
                layer = self._layer_from_row(row)
                if layer is not None:
                    selected.append((row, layer))
        return selected

    @staticmethod
    def _sanitized_layer_filename(layer_name: str) -> str:
        return layer_name.replace(" ", "_")

    def _clear_previous_vector_exports(self, vector_out_dir: Path, selected_layers: List) -> None:
        expected_names = {
            f"{self._sanitized_layer_filename(layer.name())}.geojson"
            for _, layer in selected_layers
        }

        removed = 0
        for existing_file in vector_out_dir.glob("*.geojson"):
            if existing_file.name not in expected_names:
                existing_file.unlink()
                removed += 1

        if removed:
            self.log(
                f"Removed {removed} stale GeoJSON export(s) from previous layer selections."
            )

    def _embed_layer_style_metadata(self, geojson_path: Path, color_hex: str) -> None:
        payload = json.loads(geojson_path.read_text(encoding="utf-8"))
        payload["potreecraft_style"] = {"color": color_hex}

        for feature in payload.get("features", []):
            properties = feature.setdefault("properties", {})
            properties["potreecraft_color"] = color_hex

        geojson_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _validate_common_paths(self) -> Optional[Path]:
        output_dir = self.output_folder_edit.text().strip()
        if not output_dir:
            self._show_warning("Please set a project folder.")
            return None
        out_path = Path(output_dir).expanduser()
        out_path.mkdir(parents=True, exist_ok=True)
        return out_path

    def _write_manifest(self, manifest_path: Path, vector_export_dir: Path) -> None:
        layers_data = []
        for row in range(self.layers_table.rowCount()):
            layer = self._layer_from_row(row)
            if layer is None:
                continue

            use_item = self.layers_table.item(row, 0)
            use_layer = bool(use_item and use_item.checkState() == Qt.Checked)
            ann_enabled = bool(self._annotation_checks[row].isChecked()) if row in self._annotation_checks else False
            title_field = self._annotation_title_boxes[row].currentText() if row in self._annotation_title_boxes else "(none)"
            desc_field = self._annotation_desc_boxes[row].currentText() if row in self._annotation_desc_boxes else "(none)"

            layers_data.append(
                {
                    "layer_id": layer.id(),
                    "name": layer.name(),
                    "use": use_layer,
                    "geometry": self._geometry_label(layer),
                    "color": self._layer_color_hex(layer),
                    "annotation": {
                        "enabled": ann_enabled,
                        "title_field": "" if title_field == "(none)" else title_field,
                        "description_field": "" if desc_field == "(none)" else desc_field,
                    },
                }
            )

        payload = {
            "pointcloud_default_display": self.pointcloud_mode_combo.currentText(),
            "point_vector_radius": self.point_radius_spinbox.value(),
            "raster_default_display": self.raster_mode_combo.currentText(),
            "vector_export_dir": str(vector_export_dir),
            "layers": layers_data,
        }
        manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _export_selected_vectors(self, show_messages: bool = True) -> Optional[Path]:
        output_dir = self._validate_common_paths()
        if output_dir is None:
            return None

        selected = self._selected_vector_layers()
        if not selected:
            if show_messages:
                self._show_warning("No vector layers are selected.")
            return None

        self.log(f"Exporting {len(selected)} selected vector layer(s) to GeoJSON...")

        vector_out_dir = output_dir / "vectors" / "cache"
        vector_out_dir.mkdir(parents=True, exist_ok=True)
        self._clear_previous_vector_exports(vector_out_dir, selected)

        transform_context = QgsProject.instance().transformContext()
        errors = []

        for _, layer in selected:
            sanitized = self._sanitized_layer_filename(layer.name())
            out_file = vector_out_dir / f"{sanitized}.geojson"
            layer_color = self._layer_color_hex(layer)
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GeoJSON"
            options.fileEncoding = "UTF-8"
            options.datasourceOptions = ["RFC7946=YES", "WRITE_BBOX=YES"]

            result = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, str(out_file), transform_context, options
            )

            if isinstance(result, tuple):
                code = result[0]
                message = result[1] if len(result) > 1 else ""
            else:
                code = result
                message = ""

            if code != QgsVectorFileWriter.NoError:
                errors.append(f"{layer.name()}: {message or code}")
            else:
                self._embed_layer_style_metadata(out_file, layer_color)
                self.log(f"Exported {layer.name()} -> {out_file}")

        manifest_path = output_dir / "potreecraft_project_manifest.json"
        self._write_manifest(manifest_path, vector_out_dir)
        self.log(f"Wrote manifest: {manifest_path}")

        if errors:
            error_text = "\n".join(errors)
            self.log("Vector export errors:\n" + error_text)
            if show_messages:
                self._show_warning(f"Some exports failed:\n{error_text}")
        elif show_messages:
            QMessageBox.information(self, "PotreeCraft", "Vector layers exported successfully.")

        return vector_out_dir

    def convert_selected_vectors(self) -> None:
        self.log("Convert Selected Vector Layers to Standard GeoJSON clicked.")
        self._export_selected_vectors(show_messages=True)

    def run_las_to_tif_conversion(self) -> None:
        script_path_raw = self.raster_script_edit.text().strip()
        input_las_raw = self.las_input_edit.text().strip()

        if not input_las_raw:
            self._show_warning("Please select an input LAS/LAZ path.")
            return

        input_las = Path(input_las_raw).expanduser()

        if not input_las.exists():
            self._show_warning(f"LAS/LAZ not found:\n{input_las}")
            return

        mode = self.raster_mode_combo.currentText()

        if self._raster_backend == RASTER_BACKEND_BLAST2DEM:
            output_dir = self._validate_common_paths()
            if output_dir is None:
                return

            if script_path_raw:
                blast2dem_executable = Path(script_path_raw).expanduser()
                if not blast2dem_executable.exists():
                    self._show_warning(f"blast2dem executable not found:\n{blast2dem_executable}")
                    return

            legacy_flag = LEGACY_RASTER_MODE_FLAGS.get(mode)
            if not legacy_flag:
                self._show_warning(
                    f"Raster mode '{mode}' is not supported by the legacy blast2dem backend."
                )
                return

            self._start_raster_worker(
                RasterConversionWorker(
                    backend=self._raster_backend,
                    input_las=input_las,
                    mode=mode,
                    script_path_raw=script_path_raw,
                    output_dir=output_dir,
                )
            )
            return

        output_dir = self._validate_common_paths()
        if output_dir is None:
            return

        project_authid = QgsProject.instance().crs().authid().strip()
        if not project_authid.startswith("EPSG:"):
            self._show_warning(
                "PotreeCraft raster conversion requires the current QGIS project CRS to be an EPSG code."
            )
            return

        output_epsg = project_authid.split(":", 1)[1]
        self.log("Running LAS->GeoTIFF conversion:")
        self.log(f"Selected backend: {RASTER_BACKEND_LABELS[self._raster_backend]}")
        self.log(f"Using project CRS: {project_authid}")
        self._start_raster_worker(
            RasterConversionWorker(
                backend=self._raster_backend,
                input_las=input_las,
                mode=mode,
                script_path_raw=script_path_raw,
                output_dir=output_dir,
                output_epsg=int(output_epsg),
            )
        )

    def compile_project(self) -> None:
        las_input_raw = self.las_input_edit.text().strip()
        output_dir = self._validate_common_paths()
        if output_dir is None:
            return
        potreeconverter_raw = self.potreeconverter_path_edit.text().strip()
        if not potreeconverter_raw:
            self._show_warning("Please set the PotreeConverter executable path before compiling.")
            return
        if not las_input_raw:
            self._show_warning("Please select an input LAS/LAZ path.")
            return

        potreeconverter_path = Path(potreeconverter_raw).expanduser()
        if not potreeconverter_path.exists() or not potreeconverter_path.is_file():
            self._show_warning(f"PotreeConverter executable not found:\n{potreeconverter_path}")
            return

        self._save_potreeconverter_path(str(potreeconverter_path))
        las_input = Path(las_input_raw).expanduser()
        if not las_input.exists():
            self._show_warning(f"LAS/LAZ not found:\n{las_input}")
            return

        vector_dir = self._export_selected_vectors(show_messages=False)
        if vector_dir is None:
            self._show_warning("Cannot compile without exported vector GeoJSON files.")
            return

        project_name = self.project_name_edit.text().strip() or las_input.stem
        projection_authid = QgsProject.instance().crs().authid().strip()
        projection_value = projection_authid if projection_authid.startswith("EPSG:") else ""

        self.log("Running Potree project compilation:")
        self.log(f"Using PotreeConverter executable: {potreeconverter_path}")
        self.log(f"Selected default pointcloud display: {self.pointcloud_mode_combo.currentText()}")
        self.log(f"Selected point overlay radius: {self.point_radius_spinbox.value():.3f}")
        self.log(
            f"Cesium base map: {'enabled' if self.cesium_map_checkbox.isChecked() else 'disabled'}"
        )
        if self.cesium_map_checkbox.isChecked():
            self.log(
                f"Cesium map elevation: {self.cesium_elevation_spinbox.value():.1f} m"
            )
        self._start_compile_worker(
            CompileProjectWorker(
                potreeconverter_path=potreeconverter_path,
                input_path=las_input,
                output_dir=output_dir,
                project_name=project_name,
                vector_data_dir=vector_dir,
                pointcloud_display_mode=self.pointcloud_mode_combo.currentText(),
                point_radius=self.point_radius_spinbox.value(),
                projection=projection_value,
                cesium_map=self.cesium_map_checkbox.isChecked(),
                cesium_map_sea_level=self.cesium_elevation_spinbox.value(),
            )
        )
