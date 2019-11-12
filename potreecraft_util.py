import logging
import threading
import time
import subprocess
from datetime import datetime, date
import os

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
    def potreeconverter_thread_function(cls,input,output,outtype,pagename,proj,threadname,logfile):
        eov = ' "+proj=somerc +lat_0=47.14439372222222 +lon_0=19.04857177777778 +k_' \
            '0=0.99993 +x_0=650000 +y_0=200000 +ellps=GRS67 +towgs84=52.17,-71.82,-14.9,0,0,0,0 ' \
            '+units=m +no_defs "'
        # using a swiss projection. Use http://spatialreference.org/ to find projections in proj4 format
        # PotreeConverter.exe C:/data -o C:/potree_converted -p pageName --projection "+proj=somerc +lat_0=46.95240555555556 +lon_0=7.439583333333333 +k_0=1 +x_0=600000 +y_0=200000 +ellps=bessel +towgs84=674.4,15.1,405.3,0,0,0,0 +units=m +no_defs" --overwrite
        logging.info("Thread %s: starting", threadname)
        #print(threadname,input,cltype,stepsize)
        if (proj == None) or (proj == "+proj=longlat +datum=WGS84 +no_defs"):
            cmd = str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + '').split()
            logfile.write(str(str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + '').split()))
            cmd[0] = cmd[0].replace("\\", "/")
            print(str(cmd))
            subprocess.call(cmd, shell=False)
        else:
            cmd = str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + ' --projection "'+proj+'"').split()
            logfile.write(str(str(cls.potreeconverterpath + r'PotreeConverter.exe ' + input + ' -o ' + output + ' -a ' + outtype + ' --generate-page ' + pagename + ' --projection "'+proj+'"').split()))
            print(cmd)
            cmd[0] = cmd[0].replace("\\", "/")
            subprocess.call(cmd, shell=False)
        #subprocess.call(cmd, shell=False)

        logging.info("Thread %s: finishing", threadname)

    @classmethod
    def lasconvert_isready(cls, input, cltype, stepsize):
        timefortempname = datetime.now()
        output = 'cloud_'+str(timefortempname.strftime("%y%m%d%H%M%S"))+'.asc'
        PotreeCraftSupport.readcfg()

        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")

        logging.info("Main    : before creating thread")
        x = threading.Thread(target=PotreeCraftSupport.blast2dem_thread_function, args=(input,(cls.potreeconverterpath + output) ,cltype,stepsize,"Blast2dem thread - "+output))
        #x = threading.Thread(target=PotreeCraftSupport.blast2dem_thread_function, args=(r'c:\PotreeConverter_16\3DModel_Pcld_LASCloud.las', 'caslte.asc', '-rgb', '0.1', 'asdf'))
        logging.info("Main    : before running thread")
        x.start()
        logging.info("Main    : wait for the thread to finish")
        x.join()
        logging.info("Main    : all done")
        return output

    @classmethod
    def pcconvert_isready(cls, input,output,outtype,pagename,proj,threadname):
        timefortempname = datetime.now()
        #output = 'cloud_'+str(timefortempname.strftime("%y%m%d%H%M%S"))+'.asc'
        PotreeCraftSupport.readcfg()
        f = open("d:\pcconvertlog.txt", "a")


        format = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format, level=logging.INFO,
                            datefmt="%H:%M:%S")

        logging.info("Main    : before creating thread")
        x = threading.Thread(target=PotreeCraftSupport.potreeconverter_thread_function, args=(input,output,outtype,pagename,proj,"PotreeConverter thread - "+threadname,f))
        #x = threading.Thread(target=PotreeCraftSupport.blast2dem_thread_function, args=(r'c:\PotreeConverter_16\3DModel_Pcld_LASCloud.las', 'caslte.asc', '-rgb', '0.1', 'asdf'))
        f.write("time: "+ str(timefortempname)+"\n")
        f.write("args: ")
        f.write("input: "+ str(input)+"\n")
        f.write("output: " +str(output)+"\n")
        f.write("outtype: "+ str(outtype)+"\n")
        f.write("pagename: "+str(pagename)+"\n")
        f.write("proj: "+str(proj)+"\n")
        f.write("threadname: "+str(threadname)+"\n")
        f.write(str(x))
        logging.info("Main    : before running thread")
        x.start()
        logging.info("Main    : wait for the thread to finish")
        x.join()
        logging.info("Main    : all done")
        f.close()
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
    #

class PotreeGenericLayerInfo():
    # This class is more-or-less an abstact which serves as a common base for all layer info storage classes.
    # Provides empty functions which will be overridden for shape, json and shape layer processing.
    # Generic values stored about each layer we add to the potree project.
    layername = None
    layertype = None
    layercrs = None
    layerhexcolor = None
    fileName: object = None

    def __init__(self, layername, layertype, layercrs, layerhexcolor, filename):
        self.layername = layername
        self.layertype = layertype
        self.layercrs = layercrs
        self.layerhexcolor = layerhexcolor
        self.filename = filename

    def setBasicInfo(self, layername, layertype, layercrs, layerhexcolor, filename):
        pass

    def getBasicInfo(self):
        pass

class PotreeJsonVectorLayerInfo(PotreeGenericLayerInfo):
    def __init__(self, layername, layertype, layercrs, layerhexcolor, filename):
        super().__init__(layername, layertype, layercrs, layerhexcolor, filename)

    def setBasicInfo(self, layername, layertype, layercrs, layerhexcolor, filename):
        pass

    def getBasicInfo(self):
        return [self.layername,self.layertype,self.layercrs,self.layerhexcolor,self.filename]

class PotreeShapeVectorLayerInfo(PotreeGenericLayerInfo):
    pass

class PotreeCloudObjectInfo(PotreeGenericLayerInfo):
    pass




if __name__ == "__main__":

    #cloudname = PotreeCraftSupport.lasconvert_isready(r'c:\PotreeConverter_16\3DModel_Pcld_LASCloud.las','-rgb','0.1')
    #print(cloudname)

    x = PotreeJsonVectorLayerInfo('d','s','s','a','fn')
    print(x.getBasicInfo())



