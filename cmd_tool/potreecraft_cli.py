#!/usr/bin/env python3
"""PotreeCraft CLI wrapper for PotreeConverter + vector HTML generation."""

import argparse
import configparser
import shutil
import subprocess
from pathlib import Path

CONFIG_PATH = Path(__file__).with_name("potreecraft_cli.ini")
GEOJSON_READER_SCRIPT = Path(__file__).with_name("potreecraft_geojson_reader.py")
JSLIBS_DIR = Path(__file__).with_name("jslibs")
CONFIG_SECTION = "potreeconverter_location"
CONFIG_KEY = "path"


def resolve_custom_lib_sources():
    candidates = [
        JSLIBS_DIR,
        Path(__file__).resolve().parents[1] / "poc_scripts" / "base_html_examples",
    ]

    for base in candidates:
        cesium_dir = base / "Cesium183"
        three_dir = base / "three.js"
        if cesium_dir.exists() and cesium_dir.is_dir() and three_dir.exists() and three_dir.is_dir():
            return cesium_dir, three_dir

    return None, None


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PotreeConverter wrapper for PotreeCraft.")
    parser.add_argument("--configure", action="store_true", help="Configure PotreeConverter executable location.")
    parser.add_argument("-i", "--input", type=Path, help="Input LAS/LAZ file path.")
    parser.add_argument("-o", "--output", type=Path, help="Output directory path.")
    parser.add_argument("-p", "--generate-page", dest="project_name", metavar="PROJECT_NAME", help="Generate page with project name.")
    parser.add_argument("--projection", metavar="PROJ4", nargs="+", help="Projection in Proj4 format.")
    parser.add_argument("--encoding", choices=["BROTLI", "UNCOMPRESSED"], help="Encoding type.")
    parser.add_argument("-m", "--method", choices=["poisson", "poisson_average", "random"], help="Point sampling method.")
    parser.add_argument("--chunkMethod", dest="chunk_method", help="Chunking method.")
    parser.add_argument("--keep-chunks", action="store_true", help="Keep temporary chunks.")
    parser.add_argument("--no-chunking", action="store_true", help="Disable chunking.")
    parser.add_argument("--no-indexing", action="store_true", help="Disable indexing.")
    parser.add_argument("--attributes", help="Attributes in output file.")
    parser.add_argument("--title", help="Page title for generated web page.")
    parser.add_argument("--vector-data", type=Path, help="Path to vector data folder.")

    parser.add_argument(
        "--cesium-map",
        type=parse_bool,
        nargs="?",
        const=True,
        default=False,
        help="Enable Cesium 1.83 baseline map integration (true/false).",
    )
    parser.add_argument(
        "--cesium-map-sea-level",
        type=float,
        default=0.0,
        help="MAP_ELEVATION_OFFSET_M value for Cesium terrain baseline. Default: 0.",
    )
    return parser


def read_potreeconverter_location(config_path: Path) -> str:
    config = configparser.ConfigParser()
    if not config_path.exists():
        return ""
    config.read(config_path)
    return config.get(CONFIG_SECTION, CONFIG_KEY, fallback="").strip()


def write_potreeconverter_location(config_path: Path, executable_path: str) -> None:
    config = configparser.ConfigParser()
    config[CONFIG_SECTION] = {CONFIG_KEY: executable_path.strip()}
    with config_path.open("w", encoding="utf-8") as config_file:
        config.write(config_file)


def run_configure(config_path: Path) -> int:
    location = input("PotreeConverter executable location: ").strip()
    write_potreeconverter_location(config_path, location)
    print(f"Saved PotreeConverter location to {config_path}")
    return 0


def copy_custom_jslibs(output_dir: Path) -> int:
    libs_target_dir = output_dir / "libs"
    libs_target_dir.mkdir(parents=True, exist_ok=True)

    cesium_source, three_source = resolve_custom_lib_sources()
    if not cesium_source or not three_source:
        print("Custom library sources not found.")
        print("Expected one of:")
        print(f"  - {JSLIBS_DIR}/Cesium183 and {JSLIBS_DIR}/three.js")
        print("  - <repo>/poc_scripts/base_html_examples/Cesium183 and three.js")
        return 1

    source_map = {"Cesium183": cesium_source, "three.js": three_source}
    for lib_name, source_lib in source_map.items():
        target_lib = libs_target_dir / lib_name
        if target_lib.exists():
            target_lib = libs_target_dir / f"{lib_name}_potreecraft"

        shutil.copytree(source_lib, target_lib, dirs_exist_ok=True)
        print(f"Copied/updated library: {target_lib}")

    return 0


def prepare_vectors_folder(source_vector_dir: Path, output_dir: Path):
    vectors_output_dir = output_dir / "vectors"
    vectors_output_dir.mkdir(parents=True, exist_ok=True)

    copied_files = 0
    for source_file in source_vector_dir.iterdir():
        if source_file.is_file() and source_file.suffix.lower() == ".geojson":
            shutil.copy2(source_file, vectors_output_dir / source_file.name)
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


