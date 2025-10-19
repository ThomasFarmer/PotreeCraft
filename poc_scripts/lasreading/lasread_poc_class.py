import laspy
import numpy as np
from scipy.interpolate import griddata
import rasterio
from rasterio.transform import from_origin
import os


class FlatLas():
    def __init__(self, filename, filepath, crs, itype):
        self.filepath = filepath
        self.filename = filename
        self.output_crs_no = crs
        self.itype = itype
    def read_las(self):
        if str(self.filename[-4:]).lower() == ".las":
            las = laspy.read(os.path.join(self.filepath,self.filename))
        elif str(self.filename[-4:]).lower() == ".laz":
            with laspy.open(os.path.join(self.filepath,self.filename), laz_backend=laspy.LazBackend.Laszip) as lazf:
                las = lazf.read()
        else:
            raise Exception('Not a .las or .laz file. ({})'.format(self.filename))
        self.x = las.x
        self.y = las.y
        self.z = las.z
        self.intensity = las.intensity
        
    
    def interpolate_las(self):
        # Define grid
        xi = np.linspace(self.x.min(), self.x.max(), 1000)
        yi = np.linspace(self.y.min(), self.y.max(), 1000)
        xi, yi = np.meshgrid(xi, yi)

        # Interpolate z values
        #zi = griddata((x, y), z, (xi, yi), method="linear")
        if self.itype == "ELEVATION":
            zi = griddata((self.x, self.y), self.z, (xi, yi), method="nearest")
        elif self.itype == "INTENSITY":
            zi = griddata((self.x, self.y), self.intensity, (xi, yi), method="nearest")
        else:
            zi = griddata((self.x, self.y), self.z, (xi, yi), method="nearest")

        print("zi:", zi)
        transform = from_origin(self.x.min(), self.y.max(), (self.x.max()-self.x.min())/zi.shape[1], (self.y.max()-self.y.min())/zi.shape[0])

        return transform, zi
    
    def save_tif(self, transform, zi):
        with rasterio.open(
            "{}_{}_{}.tif".format(self.filename[:-4],self.output_crs_no,str(self.itype).lower()),
            "w",
            driver="GTiff",
            height=zi.shape[0],
            width=zi.shape[1],
            count=1,
            dtype="float32",
            #crs="EPSG:23700",  # adjust to your coordinate system
            crs="EPSG:{}".format(self.output_crs_no),
            transform=transform,
            nodata=np.nan,
        ) as dst:
            dst.write(np.flipud(zi).astype("float32"), 1)
        print("{}_{}_{}.tif".format(self.filename[:-4],self.output_crs_no,str(self.itype).lower()) + " saved.")

if __name__ == "__main__":
    newtif = FlatLas("roadsection.las",".","23700", "INTENSITY")
    newtif.read_las()
    lastr, laszi = newtif.interpolate_las()
    newtif.save_tif(lastr, laszi)

