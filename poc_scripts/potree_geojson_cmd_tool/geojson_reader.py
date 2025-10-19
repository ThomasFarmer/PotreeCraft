import json
import random
import logging
from os import listdir
from os.path import isfile, join

geojsonlist = []
gjs_feature_list = []
logging.basicConfig(filename="geojson_reader.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.DEBUG)

class simple_geojson_reader():
    def __init__(self, filepath):
        self.filepath = filepath
        self.name = None
        self.crs = None
        self.geomtype = None
        self.feature_count = None
        self.feature_list = []
        with open(self.filepath) as f:
            d = json.load(f)
            #print(d)
            self.name = d.get('name')
            self.crs = d.get('crs').get('properties')
            self.geomtype = d.get('features')[0].get('geometry').get('type')
            self.feature_count = len(d.get('features'))
    def print_metadata(self):
        logging.info("Name: {}" .format(self.name))
        logging.info("CRS info: {}".format(self.crs))
        logging.info("geometry info: {}".format(self.geomtype))
        logging.info("feature count: {}".format(self.feature_count))


    def extract_coordinates(self):
        with open(self.filepath) as f:
            d = json.load(f)
            linectr = 0
            lcolor= "#{r}{g}{b}".format(r=str(hex(random.randint(0,255)))[2:4],g=str(hex(random.randint(0,255)))[2:4],b=str(hex(random.randint(0,255)))[2:4])

            for ft in d.get('features'):
                
                coorddata = ft.get('geometry').get('coordinates')
                
                if ft.get('geometry').get('type') == "LineString":
                    logging.debug("LineString")
                    coordsmerged = []
                    for coordinates in coorddata:
                        print("coordinates:"+str(coordinates))
                        coordsmerged = coordsmerged+coordinates
                    print("coordsmerged:"+str(coordsmerged))
                    linectr+=1
                    gjs_feature_list.append({"line_color": lcolor,"coordinates": coordsmerged, "linename": self.name+"_"+str(linectr) })

                elif ft.get('geometry').get('type') == "MultiLineString":
                    logging.debug("MultiLineString")
                    #print(coorddata)
                    for line in coorddata:
                        coordsmerged = []
                        for coordinates in line:
                            print("coordinates:"+str(coordinates))
                            coordsmerged = coordsmerged+coordinates
                        print("coordsmerged:"+str(coordsmerged))
                        linectr+=1
                        gjs_feature_list.append({"line_color": lcolor ,"coordinates": coordsmerged, "linename": self.name+"_"+str(linectr) })
                        
        logging.debug(self.feature_list)
                
class potree_html_generator():
    def __init__(self):
        pass
    @classmethod
    def write_potree_html(cls):
        with open("potree_main.html", "w") as f:
            # original potree html section, untouched
            f.write(r'''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="description" content="">
	<meta name="author" content="">
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
	<script src="./libs/three.js/build/three.min.js"></script>
	<script src="./libs/three.js/extra/lines.js"></script>
	<script src="./libs/other/BinaryHeap.js"></script>
	<script src="./libs/tween/tween.min.js"></script>
	<script src="./libs/d3/d3.js"></script>
	<script src="./libs/proj4/proj4.js"></script>
	<script src="./libs/openlayers3/ol.js"></script>
	<script src="./libs/i18next/i18next.js"></script>
	<script src="./libs/jstree/jstree.js"></script>
	<script src="./libs/potree/potree.js"></script>
	<script src="./libs/plasio/js/laslaz.js"></script>
	
	<!-- INCLUDE ADDITIONAL DEPENDENCIES HERE -->
		document.title = "";
		viewer.setEDLEnabled(false);
		viewer.setBackground("gradient"); // ["skybox", "gradient", "black", "white"];
		viewer.setDescription(``);
	
	<div class="potree_container" style="position: absolute; width: 100%; height: 100%; left: 0px; top: 0px; ">
		<div id="potree_render_area" style="background-image: url('./libs/potree/resources/images/background.jpg');"></div>
		<div id="potree_sidebar_container"> </div>
	</div>
	
	<script>
	
		window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));
		
		viewer.setEDLEnabled(true);
		viewer.setFOV(60);
		viewer.setPointBudget(2_000_000);
		document.title = "";
		viewer.setEDLEnabled(false);
		viewer.setBackground("gradient"); // ["skybox", "gradient", "black", "white"];
		viewer.setDescription(``);
		viewer.loadSettingsFromURL();
		
		viewer.setDescription("");
		
		viewer.loadGUI(() => {
			viewer.setLanguage('en');
			$("#menu_appearance").next().show();
			$("#menu_tools").next().show();
			$("#menu_clipping").next().show();
			viewer.toggleSidebar();
		});
		
		Potree.loadPointCloud("pointclouds/asdlol/cloud.js", "asdlol", e => {
			let pointcloud = e.pointcloud;
			let material = pointcloud.material;
			viewer.scene.addPointCloud(pointcloud);
			//material.activeAttributeName = "rgba"; //[rgba, intensity, classification, ...]
			material.size = 1;
			material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
			material.shape = Potree.PointShape.SQUARE;
			viewer.fitToScreen();
		});

	</script>
                    
'''
                    )
            # second script, including our class declaration for lines
            f.write(r''' 	<script>

		// basic vector drawing script, v2
		// create instances of LineOnScreen class with coordinates matching the cloud's crs, and give proper parameters for coloring

		class LineOnScreen {
			constructor(coords, lcolor, lwidth, lopacity, groupname) {
			this.coords = coords;
			this.lcolor = lcolor;
			this.lwidth = lwidth;
			this.lopacity = lopacity;
			this.groupname = groupname;
			}
			displayline(){
				//console.log("drawing line at: " + this.coords);

				const positions = new Float32Array(this.coords);
				const geometry = new THREE.BufferGeometry();
				geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
				//console.log(geometry);

				const material = new THREE.LineBasicMaterial({
				linewidth: this.lwidth,          // note: linewidth only works on special builds / some platforms
				transparent: true,
				color: this.lcolor,
				opacity: this.lopacity
				});

				const line = new THREE.Line(geometry, material);

				const vectorGroup = new THREE.Group();
				vectorGroup.name = this.groupname;
				vectorGroup.add(line);

				this.vectorGroup = vectorGroup;

				viewer.scene.scene.add(vectorGroup);
				//console.log("Added line group to scene:", vectorGroup);
				
			}
  
		}
'''
                    )
            # third segment, the dynamic section using the LineOnScreen class

            for ft in gjs_feature_list:
                f.write(r'		// pole of street sign'+'\n')
                f.write("		const {} = new LineOnScreen(".format(ft.get("linename"))+'\n')
                f.write('           {jscoords},'.format(jscoords=ft.get('coordinates'))+'\n')
                f.write('           "{jslinecolor}",'.format(jslinecolor=ft.get('line_color'))+'\n')
                f.write('           {jslinewidth},'.format(jslinewidth=1)+'\n')
                f.write('           {jslineopacity},'.format(jslineopacity=0.75)+'\n')
                f.write('           "{jsgroup}");'.format(jsgroup="vectorclass")+'\n')
                f.write('		{}.displayline();\n\n'.format(ft.get("linename"))+'\n')


            # fourth, closing segment
            f.write(r'''        // ------------------------------------------------------------------

		viewer.renderer.render(viewer.scene.scene, viewer.scene.getActiveCamera());

		</script>
	
  </body>
</html>
 '''
                    )

# Main section of the code, this is where it is tied together. Put behind main for future modular use.
if __name__ == "__main__":
    print("Welcome to the simple potree geojson reader script.")
    print("Please type in the location of the vector data input folder: ")
    folderpath = input()
    geojsonlist = listdir(folderpath)

    if len(geojsonlist) == 0:
        print("This folder contains no data.")
    for gjs in geojsonlist:
        print("Files to be processed: {}".format(geojsonlist))
        logging.info("Files to be processed: {}".format(geojsonlist))
        try:
            current_gjs = simple_geojson_reader(join(folderpath,gjs))

            current_gjs.print_metadata()
            current_gjs.extract_coordinates()
        except Exception as genex:
            logging.exception("Error processing file: {}".format(join(folderpath,gjs)))

        potree_html_generator.write_potree_html()