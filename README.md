# PotreeCraft
###### version 0.3b.0128, Pre-alpha build

PotreeCraft is a QGIS plugin which provides a graphic UI for integrating vector-based data into Potree projects.
This is an open source tool for beginner users of the potree project or colleagues with no javascript knowledge. The PotreeCraft tool builds on the well-known Potree project, and lets users create pointcloud publications with integrated shapefile-based vector data with little to no effort. The plugin reads the added vector layer information of a given QGIS project and passed over the layer metadata and coloring styles to Potree, thus allowing the user to manage the vector-based data through a familiar and user-friendly interface what QGIS 3 provides.
The plugin itself relies on LAStools and PotreeConverter:
- LAStools' blast2dem function allows this widget to import pointclouds as raster layers, so the users would be able to check if the vector layers align,
- PotreeConverter will create the blank Potree project itself, which later recieves the additional vector data files and a new homepage for the project with the necessary javascript code added.

If you do not have these installed on your computer, you can download a copy of LAStools through [this link](https://mega.nz/#!GhFxVKqD!7fD5PeldRdDT6j9O4_zoIgSDc82KnOjP0B2bgHPlH-s). 
and you can download PotreeConverter 1.6 stable release from the project's [github page](https://github.com/potree/PotreeConverter/releases/tag/1.6).

This project was created and tested with the version 1.6, migration to 1.7 will follow soon.

## Known issues
- The base Python threading seems to be incompatible with Qt5 in general or QGIS. While the window itself can be moved during process calls, the interface freezes. Migration to QThread class required. With this I think it is needless to say that the process bar in the bottom left corner absolutely lacks any functionality.
- Interface and functions to set Page title, Opacity and other cloud paramters are not implemented yet.
- Layer functionality interface (vector layer settings tab) is in a "rough-at-the-edges" state. Point layers later have the option to be marked as "Annotation" layers, which allows them to appear as such in Potree. The text appearing above these points are read from a selected record of the shape file itself. These layer markings are not represented yet in the QTreeView object itself.
- The vector layer handling needs a rework, because with the implementation of the annotations there are a lot of redundant data, extra checks and design issues in the code. The plan is to create distinct memory tables / dictionaries which can store the required information for points and annotations (and other elements added later), and the QTreeView widget will get its information from that. In its current state the load vectors function reads and parses the data it finds directly from QGIS, which makes the editing methods a lot more complicated than they should be.


## How to use the plugin

First, download the [.ZIP here](https://github.com/ThomasFarmer/PotreeCraft/tree/master/_build_), and install it in QGIS. *(plugins -> manage and install plugins -> install plugin from zip)*

For testing purposes the same .las cloud and two shape files which can be seen on the screenshots can be downloaded from [this link here](https://mega.nz/#!m48E3SrC!GvYnKGQ_2k2lBCbRszaMi26UjHj7SSvO9VVOP-p0y9Q).

After the installation go to the settings tab, and show the plugin where can it find LAStools and PotreeConverter, and press "save". If the locations are correct and the plugin found the required files the plugin will enable the rest of the interface, and will prompt the user that it is ready for use.

- [x] 1. Select the pointcloud, and load it into QGIS. The "blast2dem coloring for QGIS" radiobutton group selects the coloring theme for the raster layer. A console window will pop up, just wait patiently to finish the task it's been assigned to do. After that QGIS will prompt the user with a CRS selection screen (as part of the "add raster layer" task). *Note: With my test data RGB coloring ended up being a grayscale version of the RGB image.*
- [x] 2. Add some vector data as well.
- [x] 3. The window loads the layer data on opening, but in case of a change, there's a button on the Vector layer settings tab labeled "Reload layers from current project". That will refresh the data and pre-process the necessary information for the compilation procedure.
- [x] 4. Then select an output folder for the potree project and press "Compile project", let it run like in the previous case.
- [x] 5. Finally, check it in the browser. *Note: Potree requires a web server to operate, such as python's SimpleHTTPServer, or Apache. For more information on this topic check out the official Potree github page.*

## Screenshots
**Landing / information page:**
![info](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/about_window.jpg)

**Configuring the plugin:**
![settings](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/settings_window.jpg)

**Loading the pointcloud into QGIS as a raster layer:**
![pointcloud_window](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/pointcloud_window.jpg)
![blast2dem](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/blast2dem_running.jpg)

**The demo project in QGIS before passing it over to PotreeConverter - no annotations in this case:**
![qgis](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/qgis_project.jpg)

**The same demo project in QGIS with a point layer added as annotations:**
![qgis_atbl](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/attribute_table.jpg)

**A final check on the vector layer window:**
![vector_window](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/vector_window.jpg)

**Compiling the project:**
![potreeconverter](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/potreeconverter_running.jpg)

**The final state of the demo project with no annotations:**
![potree_running](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/potree_running_1130.jpg)

**The final state of the demo project with the first verse of "The Rocky Road To Dublin" added as annotations:**
![potree_running](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/potree_running_with_annots_1203.jpg)

**A section of the generated source code of the page:**
![potree_running](https://raw.githubusercontent.com/ThomasFarmer/PotreeCraft/master/_doc_/potree_page_source_code.jpg)

