#!/usr/bin/env python3
"""Generate Potree HTML with vector overlays, optionally with Cesium 1.83 map."""

import argparse
import json
import logging
import os
import random
import re
import tempfile
from pathlib import Path
from os import listdir
from os.path import join
from typing import Optional, Sequence, Tuple

geojsonlist = []
lns_gjs_feature_list = []
pts_gjs_feature_list = []
ply_gjs_feature_list = []
annotation_gjs_feature_list = []

CAMERA_MODE_FIT_TO_SCREEN = "fit_to_screen"
CAMERA_MODE_CUSTOM = "custom_camera_position"


def _writable_log_path(filename: str) -> Path:
    """Return a user-writable log path without depending on the current cwd."""
    candidate_dirs = []

    for env_var in ("APPDATA", "LOCALAPPDATA"):
        base = os.environ.get(env_var)
        if base:
            candidate_dirs.append(Path(base) / "PotreeCraft" / "logs")

    home = Path.home()
    candidate_dirs.extend(
        [
            home / ".potreecraft" / "logs",
            home / "PotreeCraft" / "logs",
            Path(tempfile.gettempdir()) / "PotreeCraft" / "logs",
        ]
    )

    for log_dir in candidate_dirs:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / filename
            with log_path.open("a", encoding="utf-8"):
                pass
            return log_path
        except OSError:
            continue

    return Path(tempfile.gettempdir()) / filename


logging.basicConfig(
    filename=str(_writable_log_path("geojson_reader.log")),
    filemode="a",
    format="%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.DEBUG,
)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError("expected true/false")


def js_identifier(value: str) -> str:
    normalized = re.sub(r"\W+", "_", (value or "").strip())
    normalized = normalized.strip("_")
    if not normalized:
        return "vector_overlay"
    if normalized[0].isdigit():
        return f"vector_{normalized}"
    return normalized


def random_hex_color() -> str:
    r, g, b = [random.randint(0, 255) for _ in range(3)]
    return f"#{r:02x}{g:02x}{b:02x}"


def resolve_geojson_color(data: dict) -> str:
    style_color = data.get("potreecraft_style", {}).get("color")
    if isinstance(style_color, str) and style_color.strip():
        return style_color.strip()

    for feature in data.get("features", []):
        properties = feature.get("properties", {})
        for key in ("potreecraft_color", "stroke", "fill", "marker-color"):
            value = properties.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return random_hex_color()


def sanitized_layer_filename(layer_name: str) -> str:
    """Match the GUI export naming used for GeoJSON layer files."""
    return (layer_name or "").replace(" ", "_")


def ensure_3d_coordinates(coorddata):
    """Normalize a coordinate tuple/list into a three-value XYZ list."""
    if not isinstance(coorddata, (list, tuple)) or len(coorddata) < 2:
        return [0, 0, 0]
    x = coorddata[0]
    y = coorddata[1]
    z = coorddata[2] if len(coorddata) >= 3 else 0
    return [x, y, z]


def point_mesh_height_scale(function_name: str) -> float:
    """Return the vertical scale factor for mesh point rendering."""
    if function_name == "point (mesh disc)":
        return 1.0 / 6.0
    return 1.0


def line_vertices_3d(coorddata) -> list[list[float]]:
    """Normalize a line coordinate sequence into XYZ vertex triplets."""
    if not isinstance(coorddata, (list, tuple)):
        return []
    return [ensure_3d_coordinates(vertex) for vertex in coorddata if isinstance(vertex, (list, tuple))]


def stringify_feature_property(properties: dict, field_name: str) -> str:
    """Extract a readable string value from feature properties for annotation text."""
    if not field_name:
        return ""
    value = properties.get(field_name)
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def load_manifest_layer_map(manifest_path: Path | None) -> dict:
    """Load layer configuration metadata keyed by exported GeoJSON filename."""
    if manifest_path is None or not manifest_path.exists():
        return {}

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        logging.exception("Failed to read manifest: %s", manifest_path)
        return {}

    layer_map = {}
    for layer in payload.get("layers", []):
        layer_name = layer.get("name", "")
        if not layer_name:
            continue
        layer_map[f"{sanitized_layer_filename(layer_name)}.geojson"] = layer
    return layer_map


