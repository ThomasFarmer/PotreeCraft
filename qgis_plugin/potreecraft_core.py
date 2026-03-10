from __future__ import annotations

import subprocess
import shutil
from pathlib import Path
from typing import Callable, Optional

from .potreecraft_geojson_reader import generate_potree_html

JSLIBS_DIR = Path(__file__).with_name("jslibs")

LogCallback = Optional[Callable[[str], None]]


def _emit(log_callback: LogCallback, message: str) -> None:
    if log_callback is not None:
        log_callback(message)


def prepare_vectors_folder(source_vector_dir: Path, output_dir: Path):
    vectors_output_dir = output_dir / "vectors"
    vectors_output_dir.mkdir(parents=True, exist_ok=True)

    copied_files = 0
    for source_file in source_vector_dir.iterdir():
        if source_file.is_file() and source_file.suffix.lower() == ".geojson":
            target = vectors_output_dir / source_file.name
            target.write_bytes(source_file.read_bytes())
            copied_files += 1

    return vectors_output_dir, copied_files


def resolve_pointcloud_name(output_dir: Path, requested_name: str) -> str:
    if requested_name:
        return requested_name

    pointclouds_dir = output_dir / "pointclouds"
    if not pointclouds_dir.exists() or not pointclouds_dir.is_dir():
        return ""

    pointcloud_dirs = [d for d in pointclouds_dir.iterdir() if d.is_dir()]
    if len(pointcloud_dirs) == 1:
        return pointcloud_dirs[0].name
    return ""


def copy_plugin_jslibs(output_dir: Path, log_callback: LogCallback = None) -> None:
    if not JSLIBS_DIR.exists() or not JSLIBS_DIR.is_dir():
        raise FileNotFoundError(f"Plugin jslibs folder is missing:\n{JSLIBS_DIR}")

    libs_target_dir = output_dir / "libs"
    libs_target_dir.mkdir(parents=True, exist_ok=True)

    source_map = {
        "Cesium183": JSLIBS_DIR / "Cesium183",
        "three.js_potreecraft": JSLIBS_DIR / "three.js",
    }
    for target_name, source_dir in source_map.items():
        if not source_dir.exists() or not source_dir.is_dir():
            raise FileNotFoundError(f"Required plugin runtime library is missing:\n{source_dir}")

        target_dir = libs_target_dir / target_name
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
        _emit(log_callback, f"Copied/updated runtime library: {target_dir}")


def compile_potree_project(
    *,
    potreeconverter_path: Path,
    input_path: Path,
    output_dir: Path,
    project_name: str,
    vector_data_dir: Path,
    pointcloud_display_mode: str = "rgb",
    projection: str = "",
    cesium_map: bool = False,
    cesium_map_sea_level: float = 0.0,
    log_callback: LogCallback = None,
) -> int:
    converter_path = Path(potreeconverter_path).expanduser()
    if not converter_path.exists() or not converter_path.is_file():
        raise FileNotFoundError(f"PotreeConverter path is invalid:\n{converter_path}")

    input_path = Path(input_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    vector_data_dir = Path(vector_data_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        str(converter_path),
        "-i",
        str(input_path),
        "-o",
        str(output_dir),
        "-p",
        project_name,
    ]
    if projection:
        command.extend(["--projection", projection])

    _emit(log_callback, "Running PotreeConverter:")
    _emit(log_callback, " ".join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(converter_path.parent),
        bufsize=1,
    )

    if process.stdout is not None:
        for line in process.stdout:
            _emit(log_callback, line.rstrip())

    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"PotreeConverter exited with code {return_code}")

    libs_dir = output_dir / "libs"
    if not libs_dir.exists() or not any(libs_dir.iterdir()):
        raise RuntimeError(
            "PotreeConverter finished, but output libs/ is empty. "
            "Check PotreeConverter installation integrity and run again."
        )

    copy_plugin_jslibs(output_dir, log_callback)

    if not vector_data_dir.exists() or not vector_data_dir.is_dir():
        raise FileNotFoundError(f"Vector data folder is invalid:\n{vector_data_dir}")

    vectors_output_dir, copied_count = prepare_vectors_folder(vector_data_dir, output_dir)
    _emit(log_callback, f"Copied {copied_count} GeoJSON file(s) into {vectors_output_dir}")
    if copied_count == 0:
        raise RuntimeError("No .geojson files found in exported vector-data folder.")

    pointcloud_name = resolve_pointcloud_name(output_dir, project_name)
    if not pointcloud_name:
        raise RuntimeError("Could not resolve pointcloud project name for HTML generation.")

    geojson_return_code = generate_potree_html(
        vector_folder=vectors_output_dir,
        project_name=pointcloud_name,
        pointcloud_display_mode=pointcloud_display_mode,
        fallback_projection=projection,
        cesium_map=cesium_map,
        cesium_map_sea_level=cesium_map_sea_level,
        output_dir=output_dir,
    )
    if geojson_return_code != 0:
        raise RuntimeError(f"GeoJSON HTML generation exited with code {geojson_return_code}")

    _emit(log_callback, f"Generated Potree project HTML in {output_dir / 'potree_main.html'}")
    return 0
