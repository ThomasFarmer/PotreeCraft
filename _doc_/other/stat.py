from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsProject,
    QgsSpatialIndex,
    QgsFeature,
    QgsVectorLayer,
    QgsField,
    QgsFields,
    QgsWkbTypes,
    QgsVectorFileWriter
)
import os
import csv
import statistics

# =========================
# USER SETTINGS
# =========================

# Name of your polygon footprint layer in QGIS
INPUT_LAYER_NAME = "camera_shots_polygon_eov"

# Optional attribute to carry through into the report
# Set to None if you do not want one
ID_FIELD = "filename"

# Output paths
OUTPUT_GPKG = "/mnt/data/overlap_report.gpkg"
OUTPUT_LAYER_NAME = "overlap_report"
OUTPUT_CSV = "/mnt/data/overlap_report.csv"

# Tiny tolerance to avoid divide-by-zero issues
EPS = 1e-9

# =========================
# LOAD INPUT LAYER
# =========================

layers = QgsProject.instance().mapLayersByName(INPUT_LAYER_NAME)
if not layers:
    raise Exception(f"Layer not found: {INPUT_LAYER_NAME}")

layer = layers[0]

if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
    raise Exception("Input layer must be a polygon layer.")

# =========================
# PREPARE FEATURES + INDEX
# =========================

features = list(layer.getFeatures())
if not features:
    raise Exception("Input layer has no features.")

feature_by_id = {f.id(): f for f in features}
index = QgsSpatialIndex(features)

# =========================
# PREPARE OUTPUT LAYER
# =========================

crs_authid = layer.crs().authid()
out_layer = QgsVectorLayer(f"Polygon?crs={crs_authid}", OUTPUT_LAYER_NAME, "memory")
prov = out_layer.dataProvider()

fields = QgsFields()
fields.append(QgsField("src_fid", QVariant.Int))
if ID_FIELD and ID_FIELD in [fld.name() for fld in layer.fields()]:
    fields.append(QgsField("src_id", QVariant.String))
fields.append(QgsField("area_m2", QVariant.Double))
fields.append(QgsField("n_neighbors", QVariant.Int))
fields.append(QgsField("max_pairpct", QVariant.Double))
fields.append(QgsField("mean_pairpct", QVariant.Double))
fields.append(QgsField("cover_any_pct", QVariant.Double))
fields.append(QgsField("uncovered_pct", QVariant.Double))
fields.append(QgsField("sum_pairpct", QVariant.Double))

prov.addAttributes(fields)
out_layer.updateFields()

# =========================
# MAIN ANALYSIS
# =========================

rows = []

for i, feat in enumerate(features, start=1):
    geom = feat.geometry()
    if geom is None or geom.isEmpty():
        continue

    area_i = geom.area()
    if area_i <= EPS:
        continue

    bbox = geom.boundingBox()
    candidate_ids = index.intersects(bbox)

    pair_pcts = []
    neighbor_geoms = []
    n_neighbors = 0

    for cand_id in candidate_ids:
        if cand_id == feat.id():
            continue

        other = feature_by_id[cand_id]
        other_geom = other.geometry()
        if other_geom is None or other_geom.isEmpty():
            continue

        if not geom.intersects(other_geom):
            continue

        inter = geom.intersection(other_geom)
        if inter.isEmpty():
            continue

        inter_area = inter.area()
        if inter_area <= EPS:
            continue

        n_neighbors += 1
        pair_pct = 100.0 * inter_area / area_i
        pair_pcts.append(pair_pct)
        neighbor_geoms.append(other_geom)

    if pair_pcts:
        max_pairpct = max(pair_pcts)
        mean_pairpct = sum(pair_pcts) / len(pair_pcts)
        sum_pairpct = sum(pair_pcts)
    else:
        max_pairpct = 0.0
        mean_pairpct = 0.0
        sum_pairpct = 0.0

    # True "covered by at least one other image" percentage:
    # dissolve logically by repeated combine, then intersect with current geom
    cover_any_pct = 0.0
    uncovered_pct = 100.0

    if neighbor_geoms:
        combined = neighbor_geoms[0]
        for g in neighbor_geoms[1:]:
            combined = combined.combine(g)

        covered_geom = geom.intersection(combined)
        covered_area = covered_geom.area() if not covered_geom.isEmpty() else 0.0
        cover_any_pct = 100.0 * covered_area / area_i
        uncovered_pct = max(0.0, 100.0 - cover_any_pct)

    out_feat = QgsFeature(out_layer.fields())
    out_feat.setGeometry(geom)
    attrs = [feat.id()]
    if ID_FIELD and ID_FIELD in [fld.name() for fld in layer.fields()]:
        attrs.append(str(feat[ID_FIELD]))
    attrs.extend([
        float(area_i),
        int(n_neighbors),
        float(max_pairpct),
        float(mean_pairpct),
        float(cover_any_pct),
        float(uncovered_pct),
        float(sum_pairpct),
    ])
    out_feat.setAttributes(attrs)
    prov.addFeature(out_feat)

    row = {
        "src_fid": feat.id(),
        "src_id": str(feat[ID_FIELD]) if ID_FIELD and ID_FIELD in [fld.name() for fld in layer.fields()] else "",
        "area_m2": area_i,
        "n_neighbors": n_neighbors,
        "max_pairpct": max_pairpct,
        "mean_pairpct": mean_pairpct,
        "cover_any_pct": cover_any_pct,
        "uncovered_pct": uncovered_pct,
        "sum_pairpct": sum_pairpct,
    }
    rows.append(row)

    if i % 20 == 0:
        print(f"Processed {i} / {len(features)} features")

out_layer.updateExtents()
QgsProject.instance().addMapLayer(out_layer)

# =========================
# WRITE GPKG
# =========================

if os.path.exists(OUTPUT_GPKG):
    os.remove(OUTPUT_GPKG)

err = QgsVectorFileWriter.writeAsVectorFormat(
    out_layer,
    OUTPUT_GPKG,
    "UTF-8",
    out_layer.crs(),
    "GPKG"
)
print("GeoPackage write result:", err)

# =========================
# WRITE CSV
# =========================

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "src_fid", "src_id", "area_m2", "n_neighbors",
            "max_pairpct", "mean_pairpct", "cover_any_pct",
            "uncovered_pct", "sum_pairpct"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("CSV written to:", OUTPUT_CSV)

# =========================
# SUMMARY STATS
# =========================

if rows:
    cover_vals = [r["cover_any_pct"] for r in rows]
    neigh_vals = [r["n_neighbors"] for r in rows]
    max_vals = [r["max_pairpct"] for r in rows]

    print("\nSummary:")
    print(f"Features: {len(rows)}")
    print(f"Mean cover_any_pct: {statistics.mean(cover_vals):.2f}")
    print(f"Median cover_any_pct: {statistics.median(cover_vals):.2f}")
    print(f"Min cover_any_pct: {min(cover_vals):.2f}")
    print(f"Mean n_neighbors: {statistics.mean(neigh_vals):.2f}")
    print(f"Mean max_pairpct: {statistics.mean(max_vals):.2f}")