# Author: Robert H. Cudmore
# Date: 20160913

'''
   This is an ImageJ/Fiji Jython script that converts a folder of Prairie folders
   into single file .tif files (one multi-page .tif file for each original prairie folder)

   Prairie scope parameters, are written into the output .tif file headers with the prefix 'b_'.
   
   For example:
      b_dateStr
      b_timeStr
      b_voxelx
      b_voxely
      b_zStep
      
   Important:
      (1) The user must specify 'date_order' below to match the format of dates saved into
      		the prairie view tiff header
      	Possible values are:
      		date_order = 'yyyymmdd'
			date_order = 'ddmmyyyy'
			date_order = 'mmddyyyy'

      (2) This script is designed to read the files saved directly from the PrairieView software.
      Please only use this script with the raw .tif files saved by PrairieView
      If you open and then resave these .tif files by hand (in Fiji for example) you will
      loose the Prairie header information.

      (3) This script will work with 1-3 color channel images.
      		It will not work with >= 4 color channels

   History:
   	20170314, expanding to handle 3 color channels for Daisuke
	201710, reading prairie view v='4.3.2.24' for Daisuke
	20171004, add save max project
	20171004, reading x/y scale for Daisuke (z scale is not finished)
	20171004, fixed 12pm time bug
	20171025, v0.0
	
   To Do:
      - Make loops to go through channels. Right now channels 1/2/3 are hard coded
      - Before I write any more xml parse code, I need to understand what the hell I am doing
      - Convert all dates to yyyymmdd
      
'''

#imagej (java)
from ij import IJ
from ij import WindowManager, ImagePlus, ImageStack
from ij.io import DirectoryChooser, FileSaver
from ij.process import ImageConverter # default convert to 8-bit will scale. Turn it off. See: https://ilovesymposia.com/2014/02/26/fiji-jython/
from ij.plugin import ZProjector
from ij.plugin import Concatenator # this append slices to imageplus
from ij.plugin import StackCombiner # this combines by adding rows, use StackCombiner.combineVertically(imp1,imp2)
from ij.gui import GenericDialog

#python
import os
import time
from os.path import basename
import xml.etree.ElementTree as ET

gVersionStr = 'bPrairie2tif.v0.0'

#date_order = 'yyyymmdd' # johns czi files (core computers are set up this way?)
#date_order = 'ddmmyyyy'
date_order = 'mmddyyyy' # possible values here are: yyyymmdd, mmddyyyy, ddmmyyyy

'''
Notes
(1) For a Z Series we need to read the position of sequential frames to get 'Z Step' in um
	e.g.
	(1) read each value="937.33" in <SubindexedValue subindex="0" value="937.33" description="Z Focus" />
	(2) take difference between each <Frame>

	This is way to complicated

    <Frame relativeTime="5.30900000000111" absoluteTime="5.38999999999942" index="3" parameterSet="CurrentSettings">
      <File channel="1" channelName="Red" filename="20161123_a189b-087_Cycle00001_Ch1_000003.ome.tif" />
      <File channel="2" channelName="Green" filename="20161123_a189b-087_Cycle00001_Ch2_000003.ome.tif" />
      <ExtraParameters lastGoodFrame="0" />
      <PVStateShard>
        <PVStateValue key="laserPower">
          <IndexedValue index="0" value="161" description="Pockels" />
          <IndexedValue index="1" value="0" description="Blue" />
          <IndexedValue index="2" value="0" description="Yellow" />
        </PVStateValue>
        <PVStateValue key="pmtGain">
          <IndexedValue index="0" value="700" description="Red 1 HV" />
          <IndexedValue index="1" value="700" description="Green 2 HV" />
        </PVStateValue>
        <PVStateValue key="positionCurrent">
          <SubindexedValues index="XAxis">
            <SubindexedValue subindex="0" value="330.78" />
          </SubindexedValues>
          <SubindexedValues index="YAxis">
            <SubindexedValue subindex="0" value="-787.33" />
          </SubindexedValues>
          <SubindexedValues index="ZAxis">
            <SubindexedValue subindex="0" value="937.33" description="Z Focus" />
            <SubindexedValue subindex="1" value="-125" description="Bruker 250 m Piezo" />
          </SubindexedValues>
        </PVStateValue>
        <PVStateValue key="twophotonLaserPower">
          <IndexedValue index="0" value="1650.25" />
        </PVStateValue>
      </PVStateShard>
    </Frame>

(2) I can't find samples per pixel in z-series (I am using b_resonantSamplesPerPixel for resonant)

(3) I am not reading .env file (only reading .xml file)

	Could read pmt from .env file

	  <PVPMTs>
	    <PVPMT index="0" previousDisplayValue="700" zeroed="False" />
	    <PVPMT index="1" previousDisplayValue="700" zeroed="False" />
	  </PVPMTs>

'''


gAllowOverwrite = True # if true then replace existing output .tif files, if false do not
gOutputHeader = True # output a single .txt file with header information for each .tif (one tif per row)
gOutputTif = True # open/save tif files (this is the main point of this plugin)
gTextDelim = '\t'

globalOptions = {}
globalOptions['medianFilter'] = 0
globalOptions['convertToEightBit'] = False

