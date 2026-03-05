import json
import random
import logging
import argparse
from os import listdir
from os.path import isfile, join

geojsonlist = []
lns_gjs_feature_list = []
pts_gjs_feature_list = []
ply_gjs_feature_list = []
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
			try:
				logging.info("self.geomtype -> d.get('features'): " + str(d.get('features')))
				self.geomtype = d.get('features')[0].get('geometry').get('type')
			except AttributeError as ae:
				self.geomtype = d.get('features').get('geometry').get('type')
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
			#lcolor= "#{r}{g}{b}".format(r=str(hex(random.randint(0,255)))[2:4],g=str(hex(random.randint(0,255)))[2:4],b=str(hex(random.randint(0,255)))[2:4])
			r, g, b = [random.randint(0, 255) for _ in range(3)]
			lcolor = f"#{r:02x}{g:02x}{b:02x}"
			logging.debug("Generated RBG color for {} layer is: {}".format(self.name, lcolor))
			for ft in d.get('features'):
				
				coorddata = ft.get('geometry').get('coordinates')
				
				if ft.get('geometry').get('type') == "LineString":
					logging.debug("LineString")
					coordsmerged = []
					for coordinates in coorddata:
						logging.debug("coordinates-in-coorddata: "+str(coordinates))
						coordsmerged = coordsmerged+coordinates
					logging.debug("coordsmerged: "+str(coordsmerged))
					linectr+=1
					lns_gjs_feature_list.append({"line_color": lcolor,"coordinates": coordsmerged, "linename": self.name+"_"+str(linectr) })

				elif ft.get('geometry').get('type') == "MultiLineString":
					logging.debug("MultiLineString")
					#print(coorddata)
					for line in coorddata:
						coordsmerged = []
						for coordinates in line:
							logging.debug("coordinates-in-line-in-coorddata: "+str(coordinates))
							coordsmerged = coordsmerged+coordinates
						logging.debug("coordsmerged: "+str(coordsmerged))
						linectr+=1
						lns_gjs_feature_list.append({"line_color": lcolor ,"coordinates": coordsmerged, "linename": self.name+"_"+str(linectr) })
				elif ft.get('geometry').get('type') == "Point":
					logging.debug("Point")
					coordsmerged = coorddata
					logging.debug("coorddata: "+str(coorddata))
					linectr+=1
					pts_gjs_feature_list.append({"line_color": lcolor,"coordinates": coorddata, "linename": self.name+"_"+str(linectr) })
				elif ft.get('geometry').get('type') == "MultiPoint":
					logging.debug("MultiPoint")
					#print(coorddata)
					for point in coorddata:
						logging.debug("point-in-coorddata: "+str(point))
						linectr+=1
						pts_gjs_feature_list.append({"line_color": lcolor ,"coordinates": point, "linename": self.name+"_"+str(linectr) })

				elif ft.get('geometry').get('type') == "Polygon":
					logging.debug("Polygon")
					exterior = coorddata[0]
					if len(exterior) < 3:
						logging.warning("Polygon exterior ring has fewer than 3 points, skipping")
						continue
					exterior_3d = [list(pt) if len(pt) >= 3 else [pt[0], pt[1], 0] for pt in exterior]
					linectr += 1
					ply_gjs_feature_list.append({
						"line_color": lcolor,
						"coordinates": exterior_3d,
						"linename": self.name + "_" + str(linectr)
					})

				elif ft.get('geometry').get('type') == "MultiPolygon":
					logging.debug("MultiPolygon")
					for polygon in coorddata:
						exterior = polygon[0]
						if len(exterior) < 3:
							logging.warning("MultiPolygon exterior ring has fewer than 3 points, skipping")
							continue
						exterior_3d = [list(pt) if len(pt) >= 3 else [pt[0], pt[1], 0] for pt in exterior]
						linectr += 1
						ply_gjs_feature_list.append({
							"line_color": lcolor,
							"coordinates": exterior_3d,
							"linename": self.name + "_" + str(linectr)
						})
						
		logging.debug(self.feature_list)
				
