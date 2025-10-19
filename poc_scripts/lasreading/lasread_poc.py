import laspy
import numpy as np
from scipy.interpolate import griddata
import rasterio
from rasterio.transform import from_origin

# step 1 - get raw data from file with laspy
#las = laspy.read("roadsection.las")
#las = laspy.read("autzen-classified.copc.laz")

with laspy.open("autzen_wgs84.laz", laz_backend=laspy.LazBackend.Laszip) as lazf:
    las = lazf.read()

x = las.x
y = las.y
z = las.z

print("x:", x)
print("y:", y)
print("z:", z)

# step 2 - interpolate to raser with scipy

# Define grid
xi = np.linspace(x.min(), x.max(), 1000)
yi = np.linspace(y.min(), y.max(), 1000)
xi, yi = np.meshgrid(xi, yi)

# Interpolate z values
#zi = griddata((x, y), z, (xi, yi), method="linear")
zi = griddata((x, y), z, (xi, yi), method="nearest")
print("zi:", zi)

# step 3 - save geotiff

transform = from_origin(x.min(), y.max(), (x.max()-x.min())/zi.shape[1], (y.max()-y.min())/zi.shape[0])

with rasterio.open(
    "test4.tif",
    "w",
    driver="GTiff",
    height=zi.shape[0],
    width=zi.shape[1],
    count=1,
    dtype="float32",
    crs="EPSG:4326",  # adjust to your coordinate system
    transform=transform,
    nodata=np.nan,
) as dst:
    dst.write(zi.astype("float32"), 1)