def optionsDialog():
	gd = GenericDialog('bPrairie2tif options')

	# label, value, digits
	gd.addNumericField('Median Filter Pixel Size (0 for no filtering)', globalOptions['medianFilter'], 0)
	gd.addCheckbox('Convert to 8 bit', globalOptions['convertToEightBit'])
	
	gd.showDialog()
	if gd.wasCanceled():
		return None

	globalOptions['medianFilter'] = gd.getNextNumber()
	globalOptions['convertToEightBit'] = gd.getNextBoolean()

	return 1
	
class bPrairieStack:
	def __init__(self, srcFolder):

		if not os.path.isdir(srcFolder):
			bPrintLog('ERROR: bPrairieStack() did not find folder: ' + srcFolder,0)
			return 0

		self.srcFolder = srcFolder # the folder that contains a number of .tif
		self.enclosingFolder = os.path.split(srcFolder)[0] # full path to srcFolder (without /)
		self.sessionFolderPath, self.enclosingFolderName = os.path.split(self.enclosingFolder)
		self.sessionFolderName = os.path.split(self.sessionFolderPath)[1]
		self.dstFolder = os.path.join(self.sessionFolderPath, self.sessionFolderName + '_out')

		# to write parems to one file (one row per tif)
		self.dstTextFile = os.path.join(self.dstFolder, self.sessionFolderName + '.txt')

		self.dstTextFile0 = os.path.join(self.dstFolder, self.enclosingFolderName + '.txt')
		
		self.imp_ch1 = None # the ImagePlus (imp) we are making
		self.imp_ch2 = None
		self.imp_ch3 = None

		self.frameTimes = []
		self.ch1_names = []
		self.ch2_names = []
		self.ch3_names = []

		self.zPosition = [] # record z position of each <Frame> for Z-Series
		self.zStep = None

		self.laserPower = []
		self.pmt0 = []
		self.pmt1 = []
		self.pmt2 = []
		
		self.header = self.GetPrairieHeader() # get acquisition params from .xml file
		self.infoStr0 = ''
		if self.header:
			for key, value in self.header.iteritems():
				self.infoStr0 += key + '=' + value + '\n'
			#print 'DEBUG: self.infoStr0:', self.infoStr0
			
		# single channel .tif files
		self.savePath_ch1 = os.path.join(self.dstFolder, self.enclosingFolderName + '_ch1.tif')
		self.savePath_ch2 = os.path.join(self.dstFolder, self.enclosingFolderName + '_ch2.tif')
		self.savePath_ch3 = os.path.join(self.dstFolder, self.enclosingFolderName + '_ch3.tif')

		# max projection file
		self.dstMaxFolder = os.path.join(self.dstFolder,'max')
		if not os.path.isdir(self.dstMaxFolder):
			os.makedirs(self.dstMaxFolder)
		
		self.savePathMax_ch1 = os.path.join(self.dstMaxFolder, 'max_' + self.enclosingFolderName + '_ch1.tif')
		self.savePathMax_ch2 = os.path.join(self.dstMaxFolder, 'max_' + self.enclosingFolderName + '_ch2.tif')
		self.savePathMax_ch3 = os.path.join(self.dstMaxFolder, 'max_' + self.enclosingFolderName + '_ch3.tif')
		
	def loadTif(self, allowOverwrite=1):
		if self.header['b_sequence'] == 'Linescan':
			bPrintLog('Skipping: bPrairie2tif does not support Linescan, email bob and have him implement this', 3)
			return 0
			
		width = None
		height = None
		#ip_ch1 = [] # a list of images as a list of 'image processor'
		#ip_ch2 = []
		#ip_ch3 = []

		bPrintLog('Loading ' + str(self.header['b_numSlices']) + ' Files ...', 3)
		numFiles = 0
		infoStr = ''
		
		# sort individual .tif files into ch1 and ch2
		for filename in os.listdir(self.srcFolder):
			if filename.endswith(".tif") and not filename.startswith('.'):
				# bPrintLog('opening:' + filename, 3)
				try:
					imp = IJ.openImage(self.srcFolder + filename)  
					if imp is None:  
						bPrintLog("ERROR: prairie2stack() could not open image from file:" + self.srcFolder + filename)  
						continue  
					isch1 = '_Ch1_' in filename
					isch2 = '_Ch2_' in filename
					isch3 = '_Ch3_' in filename
					if numFiles == 0:
						# don;t do this, header is to big to keep with output .tif
						#infoStr = imp.getProperty("Info") #get all tags, this is usefless
						infoStr += '\n' + self.infoStr0 # when appending, '\n' (EOL) is important because header does NOT end in EOL
						width = imp.width
						height = imp.height
					
					#stack = imp.getImageStack() 
					#cp = stack.getProcessor(1) # assume 1 channel 
					if isch1:
						#ip_ch1.append(cp)
						if self.imp_ch1 is None:
							self.imp_ch1 = imp
						else:
							self.imp_ch1 = Concatenator.run(self.imp_ch1, imp)
					elif isch2:
						#ip_ch2.append(cp)
						if self.imp_ch2 is None:
							self.imp_ch2 = imp
						else:
							self.imp_ch2 = Concatenator.run(self.imp_ch2, imp)
					elif isch3:
						#ip_ch3.append(cp)
						if self.imp_ch3 is None:
							self.imp_ch3 = imp
						else:
							self.imp_ch3 = Concatenator.run(self.imp_ch3, imp)
					else:
						bPrintLog('ERROR: did not find channel name in file:' + filename)
					
					numFiles += 1
				except:
					continue
					#bPrintLog("exception error: prairie2stack() could not open image from file:" + self.srcFolder + filename)  
		
		bPrintLog('Loaded ' + str(numFiles) + ' files ...', 3)
		'''
		bPrintLog('ch1 has ' + str(len(ip_ch1)) + ' slices', 4)
		bPrintLog('ch2 has ' + str(len(ip_ch2)) + ' slices', 4)
		bPrintLog('ch3 has ' + str(len(ip_ch3)) + ' slices', 4)
		'''
		
		#20170314, need to rewrite this to loop through channels (lots of repeated code here

		if self.imp_ch1 is not None:
			self.imp_ch1.setProperty("Info", infoStr);
		if self.imp_ch2 is not None:
			self.imp_ch2.setProperty("Info", infoStr);
		if self.imp_ch3 is not None:
			self.imp_ch3.setProperty("Info", infoStr);

		#ch1
		#if ip_ch1:
		if self.imp_ch1:
			# bPrintLog('ch1 has ' + str(self.imp_ch1.getNSlices()) + ' slices', 4)
			'''
			stack_ch1 = ImageStack(width, height)
			for fp in ip_ch1:
				stack_ch1.addSlice(fp)
			self.imp_ch1 = ImagePlus('xxx', stack_ch1)  
			self.imp_ch1.setProperty("Info", infoStr);
			'''
			
			# median filter
			if globalOptions['medianFilter']>0:
				bPrintLog('ch1: Running median filter: ' + str(globalOptions['medianFilter']), 4)
				medianArgs = 'radius=' + str(globalOptions['medianFilter']) + ' stack'
				IJ.run(self.imp_ch1, "Median...", medianArgs);
				infoStr += 'bMedianFilter=' + str(globalOptions['medianFilter']) + '\n'
				self.imp_ch1.setProperty("Info", infoStr)

			if globalOptions['convertToEightBit']:
				bPrintLog('converting to 8-bit by dividing image down and then convert to 8-bit with ImageConverter.setDoScaling(False)', 4)
				bitDepth = 2^13
				divideBy = bitDepth / 2^8
				# divide the 13 bit image down to 8 bit
				#run("Divide...", "value=32 stack");
				bPrintLog('divideBy:' + str(divideBy), 4)
				divideArgs = 'value=' + str(divideBy) + ' stack'
				IJ.run(self.imp_ch1, "Divide...", divideArgs);
				# convert to 8-bit will automatically scale, to turn this off use
				# eval("script", "ImageConverter.setDoScaling(false)"); 
				ImageConverter.setDoScaling(False)
				# run("8-bit");
				bPrintLog('converting to 8-bit with setDoScaling False', 4)
				IJ.run(self.imp_ch1, "8-bit", '');

			# print stats including intensity for the stack we just made
			# Returns the dimensions of this image (width, height, nChannels, nSlices, nFrames) as a 5 element int array.
			d = self.imp_ch1.getDimensions() # width, height, nChannels, nSlices, nFrames
			stats = self.imp_ch1.getStatistics() # stats.min, stats.max
			bPrintLog('ch1 dimensions w:' + str(d[0]) + ' h:' + str(d[1]) + ' channels:' + str(d[2]) + ' slices:' + str(d[3]) + ' frames:' + str(d[4]), 4)
			bPrintLog('ch1 intensity min:' + str(stats.min) + ' max:' + str(stats.max), 4)

			# set the voxel size so opening in Fiji will report correct bit depth
			# run("Properties...", "channels=1 slices=300 frames=1 unit=um pixel_width=.2 pixel_height=.3 voxel_depth=.4");


		#ch2
		#if ip_ch2:
		if self.imp_ch2:
			# bPrintLog('ch2 has ' + str(self.imp_ch2.getNSlices()) + ' slices', 4)
			'''
			stack_ch2 = ImageStack(width, height) 
			for fp in ip_ch2:
				stack_ch2.addSlice(fp)
	
			self.imp_ch2 = ImagePlus('xxx', stack_ch2)  
			self.imp_ch2.setProperty("Info", infoStr);
			'''
			# median filter
			if globalOptions['medianFilter']>0:
				bPrintLog('ch2: Running median filter: ' + str(globalOptions['medianFilter']), 4)
				medianArgs = 'radius=' + str(globalOptions['medianFilter']) + ' stack'
				IJ.run(self.imp_ch2, "Median...", medianArgs);
				infoStr += 'bMedianFilter=' + str(globalOptions['medianFilter']) + '\n'
				self.imp_ch2.setProperty("Info", infoStr)

			if globalOptions['convertToEightBit']:
				bPrintLog('converting to 8-bit by dividing image down and then convert to 8-bit with ImageConverter.setDoScaling(False)', 4)
				bitDepth = 2^13
				divideBy = bitDepth / 2^8
				# divide the 13 bit image down to 8 bit
				#run("Divide...", "value=32 stack");
				bPrintLog('divideBy:' + str(divideBy), 4)
				divideArgs = 'value=' + str(divideBy) + ' stack'
				IJ.run(self.imp_ch2, "Divide...", divideArgs);
				# convert to 8-bit will automatically scale, to turn this off use
				# eval("script", "ImageConverter.setDoScaling(false)"); 
				ImageConverter.setDoScaling(False)
				# run("8-bit");
				bPrintLog('converting to 8-bit with setDoScaling False', 4)
				IJ.run(self.imp_ch2, "8-bit", '');

			# print stats including intensity for the stack we just made
			d = self.imp_ch2.getDimensions() # width, height, nChannels, nSlices, nFrames
			stats = self.imp_ch2.getStatistics() # stats.min, stats.max
			bPrintLog('ch2 dimensions w:' + str(d[0]) + ' h:' + str(d[1]) + ' channels:' + str(d[2]) + ' slices:' + str(d[3]) + ' frames:' + str(d[4]), 4)
			bPrintLog('ch2 intensity min:' + str(stats.min) + ' max:' + str(stats.max), 4)
			
		#ch2
		#if ip_ch3:
		if self.imp_ch3:
			# bPrintLog('ch1 has ' + str(self.imp_ch3.getNSlices()) + ' slices', 4)
			'''
			stack_ch3 = ImageStack(width, height) 
			for fp in ip_ch3:
				stack_ch3.addSlice(fp)
	
			self.imp_ch3 = ImagePlus('xxx', stack_ch3)  
			self.imp_ch3.setProperty("Info", infoStr);
			'''
			
			# median filter
			if globalOptions['medianFilter']>0:
				bPrintLog('ch3: Running median filter: ' + str(globalOptions['medianFilter']), 4)
				medianArgs = 'radius=' + str(globalOptions['medianFilter']) + ' stack'
				IJ.run(self.imp_ch3, "Median...", medianArgs);
				infoStr += 'bMedianFilter=' + str(globalOptions['medianFilter']) + '\n'
				self.imp_ch3.setProperty("Info", infoStr)

			if globalOptions['convertToEightBit']:
				bPrintLog('converting to 8-bit by dividing image down and then convert to 8-bit with ImageConverter.setDoScaling(False)', 4)
				bitDepth = 2^13
				divideBy = bitDepth / 2^8
				# divide the 13 bit image down to 8 bit
				#run("Divide...", "value=32 stack");
				bPrintLog('divideBy:' + str(divideBy), 4)
				divideArgs = 'value=' + str(divideBy) + ' stack'
				IJ.run(self.imp_ch3, "Divide...", divideArgs);
				# convert to 8-bit will automatically scale, to turn this off use
				# eval("script", "ImageConverter.setDoScaling(false)"); 
				ImageConverter.setDoScaling(False)
				# run("8-bit");
				bPrintLog('converting to 8-bit with setDoScaling False', 4)
				IJ.run(self.imp_ch3, "8-bit", '');

			# print stats including intensity for the stack we just made
			d = self.imp_ch3.getDimensions() # width, height, nChannels, nSlices, nFrames
			stats = self.imp_ch3.getStatistics() # stats.min, stats.max
			bPrintLog('ch3 dimensions w:' + str(d[0]) + ' h:' + str(d[1]) + ' channels:' + str(d[2]) + ' slices:' + str(d[3]) + ' frames:' + str(d[4]), 4)
			bPrintLog('ch3 intensity min:' + str(stats.min) + ' max:' + str(stats.max), 4)

		return 1
		
	def saveTif(self, allowOverwrite=1):
		#make output folder
		if not os.path.isdir(self.dstFolder):
			os.makedirs(self.dstFolder)

		#ch1
		if self.imp_ch1:
			#savePath = self.dstFolder + self.enclosingFolderName + '_ch1.tif' #save into new folder
			if os.path.isfile(self.savePath_ch1) and not allowOverwrite:
				print bPrintLog('File Exists NOT Saving: ' + savePath, 3)
			else:
				fs = FileSaver(self.imp_ch1)
				bPrintLog('Saving: ' + self.savePath_ch1, 3)
				if self.imp_ch1.getNSlices()>1:
					fs.saveAsTiffStack(self.savePath_ch1)
				else:
					fs.saveAsTiff(self.savePath_ch1)
			
		#ch2
		if self.imp_ch2:
			#save into new folder
			#savePath = self.dstFolder + self.enclosingFolderName + '_ch2.tif' #save into new folder
			if os.path.isfile(self.savePath_ch2) and not allowOverwrite:
				bPrintLog('File Exists NOT Saving: ' + self.savePath_ch2, 3)
			else:
				fs = FileSaver(self.imp_ch2)
				bPrintLog('Saving: ' + self.savePath_ch2, 3)
				if self.imp_ch2.getNSlices()>1:
					fs.saveAsTiffStack(self.savePath_ch2)
				else:
					fs.saveAsTiff(self.savePath_ch2)
	
		#ch3
		if self.imp_ch3:
			#save into new folder
			#savePath = self.dstFolder + self.enclosingFolderName + '_ch3.tif' #save into new folder
			if os.path.isfile(self.savePath_ch3) and not allowOverwrite:
				bPrintLog('File Exists NOT Saving: ' + self.savePath_ch3, 3)
			else:
				fs = FileSaver(self.imp_ch3)
				bPrintLog('Saving: ' + self.savePath_ch3, 3)
				if self.imp_ch3.getNSlices()>1:
					fs.saveAsTiffStack(self.savePath_ch3)
				else:
					fs.saveAsTiff(self.savePath_ch3)

	def saveMaxProject(self, destFolder=''):
		# ch1
		if self.imp_ch1:
			# make max project
			zp = ZProjector(self.imp_ch1)
			zp.setMethod(ZProjector.MAX_METHOD)
			zp.doProjection()
			zimp = zp.getProjection()

			# save
			fs = FileSaver(zimp)
			bPrintLog('saveMaxProject():' + self.savePathMax_ch1, 3)
			fs.saveAsTiff(self.savePathMax_ch1)
		# ch2
		if self.imp_ch2:
			# make max project
			zp = ZProjector(self.imp_ch2)
			zp.setMethod(ZProjector.MAX_METHOD)
			zp.doProjection()
			zimp = zp.getProjection()

			# save
			fs = FileSaver(zimp)
			bPrintLog('saveMaxProject():' + self.savePathMax_ch2, 3)
			fs.saveAsTiff(self.savePathMax_ch2)
		# ch1
		if self.imp_ch3:
			# make max project
			zp = ZProjector(self.imp_ch3)
			zp.setMethod(ZProjector.MAX_METHOD)
			zp.doProjection()
			zimp = zp.getProjection()

			# save
			fs = FileSaver(zimp)
			bPrintLog('saveMaxProject():' + self.savePathMax_ch3, 3)
			fs.saveAsTiff(self.savePathMax_ch3)

	def closeTif(self):
		if self.imp_ch1:
			bPrintLog('bPrairieStack.closeTif() ch1', 3)
			self.imp_ch1.changes= False
			self.imp_ch1.close()
			self.imp_ch1 = None
		if self.imp_ch2:
			bPrintLog('bPrairieStack.closeTif() ch2', 3)
			self.imp_ch2.changes= False
			self.imp_ch2.close()
			self.imp_ch2 = None
		if self.imp_ch3:
			bPrintLog('bPrairieStack.closeTif() ch3', 3)
			self.imp_ch3.changes= False
			self.imp_ch3.close()
			self.imp_ch3 = None

	def saveHeaderFile(self):
		# save all b_ headers in a text file
		# self.header
		bPrintLog('saveHeaderFile():' + self.dstTextFile0, 3)
		headerFile = self.dstTextFile0
		f = open(headerFile, 'a')
		for name, value in self.header.iteritems():
			print name, value
			f.write(name + '=' + str(value) + '\n')
		f.close()
		
	def GetPrairieHeader(self):
		'''
		srcFolder is a folder containing a number of single image .tif and a single .xml
		'''
		folderpath, enclosingFolderName = os.path.split(os.path.dirname(self.srcFolder))
		xmlFile = self.srcFolder + enclosingFolderName + '.xml'
	
		if os.path.isfile(xmlFile):
			bPrintLog('parsing xmlFile: ' + xmlFile, 3)
		else:
			bPrintLog('WARNING: getPrairieHeader() did not find xml file in folder ' + self.srcFolder + ' file:' + xmlFile)
			return None
	
		header = {}
		header['b_Macro'] = gVersionStr
		
		tree = ET.parse(xmlFile)
		root = tree.getroot()

		# date/time
		prairieDateTimeStr = root.attrib['date']
		dateStr, timeStr = self.GetDateTime(prairieDateTimeStr)
		dateStr = bFixDate(dateStr)
		header['b_dateStr'] = dateStr
		header['b_timeStr'] = timeStr

		for Sequence in root.findall('Sequence'):
			#print 'Sequence:', Sequence
			header['b_sequence'] = Sequence.attrib['type']

			#201710, daisuke
			#version="4.3.2.24"
			frameNum = 0
			zPos = []
			for Frame in Sequence.findall('Frame'):
				firstShard = Frame.find('PVStateShard')
				for Key in firstShard.findall('Key'):
					if Key.attrib['key'] == 'micronsPerPixel_YAxis':
						header['b_voxely'] = Key.attrib['value']
					if Key.attrib['key'] == 'micronsPerPixel_XAxis':
						header['b_voxelx'] = Key.attrib['value']
					if Key.attrib['key'] == 'positionCurrent_ZAxis':
						zPos.append(float(Key.attrib['value']))
					if Key.attrib['key'] == 'bitDepth':
						header['b_bitDepth'] = Key.attrib['value']
					if Key.attrib['key'] == 'opticalZoom':
						header['b_opticalZoom'] = Key.attrib['value']
					if Key.attrib['key'] == 'dwellTime':
						header['b_dwellTime'] = Key.attrib['value']
					if Key.attrib['key'] == 'scanlinePeriod':
						header['b_scanlinePeriod'] = Key.attrib['value']
					if Key.attrib['key'] == 'framePeriod':
						header['b_framePeriod'] = Key.attrib['value']
				if frameNum == 1:
					if len(zPos) == 2:
						self.zStep = abs(zPos[1] - zPos[0])
						header['b_voxelz'] = str(self.zStep)
					break
				frameNum += 1

		for child in root:
			#print 'child:', child
			#print 'child:', child.tag, child.attrib
			'''
			for Sequence in child.findall('Sequence'):
				#print 'Sequence:', Sequence
				header['b_sequence'] = Sequence.attrib['type']
			'''
								
			# worley/shuler prairie scope is version="5.3.64.400"
			#for PVStateValue in child.findall('PVStateShard'):
			for PVStateValue in child.findall('PVStateValue'):
				attrib = PVStateValue.attrib
				#print attrib
				if attrib['key'] == 'activeMode':
					header['b_activeMode'] = attrib['value']
				if attrib['key'] == 'framePeriod':
					header['b_framePeriod'] = attrib['value']
				if attrib['key'] == 'linesPerFrame':
					header['b_linesPerFrame'] = attrib['value']
				if attrib['key'] == 'pixelsPerLine':
					header['b_pixelsPerLine'] = attrib['value']
				if attrib['key'] == 'opticalZoom':
					header['b_opticalZoom'] = attrib['value']
				if attrib['key'] == 'objectiveLens': # the name
					header['b_objectiveLens'] = attrib['value']
				if attrib['key'] == 'objectiveLensMag': # the mag of the physical objective lens
					header['b_objectiveLensMag'] = attrib['value']
				if attrib['key'] == 'bitDepth':
					header['b_bitDepth'] = attrib['value']
				if attrib['key'] == 'dwellTime':
					header['b_dwellTime'] = attrib['value']
				if attrib['key'] == 'resonantSamplesPerPixel':
					header['b_resonantSamplesPerPixel'] = attrib['value']
				if attrib['key'] == 'scanLinePeriod':
					header['b_scanLinePeriod'] = attrib['value']
				if attrib['key'] == 'rotation':
					header['b_rotation'] = attrib['value']
	   
				if attrib['key'] == 'laserPower':
					for sub in PVStateValue.findall('IndexedValue'):
						if sub.attrib['index'] == '0':
							header['b_laserPower'] = sub.attrib['value']

				if attrib['key'] == 'twophotonLaserPower': # total power of laser
					for sub in PVStateValue.findall('IndexedValue'):
						if sub.attrib['index'] == '0':
							header['b_twophotonLaserPower'] = sub.attrib['value']

				if attrib['key'] == 'laserWavelength':
					for sub in PVStateValue.findall('IndexedValue'):
						if sub.attrib['index'] == '0':
							header['b_laserWavelength'] = sub.attrib['value']

				if attrib['key'] == 'micronsPerPixel':
					for sub in PVStateValue.findall('IndexedValue'):
						#print 'sub:', sub.attrib
						if sub.attrib['index'] == 'XAxis':
							header['b_voxelx'] = sub.attrib['value']
						if sub.attrib['index'] == 'YAxis':
							header['b_voxely'] = sub.attrib['value']

				if attrib['key'] == 'positionCurrent':
					for sub in PVStateValue.findall('SubindexedValues'):
						#print 'sub:', sub.attrib
						if sub.attrib['index'] == 'XAxis':
							for sub2 in sub.findall('SubindexedValue'): #SubindexedValue is repeated here
								header['b_xMotor'] = sub2.attrib['value']
						if sub.attrib['index'] == 'YAxis':
							for sub2 in sub.findall('SubindexedValue'): #SubindexedValue is repeated here
								header['b_yMotor'] = sub2.attrib['value']
						if sub.attrib['index'] == 'ZAxis':
							#for sub2 in sub.findall('SubindexedValue'): #SubindexedValue is repeated here
							#	header['zMotor'] = sub2.attrib['value']
							sub2 = sub.findall('SubindexedValue')[0]
							header['b_zMotor'] = sub2.attrib['value']
							
			numSlices = 0
			currFrame = 0
			for frame in child.findall('Frame'):
				numSlices += 1
				self.frameTimes.append(frame.attrib['relativeTime'])
				for fileToken in frame.findall('File'):
					if fileToken.attrib['channel'] == "1": #need the ""
						self.ch1_names.append(fileToken.attrib['filename'])
					if fileToken.attrib['channel'] == "2": #need the ""
						self.ch2_names.append(fileToken.attrib['filename'])
					if fileToken.attrib['channel'] == "3": #need the ""
						self.ch3_names.append(fileToken.attrib['filename'])
				
				# get motor position from sequential <Frame>
				for PVStateShard in frame.findall('PVStateShard'):
					for PVStateValue in PVStateShard.findall('PVStateValue'):
						if PVStateValue.attrib['key'] == 'positionCurrent':
							for SubindexedValues in PVStateValue.findall('SubindexedValues'):
								if SubindexedValues.attrib['index'] == 'ZAxis':
									for SubindexedValue in SubindexedValues.findall('SubindexedValue'):
										if SubindexedValue.attrib['subindex']=='0':
											#print 'SubindexedValue:', SubindexedValue.attrib['value'] # this is the z posiiton of each frame
											self.zPosition.append(float(SubindexedValue.attrib['value']))
											if currFrame == 2: # use '2' becase first <Frame> has no ZAxis position
												#print 'currFrame:', currFrame, 'self.zPosition:', self.zPosition
												self.zStep = self.zPosition[1] - self.zPosition[0]
												header['b_zStep'] = str(self.zStep)
						# get laser power and then report min/max
						if PVStateValue.attrib['key'] == 'laserPower':
							for IndexedValue in PVStateValue.findall('IndexedValue'):
								if IndexedValue.attrib['index'] == '0':
									self.laserPower.append(float(IndexedValue.attrib['value']))
						# get pmt gain and then report min/max
						if PVStateValue.attrib['key'] == 'pmtGain':
							for IndexedValue in PVStateValue.findall('IndexedValue'):
								# there are two pmt's (red/green), I am just using 0/1
								if IndexedValue.attrib['index'] == '0': #channel 1
									self.pmt0.append(float(IndexedValue.attrib['value']))
								if IndexedValue.attrib['index'] == '1': # channel 2
									self.pmt1.append(float(IndexedValue.attrib['value']))
								if IndexedValue.attrib['index'] == '2': # channel 3
									self.pmt2.append(float(IndexedValue.attrib['value']))
									
				currFrame += 1
				
			#stats (num frames, num channels)
			header['b_numSlices'] = str(numSlices)
			numChannels = 0
			if self.ch1_names:
				numChannels += 1
			if self.ch2_names:
				numChannels += 1
			if self.ch3_names:
				numChannels += 1
			header['b_numChannels'] = str(numChannels)

			# min/max of self.laserPower
			if self.laserPower:
				laserMin = min(self.laserPower)
				laserMax = max(self.laserPower)
				header['b_laserMin'] = str(laserMin)
				header['b_laserMax'] = str(laserMax)
			# min/max of self.pmt0
			if self.pmt0:
				pmtMin = min(self.pmt0)
				pmtMax = max(self.pmt0)
				header['b_pmt0_Min'] = str(pmtMin)
				header['b_pmt0_Max'] = str(pmtMax)
			# min/max of self.pmt1
			if self.pmt1:
				pmtMin = min(self.pmt1)
				pmtMax = max(self.pmt1)
				header['b_pmt1_Min'] = str(pmtMin)
				header['b_pmt1_Max'] = str(pmtMax)
			if self.pmt2:
				pmtMin = min(self.pmt2)
				pmtMax = max(self.pmt2)
				header['b_pmt1_Min'] = str(pmtMin)
				header['b_pmt1_Max'] = str(pmtMax)
			
		return header
		
	def printheader(self):
		#print what we just found
		printLevel = 4
		header = self.header
		bPrintLog(header['b_dateStr'] + ' ' + header['b_timeStr'], printLevel)
		bPrintLog('pixels: ' + header['b_pixelsPerLine'] + ',' + header['b_linesPerFrame'],printLevel)
		bPrintLog('voxels: ' + header['b_voxelx'] + ',' + header['b_voxely'],printLevel)
		bPrintLog('opticalZoom: ' + header['b_opticalZoom'], printLevel)
		bPrintLog('framePeriod: ' + header['b_framePeriod'], printLevel)

	def getHeaderAsText(self, justHeaders=False):
		'''
		Used to output tif header as text file
		'''
		ret = ''
		# make a list of header tokens
		hlist = []
		#hlist.append('sessionFolderName')
		
		hlist.append('b_dateStr')
		hlist.append('b_timeStr')
		hlist.append('b_sequence') # (ZSeries, TSeries)
		hlist.append('b_activeMode') #
		
		hlist.append('b_linesPerFrame')
		hlist.append('b_pixelsPerLine')

		hlist.append('b_numSlices')
		hlist.append('b_numChannels')

		hlist.append('b_objectiveLens') # the name of the objective (in the software)
		hlist.append('b_objectiveLensMag') # the mag of the physical lens
		hlist.append('b_opticalZoom') # actual mag used for acquisition

		hlist.append('b_voxelx')
		hlist.append('b_voxely')
		hlist.append('b_zStep')
		# there is no voxel z for Z-Series ???
		
		hlist.append('b_xMotor')
		hlist.append('b_yMotor')
		hlist.append('b_zMotor')

		hlist.append('b_bitDepth')

		hlist.append('b_framePeriod')
		hlist.append('b_scanLinePeriod')
		hlist.append('b_dwellTime')
		hlist.append('b_resonantSamplesPerPixel') # resonant
		hlist.append('b_rotation') # NOT available in resonant
		
		hlist.append('b_twophotonLaserPower') # total laser power
		hlist.append('b_laserPower') # actual laser power used
		hlist.append('b_laserWavelength')
		hlist.append('b_laserMin') # i am deriving this for Z-Series using each <Frame>
		hlist.append('b_laserMax')

		hlist.append('b_pmt0_Min')
		hlist.append('b_pmt0_Max')
		hlist.append('b_pmt1_Min')
		hlist.append('b_pmt1_Max')
		hlist.append('b_pmt2_Min')
		hlist.append('b_pmt2_Max')

		if justHeaders:
			# always print all headers in hlist
			ret += 'sessionFolderName' + gTextDelim + 'enclosingFolderName' + gTextDelim
			for key in hlist:
				if key in self.header:
					ret += key + gTextDelim
				else:
					ret += key + gTextDelim
					#print 'error: getHeaderAsText() did not find key', key, 'in header'
		else:
			# print values for each value in hlist, if missing, print ''
			ret += self.sessionFolderName + gTextDelim + self.enclosingFolderName + gTextDelim
			for key in hlist:
				if key in self.header:
					ret += self.header[key] + gTextDelim
				else:
					ret += '' + gTextDelim # empy value
					#print 'warning: getHeaderAsText() did not find key', key, 'in header. This is ok'
		return ret
		
	#utility
	def GetDateTime(self, prairieDateTimeStr):
		'''
		split a prairie dat/time string into date and time
		format is: '9/13/2016 10:40:48 AM'
		'''
		sList = prairieDateTimeStr.split() # gives [date, time, am/pm]
		dateStr = sList[0]
		timeStr = sList[1]
		ampmStr = sList[2]
		timeList = timeStr.split(':') # gives [h, m, s]
		if ampmStr == 'PM' and (not (int(timeList[0]) == 12)):
			#make time on 24hr clock
			# 12 pn stays the same, anyhing past 12 pm (e.g. 1 pm, 2 pm, etc.) is +12 hours
			timeList[0] = str(int(timeList[0]) + 12)
		timeStr = timeList[0] + ':' + timeList[1] + ':' + timeList[2]
		return dateStr, timeStr
	
