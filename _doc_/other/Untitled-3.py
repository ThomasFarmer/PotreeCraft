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
import math
import statistics

# =========================
# USER SETTINGS
# =========================

INPUT_LAYER_NAME = "camera_shots_polygon_eov"
ID_FIELD = "filename"     # set to None if needed

OUTPUT_GPKG = "/home/troll4hire/vm_share/swamp_test_vectors/front_side_overlap_report.gpkg"
OUTPUT_LAYER_NAME = "front_side_overlap_report"
OUTPUT_CSV = "/home/troll4hire/vm_share/swamp_test_vectors/front_side_overlap_report.csv"

EPS = 1e-9

# Search radius for candidate neighbors (meters)
SEARCH_RADIUS = 400.0

# Angular tolerance for accepting forward/side candidates (degrees)
FORWARD_ANGLE_MAX = 35.0
SIDE_ANGLE_TOL = 35.0

# If True, deduplicate by ID_FIELD
DEDUP_BY_ID = True

# =========================
# HELPER FUNCTIONS
# =========================

def geom_area(g):
    return 0.0 if g is None or g.isEmpty() else g.area()

def overlap_pct(base_geom, other_geom):
    if base_geom is None or other_geom is None:
        return 0.0
    a = base_geom.area()
    if a <= EPS:
        return 0.0
    if not base_geom.intersects(other_geom):
        return 0.0
    inter = base_geom.intersection(other_geom)
    if inter.isEmpty():
        return 0.0
    return 100.0 * inter.area() / a

def centroid_xy(feat):
    c = feat.geometry().centroid().asPoint()
    return (c.x(), c.y())

def dist(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)

def normalize(vx, vy):
    n = math.hypot(vx, vy)
    if n <= EPS:
        return (0.0, 0.0)
    return (vx / n, vy / n)

def dot(ax, ay, bx, by):
    return ax * bx + ay * by

def perp_left(vx, vy):
    return (-vy, vx)

def angle_deg_between(ax, ay, bx, by):
    na = math.hypot(ax, ay)
    nb = math.hypot(bx, by)
    if na <= EPS or nb <= EPS:
        return 180.0
    c = max(-1.0, min(1.0, (ax * bx + ay * by) / (na * nb)))
    return math.degrees(math.acos(c))

def nearest_distance_same_id(feat_list):
    # fallback estimate if needed
    if len(feat_list) < 2:
        return None
    coords = [centroid_xy(f) for f in feat_list]
    best = None
    for i in range(len(coords)):
        x1, y1 = coords[i]
        for j in range(i + 1, len(coords)):
            x2, y2 = coords[j]
            d = dist(x1, y1, x2, y2)
            if d > EPS and (best is None or d < best):
                best = d
    return best

def estimate_global_forward_vector(features):
    # PCA-like estimate from centroids: longest spread direction
    pts = [centroid_xy(f) for f in features]
    if len(pts) < 2:
        return (1.0, 0.0)

    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)

    sxx = sum((p[0] - mx) ** 2 for p in pts)
    syy = sum((p[1] - my) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)

    # principal eigenvector of [[sxx, sxy], [sxy, syy]]
    trace = sxx + syy
    det = sxx * syy - sxy * sxy
    disc = max(0.0, trace * trace - 4.0 * det)
    lam = 0.5 * (trace + math.sqrt(disc))

    if abs(sxy) > EPS:
        vx = lam - syy
        vy = sxy
    else:
        vx, vy = (1.0, 0.0) if sxx >= syy else (0.0, 1.0)

    return normalize(vx, vy)

def estimate_local_forward(feat, feature_by_id, index, global_fwd):
    """
    Estimate local forward direction from nearby centroids.
    Chooses the nearest neighbor roughly aligned to global forward axis.
    """
    x0, y0 = centroid_xy(feat)
    rect = feat.geometry().boundingBox()
    rect.grow(SEARCH_RADIUS)
    cand_ids = index.intersects(rect)

    best_plus = None
    best_minus = None

    gfx, gfy = global_fwd

    for cid in cand_ids:
        if cid == feat.id():
            continue
        other = feature_by_id[cid]
        x1, y1 = centroid_xy(other)
        vx, vy = x1 - x0, y1 - y0
        d = math.hypot(vx, vy)
        if d <= EPS:
            continue

        ang = angle_deg_between(vx, vy, gfx, gfy)
        if ang <= FORWARD_ANGLE_MAX:
            if best_plus is None or d < best_plus[0]:
                best_plus = (d, vx, vy)
        elif angle_deg_between(vx, vy, -gfx, -gfy) <= FORWARD_ANGLE_MAX:
            if best_minus is None or d < best_minus[0]:
                best_minus = (d, vx, vy)

    if best_plus is not None:
        return normalize(best_plus[1], best_plus[2])
    if best_minus is not None:
        return normalize(-best_minus[1], -best_minus[2])

    return global_fwd

