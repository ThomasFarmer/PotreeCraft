# PotreeCraft
version 0.2.1120, Pre-alpha build

PotreeCraft is a QGIS plugin which provides a graphic UI for integrating vector-based data into Potree projects.
This is an open source tool for beginner users of the potree project or colleagues with no javascript knowledge. The PotreeCraft tool builds on the well-known Potree project, and lets users create pointcloud publications with integrated shapefile-based vector data with little to no effort. The plugin reads the added vector layer information of a given QGIS project and passed over the layer metadata and coloring styles to Potree, thus allowing the user to manage the vector-based data through a familiar and user-friendly interface what QGIS 3 provides.
The plugin itself relies on LAStools and PotreeConverter:
- LAStools' blast2dem function allows this widget to import pointclouds as raster layers, so the users would be able to check if the vector layers align,
- PotreeConverter will create the blank Potree project itself, which later recieves the additional vector data files and a new homepage for the project with the necessary javascript code added.

If you do not have these installed on your computer, you can download a copy of LAStools here: 
and you can download PotreeConverter from the project's github page, or this link:

This project was created and tested with the version 1.6, migration to 1.7 will follow soon.

# How to use the plugin

First, download the ZIP here, and install it in QGIS. (plugins -> manage and install plugins -> install plugin from zip)
Link:

After the installation go to the settings tab, and show the plugin where can it find LAStools and PotreeConverter, and press "save". If the locations are correct and the plugin found the required files the plugin will enable the rest of the interface, and will prompt the user that it is ready for use.

1. Select the pointcloud, and load it into QGIS. The "blast2dem coloring for QGIS" radiobutton group selects the coloring theme for the raster layer. A console window will pop up, just wait patiently to finish the task it's been assigned to do. After that QGIS will prompt the user with a CRS selection screen (as part of the "add raster layer" task).
Note: With my test data RGB coloring ended up being a grayscale version of the RGB image.
![pointcloud_window](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/pointcloud_window.jpg)
![blast2dem](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/blast2dem_running.jpg)

2. Add some vector data as well.
![qgis](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/qgis_project.jpg)

3. The window loads the layer data on opening, but in case of a change, there's a button on the Vector layer settings tab labeled "Reload layers from current project". That will refresh the data and pre-process the necessary information for the compilation procedure.
![vector_window](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/vector_window.jpg)

4. Then select an output folder for the potree project and press "Compile project", let it run like in the previous case.
![potreeconverter](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/potreeconverter_running.jpg)
5. Finally, check it in the browser.
Note: Potree requires a web server to operate, such as python's SimpleHTTPServer, or Apache. For more information on this topic check out the official Potree github page.
![potree_running](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/potree_running_1119.jpg)
