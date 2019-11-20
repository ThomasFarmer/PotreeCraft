import logging
import threading
import time
import subprocess
from datetime import datetime, date
import os
import shutil

class PotreeCraftSupport:

    lastoolspath = None
    potreeconverterpath = None

    vectorLayers = None
    rasterLayers = None

    def __init__(self):
        print(os.path.dirname(os.path.abspath(__file__)))
        print(os.getcwd())



    @classmethod
    def readcfg(cls):
        try:
            configfile = open(os.path.dirname(os.path.abspath(__file__))+"/potreecraft_config.ini", "r+")
            configz = configfile.readlines()
            # print(configz[0].split('"')[1])
            # print(configz[1].split('"')[1])
            cls.lastoolspath = configz[0].split('"')[1]
            cls.potreeconverterpath = configz[1].split('"')[1]
            if cls.potreeconverterpath[-1] != '\\':
                cls.potreeconverterpath += "\\"
            if cls.lastoolspath[-1] != '\\':
                cls.lastoolspath += '\\'
            print('LASTools folder path: '+cls.lastoolspath)
            print('PotreeConverter folder path: '+cls.potreeconverterpath)
            return [cls.lastoolspath, cls.potreeconverterpath]
        except Exception as genex:
            print(genex)
            print("Using default values for tool paths:")
            return ["c:\\LAStools\\", "c:\\PotreeConverter_16\\"]


    @classmethod
    def readwholefile(self):
        configfile = open(os.path.dirname(os.path.abspath(__file__))+"/potreecraft_config.ini", "r+")
        configz = configfile.readlines()
        return configz

    @classmethod
    def writecfg(cls,lastoolspath,pcpath):
        configfile = open(os.path.dirname(os.path.abspath(__file__))+"/potreecraft_config.ini", "w")
        pcpath = pcpath.replace("/","\\")
        lastoolspath = lastoolspath.replace("/","\\")
        if pcpath[-1] != '\\':
            pcpath += "\\"
        if lastoolspath[-1] != '\\':
            lastoolspath += '\\'

        cls.lastoolspath = lastoolspath
        cls.potreeconverterpath = pcpath

        configlines = ['lastools_path="' + lastoolspath + '"\n', 'potreeconverter_path="' + pcpath + '"']
        configfile.writelines(configlines)
        configfile.close()

    @classmethod
    def checkPathValidity(cls):
        print(cls.lastoolspath + r'bin\blast2dem.exe')
        print(os.path.isfile(cls.lastoolspath + r'bin\blast2dem.exe'))
        print(cls.potreeconverterpath + r'PotreeConverter.exe')
        print(os.path.isfile(cls.potreeconverterpath + r'PotreeConverter.exe'))
        if os.path.isfile(cls.lastoolspath + r'bin\blast2dem.exe') and os.path.isfile(cls.potreeconverterpath + r'PotreeConverter.exe'):
            print("return true")
            return True
        else:
            print("return false")
            return False



    @classmethod
    def blast2dem_thread_function(cls,input,output,cltype,stepsize,threadname):
        logging.info("Thread %s: starting", threadname)

        cmd = str(cls.lastoolspath + r'bin\blast2dem.exe -i '+input+' -o '+output+' -v '+cltype+' -step '+stepsize+'').split()
        print(cmd)

        subprocess.call(cmd, shell=False)

        logging.info("Thread %s: finishing", threadname)

    @classmethod
    def potreeconverter_thread_function(cls,input,output,outtype,pagename,proj,threadname='lol'):
        eov = ' "+proj=somerc +lat_0=47.14439372222222 +lon_0=19.04857177777778 +k_' \
            '0=0.99993 +x_0=650000 +y_0=200000 +ellps=GRS67 +towgs84=52.17,-71.82,-14.9,0,0,0,0 ' \
            '+units=m +no_defs "'
        # using a swiss projection. Use http://spatialreference.org/ to find projections in proj4 format
        # PotreeConverter.exe C:/data -o C:/potree_converted -p pageName --projection "+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=600000 +y_0=200000 +ellps=bessel +towgs84=674.4,15.1,405.3,0,0,0,0 +units=m +no_defs" --overwrite
        logging.info("Thread %s: starting", threadname)
        #print(threadname,input,cltype,stepsize)
        if (proj == None) or (proj == "+proj=longlat +datum=WGS84 +no_defs"):
            cmd = str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + '').split()
            #logfile.write(str(str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + '').split()))
            cmd[0] = cmd[0].replace("\\", "/")
            #print(str(cmd))
            subprocess.call(cmd, shell=False)
        else:
            cmd = str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + ' --projection "'+proj+'"').split()
            #logfile.write(str(str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + ' --projection "'+proj+'"').split()))
            #print(cmd)
            cmd[0] = cmd[0].replace("\\", "/")
            subprocess.call(cmd, shell=False)
        #subprocess.call(cmd, shell=False)

        logging.info("Thread is finishing")

    @classmethod
    def lasconvert_isready(cls, input, cltype, stepsize):
        timefortempname = datetime.now()
        output = 'cloud_'+str(timefortempname.strftime("%y%m%d%H%M%S"))+'.asc'
        PotreeCraftSupport.readcfg()

        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")
        #logging.info("Main    : before creating thread")
        x = threading.Thread(target=PotreeCraftSupport.blast2dem_thread_function, args=(input,(cls.potreeconverterpath + output) ,cltype,stepsize,"Blast2dem thread - "+output))
        #x = threading.Thread(target=PotreeCraftSupport.blast2dem_thread_function, args=(r'c:\PotreeConverter_16\3DModel_Pcld_LASCloud.las', 'caslte.asc', '-rgb', '0.1', 'asdf'))
        #logging.info("Main    : before running thread")
        x.start()
        #logging.info("Main    : wait for the thread to finish")
        x.join()
        #logging.info("Main    : all done")
        return output

    @classmethod
    def pcconvert_isready(cls, input,output,outtype,pagename,proj,threadname='lol'):
        timefortempname = datetime.now()

        #output = 'cloud_'+str(timefortempname.strftime("%y%m%d%H%M%S"))+'.asc'
        PotreeCraftSupport.readcfg()

        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")
        #logging.info("Main    : before creating thread")
        x = threading.Thread(target=PotreeCraftSupport.potreeconverter_thread_function, args=(input,output,outtype,pagename,proj,"PotreeConverter thread - "+threadname))
        #x = threading.Thread(target=PotreeCraftSupport.blast2dem_thread_function, args=(r'c:\PotreeConverter_16\3DModel_Pcld_LASCloud.las', 'caslte.asc', '-rgb', '0.1', 'asdf'))
        #logging.info("Main    : before running thread")
        x.start()
        #logging.info("Main    : wait for the thread to finish")
        x.join()
        #logging.info("Main    : all done")
        return output
    #
    # # TO DO
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # megírni potreeconvert_isready metódust
    # az x-ben félkész de ott a változó
    # threading bugos pluginban megfagy felugró ablaktól... de végülis nem akkora baj
    # 2D kép már megy.
    # ha potree konvert is lefut, akkor jön a végső fázis:
    #
    # - shape és .js file másolás .html törlése/felülírása
    # - javascript editing
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # js THREE point
    # https://threejs.org/docs/#api/en/objects/Points
    @classmethod
    def prepareProject(cls,projectPath,layerList):
        if not os.path.exists(projectPath+"/vector_data/"):
            os.makedirs(projectPath+"/vector_data/")
        print(projectPath)
        #copyfile("./shapefile-w3d.js", projectPath+"/libs/shapefile/")
        #os.path.isfile(file_path)
        shutil.copy('./shapefile-w3d.js', projectPath+'libs/shapefile/')
        for lyr in layerList:
            #print(lyr[0:-3])

            # .shp
            if os.path.isfile(lyr):
                shutil.copy2(lyr, projectPath + '/vector_data/')
            else:
                print(lyr + ' -- file not found')

            # .shx
            if os.path.isfile(lyr[0:-3]+'shx'):
                shutil.copy2(lyr[0:-3]+'shx', projectPath + '/vector_data/')
            else:
                print(lyr[0:-3]+'shx' + ' -- file not found')

            # .dbf
            if os.path.isfile(lyr[0:-3]+'dbf'):
                shutil.copy2(lyr[0:-3]+'dbf', projectPath + '/vector_data/')
            else:
                print(lyr[0:-3]+'dbf' + ' -- file not found')

            # .prj
            if os.path.isfile(lyr[0:-3]+'prj'):
                shutil.copy2(lyr[0:-3]+'prj', projectPath + '/vector_data/')
            else:
                print(lyr[0:-3]+'prj' + ' -- file not found')

            # .cpg
            if os.path.isfile(lyr[0:-3]+'cpg'):
                shutil.copy2(lyr[0:-3]+'cpg', projectPath + '/vector_data/')
            else:
                print(lyr[0:-3]+'cpg' + ' -- file not found')

            # .qpj
            if os.path.isfile(lyr[0:-3]+'qpj'):
                shutil.copy2(lyr[0:-3]+'qpj', projectPath + '/vector_data/')
            else:
                print(lyr[0:-3]+'qpj' + ' -- file not found')


    @classmethod
    def writeHtml(cls,projecthtmlpath,cloudname,cloudparams,layerNameArray,layerColorArray):
        # cloudparams[0]: coloring, pl 'INTENSITY'
        # cloudparams[1]: crs tömb, név és proj, pl ["WGS84", "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"], opcionális, default bejövőérték: None
        # cloudparams[2]: opacity? később.
        f = open(projecthtmlpath, "a")
        path = "./vector_data/"

        # -------------------------------------------------------------------------------------------------
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('<head>\n')
        f.write('	<meta charset="utf-8">\n')
        f.write('	<meta name="description" content="">\n')
        f.write('	<meta name="author" content="">\n')
        f.write('	<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">\n')
        f.write('	<title>Potree Viewer</title>\n')
        f.write('\n')
        f.write('	<link rel="stylesheet" type="text/css" href="libs/potree/potree.css">\n')
        f.write('	<link rel="stylesheet" type="text/css" href="libs/jquery-ui/jquery-ui.min.css">\n')
        f.write('	<link rel="stylesheet" type="text/css" href="libs/perfect-scrollbar/css/perfect-scrollbar.css">\n')
        f.write('	<link rel="stylesheet" type="text/css" href="libs/openlayers3/ol.css">\n')
        f.write('	<link rel="stylesheet" type="text/css" href="libs/spectrum/spectrum.css">\n')
        f.write('	<link rel="stylesheet" type="text/css" href="libs/jstree/themes/mixed/style.css">\n')
        f.write('</head>\n')
        f.write('\n')
        f.write('<body>\n')
        f.write('	<script src="libs/jquery/jquery-3.1.1.min.js"></script>\n')
        f.write('	<script src="libs/spectrum/spectrum.js"></script>\n')
        f.write('	<script src="libs/perfect-scrollbar/js/perfect-scrollbar.jquery.js"></script>\n')
        f.write('	<script src="libs/jquery-ui/jquery-ui.min.js"></script>\n')
        f.write('	<script src="libs/three.js/build/three.min.js"></script>\n')
        f.write('	<script src="libs/other/BinaryHeap.js"></script>\n')
        f.write('	<script src="libs/tween/tween.min.js"></script>\n')
        f.write('	<script src="libs/d3/d3.js"></script>\n')
        f.write('	<script src="libs/proj4/proj4.js"></script>\n')
        f.write('	<script src="libs/openlayers3/ol.js"></script>\n')
        f.write('	<script src="libs/i18next/i18next.js"></script>\n')
        f.write('	<script src="libs/jstree/jstree.js"></script>\n')
        f.write('	<script src="libs/potree/potree.js"></script>\n')
        f.write('	<script src="libs/plasio/js/laslaz.js"></script>\n')
        f.write('	<script src="libs/shapefile/shapefile-w3d.js"></script>\n')
        f.write('	\n')
        f.write('	\n')
        f.write('	<!-- INCLUDE ADDITIONAL DEPENDENCIES HERE -->\n')
        f.write('		document.title = "";\n')
        f.write('		viewer.setEDLEnabled(false);\n')
        f.write('		viewer.setBackground("gradient"); // ["skybox", "gradient", "black", "white"];\n')
        f.write('		viewer.setDescription(``);\n')
        f.write('	\n')
        f.write('	<div class="potree_container" style="position: absolute; width: 100%; height: 100%; left: 0px; top: 0px; ">\n')
        f.write('		<div id="potree_render_area"></div>\n')
        f.write('		<div id="potree_sidebar_container"> </div>\n')
        f.write('	</div>\n')
        f.write('	\n')
        f.write('	<script>\n')
        f.write('	\n')
        f.write('		window.viewer = new Potree.Viewer(document.getElementById("potree_render_area"));\n')
        f.write('		\n')
        f.write('		viewer.setEDLEnabled(true);\n')
        f.write('		viewer.setFOV(60);\n')
        f.write('		viewer.setPointBudget(1*1000*1000);\n')
        f.write('		document.title = "";\n')
        f.write('		viewer.setEDLEnabled(false);\n')
        f.write('		viewer.setBackground("gradient"); // ["skybox", "gradient", "black", "white"];\n')
        f.write('		viewer.setDescription(``);\n')
        f.write('		viewer.loadSettingsFromURL();\n')
        f.write('		\n')
        f.write('		viewer.loadGUI(() => {\n')
        f.write("			viewer.setLanguage('en');\n")
        f.write('			$("#menu_appearance").next().show();\n')
        f.write('			$("#menu_tools").next().show();\n')
        f.write('			$("#menu_scene").next().show();\n')
        f.write('			viewer.toggleSidebar();\n')
        f.write('		});\n')
        f.write('		\n')
        f.write('		Potree.loadPointCloud("pointclouds/'+cloudname+'/cloud.js", "'+cloudname+'", e => {\n')
        f.write('			let pointcloud = e.pointcloud;\n')
        f.write('			let material = pointcloud.material;\n')
        f.write('			viewer.scene.addPointCloud(pointcloud);\n')
        f.write('			material.pointColorType = Potree.PointColorType.'+cloudparams[0]+'; // any Potree.PointColorType.XXXX \n')
        f.write('			material.size = 1;\n')
        f.write('			material.pointSizeType = Potree.PointSizeType.ATTENUATED;\n')
        f.write('			material.shape = Potree.PointShape.SQUARE;\n')
        f.write('			material.opacity = 0.08;\n')
        f.write('			//material.rgbGamma = 2.20;\n')
        f.write('			material.intensityGamma = 1.70;\n')
        f.write('			material.intensityRange = [25000,59000];\n')
        f.write('			material.intensityMin = 24200\n')
        f.write('			viewer.fitToScreen();\n')
        f.write('			{\n')
        f.write('				// *** shape beolvasó kódrész ***\n')
        f.write('				// *** shape reading code section ***\n')
        f.write('\n')
        f.write('				//proj4.defs("pointcloud", pointcloud.projection);\n')
        f.write('				//proj4.defs("WGS84", "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs");\n')
        f.write('				//let toScene = proj4("WGS84", "pointcloud");\n')
        f.write('\n')
        f.write(
            '				// *** proj4 könyvtár jelen pillanatban nem működik ezzel a példával, figyelj rá, hogy minden felhasznált file megfelelő crs-ben van. ***\n')
        f.write(
            '				// *** proj4 library is currently not working with this example, make sure that all your files are in the right crs. ***\n')
        f.write('\n')
        f.write('				let featureToSceneNode = (feature, color) => {\n')
        f.write('					let geometry = feature.geometry;\n')
        f.write('\n')
        f.write('					var color = color ? color : new THREE.Color(1, 1, 1);\n')
        f.write('\n')
        f.write('					if(feature.geometry.type === "Point"){\n')
        f.write('						let sg = new THREE.SphereGeometry(1, 18, 18);\n')
        f.write('						let sm = new THREE.MeshNormalMaterial();\n')
        f.write('						let s = new THREE.Mesh(sg, sm);\n')
        f.write('\n')
        f.write('						let [long, lat] = geometry.coordinates;\n')
        f.write('						let pos = ([long, lat]);\n')
        f.write('						let alt = geometry.coordinates[2]?geometry.coordinates[2]:20;\n')
        f.write('						s.position.set(...pos, alt);\n')
        f.write('						s.scale.set(0.3, 0.3, 0.05);\n')
        f.write('\n')
        f.write('						return s;\n')
        f.write('					}else if(geometry.type === "LineString"){\n')
        f.write('						let coordinates = [];\n')
        f.write('						let min = new THREE.Vector3(Infinity, Infinity, Infinity);\n')
        f.write('\n')
        f.write('						for(let i = 0; i < geometry.coordinates.length; i++){\n')
        f.write('							let [long, lat] = geometry.coordinates[i];\n')
        f.write('							let pos = ([long, lat]);\n')
        f.write('\n')
        f.write('							//console.log("LSZ: ",pos, geometry.coordinates[i][2])\n')
        f.write('\n')
        f.write('							let alt = 20;\n')
        f.write('							min.x = Math.min(min.x, pos[0]);\n')
        f.write('							min.y = Math.min(min.y, pos[1]);\n')
        f.write('							min.z = Math.min(min.z, alt);\n')
        f.write('\n')
        f.write('							coordinates.push(...pos, alt);\n')
        f.write('							if(i > 0 && i < geometry.coordinates.length - 1){\n')
        f.write('								coordinates.push(...pos, alt);\n')
        f.write('							}\n')
        f.write('						}\n')
        f.write('\n')
        f.write('						for(let i = 0; i < coordinates.length; i += 3){\n')
        f.write('							coordinates[i+0] -= min.x;\n')
        f.write('							coordinates[i+1] -= min.y;\n')
        f.write('							coordinates[i+2] -= min.z;\n')
        f.write('						}\n')
        f.write('\n')
        f.write('						let positions = new Float32Array(coordinates);\n')
        f.write('						let lineGeometry = new THREE.BufferGeometry();\n')
        f.write('						lineGeometry.addAttribute("position", new THREE.BufferAttribute(positions, 3));\n')
        f.write('\n')
        f.write('						let material = new THREE.LineBasicMaterial( { color: color} );\n')
        f.write('						let line = new THREE.LineSegments(lineGeometry, material);\n')
        f.write('						line.position.copy(min);\n')
        f.write('\n')
        f.write('						return line;\n')
        f.write('\n')
        f.write('					}else if(geometry.type === "LineStringZ"){\n')
        f.write('						let coordinates = [];\n')
        f.write('						let min = new THREE.Vector3(Infinity, Infinity, Infinity);\n')
        f.write('\n')
        f.write('						for(let i = 0; i < geometry.coordinates.length; i++){\n')
        f.write('							let [long, lat] = geometry.coordinates[i];\n')
        f.write('							let pos = ([long, lat]);\n')
        f.write('\n')
        f.write('							//console.log("LSZ: ",pos, geometry.coordinates[i][2])\n')
        f.write('\n')
        f.write('							let alt = geometry.coordinates[i][2]?geometry.coordinates[i][2]:20;\n')
        f.write('							min.x = Math.min(min.x, pos[0]);\n')
        f.write('							min.y = Math.min(min.y, pos[1]);\n')
        f.write('							min.z = Math.min(min.z, alt);\n')
        f.write('\n')
        f.write('							coordinates.push(...pos, alt);\n')
        f.write('							if(i > 0 && i < geometry.coordinates.length - 1){\n')
        f.write('								coordinates.push(...pos, alt);\n')
        f.write('							}\n')
        f.write('						}\n')
        f.write('						for(let i = 0; i < coordinates.length; i += 3){\n')
        f.write('							coordinates[i+0] -= min.x;\n')
        f.write('							coordinates[i+1] -= min.y;\n')
        f.write('							coordinates[i+2] -= min.z;\n')
        f.write('						}\n')
        f.write('\n')
        f.write('						let positions = new Float32Array(coordinates);\n')
        f.write('						let lineGeometry = new THREE.BufferGeometry();\n')
        f.write('						lineGeometry.addAttribute("position", new THREE.BufferAttribute(positions, 3));\n')
        f.write('\n')
        f.write('						let material = new THREE.LineBasicMaterial( { color: color} );\n')
        f.write('						let line = new THREE.LineSegments(lineGeometry, material);\n')
        f.write('						line.position.copy(min);\n')
        f.write('\n')
        f.write('						return line;\n')
        f.write('\n')
        f.write('					}else if(geometry.type === "Polygon"){\n')
        f.write('						for(let pc of geometry.coordinates){\n')
        f.write('							let coordinates = [];\n')
        f.write('\n')
        f.write('							let min = new THREE.Vector3(Infinity, Infinity, Infinity);\n')
        f.write('							for(let i = 0; i < pc.length; i++){\n')
        f.write('								let [long, lat] = pc[i];\n')
        f.write('								let pos = ([long, lat]);\n')
        f.write('								let alt = pc[i][2]?pc[i][2]:20;\n')
        f.write('								min.x = Math.min(min.x, pos[0]);\n')
        f.write('								min.y = Math.min(min.y, pos[1]);\n')
        f.write('								min.z = Math.min(min.z, alt);\n')
        f.write('\n')
        f.write('								coordinates.push(...pos, alt);\n')
        f.write('								if(i > 0 && i < pc.length - 1){\n')
        f.write('									coordinates.push(...pos, alt);\n')
        f.write('								}\n')
        f.write('							}\n')
        f.write('\n')
        f.write('							for(let i = 0; i < coordinates.length; i += 3){\n')
        f.write('								coordinates[i+0] -= min.x;\n')
        f.write('								coordinates[i+1] -= min.y;\n')
        f.write('								coordinates[i+2] -= min.z;\n')
        f.write('							}\n')
        f.write('\n')
        f.write('							let positions = new Float32Array(coordinates);\n')
        f.write('\n')
        f.write('							let lineGeometry = new THREE.BufferGeometry();\n')
        f.write(
            '							lineGeometry.addAttribute("position", new THREE.BufferAttribute(positions, 3));\n')
        f.write('\n')
        f.write('							let material = new THREE.LineBasicMaterial( { color: color} );\n')
        f.write('							let line = new THREE.LineSegments(lineGeometry, material);\n')
        f.write('							line.position.copy(min);\n')
        f.write('\n')
        f.write('							return line;\n')
        f.write('						}\n')
        f.write('					}else{\n')
        f.write('						console.log("unhandled feature: ", feature);\n')
        f.write('					}\n')
        f.write('				};\n')
        f.write('\n')
        f.write('// --- automated generator of shape layers -- \n')
        f.write('\n')


        for rowNo in range(len(layerNameArray)):

            lyrHex = '999999'
            # row[1 ] -> shn_xx
            # row[2] -> nodeID_xx
            # path + row[0] -> ./shp/EP_Lepcso_line.shp"
            # lyrName -> EP_Lepcso_line
            # lyrHex -> A0522D

            f.write("				let shn_" + str(rowNo) + " = new THREE.Object3D();\n")
            f.write("				viewer.scene.scene.add(shn_" + str(rowNo) + ");\n")
            f.write('\n')

            f.write(
                '			    Potree.utils.loadShapefileFeatures("' + path + layerNameArray[rowNo] + '.shp", features => {\n')
            f.write('					// feature-ök felláncolása\n')
            f.write('					// chaining up features\n')
            f.write('					for(let feature of features){\n')

            f.write('						let node = featureToSceneNode(feature, 0x' + layerColorArray[rowNo].replace("#","").upper() + ');\n')
            f.write('						shn_' + str(rowNo) + '.add(node);	\n')
            f.write('					}\n')
            f.write('					viewer.onGUILoaded(() => {\n')
            f.write('					let tree = $(`#jstree_scene`);\n')
            f.write('					let parentNode = "other";\n')
            f.write('					//console.log(tree);\n')
            f.write('\n')
            f.write("					let nodeID_" + str(rowNo) + " = tree.jstree('create_node', parentNode, { \n")
            f.write('						"text": "' + layerNameArray[rowNo] + '", \n')
            f.write('						"icon": `${Potree.resourcePath}/icons/triangle.svg`,\n')
            f.write('						"data": shn_' + str(rowNo) +'\n')
            f.write('					}, \n')
            f.write('					"last", false, false);\n')
            f.write(
                '					tree.jstree(shn_' + str(rowNo) + '.visible ? "check_node" : "uncheck_node", nodeID_' + str(rowNo) + ');\n')
            f.write('					});\n')
            f.write('				});\n')
            f.write('\n')

        f.write('\n')
        f.write('			}\n')
        f.write('		});\n')
        f.write('	</script>\n')
        f.write('  </body>\n')
        f.write('</html>\n')


if __name__ == "__main__":
    pass