class simple_geojson_reader:
    """Read GeoJSON metadata and normalize features for Potree overlay generation."""

    def __init__(self, filepath, layer_config=None):
        """Load GeoJSON metadata and cache basic dataset properties."""
        self.filepath = filepath
        self.layer_config = layer_config or {}
        self.name = None
        self.crs = None
        self.geomtype = None
        self.feature_count = None
        self.feature_list = []

        with open(self.filepath, encoding="utf-8") as f:
            d = json.load(f)
            self.name = d.get("name")
            self.crs = d.get("crs", {}).get("properties")
            features = d.get("features", [])
            try:
                self.geomtype = features[0].get("geometry", {}).get("type")
            except Exception:
                self.geomtype = None
            self.feature_count = len(features)

    def print_metadata(self):
        """Log a compact summary of the loaded GeoJSON dataset."""
        logging.info("Name: %s", self.name)
        logging.info("CRS info: %s", self.crs)
        logging.info("geometry info: %s", self.geomtype)
        logging.info("feature count: %s", self.feature_count)

    def extract_coordinates(self):
        """Flatten supported geometries into Potree-ready feature collections."""
        with open(self.filepath, encoding="utf-8") as f:
            d = json.load(f)

        linectr = 0
        lcolor = resolve_geojson_color(d)

        for ft in d.get("features", []):
            geom = ft.get("geometry", {})
            gtype = geom.get("type")
            coorddata = geom.get("coordinates")

            if gtype == "LineString":
                linectr += 1
                self._store_line_feature(coorddata, lcolor, linectr)

            elif gtype == "MultiLineString":
                for line in coorddata:
                    linectr += 1
                    self._store_line_feature(line, lcolor, linectr)

            elif gtype == "Point":
                linectr += 1
                self._store_point_feature(coorddata, ft.get("properties", {}), lcolor, linectr)

            elif gtype == "MultiPoint":
                for point in coorddata:
                    linectr += 1
                    self._store_point_feature(point, ft.get("properties", {}), lcolor, linectr)

            elif gtype == "Polygon":
                exterior = coorddata[0]
                if len(exterior) < 3:
                    continue
                exterior_3d = [list(pt) if len(pt) >= 3 else [pt[0], pt[1], 0] for pt in exterior]
                linectr += 1
                ply_gjs_feature_list.append(
                    {
                        "line_color": lcolor,
                        "coordinates": exterior_3d,
                        "linename": js_identifier(f"{self.name}_{linectr}"),
                        "function": self.layer_config.get("function", "polygon"),
                    }
                )

            elif gtype == "MultiPolygon":
                for polygon in coorddata:
                    exterior = polygon[0]
                    if len(exterior) < 3:
                        continue
                    exterior_3d = [list(pt) if len(pt) >= 3 else [pt[0], pt[1], 0] for pt in exterior]
                    linectr += 1
                    ply_gjs_feature_list.append(
                        {
                            "line_color": lcolor,
                            "coordinates": exterior_3d,
                            "linename": js_identifier(f"{self.name}_{linectr}"),
                            "function": self.layer_config.get("function", "polygon"),
                        }
                    )

    def _store_point_feature(self, coorddata, properties, layer_color: str, linectr: int) -> None:
        """Store a point feature either as a vector point or a Potree annotation."""
        function_name = self.layer_config.get("function", "point (circle)")
        if function_name == "annotation":
            annotation_cfg = self.layer_config.get("annotation", {})
            title_field = annotation_cfg.get("title_field", "")
            description_field = annotation_cfg.get("description_field", "")
            annotation_gjs_feature_list.append(
                {
                    "coordinates": ensure_3d_coordinates(coorddata),
                    "title": stringify_feature_property(properties, title_field),
                    "description": stringify_feature_property(properties, description_field),
                    "linename": js_identifier(f"{self.name}_{linectr}"),
                }
            )
            return

        pts_gjs_feature_list.append(
            {
                "line_color": layer_color,
                "coordinates": ensure_3d_coordinates(coorddata),
                "linename": js_identifier(f"{self.name}_{linectr}"),
                "function": function_name,
            }
        )

    def _store_line_feature(self, coorddata, layer_color: str, linectr: int) -> None:
        """Store a line feature either as a vector line, measurement, or profile."""
        vertices = line_vertices_3d(coorddata)
        if len(vertices) < 2:
            return

        coordsmerged = []
        for vertex in vertices:
            coordsmerged.extend(vertex)

        lns_gjs_feature_list.append(
            {
                "line_color": layer_color,
                "coordinates": coordsmerged,
                "vertices": vertices,
                "linename": js_identifier(f"{self.name}_{linectr}"),
                "function": self.layer_config.get("function", "linestring"),
            }
        )