class potree_html_generator():
	def __init__(self):
		pass
	@classmethod
	def write_potree_html(cls, pointcloud_name):
		with open("potree_main.html", "w") as f:
			# original potree html section, untouched
			template = r'''<!DOCTYPE html>
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
	<script src="./libs/other/BinaryHeap.js"></script>
	<script src="./libs/tween/tween.min.js"></script>
	<script src="./libs/d3/d3.js"></script>
	<script src="./libs/proj4/proj4.js"></script>
	<script src="./libs/openlayers3/ol.js"></script>
	<script src="./libs/i18next/i18next.js"></script>
	<script src="./libs/jstree/jstree.js"></script>
	<script src="./libs/three.js_potreecraft/build/three.min.older.js""></script>
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
		
		Potree.loadPointCloud("./pointclouds/__POINTCLOUD_NAME__/metadata.json", "__POINTCLOUD_NAME__", e => {
			let scene = viewer.scene;
			let pointcloud = e.pointcloud;
			let material = pointcloud.material;
			material.size = 1;
			material.pointSizeType = Potree.PointSizeType.ADAPTIVE;
			material.shape = Potree.PointShape.SQUARE;
			material.activeAttributeName = "rgba";
			
			scene.addPointCloud(pointcloud);
			viewer.fitToScreen();
		});

	</script>
					
'''
			f.write(template.replace("__POINTCLOUD_NAME__", pointcloud_name))
			# second script, including our class declaration for lines
			f.write(r''' 	<script>

		// basic vector drawing script, v2
		// create instances of LineOnScreen class with coordinates matching the cloud's crs, and give proper parameters for coloring
		class CircleOnScreen {
			constructor(center, radius, segments, color, opacity, groupname) {
				this.center = center;       // [x, y, z]
				this.radius = radius;       // circle radius
				this.segments = segments;   // number of vertices (e.g., 64)
				this.color = color;
				this.opacity = opacity;
				this.groupname = groupname;
			}

			displaycircle() {
				const points = [];
				for (let i = 0; i <= this.segments; i++) {
					const theta = (i / this.segments) * Math.PI * 2;
					const x = this.center[0] + this.radius * Math.cos(theta);
					const y = this.center[1] + this.radius * Math.sin(theta);
					const z = this.center[2];
					points.push(new THREE.Vector3(x, y, z));
				}

				const geometry = new THREE.BufferGeometry().setFromPoints(points);
				const material = new THREE.LineBasicMaterial({
					color: this.color,
					transparent: true,
					opacity: this.opacity,
					linewidth: 1
				});

				const circle = new THREE.LineLoop(geometry, material);

				const circleGroup = new THREE.Group();
				circleGroup.name = this.groupname;
				circleGroup.add(circle);

				this.circleGroup = circleGroup;
				viewer.scene.scene.add(circleGroup);
			}
		}
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
		class PolygonOnScreen {
			constructor(points, color, opacity, groupname) {
				this.points = points;   // Array of [x, y, z]
				this.color = color;
				this.opacity = opacity;
				this.groupname = groupname;
			}
			// --- displays polygons with per-vertex z (3D) ---
			displaypolygon() {
				if (this.points.length < 3) {
					console.warn("Polygon needs at least 3 points");
					return;
				}

				// 2D contour for triangulation (x, y only)
				const contour = this.points.map(p => new THREE.Vector2(p[0], p[1]));
				const faces = THREE.ShapeUtils.triangulateShape(contour, []);

				// 3D positions: each vertex keeps its own x, y, z
				const positions = new Float32Array(this.points.length * 3);
				for (let i = 0; i < this.points.length; i++) {
					positions[i * 3]     = this.points[i][0];
					positions[i * 3 + 1] = this.points[i][1];
					positions[i * 3 + 2] = this.points[i][2] != null ? this.points[i][2] : 0;
				}

				// Index array from triangulation result
				const indices = [];
				for (let i = 0; i < faces.length; i++) {
					indices.push(faces[i][0], faces[i][1], faces[i][2]);
				}

				const geometry = new THREE.BufferGeometry();
				geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
				geometry.setIndex(indices);
				geometry.computeVertexNormals();

				const material = new THREE.MeshBasicMaterial({
					color: this.color,
					transparent: true,
					opacity: this.opacity,
					side: THREE.DoubleSide,
					depthWrite: false
				});

				const mesh = new THREE.Mesh(geometry, material);

				const polyGroup = new THREE.Group();
				polyGroup.name = this.groupname;
				polyGroup.add(mesh);
				viewer.scene.scene.add(polyGroup);
			}
		}
'''
					)
			# third segment, the dynamic section using the LineOnScreen class

			for ft in lns_gjs_feature_list:
				f.write(r'		// ------------------------------------------------------------------'+'\n')
				f.write("		const {} = new LineOnScreen(".format(ft.get("linename"))+'\n')
				f.write('           {jscoords},'.format(jscoords=ft.get('coordinates'))+'\n')
				f.write('           "{jslinecolor}",'.format(jslinecolor=ft.get('line_color'))+'\n')
				f.write('           {jslinewidth},'.format(jslinewidth=1)+'\n')
				f.write('           {jslineopacity},'.format(jslineopacity=0.75)+'\n')
				f.write('           "{jsgroup}");'.format(jsgroup="vectorclass")+'\n')
				f.write('		{}.displayline();\n\n'.format(ft.get("linename"))+'\n')
					
			for ft in pts_gjs_feature_list:
				f.write(r'		// ------------------------------------------------------------------'+'\n')
				f.write("		const {} = new CircleOnScreen(".format(ft.get("linename"))+'\n')
				f.write('           {jscoords},'.format(jscoords=ft.get('coordinates'))+'\n')
				f.write('           "5",'+'\n')
				f.write('           "32",'+'\n')
				f.write('           "{jslinecolor}",'.format(jslinecolor=ft.get('line_color'))+'\n')
				#f.write('           {jslinewidth},'.format(jslinewidth=1)+'\n')
				f.write('           {jslineopacity},'.format(jslineopacity=0.75)+'\n')
				f.write('           "{jsgroup}");'.format(jsgroup="vectorclass")+'\n')
				f.write('		{}.displaycircle();\n\n'.format(ft.get("linename"))+'\n')

			for ft in ply_gjs_feature_list:
				f.write(r'		// ------------------------------------------------------------------'+'\n')
				f.write("		const {} = new PolygonOnScreen(".format(ft.get("linename"))+'\n')
				f.write('           {},'.format(json.dumps(ft.get('coordinates')))+'\n')
				f.write('           "{jslinecolor}",'.format(jslinecolor=ft.get('line_color'))+'\n')
				f.write('           {jslineopacity},'.format(jslineopacity=0.75)+'\n')
				f.write('           "{jsgroup}");'.format(jsgroup="vectorclass")+'\n')
				f.write('		{}.displaypolygon();\n\n'.format(ft.get("linename"))+'\n')

			
			#const circle_example = new CircleOnScreen(
			#		[628436.065, 134472.887, 124.934],  // center x, y, z
			#		5,                   // radius
			#		64,                   // segments (smoothness)
			#		"#ff0000",            // color
			#		0.8,                  // opacity
			#		"circleclass"         // group name
			#	);


			# fourth, closing segment 628155.751, 134419.450, 152.649
			f.write(r'''        // ------------------------------------------------------------------

		viewer.renderer.render(viewer.scene.scene, viewer.scene.getActiveCamera());

		</script>
	
  </body>
</html>
 '''
					)

# Main section of the code, this is where it is tied together. Put behind main for future modular use.
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Generate Potree HTML with GeoJSON layers.")
	parser.add_argument("--vector-folder", help="Folder containing GeoJSON files.")
	parser.add_argument("--project-name", help="Pointcloud project folder name under pointclouds/.")
	args = parser.parse_args()

	print("Welcome to the simple potree geojson reader script.")
	if args.vector_folder:
		folderpath = args.vector_folder
	else:
		print("Please type in the location of the vector data input folder: ")
		folderpath = input()

	if args.project_name:
		project_name = args.project_name
	else:
		print("Please type in the pointcloud project name: ")
		project_name = input().strip()

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

		potree_html_generator.write_potree_html(project_name)
