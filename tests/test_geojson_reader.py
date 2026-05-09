import json

from qgis_plugin.potreecraft_geojson_reader import generate_potree_html


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
    assert "const Test_Points_1 = new CircleOnScreen" not in html


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