class potree_html_generator:
    """Generate the main Potree HTML file together with vector overlay payloads."""

    @classmethod
    def write_potree_html(
        cls,
        pointcloud_name: str,
        pointcloud_display_mode: str = "rgb",
        point_radius: float = 5.0,
        fallback_projection: str = "",
        projection_definitions: Optional[Sequence[dict[str, str]]] = None,
        cesium_map: bool = False,
        cesium_map_sea_level: float = 0.0,
        default_camera_mode: str = CAMERA_MODE_FIT_TO_SCREEN,
        default_camera_position: Optional[
            Tuple[Tuple[float, float, float], Tuple[float, float, float]]
        ] = None,
        output_dir: Path | None = None,
    ):
        """Write the appropriate Potree HTML template into the output directory."""
        output_dir = Path(output_dir) if output_dir else Path(".")
        cesium_runtime_exists = (output_dir / "libs/Cesium183/Build/Cesium/Cesium.js").exists()
        effective_cesium_map = cesium_map and cesium_runtime_exists
        if cesium_map and not cesium_runtime_exists:
            print("Cesium map requested, but Cesium183 runtime is missing in output libs. Falling back to non-Cesium template.")

        with (output_dir / "potree_main.html").open("w", encoding="utf-8") as f:
            if effective_cesium_map:
                f.write(
                    _template_cesium(
                        pointcloud_name,
                        pointcloud_display_mode,
                        fallback_projection,
                        projection_definitions,
                        cesium_map_sea_level,
                        point_radius,
                        default_camera_mode,
                        default_camera_position,
                    )
                )
            else:
                f.write(
                    _template_default(
                        pointcloud_name,
                        pointcloud_display_mode,
                        projection_definitions,
                        default_camera_mode,
                        default_camera_position,
                    )
                )

            f.write(_vector_classes_and_data(point_radius))


def _active_attribute_name(pointcloud_display_mode: str) -> str:
    mode = (pointcloud_display_mode or "rgb").strip().lower()
    if mode == "rgb":
        return "rgba"
    if mode in {"intensity", "elevation"}:
        return mode
    return "rgba"


def _format_camera_js(
    viewer_name: str,
    default_camera_mode: str,
    default_camera_position: Optional[
        Tuple[Tuple[float, float, float], Tuple[float, float, float]]
    ],
) -> str:
    if default_camera_mode == CAMERA_MODE_CUSTOM and default_camera_position is not None:
        camera_position, camera_target = default_camera_position
        return (
            f"            {viewer_name}.scene.view.setView(\n"
            f"                {json.dumps(list(camera_position))},\n"
            f"                {json.dumps(list(camera_target))}\n"
            f"            );"
        )

    return f"            {viewer_name}.fitToScreen();"


def _format_proj4_defs_js(projection_definitions: Optional[Sequence[dict[str, str]]]) -> str:
    rows = []
    for definition in projection_definitions or []:
        name = (definition.get("name") or "").strip()
        proj4 = (definition.get("proj4") or "").strip()
        if not name or not proj4:
            continue
        rows.append(f"        proj4.defs({json.dumps(name)}, {json.dumps(proj4)});")
    return "\n".join(rows)


def _template_default(
    pointcloud_name: str,
    pointcloud_display_mode: str,
    projection_definitions: Optional[Sequence[dict[str, str]]],
    default_camera_mode: str,
    default_camera_position: Optional[
        Tuple[Tuple[float, float, float], Tuple[float, float, float]]
    ],
) -> str:
    active_attribute_name = json.dumps(_active_attribute_name(pointcloud_display_mode))
    camera_js = _format_camera_js("viewer", default_camera_mode, default_camera_position)
    proj4_defs_js = _format_proj4_defs_js(projection_definitions)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Potree Viewer</title>

    <link rel="stylesheet" type="text/css" href="./libs/potree/potree.css">
    <link rel="stylesheet" type="text/css" href="./libs/jquery-ui/jquery-ui.min.css">
    <link rel="stylesheet" type="text/css" href="./libs/openlayers3/ol.css">
    <link rel="stylesheet" type="text/css" href="./libs/spectrum/spectrum.css">
    <link rel="stylesheet" type="text/css" href="./libs/jstree/themes/mixed/style.css">
</head>
<body>
    <script src="./libs/jquery/jquery-3.1.1.min.js"></script>
    <script src="./libs/spectrum/spectrum.js"></script>
    <script src="./libs/jquery-ui/jquery-ui.min.js"></script>
    <script src="./libs/other/BinaryHeap.js"></script>
    <script src="./libs/tween/tween.min.js"></script>
    <script src="./libs/d3/d3.js"></script>
    <script src="./libs/proj4/proj4.js"></script>
    <script src="./libs/openlayers3/ol.js"></script>
    <script src="./libs/i18next/i18next.js"></script>
    <script src="./libs/jstree/jstree.js"></script>
    <script src="./libs/potree/potree.js"></script>
    <script src="./libs/plasio/js/laslaz.js"></script>
    <script src="./libs/three.js_potreecraft/build/three.min.older.js"></script>
    <script>
{proj4_defs_js}
    </script>

    <div class="potree_container" style="position:absolute;width:100%;height:100%;left:0;top:0;">
        <div id="potree_render_area" style="background-image: url('./libs/potree/resources/images/background.jpg');"></div>
        <div id="potree_sidebar_container"></div>
    </div>

    <script>
        window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));
        viewer.setEDLEnabled(true);
        viewer.setFOV(60);
        viewer.setPointBudget(2_000_000);
        viewer.loadSettingsFromURL();
        viewer.setBackground("gradient");
        viewer.setDescription('Created with <a href="https://github.com/ThomasFarmer/PotreeCraft" target="_blank">PotreeCraft</a>.');

        viewer.loadGUI(() => {{
            viewer.setLanguage('en');
            $("#menu_appearance").next().show();
            $("#menu_tools").next().show();
            $("#menu_clipping").next().show();
            viewer.toggleSidebar();
        }});

        Potree.loadPointCloud("./pointclouds/{pointcloud_name}/metadata.json", "{pointcloud_name}", e => {{
            let scene = viewer.scene;
            let pointcloud = e.pointcloud;
            let material = pointcloud.material;
            material.size = 1;
            material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
            material.shape = Potree.PointShape.SQUARE;
            material.activeAttributeName = {active_attribute_name};
            scene.addPointCloud(pointcloud);
{camera_js}
        }});
    </script>
