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

After installation open an empty project, and populate it with some vector data.
![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/qgis_project.jpg)


![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/blast2dem_running.jpg)
![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/pointcloud_window.jpg)
![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/potree_running_1119.jpg)
![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/potreeconverter_running.jpg	)

![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/settings_window.jpg)
![alt text](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/doc/vector_window.jpg)