def best_candidate_in_direction(feat, feature_by_id, index, dir_vec, side_mode=False):
    """
    side_mode=False: seeks nearest candidate aligned with dir_vec
    side_mode=True: seeks nearest candidate aligned with dir_vec (left/right side axis)
    """
    x0, y0 = centroid_xy(feat)
    rect = feat.geometry().boundingBox()
    rect.grow(SEARCH_RADIUS)
    cand_ids = index.intersects(rect)

    best = None  # (distance, angle, feature, dx, dy)

    for cid in cand_ids:
        if cid == feat.id():
            continue
        other = feature_by_id[cid]
        x1, y1 = centroid_xy(other)
        vx, vy = x1 - x0, y1 - y0
        d = math.hypot(vx, vy)
        if d <= EPS:
            continue

        ang = angle_deg_between(vx, vy, dir_vec[0], dir_vec[1])
        if side_mode:
            if ang > SIDE_ANGLE_TOL:
                continue
        else:
            if ang > FORWARD_ANGLE_MAX:
                continue

        if best is None or d < best[0]:
            best = (d, ang, other, vx, vy)

    return best

# =========================
# LOAD INPUT LAYER
# =========================

layers = QgsProject.instance().mapLayersByName(INPUT_LAYER_NAME)
if not layers:
    raise Exception(f"Layer not found: {INPUT_LAYER_NAME}")

layer = layers[0]

if layer.geometryType() != QgsWkbTypes.PolygonGeometry:
    raise Exception("Input layer must be a polygon layer.")

field_names = [f.name() for f in layer.fields()]
if ID_FIELD is not None and ID_FIELD not in field_names:
    raise Exception(f"ID_FIELD '{ID_FIELD}' not found in layer fields.")

# =========================
# LOAD FEATURES
# =========================

raw_features = list(layer.getFeatures())
if not raw_features:
    raise Exception("Input layer has no features.")

# Optional deduplication by ID field
if DEDUP_BY_ID and ID_FIELD:
    seen = {}
    for f in raw_features:
        key = str(f[ID_FIELD])
        # keep first occurrence
        if key not in seen:
            seen[key] = f
    features = list(seen.values())
else:
    features = raw_features

if len(features) < 2:
    raise Exception("Need at least 2 features.")

feature_by_id = {f.id(): f for f in features}

index = QgsSpatialIndex()
for f in features:
    index.addFeature(f)

global_fwd = estimate_global_forward_vector(features)
global_left = perp_left(global_fwd[0], global_fwd[1])

print("Global forward vector:", global_fwd)

# =========================
# PREPARE OUTPUT
# =========================

crs_authid = layer.crs().authid()
out_layer = QgsVectorLayer(f"Polygon?crs={crs_authid}", OUTPUT_LAYER_NAME, "memory")
prov = out_layer.dataProvider()

fields = QgsFields()
fields.append(QgsField("src_fid", QVariant.Int))
if ID_FIELD:
    fields.append(QgsField("src_id", QVariant.String))
fields.append(QgsField("area_m2", QVariant.Double))

fields.append(QgsField("l_fwd", QVariant.Double))
fields.append(QgsField("l_back", QVariant.Double))
fields.append(QgsField("l_front", QVariant.Double))

fields.append(QgsField("q_left", QVariant.Double))
fields.append(QgsField("q_right", QVariant.Double))
fields.append(QgsField("q_side", QVariant.Double))

fields.append(QgsField("dist_fwd", QVariant.Double))
fields.append(QgsField("dist_back", QVariant.Double))
fields.append(QgsField("dist_left", QVariant.Double))
fields.append(QgsField("dist_right", QVariant.Double))

fields.append(QgsField("ang_fwd", QVariant.Double))
fields.append(QgsField("ang_back", QVariant.Double))
fields.append(QgsField("ang_left", QVariant.Double))
fields.append(QgsField("ang_right", QVariant.Double))

fields.append(QgsField("risk_class", QVariant.String))

prov.addAttributes(fields)
out_layer.updateFields()

rows = []

# =========================
# MAIN ANALYSIS
# =========================