'''


def _template_cesium(
    pointcloud_name: str,
    pointcloud_display_mode: str,
    fallback_projection: str,
    projection_definitions: Optional[Sequence[dict[str, str]]],
    sea_level: float,
    point_radius: float,
    default_camera_mode: str,
    default_camera_position: Optional[
        Tuple[Tuple[float, float, float], Tuple[float, float, float]]
    ],
) -> str:
    active_attribute_name = json.dumps(_active_attribute_name(pointcloud_display_mode))
    safe_fallback_projection = json.dumps(fallback_projection or "")
    camera_js = _format_camera_js("potreeViewer", default_camera_mode, default_camera_position)
    proj4_defs_js = _format_proj4_defs_js(projection_definitions)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Potree Viewer</title>

    <link rel="stylesheet" type="text/css" href="./libs/potree/potree.css">
    <link rel="stylesheet" type="text/css" href="./libs/jquery-ui/jquery-ui.min.css">
    <link rel="stylesheet" type="text/css" href="./libs/openlayers3/ol.css">
    <link rel="stylesheet" type="text/css" href="./libs/spectrum/spectrum.css">
    <link rel="stylesheet" type="text/css" href="./libs/jstree/themes/mixed/style.css">
    <link rel="stylesheet" type="text/css" href="./libs/Cesium183/Build/Cesium/Widgets/widgets.css">
</head>
<body>
    <script src="./libs/jquery/jquery-3.1.1.min.js"></script>
    <script src="./libs/spectrum/spectrum.js"></script>
    <script src="./libs/jquery-ui/jquery-ui.min.js"></script>
    <script src="./libs/other/BinaryHeap.js"></script>
    <script src="./libs/tween/tween.min.js"></script>
    <script src="./libs/d3/d3.js"></script>
    <script src="./libs/proj4/proj4.js"></script>
    <script src="./libs/openlayers3/ol.js"></script>
    <script src="./libs/i18next/i18next.js"></script>
    <script src="./libs/jstree/jstree.js"></script>
    <script src="./libs/potree/potree.js"></script>
    <script src="./libs/plasio/js/laslaz.js"></script>
    <script>window.CESIUM_BASE_URL = './libs/Cesium183/Build/Cesium/';</script>
    <script src="./libs/Cesium183/Build/Cesium/Cesium.js"></script>
    <script src="./libs/three.js_potreecraft/build/three.min.older.js"></script>
    <script>
{proj4_defs_js}
    </script>

    <div class="potree_container" style="position:absolute;width:100%;height:100%;left:0;top:0;">
        <div id="potree_render_area" style="background-image: url('./libs/potree/resources/images/background.jpg');">
            <div id="cesiumContainer" style="position:absolute;width:100%;height:100%;"></div>
        </div>
        <div id="potree_sidebar_container"></div>
    </div>

    <script>
        const MAP_ELEVATION_OFFSET_M = {sea_level};
        const FALLBACK_POINTCLOUD_PROJECTION = {safe_fallback_projection};

        const cesiumViewerOptions = {{
            useDefaultRenderLoop: false,
            animation: false,
            baseLayerPicker: false,
            fullscreenButton: false,
            geocoder: false,
            homeButton: false,
            infoBox: false,
            sceneModePicker: false,
            selectionIndicator: false,
            timeline: false,
            navigationHelpButton: false,
            imageryProvider: new Cesium.OpenStreetMapImageryProvider({{ url: 'https://a.tile.openstreetmap.org/' }}),
        }};

        if (MAP_ELEVATION_OFFSET_M !== 0) {{
            const width = 65;
            const height = 65;
            cesiumViewerOptions.terrainProvider = new Cesium.CustomHeightmapTerrainProvider({{
                width: width,
                height: height,
                callback: function() {{
                    const heights = new Float32Array(width * height);
                    heights.fill(MAP_ELEVATION_OFFSET_M);
                    return heights;
                }},
            }});
        }}

        window.cesiumViewer = new Cesium.Viewer('cesiumContainer', cesiumViewerOptions);

        window.potreeViewer = new Potree.Viewer(document.getElementById("potree_render_area"), {{ useDefaultRenderLoop: false }});
        potreeViewer.setEDLEnabled(true);
        potreeViewer.setFOV(60);
        potreeViewer.setPointBudget(1_000_000);
        potreeViewer.setMinNodeSize(0);
        potreeViewer.loadSettingsFromURL();
        potreeViewer.setBackground(null);
        potreeViewer.setDescription('Created with <a href="https://github.com/ThomasFarmer/PotreeCraft" target="_blank">PotreeCraft</a>.');

        potreeViewer.loadGUI(() => {{
            potreeViewer.setLanguage('en');
            $("#menu_appearance").next().show();
            $("#menu_tools").next().show();
            $("#menu_scene").next().show();
            potreeViewer.toggleSidebar();
            $("#potree_map_toggle").hide();
        }});

        Potree.loadPointCloud("./pointclouds/{pointcloud_name}/metadata.json", "{pointcloud_name}", e => {{
            let scene = potreeViewer.scene;
            let pointcloud = e.pointcloud;
            let material = pointcloud.material;
            scene.addPointCloud(pointcloud);
            material.size = 1;
            material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
            material.shape = Potree.PointShape.SQUARE;
            material.activeAttributeName = {active_attribute_name};
{camera_js}

            const normalizeProjectionCandidate = (candidate) => {{
                if (!candidate) return "";
                const c = String(candidate).trim();
                if (!c) return "";
                if (c === "+proj=somerc") return "EPSG:23700";
                if (c.startsWith("+proj=somerc") && !c.includes("lat_0=")) return "EPSG:23700";
                return c;
            }};

            const mapProjection = "WGS84";
            const candidates = [
                normalizeProjectionCandidate(e.pointcloud.projection),
                normalizeProjectionCandidate(FALLBACK_POINTCLOUD_PROJECTION),
                "EPSG:23700",
            ].filter(Boolean);
            window.toMap = null;
            for (const candidate of [...new Set(candidates)]) {{
                try {{
                    window.toMap = proj4(candidate, mapProjection);
                    console.log("Using pointcloud projection for Cesium sync:", candidate);
                    break;
                }} catch (err) {{
                    console.warn("Projection candidate failed:", candidate, err);
                }}
            }}
            if (!window.toMap) {{
                console.error("No valid pointcloud projection found. Cesium camera sync disabled.");
            }}
        }});

        potreeViewer.renderer.autoClear = false;

        function loop(timestamp) {{
            requestAnimationFrame(loop);
            potreeViewer.update(potreeViewer.clock.getDelta(), timestamp);
            potreeViewer.render();

            if (window.toMap !== undefined) {{
                const THREE_CTX = (window.Potree && window.Potree.THREE) ? window.Potree.THREE : window.THREE;
                if (!THREE_CTX) {{
                    return;
                }}
                let camera = potreeViewer.scene.getActiveCamera();
                let pPos = new THREE_CTX.Vector3(0, 0, 0).applyMatrix4(camera.matrixWorld);
                let pUp = new THREE_CTX.Vector3(0, 600, 0).applyMatrix4(camera.matrixWorld);
                let pTarget = potreeViewer.scene.view.getPivot();

                const toCes = (pos) => {{
                    if (!window.toMap) return null;
                    const xy = [pos.x, pos.y];
                    const height = pos.z || 0;
                    let deg;
                    try {{
                        deg = window.toMap.forward(xy);
                    }} catch (err) {{
                        return null;
                    }}
                    if (!deg || deg.length < 2) return null;
                    const lon = deg[0];
                    const lat = deg[1];
                    if (!Number.isFinite(lon) || !Number.isFinite(lat) || Math.abs(lon) > 180 || Math.abs(lat) > 90) {{
                        return null;
                    }}
                    return Cesium.Cartesian3.fromDegrees(lon, lat, height);
                }};

                let cPos = toCes(pPos);
                let cUpTarget = toCes(pUp);
                let cTarget = toCes(pTarget);
                if (!cPos || !cUpTarget || !cTarget) {{
                    return;
                }}

                let cDir = Cesium.Cartesian3.subtract(cTarget, cPos, new Cesium.Cartesian3());
                let cUp = Cesium.Cartesian3.subtract(cUpTarget, cPos, new Cesium.Cartesian3());
                cDir = Cesium.Cartesian3.normalize(cDir, new Cesium.Cartesian3());
                cUp = Cesium.Cartesian3.normalize(cUp, new Cesium.Cartesian3());

                cesiumViewer.camera.setView({{
                    destination: cPos,
                    orientation: {{ direction: cDir, up: cUp }}
                }});

                let aspect = potreeViewer.scene.getActiveCamera().aspect;
                let fovy = Math.PI * (potreeViewer.scene.getActiveCamera().fov / 180);
                if (aspect < 1) {{
                    cesiumViewer.camera.frustum.fov = fovy;
                }} else {{
                    let fovx = Math.atan(Math.tan(0.5 * fovy) * aspect) * 2;
                    cesiumViewer.camera.frustum.fov = fovx;
                }}

                cesiumViewer.render();
            }}
        }}

        requestAnimationFrame(loop);
    </script>
'''