def runOneMetaFolder(sourceFolder):
	'''
	sourceFolder is a folder containing subfolders, each subfolder has:
	   - single image .tif files that make up a stack
	   - a single .xml with acquisition parameters
	'''

	bPrintLog('runOneMetaFolder() ' + sourceFolder, 1)
	
	if not os.path.isdir(sourceFolder):
		bPrintLog('ERROR: runOneMetaFolder() did not find folder: ' + sourceFolder)
		return 0

	outTextFile = None
	
	folderList = bFolderList(sourceFolder) # list of folder we will process (Each folder has list of .tif)
	numStackFolders = len(folderList)
	outFiles = 0
	for i, folder in enumerate(folderList):
		#debug
		#if i > 4:
		#	continue
		
		#run
		bPrintLog(str(i+1) + ' of ' + str(numStackFolders),2)
		
		prairieStack = bPrairieStack(folder) # reads the header
		
		if prairieStack and prairieStack.header:
			#write header info to .txt file
			if gOutputHeader:
				if outFiles==0:
					#make output folder (this is also done in prairieStack.saveTif()
					if not os.path.isdir(prairieStack.dstFolder):
						os.makedirs(prairieStack.dstFolder)
					outTextFile = open(prairieStack.dstTextFile, 'w')
					outText = prairieStack.getHeaderAsText(justHeaders=True)
					#print outText
					outTextFile.write(outText + '\n')
				outText = prairieStack.getHeaderAsText()
				#print outText
				outTextFile.write(outText + '\n')
				
			if gOutputTif:
				#we can bail if the destination already exists
				if not gAllowOverwrite:
					if os.path.isfile(prairieStack.savePath_ch1) or os.path.isfile(prairieStack.savePath_ch2):
						bPrintLog('Warning: Skipping folder ' + folder + ' destination already exists:' + folder)
						continue
	
				tifLoaded = prairieStack.loadTif(allowOverwrite=gAllowOverwrite)
				if tifLoaded:
					prairieStack.saveTif(allowOverwrite=gAllowOverwrite)
					prairieStack.saveMaxProject()
					prairieStack.closeTif()
					prairieStack.saveHeaderFile() # save corresponding .txt file with b_ header information
	
			outFiles += 1	

		else:
			bPrintLog("Warning: runOneMetaFolder() folder " + folder + " does not have an .xml file. It is not a prairie file?")
			
	if outTextFile:
		# close output text file
		outTextFile.close()
			

	return outFiles, prairieStack.dstFolder # outFiles is the number of folders we processed

