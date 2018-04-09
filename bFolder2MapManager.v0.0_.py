"""
	Author: Robert H. Cudmore
	Date: 20160815
	Email: robert.cudmore@gmail.com
	Web: http://robertcudmore.org
	Github: https://github.com/cudmore/bob-fiji-plugins

	This script will convert a directory of image files into single channel .tif files.
	The output .tif files can then be imported into MapManager.
	All output .tif files go into new folder /src/src_tif where /src/ is the directory you specify
	This script should work for:
		- Zeiss lsm/czi
		- ScanImage 3 .tif files
		- Not sure about other formats ???
		
	If you need a slightly different converter for your specific files, please email Robert Cudmore.
	We will extend this to ScanImage 4, please email for updates.

	The name of this file must end in an underscore, '_'. Otherwise Fiji will not install it as a plugin.

	Options:
		1) magic_scan_image_scale
			For ScanImage files, set magic_scan_image_scale. If you do not do this the scale WILL BE WRONG
		2) date_order
			Check the date format on the computer you are using to acquire images and set date_order appropriately.
	
	Change Log:
		20170810: Updated to handle __name__ == __builtin__
		20170811: added acceptedExtensions = ['.lsm', '.tif']
		20170811: Should now work with ScanImage 3
		20170812: Now handles Zeiss .czi files. Date, time, zoom, and voxel size should all be correct		
"""

import os, time

from ij import IJ
from ij import WindowManager
from ij.io import DirectoryChooser, FileSaver, Opener, FileInfo
from ij.plugin import ZProjector

from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from loci.formats import ImageReader
from loci.formats import MetadataTools

###
# Options
###

# This number specifies the voxel size (um) for ScanImage .tif files at 1024x1024, zoom=1
# voxelx and voxely = magic_scan_image_scale / zoom
# If this is not set correctly (for your scope) then the output voxels will be WRONG
magic_scan_image_scale = 0.54

# Folders that are converted to Map Manager should all be following the same date format.
# If they are heterogeneous in their date formats, split your raw tif/lsm/czi files into different folders.
# Set the format for a folder and run this script, repeat on other foder and then manually merge output
date_order = 'mmddyyyy' # possible values here are: yyyymmdd, mmddyyyy, ddmmyyyy
date_order = 'yyyymmdd' # johns czi files (core computers are set up this way?)

###
# End Options
###

versionStr = '0.1' # 20170813: first version