def _vector_classes_and_data(point_radius: float = 5.0) -> str:
    rows = []
    rows.append('''
    <script>
        const activeViewer = window.potreeViewer || window.viewer;
        const THREE_CTX = (window.Potree && window.Potree.THREE) ? window.Potree.THREE : window.THREE;
        if (!THREE_CTX) {
            console.error("THREE runtime not found. Vector overlays disabled.");
        }

        class CircleOnScreen {
            constructor(center, radius, segments, color, lwidth, opacity, groupname) {
                this.center = center;
                this.radius = radius;
                this.segments = segments;
                this.color = color;
                this.lwidth = lwidth;
                this.opacity = opacity;
                this.groupname = groupname;
            }

            displaycircle() {
                if (!THREE_CTX) return;
                const points = [];
                for (let i = 0; i <= this.segments; i++) {
                    const theta = (i / this.segments) * Math.PI * 2;
                    const x = this.center[0] + this.radius * Math.cos(theta);
                    const y = this.center[1] + this.radius * Math.sin(theta);
                    const z = this.center[2];
                    points.push(new THREE_CTX.Vector3(x, y, z));
                }

                const geometry = new THREE_CTX.BufferGeometry().setFromPoints(points);
                const material = new THREE_CTX.LineBasicMaterial({
                    color: this.color,
                    transparent: true,
                    opacity: this.opacity,
                    linewidth: this.lwidth
                });

                const circle = new THREE_CTX.LineLoop(geometry, material);
                const circleGroup = new THREE_CTX.Group();
                circleGroup.name = this.groupname;
                circleGroup.add(circle);
                activeViewer.scene.scene.add(circleGroup);
            }
        }

        class MeshPointOnScreen {
            constructor(center, radius, heightScale, color, opacity, groupname) {
                this.center = center;
                this.radius = radius;
                this.heightScale = heightScale;
                this.color = color;
                this.opacity = opacity;
                this.groupname = groupname;
            }

            displaymesh() {
                if (!THREE_CTX) return;

                const geometry = new THREE_CTX.SphereGeometry(1, 18, 18);
                const meshRadius = Math.max(this.radius, 0.001) * 0.3;
                const material = new THREE_CTX.MeshNormalMaterial({
                    transparent: true,
                    opacity: this.opacity
                });

                const mesh = new THREE_CTX.Mesh(geometry, material);
                mesh.position.set(this.center[0], this.center[1], this.center[2]);
                mesh.scale.set(meshRadius, meshRadius, meshRadius * this.heightScale);
                mesh.renderOrder = 999;

                const meshGroup = new THREE_CTX.Group();
                meshGroup.name = this.groupname;
                meshGroup.renderOrder = 999;
                meshGroup.add(mesh);
                activeViewer.scene.scene.add(meshGroup);
            }
        }

        class LineOnScreen {
            constructor(coords, lcolor, lwidth, lopacity, groupname) {
                this.coords = coords;
                this.lcolor = lcolor;
                this.lwidth = lwidth;
                this.lopacity = lopacity;
                this.groupname = groupname;
            }

            displayline() {
                if (!THREE_CTX) return;
                const positions = new Float32Array(this.coords);
                const geometry = new THREE_CTX.BufferGeometry();
                geometry.setAttribute('position', new THREE_CTX.BufferAttribute(positions, 3));

                const material = new THREE_CTX.LineBasicMaterial({
                    linewidth: this.lwidth,
                    transparent: true,
                    color: this.lcolor,
                    opacity: this.lopacity
                });

                const line = new THREE_CTX.Line(geometry, material);
                const vectorGroup = new THREE_CTX.Group();
                vectorGroup.name = this.groupname;
                vectorGroup.add(line);
                activeViewer.scene.scene.add(vectorGroup);
            }
        }

        function addLineVertices(target, vertices) {
            for (const vertex of vertices) {
                target.addMarker(new THREE_CTX.Vector3(vertex[0], vertex[1], vertex[2]));
            }
        }

        function createDistanceMeasurement(vertices) {
            const measure = new Potree.Measure();
            measure.closed = false;
            measure.showDistances = true;
            measure.showCoordinates = false;
            addLineVertices(measure, vertices);
            activeViewer.scene.addMeasurement(measure);
        }

        function createHeightMeasurement(vertices) {
            const measure = new Potree.Measure();
            measure.closed = false;
            measure.showDistances = false;
            measure.showHeight = true;
            measure.showCoordinates = false;
            const endpoints = [vertices[0], vertices[vertices.length - 1]];
            addLineVertices(measure, endpoints);
            activeViewer.scene.addMeasurement(measure);
        }

        function createHeightProfile(vertices) {
            const profile = new Potree.Profile();
            profile.setWidth(6);
            addLineVertices(profile, vertices);
            activeViewer.scene.addProfile(profile);
        }

        function createCoordinateMeasurement(vertex) {
            const measure = new Potree.Measure();
            measure.showDistances = false;
            measure.showCoordinates = true;
            measure.maxMarkers = 1;
            measure.addMarker(new THREE_CTX.Vector3(vertex[0], vertex[1], vertex[2]));
            activeViewer.scene.addMeasurement(measure);
        }

        function createAreaMeasurement(vertices) {
            const measure = new Potree.Measure();
            measure.closed = true;
            measure.showArea = true;
            measure.showDistances = true;
            addLineVertices(measure, vertices);
            activeViewer.scene.addMeasurement(measure);
        }

        class PolygonOnScreen {
            constructor(points, color, opacity, groupname) {
                this.points = points;
                this.color = color;
                this.opacity = opacity;
                this.groupname = groupname;
            }

            displaypolygon() {
                if (!THREE_CTX) return;
                if (this.points.length < 3) {
                    console.warn("Polygon needs at least 3 points");
                    return;
                }

                const contour = this.points.map(p => new THREE_CTX.Vector2(p[0], p[1]));
                const faces = THREE_CTX.ShapeUtils.triangulateShape(contour, []);

                const positions = new Float32Array(this.points.length * 3);
                for (let i = 0; i < this.points.length; i++) {
                    positions[i * 3] = this.points[i][0];
                    positions[i * 3 + 1] = this.points[i][1];
                    positions[i * 3 + 2] = this.points[i][2] != null ? this.points[i][2] : 0;
                }

                const indices = [];
                for (let i = 0; i < faces.length; i++) {
                    indices.push(faces[i][0], faces[i][1], faces[i][2]);
                }

                const geometry = new THREE_CTX.BufferGeometry();
                geometry.setAttribute('position', new THREE_CTX.BufferAttribute(positions, 3));
                geometry.setIndex(indices);
                geometry.computeVertexNormals();

                const material = new THREE_CTX.MeshBasicMaterial({
                    color: this.color,
                    transparent: true,
                    opacity: this.opacity,
                    side: THREE_CTX.DoubleSide,
                    depthWrite: false
                });

                const mesh = new THREE_CTX.Mesh(geometry, material);
                const polyGroup = new THREE_CTX.Group();
                polyGroup.name = this.groupname;
                polyGroup.add(mesh);
                activeViewer.scene.scene.add(polyGroup);
            }
        }
''')

    for ft in lns_gjs_feature_list:
        function_name = ft.get("function", "linestring")
        if function_name == "distance (measurement)":
            rows.append(
                """
        createDistanceMeasurement({vertices});
""".format(vertices=json.dumps(ft.get("vertices")))
            )
        elif function_name == "height (measurement)":
            rows.append(
                """
        createHeightMeasurement({vertices});
""".format(vertices=json.dumps(ft.get("vertices")))
            )
        elif function_name == "height (profile)":
            rows.append(
                """
        createHeightProfile({vertices});
""".format(vertices=json.dumps(ft.get("vertices")))
            )
        else:
            rows.append(
                """
        const {name} = new LineOnScreen(
            {coords},
            "{color}",
            1,
            0.75,
            "vectorclass");
        {name}.displayline();
""".format(name=ft.get("linename"), coords=ft.get("coordinates"), color=ft.get("line_color"))
            )

    for ft in pts_gjs_feature_list:
        function_name = ft.get("function", "point (circle)")
        if function_name == "coordinates (measurement)":
            rows.append(
                """
        createCoordinateMeasurement({coords});
""".format(coords=json.dumps(ft.get("coordinates")))
            )
        elif function_name in {"point (mesh sphere)", "point (mesh disc)"}:
            rows.append(
                """
        const {name} = new MeshPointOnScreen(
            {coords},
            {point_radius},
            {height_scale},
            "{color}",
            0.75,
            "vectorclass");
        {name}.displaymesh();
""".format(
                    name=ft.get("linename"),
                    coords=json.dumps(ft.get("coordinates")),
                    point_radius=json.dumps(float(point_radius)),
                    height_scale=json.dumps(point_mesh_height_scale(function_name)),
                    color=ft.get("line_color"),
                )
            )
        else:
            rows.append(
                """
        const {name} = new CircleOnScreen(
            {coords},
            {point_radius},
            32,
            "{color}",
            3,
            0.75,
            "vectorclass");
        {name}.displaycircle();
""".format(
                    name=ft.get("linename"),
                    coords=json.dumps(ft.get("coordinates")),
                    point_radius=json.dumps(float(point_radius)),
                    color=ft.get("line_color"),
                )
            )

    for ft in annotation_gjs_feature_list:
        rows.append(
            """
        activeViewer.scene.annotations.add(new Potree.Annotation({{
            title: {title},
            position: {coords},
            description: {description}
        }}));
""".format(
                title=json.dumps(ft.get("title", "")),
                coords=json.dumps(ft.get("coordinates")),
                description=json.dumps(ft.get("description", "")),
            )
        )

    for ft in ply_gjs_feature_list:
        function_name = ft.get("function", "polygon")
        if function_name == "area (measurement)":
            rows.append(
                """
        createAreaMeasurement({coords});
""".format(coords=json.dumps(ft.get("coordinates")))
            )
        else:
            rows.append(
                """
        const {name} = new PolygonOnScreen(
            {coords},
            "{color}",
            0.75,
            "vectorclass");
        {name}.displaypolygon();
""".format(name=ft.get("linename"), coords=json.dumps(ft.get("coordinates")), color=ft.get("line_color"))
            )

    rows.append(
        """
    </script>
</body>
</html>
"""
    )

    return "".join(rows)