'''
Utility
'''
def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)

def bFolderList(srcFolder):
	'''
	Get a list of folders that should contain single image .tif
	We skip some folder like (_out, _video, SingleImage-)
	If any of the 'real' folder names to be processed have these string, this will fail
	'''
	folderList = []
	for child in os.listdir(srcFolder):
		childPath = os.path.join(srcFolder, child) + '/'
		if os.path.isdir(childPath):
			isOutFolder = child.endswith('_out')
			isVideoFolder = child.endswith('_video')
			isSingleFolder = child.startswith('SingleImage-')
			if isOutFolder or isVideoFolder or isSingleFolder:
				continue
			folderList.append(childPath)
			
	return folderList

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

'''
Main
'''

if __name__ in('__main__','__builtin__'): 

	bPrintLog('\n=================')
	bPrintLog('Starting prairie2tif')

	#good = optionsDialog() #ask user to get globalOptions
	#if good is None:
	#	bPrintLog('Options canceled by user', 0)
	if False:
		pass
	else:
		#debugging
		#sourceFolder = '/Volumes/fourt/data/2016/09/20160913/'	
	
		#ask user for folder, this is a folder that contains folders with single image .tif files (a folder of folders)
		sourceFolder = DirectoryChooser("Please open a directory with Prairie folders").getDirectory()
	
		startTime = time.time()
	
		numStackFolders = 0
		if (sourceFolder):
			bPrintLog('medianFilter=' + str(globalOptions['medianFilter']))
			bPrintLog('convertToEightBit=' + str(globalOptions['convertToEightBit']))
			numStackFolders, outFolder = runOneMetaFolder(sourceFolder)
		else:
			bPrintLog('Canceled by user', 0)
	
		stopTime = time.time()
		elapsedSeconds = round(stopTime-startTime,2)
		elapsedMinutes = round(elapsedSeconds / 60.0, 2)
		bPrintLog('Finished prairie2tif with ' + str(numStackFolders) + ' files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
		bPrintLog('=================\n')
	