##################################################################################################
class bImp:
	def __init__(self, filepath):
		"""
		Load an image or stack from filepath.

		Args:
			filepath (str): Full path to an image file. Can be .tif, .lsm, .czi, etc
		"""
		
		if not os.path.isfile(filepath):
			bPrintLog('ERROR: bImp() did not find file: ' + filepath,0)
			return 0

		self.filepath = filepath
		folderpath, filename = os.path.split(filepath)
		self.filename = filename
		self.enclosingPath = folderpath
		self.enclosingfolder = os.path.split(folderpath)[1]

		self.dateStr = ''
		self.timeStr = ''
		
		self.imp = None
		
		tmpBaseName, extension = os.path.splitext(filename)
		isZeiss = extension in ['.czi', '.lsm']
		self.islsm = extension == '.lsm'
		self.isczi = extension == '.czi'
		istif = extension == '.tif'
				
		if istif:
			# scanimage3 comes in with dimensions: [512, 512, 1, 52, 1]) = [width, height, numChannels, numSlices, numFrames]
			self.imp = Opener().openImage(filepath)
			self.imp.show()
			
		elif isZeiss:
			#open lsm using LOCI Bio-Formats
			options = ImporterOptions()
			#options.setColorMode(ImporterOptions.COLOR_MODE_GRAYSCALE)
			options.setId(filepath)
			imps = BF.openImagePlus(options)
			for imp in imps:
				self.imp = imp #WindowManager.getImage(self.windowname)
				imp.show()

		if not self.imp:
			bPrintLog('ERROR: bImp() was not able to open file: '+ filepath,0)
    				
		self.windowname = filename
		#self.imp = WindowManager.getImage(self.windowname)

		# numChannels is not correct for scanimage, corrected in readTiffHeader()
		(width, height, numChannels, numSlices, numFrames) = self.imp.getDimensions()

		self.width = width # pixelsPerLine
		self.height = height # linesPerFrame
		self.numChannels = numChannels
		self.numSlices = numSlices
		self.numFrames = numFrames

		self.infoStr = self.imp.getProperty("Info") #get all tags
				
		self.voxelx = 1
		self.voxely = 1
		self.voxelz = 1
		#self.numChannels = 1
		#self.bitsPerPixel = 8
		self.zoom = 1

		self.motorx = None
		self.motory = None
		self.motorz = None

		self.scanImageVersion = ''
		self.msPerLine = None
		self.dwellTime = None
		
		# read file headers (date, time, voxel size)
		if isZeiss:
			self.readZeissHeader(self.infoStr)
		elif istif:
			self.readTiffHeader(self.infoStr)

		self.updateInfoStr()
		
		self.channelWindows = []
		self.channelImp = []

		if self.numChannels == 1:
			self.channelWindows.append(self.windowname)
			self.channelImp.append(self.imp)
		else:
			self.deinterleave()
			
	def updateInfoStr(self):
		# Fill in infoStr with Map Manager tags		

		self.infoStr += 'Folder2MapManager=' + versionStr + '\n'

		self.infoStr += 'b_date=' + self.dateStr + '\n'
		self.infoStr += 'b_time=' + self.timeStr + '\n'
		
		# yevgeniya 20180314
		#if (self.numChannels > 3):
		#	self.numChannels = 3
		self.infoStr += 'b_numChannels=' + str(self.numChannels) + '\n'
		self.infoStr += 'b_pixelsPerline=' + str(self.width) + '\n'
		self.infoStr += 'b_linesPerFrame=' + str(self.height) + '\n'
		self.infoStr += 'b_numSlices=' + str(self.numSlices) + '\n'
		
		self.infoStr += 'b_voxelX=' + str(self.voxelx) + '\n'
		self.infoStr += 'b_voxelY=' + str(self.voxely) + '\n'
		self.infoStr += 'b_voxelZ=' + str(self.voxelz) + '\n'

		#self.infoStr += 'b_bitsPerPixel=' + str(self.bitsPerPixel) + '\n'

		self.infoStr += 'b_zoom=' + str(self.zoom) + '\n'
		
		self.infoStr += 'b_motorx=' + str(self.motorx) + '\n'
		self.infoStr += 'b_motory=' + str(self.motory) + '\n'
		self.infoStr += 'b_motorz=' + str(self.motorz) + '\n'

		self.infoStr += 'b_msPerLine=' + str(self.msPerLine) + '\n'

		self.infoStr += 'b_scanImageVersion=' + self.scanImageVersion + '\n'

	
	def readTiffHeader(self, infoStr):
		"""
		Read ScanImage 3/4 .tif headers
		"""
		logLevel = 3

		# splitting on '\r' for scanimage 3.x works
		# splitting on '\n' for scanimage 4.x works
		
		#we need to search whole infoStr to figure out scanimage 3 or 4.
		# we can't split info string because si3 uses \r and si4 uses \n
		
		infoStrDelim = '\n'
		if infoStr.find('scanimage.SI4') != -1:
			infoStrDelim = '\n'
			bPrintLog('Assuming SI4 infoStr to be delimited with backslash n', logLevel)
		elif infoStr.find('state.software.version') != -1:
			infoStrDelim = '\r'
			bPrintLog('Assuming SI3 infoStr to be delimited with backslash r', logLevel)
		else:
			bPrintLog('Splitting infoStr using backslah n', logLevel)

		# if we don't find zoom then voxel is an error (see end of function)
		foundZoom = False
		
		#for line in infoStr.split('\n'):
		for line in infoStr.split(infoStrDelim):
			#
			# ScanImage 4.x
			#
			
			# scanimage.SI4.versionMajor = 4.2
			if line.find('scanimage.SI4.versionMajor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.scanImageVersion = rhs
			
			# scanimage.SI4.motorPosition = [-33936.5 -106316 -55308.5]
			if line.find('scanimage.SI4.motorPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace('[','')
				rhs = rhs.replace(']','')
				floats = [float(x) for x in rhs.split()]
				self.motorx = floats[0]
				self.motory = floats[1]
				self.motorz = floats[2]

			# scanimage.SI4.channelsSave = [1;2]
			if line.find('scanimage.SI4.channelsSave') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace('[','')
				rhs = rhs.replace(']','')
				channels = [int(x) for x in rhs.split(';')]
				bPrintLog('reading scanimage.SI4.channelsSave inferred channels:' + str(channels), logLevel)
				self.numChannels = len(channels)

			# scanimage.SI4.scanZoomFactor = 5.9
			if line.find('scanimage.SI4.scanZoomFactor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.zoom = float(rhs)
				foundZoom = True
				#self.voxelx = magic_scan_image_scale / self.zoom
				#self.voxely = magic_scan_image_scale / self.zoom

			# scanimage.SI4.triggerClockTimeFirst = '18-05-2015 11:58:43.788'
			if line.find('scanimage.SI4.triggerClockTimeFirst') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace("'","") # remove enclosing ' and '
				if rhs.startswith(' '): # if date string starts with space, remove it
					rhs = rhs[1:-1]
				datetime = rhs.split(' ')
				# 20170811, there is an extra fucking space before datestr on the rhs
				# convert mm/dd/yyyy to yyyymmdd
				#print 'rhs:' + "'" + rhs + "'"
				#print 'datetime:', datetime
				datestr = bFixDate(datetime[0], logLevel)
				self.dateStr = datestr
				self.timeStr = datetime[1]
			
			#
			# ScanImage 3.x
			#
			
			# state.software.version = 3.8
			if line.find('state.software.version') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.scanImageVersion = rhs
			
			# state.acq.numberOfChannelsAcquire = 2
			if line.find('state.acq.numberOfChannelsAcquire') != -1:
				#print '\rDEBUG 12345'
				bPrintLog(line, logLevel)
				#print '\rDEBUG 12345'
				rhs = line.split('=')[1]
				self.numChannels = int(rhs)

			# state.acq.zoomFactor = 2.5
			if line.find('state.acq.zoomFactor') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.zoom = float(rhs)
				foundZoom = True
				# set (voxelx, voxely)
				#self.voxelx = magic_scan_image_scale / self.zoom
				#self.voxely = magic_scan_image_scale / self.zoom
				
			# state.acq.msPerLine = 2.32
			if line.find('state.acq.msPerLine') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.msPerLine = float(rhs)
			
			# state.acq.pixelTime = 3.2e-06
			if line.find('state.acq.pixelTime') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.dwellTime = float(rhs)

			# state.motor.absXPosition = -9894.4
			if line.find('state.motor.absXPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.motorx = float(rhs)

			# state.motor.absYPosition = -18423.4
			if line.find('state.motor.absYPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.motory = float(rhs)

			# state.motor.absZPosition = -23615.04
			if line.find('state.motor.absZPosition') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.motorz = float(rhs)

			# state.acq.zStepSize = 2
			if line.find('state.acq.zStepSize') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				self.voxelz = float(rhs)

			# state.internal.triggerTimeString = '10/2/2014 12:29:22.796'
			if line.find('state.internal.triggerTimeString') != -1:
				bPrintLog(line, logLevel)
				rhs = line.split('=')[1]
				rhs = rhs.replace("'","")
				if rhs.startswith(' '): # if date string starts with space, remove it
					rhs = rhs[1:-1]
				datetime = rhs.split(' ')
				# 20170811, there is an extra fucking space before datestr on the rhs
				# convert mm/dd/yyyy to yyyymmdd
				#print 'rhs:' + "'" + rhs + "'"
				#print 'datetime:', datetime
				self.dateStr = bFixDate(datetime[0], logLevel)
				self.timeStr = bFixTime(datetime[1], logLevel)
				

			# state.acq.acqDelay = 0.000122
			# state.acq.bidirectionalScan = 0
			# state.acq.fillFraction = 0.706206896551724
			# state.acq.frameRate = 0.841864224137931
			# huganir lab keeps this off, image pixel intensities are 2^11 * samplesperpixel (e.g. binFactor?)
			# state.acq.binFactor = 16
			# state.internal.averageSamples = 1
			# the real image bit depth is usually inputBitDepth-1 (1 bit is not used?)
			# state.acq.inputBitDepth = 12

		if foundZoom:
			self.voxelx = magic_scan_image_scale / self.zoom * (1024 / self.width)
			self.voxely = magic_scan_image_scale / self.zoom * (1024 / self.height)
		else:
			bPrintLog('ERROR: Did not find zoom in SI header, voxel x/y will be wrong', logLevel)
			
	def readZeissHeader(self, infoStr):		
		# This is incredibly difficult to get working as (date, time, voxels) are in different obscure places in lsm and czi
		# Furthermore, just trying to read the raw ome xls is futile
		#
		# parsing ome xml as a string and searching it with regular expression(re) does not work
		# it is beyond the scope of my work to figure this out
		# the fact that it does not work and there is little documentaiton is a pretty big waste of time
		#
		# get and parse xml to find date/time
		#fi = self.imp.getOriginalFileInfo(); # returns a FileInfo object
		#omexml = fi.description #omexml is a string
		#omexml = omexml.encode('utf-8')
		#omexml = omexml.replaceAll("[^\\x20-\\x7e]", "") # see: https://stackoverflow.com/questions/2599919/java-parsing-xml-document-gives-content-not-allowed-in-prolog-error

		# (1) try and search the ome xml like a string, this gives errors
		#docsPattern = '<AcquisitionDate>.*</AcquisitionDate>'
		#searchresult = re.search(docsPattern, omexml)
		#print 'searchresult:', searchresult.group(0)
		
		# 2) treat the ome xml like any other xml (because it's xml, right?)
		# well this raises errors too
		#omexml has <AcquisitionDate>2016-08-17T15:21:50</AcquisitionDate>
		#import xml.etree.ElementTree
		#e = xml.etree.ElementTree.fromstring(omexml).getroot()		#print omexml
		#for atype in e.findall('AcquisitionDate'):
		#    print 'AcquisitionDate:', atype #.get('foobar')
		#
		#

		if self.islsm:
			# lsm have date hidden in omeMeta.getImageAcquisitionDate(0)
			# this is copied from code at: https://gist.github.com/ctrueden/6282856
			reader = ImageReader()
			omeMeta = MetadataTools.createOMEXMLMetadata() #omeMeta.getImageAcquisitionDate(0)
			reader.setMetadataStore(omeMeta)
			reader.setId(self.filepath)
			#seriesCount = reader.getSeriesCount()
			dateTimeStr = omeMeta.getImageAcquisitionDate(0) #2016-08-17T16:36:26
			reader.close()
			if dateTimeStr:
				self.dateStr, self.timeStr = dateTimeStr.toString().split('T')
				self.dateStr = bFixDate(self.dateStr)
				self.timeStr = bFixTime(self.timeStr)
				#bPrintLog('LSM date/time is: ' + self.dateStr + ' ' + self.timeStr, 3)
			else:
				bPrintLog('WARNING: did not get Zeiss date/time string')

			# lsm have voxels in infoStr
			for line in infoStr.split('\n'):
				#print line
				if line.find('VoxelSizeX') != -1:
					self.voxelx = float(line.split('=')[1])
				if line.find('VoxelSizeY') != -1:
					self.voxely = float(line.split('=')[1])
				if line.find('VoxelSizeZ') != -1:
					self.voxelz = float(line.split('=')[1])
				if line.find('SizeC') != -1:
					self.numChannels = int(line.split('=')[1])
				#if line.find('BitsPerPixel') and not line.startswith('Experiment') != -1: # 20170811, startswith is for czi
				#	self.bitsPerPixel = int(line.split('=')[1])
				if line.find('RecordingZoomX#1') != -1:
					self.zoom = int(line.split('=')[1])

		if self.isczi:
			# czi has date/time in infoStr (lsm does not)
			for line in infoStr.split('\n'):
				if line.find('CreationDate #1') != -1: # w.t.f. is #1 referring to?
					lhs, rhs = line.split('=')
					rhs = rhs.replace('  ', ' ')
					if rhs.startswith(' '):
						rhs = rhs[1:-1]
					#print "lhs: '" + lhs + "'" + "rhs: '" + rhs + "'"
					if rhs.find('T') != -1:
						self.dateStr, self.timeStr = rhs.split('T')
					else:
						self.dateStr, self.timeStr = rhs.split(' ')
					self.dateStr = bFixDate(self.dateStr)
					self.timeStr = bFixTime(self.timeStr)
					#bPrintLog('CZI date/time is: ' + self.dateStr + ' ' + self.timeStr, 3)
				# .czi
				# <Pixels BigEndian="false" DimensionOrder="XYCZT" ID="Pixels:0" Interleaved="false" PhysicalSizeX="0.20756645602494875" PhysicalSizeXUnit="µm" PhysicalSizeY="0.20756645602494875" PhysicalSizeYUnit="µm" PhysicalSizeZ="0.75" PhysicalSizeZUnit="µm" SignificantBits="8" SizeC="1" SizeT="1" SizeX="1024" SizeY="1024" SizeZ="50" Type="uint8">

			# czi have voxel in calibration
			self.voxelx = self.imp.getCalibration().pixelWidth; 
			self.voxely = self.imp.getCalibration().pixelHeight; 
			self.voxelz = self.imp.getCalibration().pixelDepth; 
			#bPrintLog('readZeissHeader() read czi scale as: ' + str(self.voxelx) + ' ' + str(self.voxely) + ' ' + str(self.voxelz), 3)

			# CLEARING self.infoStr for CZI ... it was WAY to big to parse in Map Manager
			self.infoStr = ''
			
	def printParams(self, loglevel=3): # careful, thefunction print() is already taken?
		bPrintLog('file:' + self.filepath, loglevel)
		bPrintLog("date:'" + self.dateStr + "' time:'" + self.timeStr + "'", loglevel)
		bPrintLog('channels:' + str(self.numChannels), loglevel)
		bPrintLog('zoom:' + str(self.zoom), loglevel)
		bPrintLog('pixels:' + str(self.width) + ',' + str(self.height)+ ',' + str(self.numSlices), loglevel)
		bPrintLog('voxels:' + str(self.voxelx) + ',' + str(self.voxely)+ ',' + str(self.voxelz), loglevel)

	def deinterleave(self):
		if self.numChannels == 1:
			bPrintLog('Warning: deinterleave() did not deinterleave with num channels 1', 0)
			return -1
		
		#IJ.run('Deinterleave', 'how=' + str(self.numChannels) +' keep') #makes ' #1' and ' #2', with ' #2' frontmost
		cmdStr = 'how=' + str(self.numChannels) + ' keep'
		IJ.run('Deinterleave', cmdStr) #makes ' #1' and ' #2', with ' #2' frontmost
		for i in range(self.numChannels):
			currenChannel = i + 1
			currentWindowName = self.windowname + ' #' + str(currenChannel)
			self.channelWindows.append(currentWindowName)
			
			currentImp = WindowManager.getImage(currentWindowName)
			if currentImp:
				self.channelImp.append(currentImp)
			else:
				bPrintLog('ERROR: deinterleave() did not find window names:' + currentWindowName, 0)
			
	def exportTifStack(self, destFolder=''):
		channelNumber = 1
		for imp in self.channelImp:
			if not destFolder:
				destFolder = os.path.join(self.enclosingPath, self.enclosingfolder + '_tif')
			if not os.path.isdir(destFolder):
				os.makedirs(destFolder)
			
			if not imp:
				bPrintLog("ERROR: exportTifStack() did not find an imp at channel number '" + str(channelNumber) + "'", 0)
				return -1
				
			self.updateInfoStr()
			imp.setProperty("Info", self.infoStr);

			saveFile = os.path.splitext(self.filename)[0] + '_ch' + str(channelNumber) + '.tif'
			savePath = os.path.join(destFolder, saveFile)

			# save
			fs = FileSaver(imp)
			bPrintLog('saveTifStack():' + savePath, 3)
			if imp.getNSlices()>1:
				fs.saveAsTiffStack(savePath)
			else:
				fs.saveAsTiff(savePath)

			channelNumber += 1

	def saveMaxProject(self, destFolder=''):
		channelNumber = 1
		for imp in self.channelImp:
			if not destFolder:
				destFolder = os.path.join(self.enclosingPath, self.enclosingfolder + '_tif', 'max')
			if not os.path.isdir(destFolder):
				os.makedirs(destFolder)

			# make max project
			zp = ZProjector(imp)
			zp.setMethod(ZProjector.MAX_METHOD)
			zp.doProjection()
			zimp = zp.getProjection()

			# save
			saveFile = 'max_' + os.path.splitext(self.filename)[0] + '_ch' + str(channelNumber) + '.tif'
			savePath = os.path.join(destFolder, saveFile)
			fs = FileSaver(zimp)
			bPrintLog('saveMaxProject():' + savePath, 3)
			fs.saveAsTiff(savePath)

			channelNumber += 1
			
	def closeAll(self):
		self.imp.close()
		for imp in self.channelImp:
			imp.close()
			
##################################################################################################
def runOneFile(filepath):
	if not os.path.isfile(filepath):
		bPrintLog('ERROR: runOneFile() did not find file: ' + filepath,0)
		return 0

	bPrintLog('runOneFile() filepath:' + filepath, 2)
	theImage = bImp(filepath)
	theImage.printParams()
	ok = theImage.exportTifStack()
	if ok == -1:
		bPrintLog('ERROR: runOneFile() was not able to export stack:' + filepath, 0)
	theImage.saveMaxProject()
	theImage.closeAll()
		
##################################################################################################
def runOneFolder(sourceFolder):
	if not os.path.isdir(sourceFolder):
		bPrintLog('ERROR: runOneFolder() did not find folder: ' + sourceFolder)
		return 0

	bPrintLog('runOneFolder() sourceFolder:' + sourceFolder, 1)

	acceptedExtensions = ['.czi', '.lsm', '.tif']

	# count number of lsm files
	numLSM = 0
	for filename in os.listdir(sourceFolder):
		baseName, extension = os.path.splitext(filename)
		#if filename.endswith(".lsm"):
		if not filename.startswith('.') and extension in acceptedExtensions:
			numLSM += 1
				
	#fileList = []
	outLSM = 1
	for filename in os.listdir(sourceFolder):		
		baseName, extension = os.path.splitext(filename)
		
		#islsm = filename.endswith(".lsm")
		#istif = filename.endswith(".tif")
		#if outLSM==1 or outLSM==2: # to run one file for debugging
		#if 1:
		#if filename.endswith(".lsm"):
		if extension in acceptedExtensions:
			#if islsm or istif:
			#fileList.append(filename)
			filePath = sourceFolder + filename
			bPrintLog(str(outLSM) + ' of ' + str(numLSM), 2)
			runOneFile(filePath)
			outLSM += 1

	return outLSM
	
##################################################################################################
# utility
##################################################################################################
def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)

##################################################################################################
def bFixTime(timestr, logLevel=0):
	
	# remmove fractonal seconds (This ASSUMES the only place we would find a '.' is after seconds !!!)
	dotIdx = timestr.find('.')
	if dotIdx > 0:
		timestr = timestr[0:dotIdx-1]

	hh, mm, ss = timestr.split(':')
	
	# zero pad hh:mm:ss
	hh = hh.zfill(2)
	mm = mm.zfill(2)
	ss = hh.zfill(2)
	
	timestr = hh + ":" + mm + ":" + ss
	return timestr
##################################################################################################
def bFixDate(datestr, logLevel=0):
	# try and return datStr as yyyymmdd

	# determine if date is delimited with ('/', '-', '_')
	if datestr.find('/') != -1:
		datedelim = '/'
	elif datestr.find('-') != -1:
		datedelim = '-'
	elif datestr.find('_') != -1:
		datedelim = '_'
	else:
		datedelim = None
		bPrintLog('ERROR: did not recognize date:' + datestr + '. Expecting (/, -, _)', logLevel)
	
	# parse date depending on user specified global date_order
	if date_order == 'mmddyyyy':
		if datedelim:
			mm, dd, yyyy = datestr.split(datedelim)
		else:
			mm = datestr[0:1]
			dd = datestr[2:3]
			yyyy = datestr[4:7]
	elif date_order == 'ddmmyyyy':
		if datedelim:
			dd, mm, yyyy = datestr.split(datedelim)
		else:
			mm = datestr[0:1]
			dd = datestr[2:3]
			yyyy = datestr[4:7]
	elif date_order == 'yyyymmdd':
		if datedelim:
			yyyy, mm, dd = datestr.split(datedelim)
		else:
			yyyy = datestr[0:3]
			mm = datestr[4:5]
			dd = datestr[6:7]
	else:
		bPrintLog('ERROR: bFixDate() did not recognize date_order:' + date_order, logLevel)

	#zero pad mm, dd, and yyyy
	mm = mm.zfill(2)
	dd = dd.zfill(2)
	if len(yyyy) != 4:
		bPrintLog('ERROR: Y2K bug, your year should be 4 characters long, got year:' + yyyy, logLevel)
	retStr = yyyy + mm + dd
	return retStr


##################################################################################################
# main
##################################################################################################
"""
	print __name__
	This is coming up as '__builtin__' in Fiji downloaded on 20170810.
"""
if __name__ in ['__main__', '__builtin__']: 
	startTime = time.time()
	
	bPrintLog('\n=================')
	bPrintLog('Starting bFolder2MapManager')
	bPrintLog('*** IMPORTANT *** Using magic_scan_image_scale:' + str(magic_scan_image_scale) + ' for ScanImage files. voxel (um) = ' + str(magic_scan_image_scale) + '/zoom')
	
	#sourceFolder = '/Volumes/fourt/MapManager_Data/sarah_immuno/8.17.16/8.17.16.mdb/'
	sourceFolder = DirectoryChooser("Please Choose A Directory Of Files").getDirectory()

	outFiles = 0
	if (sourceFolder):
		outFiles = runOneFolder(sourceFolder)
	else:
		bPrintLog('Canceled by user', 0)
	
	stopTime = time.time()
	bPrintLog('Finished bFolder2MapManager with ' + str(outFiles) + ' files in ' + str(round(stopTime-startTime,2)) + ' seconds')
	bPrintLog('=================\n')
	