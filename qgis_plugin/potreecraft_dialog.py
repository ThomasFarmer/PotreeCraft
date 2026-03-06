# -*- coding: utf-8 -*-
"""Main PotreeCraft dialog implementation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
)
from qgis.core import QgsMapLayerType, QgsProject, QgsVectorFileWriter, QgsWkbTypes

FORM_CLASS, _ = uic.loadUiType(
    str(Path(__file__).resolve().with_name("potreecraft_dialog_base.ui"))
)


POINTCLOUD_MODES = ["intensity", "elevation", "rgb"]


class PotreeCraftDialog(QDialog, FORM_CLASS):
    """PotreeCraft UI for vector export and project compilation."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self._python_executable_path = sys.executable

        self._annotation_checks: Dict[int, QCheckBox] = {}
        self._annotation_title_boxes: Dict[int, QComboBox] = {}
        self._annotation_desc_boxes: Dict[int, QComboBox] = {}

        self.refresh_layers_button.clicked.connect(self.refresh_vector_layers)
        self.las_browse_button.clicked.connect(self._browse_las_input)
        self.output_browse_button.clicked.connect(self._browse_output_folder)
        self.raster_script_browse_button.clicked.connect(self._browse_raster_script)
        self.run_raster_conversion_button.clicked.connect(self.run_las_to_tif_conversion)
        self.convert_vectors_button.clicked.connect(self.convert_selected_vectors)
        self.compile_button.clicked.connect(self.compile_project)
        self.copy_python_path_button.clicked.connect(self._copy_python_path)
        self.button_box.rejected.connect(self.reject)
        self.button_box.accepted.connect(self.accept)

        self.pointcloud_mode_combo.clear()
        self.pointcloud_mode_combo.addItems(POINTCLOUD_MODES)
        self.raster_mode_combo.clear()
        self.raster_mode_combo.addItems(POINTCLOUD_MODES)

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

        self.refresh_vector_layers()

    def log(self, message: str) -> None:
        self.log_box.appendPlainText(message)

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
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder", "")
        if path:
            self.output_folder_edit.setText(path)

    def _browse_raster_script(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select LAS Conversion Script", "", "Python (*.py);;All files (*.*)"
        )
        if path:
            self.raster_script_edit.setText(path)

    def refresh_vector_layers(self) -> None:
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

    def _validate_common_paths(self) -> Optional[Path]:
        output_dir = self.output_folder_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "PotreeCraft", "Please set an output folder.")
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
                QMessageBox.warning(self, "PotreeCraft", "No vector layers are selected.")
            return None

        vector_out_dir = output_dir / "vectors_geojson"
        vector_out_dir.mkdir(parents=True, exist_ok=True)

        transform_context = QgsProject.instance().transformContext()
        errors = []

        for _, layer in selected:
            sanitized = layer.name().replace(" ", "_")
            out_file = vector_out_dir / f"{sanitized}.geojson"
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
                self.log(f"Exported {layer.name()} -> {out_file}")

        manifest_path = output_dir / "potreecraft_project_manifest.json"
        self._write_manifest(manifest_path, vector_out_dir)
        self.log(f"Wrote manifest: {manifest_path}")

        if errors:
            error_text = "\n".join(errors)
            self.log("Vector export errors:\n" + error_text)
            if show_messages:
                QMessageBox.warning(self, "PotreeCraft", f"Some exports failed:\n{error_text}")
        elif show_messages:
            QMessageBox.information(self, "PotreeCraft", "Vector layers exported successfully.")

        return vector_out_dir

    def convert_selected_vectors(self) -> None:
        self._export_selected_vectors(show_messages=True)

    def run_las_to_tif_conversion(self) -> None:
        script_path_raw = self.raster_script_edit.text().strip()
        input_las_raw = self.las_input_edit.text().strip()
        output_dir = self._validate_common_paths()

        if not script_path_raw:
            QMessageBox.warning(self, "PotreeCraft", "Please select a LAS conversion script path.")
            return
        if not input_las_raw:
            QMessageBox.warning(self, "PotreeCraft", "Please select an input LAS/LAZ path.")
            return
        if output_dir is None:
            return

        script_path = Path(script_path_raw).expanduser()
        input_las = Path(input_las_raw).expanduser()

        if not script_path.exists():
            QMessageBox.warning(self, "PotreeCraft", f"Script not found:\n{script_path}")
            return
        if not input_las.exists():
            QMessageBox.warning(self, "PotreeCraft", f"LAS/LAZ not found:\n{input_las}")
            return

        mode = self.raster_mode_combo.currentText()
        tif_out = output_dir / f"{input_las.stem}_{mode}.tif"

        command = [
            sys.executable,
            str(script_path),
            "--input",
            str(input_las),
            "--output",
            str(tif_out),
            "--mode",
            mode,
        ]

        self.log("Running LAS->GeoTIFF conversion:")
        self.log(" ".join(command))
        process = subprocess.run(command, capture_output=True, text=True)
        if process.stdout:
            self.log(process.stdout.rstrip())
        if process.stderr:
            self.log(process.stderr.rstrip())

        if process.returncode != 0:
            QMessageBox.warning(
                self,
                "PotreeCraft",
                f"LAS conversion script failed with code {process.returncode}.",
            )
            return

        if not tif_out.exists():
            QMessageBox.warning(
                self,
                "PotreeCraft",
                f"Script finished but output raster was not found:\n{tif_out}",
            )
            return

        layer_name = tif_out.stem
        raster = self.iface.addRasterLayer(str(tif_out), layer_name)
        if not raster:
            QMessageBox.warning(self, "PotreeCraft", "GeoTIFF created, but QGIS failed to load raster layer.")
            return

        self.log(f"Raster layer added: {tif_out}")
        QMessageBox.information(self, "PotreeCraft", "LAS->GeoTIFF conversion complete and raster layer loaded.")

    def compile_project(self) -> None:
        las_input_raw = self.las_input_edit.text().strip()
        output_dir = self._validate_common_paths()
        if output_dir is None:
            return
        if not las_input_raw:
            QMessageBox.warning(self, "PotreeCraft", "Please select an input LAS/LAZ path.")
            return

        las_input = Path(las_input_raw).expanduser()
        if not las_input.exists():
            QMessageBox.warning(self, "PotreeCraft", f"LAS/LAZ not found:\n{las_input}")
            return

        vector_dir = self._export_selected_vectors(show_messages=False)
        if vector_dir is None:
            QMessageBox.warning(
                self, "PotreeCraft", "Cannot compile without exported vector GeoJSON files."
            )
            return

        project_name = self.project_name_edit.text().strip() or las_input.stem
        cli_script = Path(__file__).resolve().parents[1] / "cmd_tool" / "potreecraft_cli.py"
        if not cli_script.exists():
            QMessageBox.warning(self, "PotreeCraft", f"CLI script not found:\n{cli_script}")
            return

        command = [
            sys.executable,
            str(cli_script),
            "-i",
            str(las_input),
            "-o",
            str(output_dir),
            "-p",
            project_name,
            "--vector-data",
            str(vector_dir),
        ]

        self.log("Running Potree project compilation:")
        self.log(" ".join(command))
        process = subprocess.run(command, capture_output=True, text=True)
        if process.stdout:
            self.log(process.stdout.rstrip())
        if process.stderr:
            self.log(process.stderr.rstrip())

        if process.returncode != 0:
            QMessageBox.warning(
                self,
                "PotreeCraft",
                "Compilation failed. Check the log for details "
                "(and verify PotreeConverter path via cmd_tool --configure).",
            )
            return

        QMessageBox.information(self, "PotreeCraft", "Compilation completed successfully.")