def generate_potree_html(
    vector_folder: str | Path,
    project_name: str,
    pointcloud_display_mode: str = "rgb",
    point_radius: float = 5.0,
    fallback_projection: str = "",
    projection_definitions: Optional[Sequence[dict[str, str]]] = None,
    cesium_map: bool = False,
    cesium_map_sea_level: float = 0.0,
    default_camera_mode: str = CAMERA_MODE_FIT_TO_SCREEN,
    default_camera_position: Optional[
        Tuple[Tuple[float, float, float], Tuple[float, float, float]]
    ] = None,
    output_dir: str | Path | None = None,
    manifest_path: str | Path | None = None,
) -> int:
    global geojsonlist, lns_gjs_feature_list, pts_gjs_feature_list, ply_gjs_feature_list, annotation_gjs_feature_list

    geojsonlist = []
    lns_gjs_feature_list = []
    pts_gjs_feature_list = []
    ply_gjs_feature_list = []
    annotation_gjs_feature_list = []

    folderpath = str(vector_folder)
    layer_manifest_map = load_manifest_layer_map(Path(manifest_path) if manifest_path else None)
    geojsonlist = listdir(folderpath)
    if len(geojsonlist) == 0:
        print("This folder contains no data.")
        return 1

    for gjs in geojsonlist:
        if not gjs.lower().endswith(".geojson"):
            continue
        try:
            current_gjs = simple_geojson_reader(
                join(folderpath, gjs), layer_config=layer_manifest_map.get(gjs, {})
            )
            current_gjs.print_metadata()
            current_gjs.extract_coordinates()
        except Exception:
            logging.exception("Error processing file: %s", join(folderpath, gjs))

    potree_html_generator.write_potree_html(
        project_name,
        pointcloud_display_mode=pointcloud_display_mode,
        point_radius=point_radius,
        fallback_projection=fallback_projection,
        projection_definitions=projection_definitions,
        cesium_map=cesium_map,
        cesium_map_sea_level=cesium_map_sea_level,
        default_camera_mode=default_camera_mode,
        default_camera_position=default_camera_position,
        output_dir=Path(output_dir) if output_dir else None,
    )
    print("potree_main.html generated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Potree HTML with vector layers.")
    parser.add_argument("--vector-folder", required=True, help="Folder containing GeoJSON files.")
    parser.add_argument("--project-name", required=True, help="Pointcloud project name under pointclouds/.")
    parser.add_argument("--pointcloud-display-mode", default="rgb", choices=["intensity", "elevation", "rgb"], help="Default Potree pointcloud attribute to display.")
    parser.add_argument("--point-radius", type=float, default=5.0, help="Radius used for point vector overlays.")
    parser.add_argument("--fallback-projection", default="", help="Fallback source projection (Proj4/EPSG) for Cesium camera sync.")
    parser.add_argument("--cesium-map", type=parse_bool, default=False, help="Enable Cesium 1.83 baseline map integration.")
    parser.add_argument("--cesium-map-sea-level", type=float, default=0.0, help="MAP_ELEVATION_OFFSET_M value.")
    parser.add_argument("--manifest-path", default="", help="Optional PotreeCraft manifest path with per-layer function settings.")
    args = parser.parse_args()

    return generate_potree_html(
        vector_folder=args.vector_folder,
        project_name=args.project_name,
        pointcloud_display_mode=args.pointcloud_display_mode,
        point_radius=args.point_radius,
        fallback_projection=args.fallback_projection,
        cesium_map=args.cesium_map,
        cesium_map_sea_level=args.cesium_map_sea_level,
        manifest_path=args.manifest_path or None,
    )


if __name__ == "__main__":
    raise SystemExit(main())
