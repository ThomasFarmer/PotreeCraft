import json

from qgis_plugin.potreecraft_geojson_reader import (
    CAMERA_MODE_CUSTOM,
    CAMERA_MODE_FIT_TO_SCREEN,
    generate_potree_html,
)


def test_generate_potree_html_uses_fit_to_screen_camera_by_default(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Points.geojson").write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Point", "coordinates": [10, 20]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        default_camera_mode=CAMERA_MODE_FIT_TO_SCREEN,
        output_dir=output_dir,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "viewer.fitToScreen();" in html


def test_generate_potree_html_uses_custom_camera_position_when_requested(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Points.geojson").write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Point", "coordinates": [10, 20]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        default_camera_mode=CAMERA_MODE_CUSTOM,
        default_camera_position=((628208.246, 134458.72, 152.999), (628215.346, 134467.899, 149.243)),
        output_dir=output_dir,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "viewer.scene.view.setView(" in html
    assert "[628208.246, 134458.72, 152.999]" in html
    assert "[628215.346, 134467.899, 149.243]" in html


def test_generate_potree_html_renders_annotation_points_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    geojson_path = vector_dir / "Test_Points.geojson"
    geojson_path.write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {
                            "title_field": "Pump Station",
                            "description_field": "Status: active",
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [589769.27, 231236.83, 783.89],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Points",
                        "function": "annotation",
                        "annotation": {
                            "enabled": True,
                            "title_field": "title_field",
                            "description_field": "description_field",
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "scene.annotations.add(new Potree.Annotation" in html
    assert '"Pump Station"' in html
    assert '"Status: active"' in html
    assert '[589769.27, 231236.83, 783.89]' in html
    assert "const Test_Points_1 = new CircleOnScreen" not in html


def test_generate_potree_html_keeps_default_point_rendering_without_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    geojson_path = vector_dir / "Test_Points.geojson"
    geojson_path.write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"label": "plain point"},
                        "geometry": {"type": "Point", "coordinates": [10, 20]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "const Test_Points_1 = new CircleOnScreen" in html
    assert "scene.annotations.add(new Potree.Annotation" not in html


def test_generate_potree_html_renders_mesh_sphere_points_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Points.geojson").write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Point", "coordinates": [10, 20, 30]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Points",
                        "function": "point (mesh sphere)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "const Test_Points_1 = new MeshPointOnScreen" in html
    assert "1.0," in html
    assert "displaymesh();" in html


def test_generate_potree_html_injects_dynamic_proj4_definitions_and_fallback(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    cesium_runtime = output_dir / "libs" / "Cesium183" / "Build" / "Cesium"
    cesium_runtime.mkdir(parents=True)
    (cesium_runtime / "Cesium.js").write_text("", encoding="utf-8")

    (vector_dir / "Test_Points.geojson").write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Point", "coordinates": [10, 20]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        cesium_map=True,
        fallback_projection="EPSG:23700",
        projection_definitions=[
            {
                "name": "EPSG:23700",
                "proj4": "+proj=somerc +lat_0=47.14439372222222 +lon_0=19.04857177777778 +k_0=0.99993 +x_0=650000 +y_0=200000 +ellps=GRS67 +towgs84=52.17,-71.82,-14.9 +units=m +no_defs",
            }
        ],
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert 'proj4.defs("EPSG:23700"' in html
    assert 'const FALLBACK_POINTCLOUD_PROJECTION = "EPSG:23700";' in html


def test_generate_potree_html_renders_mesh_disc_points_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Points.geojson").write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Point", "coordinates": [10, 20, 30]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Points",
                        "function": "point (mesh disc)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "const Test_Points_1 = new MeshPointOnScreen" in html
    assert "0.16666666666666666," in html
    assert "displaymesh();" in html
    assert "const Test_Points_1 = new CircleOnScreen" not in html


def test_generate_potree_html_renders_coordinate_measurement_points_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Points.geojson").write_text(
        json.dumps(
            {
                "name": "Test Points",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {"type": "Point", "coordinates": [10, 20, 30]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Points",
                        "function": "coordinates (measurement)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "createCoordinateMeasurement([10, 20, 30]);" in html
    assert "measure.showCoordinates = true;" in html
    assert "measure.maxMarkers = 1;" in html
    assert "const Test_Points_1 = new CircleOnScreen" not in html


def test_generate_potree_html_renders_distance_measurement_lines_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Lines.geojson").write_text(
        json.dumps(
            {
                "name": "Test Lines",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Lines",
                        "function": "distance (measurement)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "createDistanceMeasurement([[1, 2, 3], [4, 5, 6], [7, 8, 9]]);" in html
    assert "activeViewer.scene.addMeasurement(measure);" in html
    assert "const Test_Lines_1 = new LineOnScreen" not in html


def test_generate_potree_html_renders_height_measurement_lines_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Lines.geojson").write_text(
        json.dumps(
            {
                "name": "Test Lines",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[1, 2, 3], [4, 5, 99], [7, 8, 9]],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Lines",
                        "function": "height (measurement)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "createHeightMeasurement([[1, 2, 3], [4, 5, 99], [7, 8, 9]]);" in html
    assert "const endpoints = [vertices[0], vertices[vertices.length - 1]];" in html
    assert "const Test_Lines_1 = new LineOnScreen" not in html


def test_generate_potree_html_renders_height_profile_lines_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Lines.geojson").write_text(
        json.dumps(
            {
                "name": "Test Lines",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "LineString",
                            "coordinates": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Lines",
                        "function": "height (profile)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "createHeightProfile([[1, 2, 3], [4, 5, 6], [7, 8, 9]]);" in html
    assert "profile.setWidth(6);" in html
    assert "activeViewer.scene.addProfile(profile);" in html
    assert "const Test_Lines_1 = new LineOnScreen" not in html


def test_generate_potree_html_renders_area_measurement_polygons_from_manifest(tmp_path):
    vector_dir = tmp_path / "vectors"
    vector_dir.mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    (vector_dir / "Test_Polygons.geojson").write_text(
        json.dumps(
            {
                "name": "Test Polygons",
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {},
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[1, 2, 3], [4, 2, 3], [4, 5, 3], [1, 2, 3]]],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    manifest_path = tmp_path / "potreecraft_project_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "layers": [
                    {
                        "name": "Test Polygons",
                        "function": "area (measurement)",
                        "annotation": {"enabled": False, "title_field": "", "description_field": ""},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = generate_potree_html(
        vector_folder=vector_dir,
        project_name="demo_cloud",
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    html = (output_dir / "potree_main.html").read_text(encoding="utf-8")

    assert result == 0
    assert "createAreaMeasurement([[1, 2, 3], [4, 2, 3], [4, 5, 3], [1, 2, 3]]);" in html
    assert "measure.closed = true;" in html
    assert "measure.showArea = true;" in html
    assert "const Test_Polygons_1 = new PolygonOnScreen" not in html