def run_geojson_html_generation(
    vector_data_path: Path,
    output_dir: Path,
    pointcloud_name: str,
    fallback_projection: str,
    cesium_map: bool,
    cesium_map_sea_level: float,
) -> int:
    if not GEOJSON_READER_SCRIPT.exists():
        print(f"GeoJSON reader script not found: {GEOJSON_READER_SCRIPT}")
        return 1

    command = [
        "python3",
        str(GEOJSON_READER_SCRIPT),
        "--vector-folder",
        str(vector_data_path),
        "--project-name",
        pointcloud_name,
        "--fallback-projection",
        fallback_projection or "",
        "--cesium-map",
        "true" if cesium_map else "false",
        "--cesium-map-sea-level",
        str(cesium_map_sea_level),
    ]

    print("Running vector HTML generator:")
    print(" ".join(command))

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=str(output_dir),
        bufsize=1,
    )

    if process.stdout is not None:
        for line in process.stdout:
            print(line, end="")

    return process.wait()


def main() -> int:
    parser = build_parser()
    args, unknown_args = parser.parse_known_args()

    if args.configure:
        return run_configure(CONFIG_PATH)

    potreeconverter_location = read_potreeconverter_location(CONFIG_PATH)
    if not potreeconverter_location:
        print("potreeconverter not found, please run --configure.")
        return 1

    if args.input is None or args.output is None:
        parser.error("the following arguments are required: -i/--input, -o/--output")
    if args.vector_data is None:
        parser.error("the following arguments are required: --vector-data")

    converter_path = Path(potreeconverter_location).expanduser()
    if not converter_path.exists() or not converter_path.is_file():
        print("Configured PotreeConverter path is invalid.")
        print(f"Path: {converter_path}")
        print("Please run --configure.")
        return 1

    # Always generate a Potree page so converter populates libs/ alongside pointclouds/.
    resolved_project_name = args.project_name or Path(args.input).stem

    projection_value = " ".join(args.projection) if isinstance(args.projection, list) else (args.projection or "")

    command = [
        str(converter_path),
        "-i",
        str(args.input),
        "-o",
        str(args.output),
        "-p",
        resolved_project_name,
    ]
    if args.title:
        command.extend(["--title", args.title])
    if projection_value:
        command.extend(["--projection", projection_value])
    if args.encoding:
        command.extend(["--encoding", args.encoding])
    if args.method:
        command.extend(["-m", args.method])
    if args.chunk_method:
        command.extend(["--chunkMethod", args.chunk_method])
    if args.keep_chunks:
        command.append("--keep-chunks")
    if args.no_chunking:
        command.append("--no-chunking")
    if args.no_indexing:
        command.append("--no-indexing")
    if args.attributes:
        command.extend(["--attributes", args.attributes])
    if unknown_args:
        command.extend(unknown_args)

    print("Running PotreeConverter:")
    print(" ".join(command))

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
            print(line, end="")

    return_code = process.wait()
    if return_code != 0:
        print(f"PotreeConverter exited with code {return_code}")
        return return_code

    output_dir = Path(args.output).expanduser().resolve()
    if not output_dir.exists() or not output_dir.is_dir():
        print(f"Output directory does not exist after conversion: {output_dir}")
        return 1

    libs_dir = output_dir / "libs"
    if not libs_dir.exists() or not any(libs_dir.iterdir()):
        print("PotreeConverter finished, but output libs/ is empty.")
        print("This wrapper expects converter-generated libs for HTML rendering.")
        print("Check PotreeConverter installation integrity and run again.")
        return 1

    jslib_copy_result = copy_custom_jslibs(output_dir)
    if jslib_copy_result != 0:
        return jslib_copy_result

    vector_data_dir = Path(args.vector_data).expanduser().resolve()
    if not vector_data_dir.exists() or not vector_data_dir.is_dir():
        print(f"Vector data folder is invalid: {vector_data_dir}")
        return 1

    vectors_output_dir, copied_count = prepare_vectors_folder(vector_data_dir, output_dir)
    if copied_count == 0:
        print("No .geojson files found in --vector-data folder.")
        return 1

    pointcloud_name = resolve_pointcloud_name(output_dir, resolved_project_name)
    if not pointcloud_name:
        print("Could not resolve pointcloud project name for HTML generation.")
        print("Please pass -p/--generate-page.")
        return 1

    geojson_return_code = run_geojson_html_generation(
        vectors_output_dir,
        output_dir,
        pointcloud_name,
        projection_value,
        args.cesium_map,
        args.cesium_map_sea_level,
    )
    if geojson_return_code != 0:
        print(f"GeoJSON HTML generation exited with code {geojson_return_code}")
        return geojson_return_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
