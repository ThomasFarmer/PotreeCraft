#!/usr/bin/env python3
"""CLI skeleton for wrapping PotreeConverter."""

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PotreeConverter wrapper skeleton (prints parsed inputs)."
    )
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Configure the PotreeConverter executable location.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Input LAS/LAZ file path.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory path.",
    )
    parser.add_argument(
        "-p",
        "--generate-page",
        dest="project_name",
        metavar="PROJECT_NAME",
        help="Generate Potree page using the given project name.",
    )
    parser.add_argument(
        "--projection",
        metavar="PROJ4",
        help="Projection in Proj4 format.",
    )
    parser.add_argument(
        "--encoding",
        choices=["BROTLI", "UNCOMPRESSED"],
        help='Encoding type: "BROTLI" or "UNCOMPRESSED".',
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=["poisson", "poisson_average", "random"],
        help='Point sampling method: "poisson", "poisson_average", or "random".',
    )
    parser.add_argument(
        "--chunkMethod",
        dest="chunk_method",
        help="Chunking method.",
    )
    parser.add_argument(
        "--keep-chunks",
        action="store_true",
        help="Skip deleting temporary chunks during conversion.",
    )
    parser.add_argument(
        "--no-chunking",
        action="store_true",
        help="Disable chunking phase.",
    )
    parser.add_argument(
        "--no-indexing",
        action="store_true",
        help="Disable indexing phase.",
    )
    parser.add_argument(
        "--attributes",
        help="Attributes in output file.",
    )
    parser.add_argument(
        "--title",
        help="Page title when generating a web page.",
    )
    parser.add_argument(
        "--vector-data",
        type=Path,
        help="Path to folder containing vector data inputs.",
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


def run_geojson_html_generation(
    vector_data_path: Path, output_dir: Path, pointcloud_name: str
) -> int:
    if not GEOJSON_READER_SCRIPT.exists():
        print(f"GeoJSON reader script not found: {GEOJSON_READER_SCRIPT}")
        return 1

    if not vector_data_path.exists() or not vector_data_path.is_dir():
        print(f"Vector data folder is invalid: {vector_data_path}")
        return 1

    print("Running vector HTML generator:")
    print(f"  script: {GEOJSON_READER_SCRIPT}")
    print(f"  input : {vector_data_path}")
    print(f"  cloud : {pointcloud_name}")
    print(f"  cwd   : {output_dir}")

    try:
        process = subprocess.Popen(
            [
                "python3",
                str(GEOJSON_READER_SCRIPT),
                "--vector-folder",
                str(vector_data_path),
                "--project-name",
                pointcloud_name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(output_dir),
            bufsize=1,
        )
    except OSError as exc:
        print(f"Failed to start GeoJSON reader: {exc}")
        return 1

    if process.stdout is not None:
        for line in process.stdout:
            print(line, end="")

    return process.wait()


def prepare_vectors_folder(source_vector_dir: Path, output_dir: Path):
    vectors_output_dir = output_dir / "vectors"
    vectors_output_dir.mkdir(parents=True, exist_ok=True)

    copied_files = 0
    for source_file in source_vector_dir.iterdir():
        if source_file.is_file() and source_file.suffix.lower() == ".geojson":
            shutil.copy2(source_file, vectors_output_dir / source_file.name)
            copied_files += 1

    return vectors_output_dir, copied_files


def copy_custom_jslibs(output_dir: Path) -> int:
    libs_target_dir = output_dir / "libs"
    libs_target_dir.mkdir(parents=True, exist_ok=True)

    required_libs = ["Cesium183", "three.js"]
    for lib_name in required_libs:
        source_lib = JSLIBS_DIR / lib_name
        if not source_lib.exists() or not source_lib.is_dir():
            print(f"Required library folder is missing: {source_lib}")
            return 1

        target_lib = libs_target_dir / lib_name
        if target_lib.exists():
            target_lib = libs_target_dir / f"{lib_name}_potreecraft"

        shutil.copytree(source_lib, target_lib, dirs_exist_ok=True)
        print(f"Copied/updated library: {target_lib}")

    return 0


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

    command = [
        str(converter_path),
        "-i",
        str(args.input),
        "-o",
        str(args.output),
    ]

    if args.project_name:
        command.extend(["-p", args.project_name])
    if args.title:
        command.extend(["--title", args.title])
    if args.projection:
        command.extend(["--projection", args.projection])
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

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except PermissionError:
        print("PotreeConverter is not executable. Please fix permissions and retry.")
        return 1
    except OSError as exc:
        print(f"Failed to start PotreeConverter: {exc}")
        return 1

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

    print(f"Copied {copied_count} GeoJSON file(s) to: {vectors_output_dir}")

    pointcloud_name = resolve_pointcloud_name(output_dir, args.project_name)
    if not pointcloud_name:
        print("Could not resolve pointcloud project name for HTML generation.")
        print("Please pass -p/--generate-page (for example: -p clitest).")
        return 1

    geojson_return_code = run_geojson_html_generation(
        vectors_output_dir, output_dir, pointcloud_name
    )
    if geojson_return_code != 0:
        print(f"GeoJSON HTML generation exited with code {geojson_return_code}")
        return geojson_return_code

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