for i, feat in enumerate(features, start=1):
    geom = feat.geometry()
    area_i = geom.area()
    if area_i <= EPS:
        continue

    # local forward estimated from neighbor centroids
    fwd = estimate_local_forward(feat, feature_by_id, index, global_fwd)
    back = (-fwd[0], -fwd[1])
    left = perp_left(fwd[0], fwd[1])
    right = (-left[0], -left[1])

    cand_fwd = best_candidate_in_direction(feat, feature_by_id, index, fwd, side_mode=False)
    cand_back = best_candidate_in_direction(feat, feature_by_id, index, back, side_mode=False)
    cand_left = best_candidate_in_direction(feat, feature_by_id, index, left, side_mode=True)
    cand_right = best_candidate_in_direction(feat, feature_by_id, index, right, side_mode=True)

    def unpack(cand):
        if cand is None:
            return (0.0, None, None)
        d, ang, other, vx, vy = cand
        pct = overlap_pct(geom, other.geometry())
        return (pct, d, ang)

    front_fwd, dist_fwd, ang_fwd = unpack(cand_fwd)
    front_back, dist_back, ang_back = unpack(cand_back)
    side_left, dist_left, ang_left = unpack(cand_left)
    side_right, dist_right, ang_right = unpack(cand_right)

    l_front = max(front_fwd, front_back)
    q_side = max(side_left, side_right)

    # Simple risk classification
    if l_front >= 80.0 and q_side >= 70.0:
        risk = "good"
    elif l_front >= 75.0 and q_side >= 60.0:
        risk = "usable"
    elif l_front >= 65.0 and q_side >= 50.0:
        risk = "weak"
    else:
        risk = "terrible"

    out_feat = QgsFeature(out_layer.fields())
    out_feat.setGeometry(geom)

    attrs = [feat.id()]
    if ID_FIELD:
        attrs.append(str(feat[ID_FIELD]))
    attrs.extend([
        float(area_i),
        float(front_fwd),
        float(front_back),
        float(l_front),
        float(side_left),
        float(side_right),
        float(q_side),
        float(dist_fwd if dist_fwd is not None else -1),
        float(dist_back if dist_back is not None else -1),
        float(dist_left if dist_left is not None else -1),
        float(dist_right if dist_right is not None else -1),
        float(ang_fwd if ang_fwd is not None else -1),
        float(ang_back if ang_back is not None else -1),
        float(ang_left if ang_left is not None else -1),
        float(ang_right if ang_right is not None else -1),
        risk
    ])
    out_feat.setAttributes(attrs)
    prov.addFeature(out_feat)

    row = {
        "src_fid": feat.id(),
        "src_id": str(feat[ID_FIELD]) if ID_FIELD else "",
        "area_m2": area_i,
        "l_fwd": front_fwd,
        "l_back": front_back,
        "l_front": l_front,
        "q_left": side_left,
        "q_right": side_right,
        "q_side": q_side,
        "dist_fwd": dist_fwd if dist_fwd is not None else -1,
        "dist_back": dist_back if dist_back is not None else -1,
        "dist_left": dist_left if dist_left is not None else -1,
        "dist_right": dist_right if dist_right is not None else -1,
        "ang_fwd": ang_fwd if ang_fwd is not None else -1,
        "ang_back": ang_back if ang_back is not None else -1,
        "ang_left": ang_left if ang_left is not None else -1,
        "ang_right": ang_right if ang_right is not None else -1,
        "risk_class": risk
    }
    rows.append(row)

    if i % 20 == 0:
        print(f"Processed {i} / {len(features)} features")

out_layer.updateExtents()
QgsProject.instance().addMapLayer(out_layer)

# =========================
# WRITE OUTPUTS
# =========================

if os.path.exists(OUTPUT_GPKG):
    os.remove(OUTPUT_GPKG)

result = QgsVectorFileWriter.writeAsVectorFormat(
    out_layer,
    OUTPUT_GPKG,
    "UTF-8",
    out_layer.crs(),
    "GPKG"
)
print("GeoPackage write result:", result)

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "src_fid", "src_id", "area_m2",
            "l_fwd", "l_back", "l_front",
            "q_left", "q_right", "q_side",
            "dist_fwd", "dist_back", "dist_left", "dist_right",
            "ang_fwd", "ang_back", "ang_left", "ang_right",
            "risk_class"
        ]
    )
    writer.writeheader()
    writer.writerows(rows)

print("CSV written to:", OUTPUT_CSV)

# =========================
# SUMMARY
# =========================

if rows:
    front_vals = [r["l_front"] for r in rows]
    side_vals = [r["q_side"] for r in rows]

    print("\nSummary:")
    print(f"Features: {len(rows)}")
    print(f"Mean front_best: {statistics.mean(front_vals):.2f}")
    print(f"Median front_best: {statistics.median(front_vals):.2f}")
    print(f"Min front_best: {min(front_vals):.2f}")
    print(f"Mean side_best: {statistics.mean(side_vals):.2f}")
    print(f"Median side_best: {statistics.median(side_vals):.2f}")
    print(f"Min side_best: {min(side_vals):.2f}")

    counts = {}
    for r in rows:
        counts[r["risk_class"]] = counts.get(r["risk_class"], 0) + 1
    print("Risk classes:", counts)