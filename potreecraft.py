# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PotreeCraft
								 A QGIS plugin
 A project building tool for Potree
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
							  -------------------
		begin				: 2019-10-07
		git sha			  : $Format:%H$
		copyright			: (C) 2019 by Béres Tamás
		email				: berestamasbela@protonmail.com
 ***************************************************************************/

/***************************************************************************
 *																		   *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License (GNU GPLv3 as    *
 *   published by the Free Software Foundation; 						   *
 *     																	   *
 ***************************************************************************/
"""
from qgis.PyQt import QtWidgets, QtGui
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QFileInfo
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from PyQt5.QtWidgets import QMessageBox, QFileDialog

# Initialize Qt resources from file resources.py
from qgis._core import QgsMapLayer, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem

from .resources import *
# Import the code for the dialog
from .potreecraft_dialog import PotreeCraftDialog
import os.path
# import simán baszik menni másik fileból valamiért
#from potreecraft_util import PotreeCraftSupport


class PotreeCraft:
	"""QGIS Plugin Implementation."""

	vector_table = []
	ascParam = '-rgb'
	pcrParam = 'INTENSITY'
	crsParam = None
	runCounterBecauseICannotInitiateButtonsInTheirDesignatedPlace = 0

	def __init__(self, iface,PotreeCraftSupport):
		"""Constructor.

		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		"""
		# Save reference to the QGIS interface
		self.iface = iface
		self.PotreeCraftSupport = PotreeCraftSupport

		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'PotreeCraft_{}.qm'.format(locale))

		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)
			QCoreApplication.installTranslator(self.translator)


		self.dlg = PotreeCraftDialog()
		
		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&PotreeCraft')


		# Check if plugin was started the first time in current QGIS session
		# Must be set in initGui() to survive plugin reloads
		self.first_start = None
		#self.dlg.fakYuButton.clicked.connect(self.selectOutputFile)

	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		"""Get the translation for a string using Qt translation API.

		We implement this ourselves since we do not inherit QObject.

		:param message: String for translation.
		:type message: str, QString

		:returns: Translated version of message.
		:rtype: QString
		"""
		# noinspection PyTypeChecker,PyArgumentList,PyCallByClass
		return QCoreApplication.translate('PotreeCraft', message)


	def add_action(
		self,
		icon_path,
		text,
		callback,
		enabled_flag=True,
		add_to_menu=True,
		add_to_toolbar=True,
		status_tip=None,
		whats_this=None,
		parent=None):
		"""Add a toolbar icon to the toolbar.

		:param icon_path: Path to the icon for this action. Can be a resource
			path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
		:type icon_path: str

		:param text: Text that should be shown in menu items for this action.
		:type text: str

		:param callback: Function to be called when the action is triggered.
		:type callback: function

		:param enabled_flag: A flag indicating if the action should be enabled
			by default. Defaults to True.
		:type enabled_flag: bool

		:param add_to_menu: Flag indicating whether the action should also
			be added to the menu. Defaults to True.
		:type add_to_menu: bool

		:param add_to_toolbar: Flag indicating whether the action should also
			be added to the toolbar. Defaults to True.
		:type add_to_toolbar: bool

		:param status_tip: Optional text to show in a popup when mouse pointer
			hovers over the action.
		:type status_tip: str

		:param parent: Parent widget for the new action. Defaults None.
		:type parent: QWidget

		:param whats_this: Optional text to show in the status bar when the
			mouse pointer hovers over the action.

		:returns: The action that was created. Note that the action is also
			added to self.actions list.
		:rtype: QAction
		"""

		icon = QIcon(icon_path)
		action = QAction(icon, text, parent)
		action.triggered.connect(callback)
		action.setEnabled(enabled_flag)

		if status_tip is not None:
			action.setStatusTip(status_tip)

		if whats_this is not None:
			action.setWhatsThis(whats_this)

		if add_to_toolbar:
			# Adds plugin icon to Plugins toolbar
			self.iface.addToolBarIcon(action)

		if add_to_menu:
			self.iface.addPluginToMenu(
				self.menu,
				action)

		self.actions.append(action)

		return action

	def initGui(self):
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""

		icon_path = ':/plugins/potreecraft/icon.png'
		self.add_action(
			icon_path,
			text=self.tr(u'PotreeCraft'),
			callback=self.run,
			parent=self.iface.mainWindow())

		#osszekapcsolasa a fuggvenyeknek es a gomboknak
		#self.dlg.loadVectorsFromPrjButton.clicked.connect(self.loadVectors)
		#self.dlg.fakYuButton.clicked.connect(self.asd)
		# will be set False in run()
		self.first_start = True
		#self.dlg.fakYuButton.clicked.connect(self.selectOutputFile)
	
	# def asd(self):
	# 	self.dlg.vectorPathLineEdit.setText("eeeeeeeee")

	def selectLASFile(self):
		filename = QFileDialog.getOpenFileName(self.dlg,"Select LAS cloud ","","*.las")
		self.dlg.pointCloudPathLineEdit.setText(str(filename[0]))
		if len(filename) > 0:
			onlyName = str(filename[0]).replace("\\","/").split("/")[-1]
			onlyName = onlyName.split(".")[0]
			#self.dlg.ascFileNameLineEdit.setText(onlyName+".asc")
			self.dlg.potreePageLineEdit.setText(onlyName)

	def selectOutputFile(self):
		filename = QFileDialog.getSaveFileName(self.dlg,"Select output file ","","*.asc")
		self.dlg.potreeVectorBameLineEdit.setText(filename)

	def selectOutputFolder(self):
		fpath = QFileDialog.getExistingDirectory(self.dlg, "Select Directory")
		if len(fpath) > 0:
			if fpath[-1] != '/' or fpath[-1] != '\\':
				fpath = fpath+'/'
		self.dlg.outputFolderLineEdit.setText(str(fpath))

	def selectLASToolsFolder(self):
		fpath = QFileDialog.getExistingDirectory(self.dlg, "Select Directory")
		self.dlg.lasToolsPathLineEdit.setText(str(fpath))

	def selectPotreeConverterFolder(self):
		fpath = QFileDialog.getExistingDirectory(self.dlg, "Select Directory")
		self.dlg.potreeConverterPathLineEdit.setText(str(fpath))

	def saveIniFileChanges(self):
		self.PotreeCraftSupport.writecfg(self.dlg.lasToolsPathLineEdit.text(),self.dlg.potreeConverterPathLineEdit.text())
		self.loadCfgIntoInterface()
		self.checkPathValidity()

	def checkPathValidity(self):
		#print(self.PotreeCraftSupport.checkPathValidity())
		if self.PotreeCraftSupport.checkPathValidity() == True:
			self.dlg.loadCloudButton.setEnabled(True)
			self.dlg.CompileButton.setEnabled(True)
			self.dlg.blast2demGroupBox.setEnabled(True)
			self.dlg.conversionTextLabel.setText("Plugin is ready to use.")

		else:
			self.dlg.loadCloudButton.setEnabled(False)
			self.dlg.CompileButton.setEnabled(False)
			self.dlg.blast2demGroupBox.setEnabled(False)
			self.dlg.conversionTextLabel.setText("Invalid LAStools or PotreeConverter path given - please visit the settings panel.")

	def unload(self):
		"""Removes the plugin menu item and icon from QGIS GUI."""
		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&PotreeCraft'),
				action)
			self.iface.removeToolBarIcon(action)

	def loadVectors(self):
		# load vectors from qgis table of contents
		self.vector_table = []
		#self.dlg.cb_invector.clear()
		#QMessageBox.about(self, "Title", "Message")
		self.dlg.vectorTreeWidget.clear()
		layers = [layer for layer in QgsProject.instance().mapLayers().values()]
		vector_layers = []
		raster_layers = []
		lctr=0

		self.dlg.vectorTreeWidget.setHeaderLabels(['Layer name','CRS info','Type info','#'])
		#tr = QtWidgets.QTreeWidgetItem(self.dlg.vectorTreeWidget,['mf','lol','asd'])
		tr = QtWidgets.QTreeWidgetItem(self.dlg.vectorTreeWidget, ['cloud.js', '', ''])
		#tc = QtWidgets.QTreeWidgetItem(tr,['lololol','sadas','fdsafdsf'])
		#addTreeRoot("A", "Root_first");
		for layer in layers:
			if layer.type() == QgsMapLayer.RasterLayer:
				raster_layers.append(layer)
			if layer.type() == QgsMapLayer.VectorLayer:
				vector_layers.append(layer)

		# checking layer type
		for vl in vector_layers:
			if ("memory?geometry" not in vl.dataProvider().dataSourceUri().split('|')[0]):
				lctr+=1
				LYR_TYPE = 'Unknown'
				LYR_ICON = '?'
				if str(vl.geometryType()) == '0':
					LYR_TYPE = 'Point'
					LYR_ICON = '⚫'
				elif str(vl.geometryType()) == '1':
					LYR_TYPE = 'Linestring'
					LYR_ICON = '☰'
				elif str(vl.geometryType()) == '2':
					LYR_TYPE = 'Polygon'
					LYR_ICON = '⏹'

				current_vl = QtWidgets.QTreeWidgetItem(tr, [vl.name(), vl.crs().description(), LYR_TYPE,str(lctr) ])
				current_path = QtWidgets.QTreeWidgetItem(current_vl, [vl.dataProvider().dataSourceUri().split('|')[0], vl.crs().authid(),str(vl.featureCount()),str(lctr)])
				current_color_box = QtWidgets.QTreeWidgetItem(current_vl, [LYR_ICON,vl.crs().toProj4(),str(vl.renderer().symbol().color().name()),str(lctr)])
				current_color_box = QtWidgets.QTreeWidgetItem.setForeground(current_color_box,0, QtGui.QBrush(QtGui.QColor(str(vl.renderer().symbol().color().name()))))
				current_vl.setExpanded(bool(1))

				self.vector_table.append([lctr,vl.name(),LYR_TYPE,vl.crs().description(),vl.crs().authid(),vl.crs().toProj4(),str(vl.renderer().symbol().color().name()),vl.dataProvider().dataSourceUri().split('|')[0]])

		# '▣ ⏹ ⚫ ●  █☰  ☡ ☈ ☓ ┼   .dataProvider().dataSourceUri()'
		# adjusting the size of the first header column to resize itself to the length which allows the longest layer name to fit.
		self.dlg.vectorTreeWidget.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
		# expand the root element by default, so layers would be visible on opening the plugin.
		tr.setExpanded(bool(1))

		#self.dlg.cb_invector.addItems(vector_layers)
		#print(vector_layers)

	#@QtCore.pyqtSlot(QtWidgets.QTreeWidgetItem, int)
	def onItemClicked(self, it, col):
		print(it, col, it.text(col),it.parent())
		if it.parent() != None:
			if str(it.parent().text(col)) == "cloud.js":
				print('király')
			else:
				print('fos')
				#it.setSelected(bool(0))
				#it.parent().setSelected(bool(1))
				print(it.parent().text(0),it.parent().text(1),it.parent().text(2))

		else:
			print('ez a gyökér')
			#it.setSelected(bool(0))

	def returnClickedData(self, node):
		pass
	# CRS Radio button methods
	def onCustomCRSRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.dlg.crsFromProjectComboBox.clear()
		self.crsParam = str(self.dlg.customCrsPlainTextEdit.toPlainText())
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.customCrsPlainTextEdit.setEnabled(True)
			self.dlg.crsFromProjectComboBox.setEnabled(False)

	def onLayerCRSRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.loadLayerCRSsForComboBox()
		crsidtext = self.dlg.crsFromProjectComboBox.currentText().split("[")[0].strip()
		crs = QgsCoordinateReferenceSystem(crsidtext)

		#crs = QgsCoordinateReferenceSystem("EPSG:27700")
		if crs.isValid():
			self.crsParam = str(crs.toProj4())
			print(self.crsParam)
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.customCrsPlainTextEdit.setEnabled(False)
			print(crs.toProj4())
			self.dlg.crsFromProjectComboBox.setEnabled(True)
	def onCRSComboboxChanged(self):
		crsidtext = self.dlg.crsFromProjectComboBox.currentText().split("[")[0].strip()
		crs = QgsCoordinateReferenceSystem(crsidtext)
		if crs.isValid():
			self.crsParam = str(crs.toProj4())
			print(self.crsParam)
			print(crs.toProj4())
	# blast2dem coloring radio button methods

	def onAscRgbColorRadioButtonClicked(self):
		self.ascParam = "-rgb"
		#print(self.crsParam)
	def onAscGrayColorRadioButtonClicked(self):
		self.ascParam = "-gray"
	def onAscSlopeColorRadioButtonClicked(self):
		self.ascParam = "-slope"
	def onAscIntensityColorRadioButtonClicked(self):
		self.ascParam = "-intensity"
	def onAscElevationColorRadioButtonClicked(self):
		self.ascParam = "-elevation"
	def onAscFalseColorRadioButtonClicked(self):
		self.ascParam = "-false"


	# Default cloud coloring radio button methods

	def onRgbColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = thisRadioButton.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(False)



	def onIntColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = thisRadioButton.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(False)


	def onIntGradColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = thisRadioButton.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(False)


	def onHeightColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = thisRadioButton.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(False)


	def onRgbHeightColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = thisRadioButton.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(False)

	def onClassColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = thisRadioButton.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(False)

	def onCustomColorRadioButtonClicked(self):
		thisRadioButton = self.dlg.sender()
		self.pcrParam = self.dlg.CustomColoringLineEdit.text()
		#self.loadLayerCRSsForComboBox()
		if thisRadioButton.isChecked():
			print("selected: %s" % (thisRadioButton.text()))
			self.dlg.CustomColoringLineEdit.setEnabled(True)
			#self.dlg.crsFromProjectComboBox.setEnabled(False)

	# loading methods
	def loadLayerCRSsForComboBox(self):
		self.dlg.crsFromProjectComboBox.clear()
		layers = [layer for layer in QgsProject.instance().mapLayers().values()]
		for l in layers:
			AllItems = [self.dlg.crsFromProjectComboBox.itemText(i) for i in range(self.dlg.crsFromProjectComboBox.count())]
			if (str(l.crs().authid()) + " [" + str(l.crs().description())+"]") not in AllItems:
				self.dlg.crsFromProjectComboBox.addItem(str(l.crs().authid()) + " [" + str(l.crs().description())+"]")

	def loadCfgIntoInterface(self):
		self.dlg.configIniTextEdit.clear()
		paths = self.PotreeCraftSupport.readcfg()
		self.dlg.lasToolsPathLineEdit.setText(paths[0])
		self.dlg.potreeConverterPathLineEdit.setText(paths[1])
		for l in self.PotreeCraftSupport.readwholefile():
			self.dlg.configIniTextEdit.setPlainText(str(self.dlg.configIniTextEdit.toPlainText()) + str(l))

	def loadCloudIntoQGIS(self):
		try:
			# loadCloudButton ascFileNameLineEdit pointCloudPathLineEdit stepSizeSpinBox blast2demGroupBox consoleCommandPlainTextEdit
			self.dlg.selectCloudButton.setEnabled(False)
			self.dlg.loadCloudButton.setEnabled(False)
			self.dlg.ascFileNameLineEdit.setEnabled(False)
			self.dlg.pointCloudPathLineEdit.setEnabled(False)
			self.dlg.stepSizeSpinBox.setEnabled(False)
			self.dlg.blast2demGroupBox.setEnabled(False)
			self.dlg.pageDescPlainTextEdit.setEnabled(False)

			#cloudfile = self.PotreeCraftSupport.lasconvert_isready(r'c:\PotreeConverter_16\3DModel_Pcld_LASCloud.las', '-rgb', '0.1')
			cloudfile = self.PotreeCraftSupport.lasconvert_isready(self.dlg.pointCloudPathLineEdit.text(), self.ascParam, self.dlg.stepSizeSpinBox.text().replace(',','.'))
			self.dlg.ascFileNameLineEdit.setText(cloudfile)
			print(self.PotreeCraftSupport.potreeconverterpath+cloudfile)
			# add raster layer
			fileInfo = QFileInfo(self.PotreeCraftSupport.potreeconverterpath+cloudfile)
			print(fileInfo)
			path = fileInfo.filePath()
			baseName = fileInfo.baseName()

			layer = QgsRasterLayer(path, baseName)
			QgsProject.instance().addMapLayer(layer)

			if layer.isValid() is True:
				print("Layer was loaded successfully!")
			else:
				print("Unable to read basename and file path - Your string is probably invalid")

			self.dlg.selectCloudButton.setEnabled(True)
			self.dlg.loadCloudButton.setEnabled(True)
			self.dlg.ascFileNameLineEdit.setEnabled(True)
			self.dlg.pointCloudPathLineEdit.setEnabled(True)
			self.dlg.stepSizeSpinBox.setEnabled(True)
			self.dlg.blast2demGroupBox.setEnabled(True)
			self.dlg.pageDescPlainTextEdit.setEnabled(True)

		except Exception as genex:
			print('PYTHON EXCEPTOIN CAUGHT:')
			print(str(genex))
			self.dlg.selectCloudButton.setEnabled(True)
			self.dlg.loadCloudButton.setEnabled(True)
			self.dlg.ascFileNameLineEdit.setEnabled(True)
			self.dlg.pointCloudPathLineEdit.setEnabled(True)
			self.dlg.stepSizeSpinBox.setEnabled(True)
			self.dlg.blast2demGroupBox.setEnabled(True)
			self.dlg.pageDescPlainTextEdit.setEnabled(True)

	def compileProject(self):
		#input,output,outtype,pagename,proj,threadname
		vectorPathList = []
		vectorNameList = []
		vectorColorList = []
		for l in self.vector_table:
			vectorNameList.append((l[1]))
			vectorColorList.append(l[6])
			vectorPathList.append(l[7])
		#print(vectorPathList)
		self.PotreeCraftSupport.pcconvert_isready(self.dlg.pointCloudPathLineEdit.text(),self.dlg.outputFolderLineEdit.text(),self.pcrParam,self.dlg.potreePageLineEdit.text(),self.crsParam,self.dlg.potreePageLineEdit.text())
		self.PotreeCraftSupport.prepareProject(self.dlg.outputFolderLineEdit.text(),vectorPathList)
		self.PotreeCraftSupport.writeHtml(self.dlg.outputFolderLineEdit.text()+'main.html',self.dlg.potreePageLineEdit.text(),[self.pcrParam,None,None,None],vectorNameList,vectorColorList,str(self.dlg.pageDescPlainTextEdit.toPlainText()))
	def run(self):
		"""Run method that performs all the real work"""
		# Create the dialog with elements (after translation) and keep reference
		# Only create GUI ONCE in callback, so that it will only load when the plugin is started

		if self.first_start == True:
			self.first_start = False
			self.dlg = PotreeCraftDialog()

		# show the dialog
		self.dlg.show()

		self.loadLayerCRSsForComboBox()
		self.loadCfgIntoInterface()
		self.checkPathValidity()

		# button connect didn't work in suggested locaiton by pyqgis documentation (init). so i moved it here for now.
		#
		if self.runCounterBecauseICannotInitiateButtonsInTheirDesignatedPlace == 0:
			# -- main window --
			self.dlg.CompileButton.clicked.connect(self.compileProject)

			# -- pointcloud conversion panel --
			self.dlg.crsCustomRadioButton.toggled.connect(self.onCustomCRSRadioButtonClicked)
			self.dlg.crsFromLayerRadioButton.toggled.connect(self.onLayerCRSRadioButtonClicked)
			self.dlg.crsFromProjectComboBox.currentTextChanged.connect(self.onCRSComboboxChanged)

			self.dlg.rgbColorRadioButton.toggled.connect(self.onRgbColorRadioButtonClicked)
			self.dlg.intColorRadioButton.toggled.connect(self.onIntColorRadioButtonClicked)
			self.dlg.intGradColorRadioButton.toggled.connect(self.onIntGradColorRadioButtonClicked)
			self.dlg.heightColorRadioButton.toggled.connect(self.onHeightColorRadioButtonClicked)
			self.dlg.rgbHeightColorRadioButton.toggled.connect(self.onRgbHeightColorRadioButtonClicked)
			self.dlg.classColorRadioButton.toggled.connect(self.onClassColorRadioButtonClicked)
			self.dlg.customColorRadioButton.toggled.connect(self.onCustomColorRadioButtonClicked)

			self.dlg.loadCloudButton.clicked.connect(self.loadCloudIntoQGIS)
			self.dlg.selectCloudButton.clicked.connect(self.selectLASFile)
			self.dlg.selectOutputFolderButton.clicked.connect(self.selectOutputFolder)

			self.dlg.ascGrayRadioButton.toggled.connect(self.onAscGrayColorRadioButtonClicked)
			self.dlg.ascSlopeRadioButton.toggled.connect(self.onAscSlopeColorRadioButtonClicked)
			self.dlg.ascRgbRadioButton.toggled.connect(self.onAscRgbColorRadioButtonClicked)
			self.dlg.ascIntensityRadioButton.toggled.connect(self.onAscIntensityColorRadioButtonClicked)
			self.dlg.ascElevationRadioButton.toggled.connect(self.onAscElevationColorRadioButtonClicked)
			self.dlg.ascFalseRadioButton.toggled.connect(self.onAscFalseColorRadioButtonClicked)

			# -- vector layer panel --
			self.dlg.loadVectorsFromPrjButton.clicked.connect(self.loadVectors)
			self.dlg.vectorTreeWidget.itemClicked.connect(self.onItemClicked)

			# -- plugin settings panel --
			self.dlg.selectLasToolsPushButton.clicked.connect(self.selectLASToolsFolder)
			self.dlg.selectPotreeConverterPushButton.clicked.connect(self.selectPotreeConverterFolder)
			self.dlg.saveConfigButton.clicked.connect(self.saveIniFileChanges)
			#self.dlg.checkConfigButton.clicked.connect(self.checkPathValidity)


		# loading up vectors on window popup
		self.loadVectors()
		#print("is signal connected: " + str(self.dlg.CompileButton.isSignalConnected()))
		# Run the dialog event loop
		result = self.dlg.exec_()

		#
		# -- overcoming design issues --
		#
		self.runCounterBecauseICannotInitiateButtonsInTheirDesignatedPlace += 1

		# See if OK was pressed
		if result:
			# Do something useful here - delete the line containing pass and
			# substitute with your code.
			# format c:
			pass
