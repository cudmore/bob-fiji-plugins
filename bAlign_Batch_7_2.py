# Purpose: take a user specified folder of .tif files and depending on options ...
#   Convert a hard-drive folder of .tif files and perform the following:
#      -Split 2 channel files into _ch1.tif and _ch2.tif channel separated files.
#      -Perform slice-by-slice stack alignment on one channel and apply transformations to the other.
#         This requires 'MultiStackReg' to be installed (http://bradbusse.net/downloads.html).
#      -[optional] For scanimage4 .tif files, remove linear calibration
#      -[optional] For scanimage4 .tif files, crop all files to a rectangle specified, in pixels, as (left, top, width, height)
#      -Save 8-bit versions
#
# Author: Robert H Cudmore
# web: http://www.robertcudmore.org
#
# As of March 18, 2015 this works with Fiji/ImageJ 1.47v
# Please check your ImageJ version if you have problems running this plugin
# Especially if the plugin seems to do nothing when run
#
# version:
#   August, 2014: v0.1
#   Oct 1, 2014: added gDoCrop and gAlignOnMiddleSlice
#   Feb 23, 2015: fixed bug where globals were not being assigned when user changed them in dialog
#   Feb 23, 2015: fixed bug where max project did not have _ch1/_ch2 appended to max .tif file name
#   March 18, 2015: Fixed import errors introduced in new versions of Fiji, now works for Fiji/ImageJ 1.47v
#   July 1, 2015: Removing ScanImage4 'shift all pixels' and replacing with 'p[i] = 0 if p[i]>0, otherwise p[i] = p[i]'
#   July 23, 2015: (1) removing linear calibration and shifting by 2^15-128 and checking for negative (see gLinearShift)
#				   (2) updated bAlignBatch .tif header information
#				   (3) aligning on cropped but then applying alignment to FULL IMAGE
#   July 30, 2015: Adding support for lsm (again).
#   November 10, 2015: increasing linear shift for scanimage4, it is now 2^15-512 (was previously 2^15-128)
#
from ij import IJ, ImagePlus, WindowManager
from ij.gui import GenericDialog, Roi
from ij.process import StackStatistics
from ij.io import Opener, FileSaver, DirectoryChooser
from java.io import File, FilenameFilter
import sys, os, re, math
from string import find
import time # for yyyymmdd, for wait
from ij.plugin import Duplicator # for Duplicator().run(imp)

#globals
global gFileType # tif or lsm
global gAlignBatchVersion

global gLinearShift

global gGetNumChanFromScanImage
global gNumChannels
	
global gDoAlign
global gAlignThisChannel

global gDoCrop
global gCropLeft
global gCropTop
global gCropWidth
global gCropHeight

global gAlignOnMiddleSlice
global gAlignOnThisSlice
global gRemoveCalibration
global gSave8bit

# 0...#5 are the order of operation
# 0
gFileType = 'lsm' # tif or lsm
gAlignBatchVersion = 7.1 # version 7.1 was created on 20150723
# 1
gGetNumChanFromScanImage = 0 # 0 is off, 1 is on
gNumChannels = 1
# 2
gDoCrop = 0 # 0 is off, 1 is on
gCropLeft = 100 #default left of cropping rectangle
gCropTop = 0 #default top of cropping rectangle
gCropWidth = 850 #default width of cropping rectangle
gCropHeight = 1024 #default height of cropping rectangle
# 3
gRemoveCalibration = 0 # 0 is off, 1 is on
#20151110 was this
#gLinearShift = math.pow(2,15) - 128
gLinearShift = math.pow(2,15) - 512
# 4
gDoAlign = 0 # 0 is off, 1 is on
gAlignThisChannel = 1
gAlignOnMiddleSlice = 1
gAlignOnThisSlice = 0
# 5
gSave8bit = 0 # 0 is off, 1 is on

### DEBUG ###
if 0:
	gNumChannels = 1
	gDoCrop = 1 # 0 is off, 1 is on
	gCropLeft = 100 #default left of cropping rectangle
	gCropTop = 0 #default top of cropping rectangle
	gCropWidth = 300 #default width of cropping rectangle
	gCropHeight = 512 #default height of cropping rectangle
	gRemoveCalibration = 1 # 0 is off, 1 is on

# only call if we know for sure there is a sourceFolder
def Options(sourceFolder):
	#globals
	global gFileType
	global gGetNumChanFromScanImage
	global gNumChannels
		
	global gDoAlign
	global gAlignThisChannel
	
	global gDoCrop
	global gCropLeft
	global gCropTop
	global gCropWidth
	global gCropHeight
	
	global gAlignOnMiddleSlice
	global gAlignOnThisSlice
	global gRemoveCalibration
	global gLinearShift
	global gSave8bit

	tifNames = [file.name for file in File(sourceFolder).listFiles(Filter())]
	lsmNames = [file.name for file in File(sourceFolder).listFiles(Filter_LSM())]
	
	numTifs = len(tifNames)
	numLSM = len(lsmNames)

	gd = GenericDialog('Align Batch 7 Options')
	#gd.addStringField('Command: ', '')

	gd.addMessage('Source Folder: ' + sourceFolder)
	gd.addMessage('Number of .tif files: ' + str(numTifs))
	gd.addMessage('Number of .lsm files: ' + str(numLSM))
	
	gd.addChoice('File Type', ['tif','lsm'], gFileType)
	
	#gd.setInsets(5,0,3)
	#0
	gd.addCheckboxGroup(1, 1, ['Get Number Of Channels From ScanImage 3.x or 4.x header'], [gGetNumChanFromScanImage], ['Channels'])
	gd.addNumericField('Otherwise, Assume All Stacks Have This Number Of Channels: ', gNumChannels, 0)

	print gLinearShift
	
	#1
	gd.addCheckboxGroup(1, 1, ['Remove Linear Calibration From ScanImage 4.x'], [gRemoveCalibration], ['ScanImage4'])
	gd.addNumericField('And offset (subtract) by this amount: ', gLinearShift, 0)
	gd.addMessage('20151110, this number = 2^15-512 = 32768-512 = 32256')
	
	#2
	gd.addCheckboxGroup(1, 1, ['Crop All Images (pixels)'], [gDoCrop], ['Crop'])
	gd.addNumericField('Left', gCropLeft, 0)
	gd.addNumericField('Top', gCropTop, 0)
	gd.addNumericField('Width', gCropWidth, 0)
	gd.addNumericField('Height', gCropHeight, 0)

	#gd.setInsets(5,0,3)
	#3
	gd.addCheckboxGroup(1, 1, ['Run MultiStackReg'], [gDoAlign], ['MultStackReg'])
	gd.addNumericField('If 2 Channels Then Align On This Channel', gAlignThisChannel, 0)
	
	#4
	gd.addCheckboxGroup(1, 1, ['Start Alignment On Middle Slice'], [gAlignOnMiddleSlice], ['Align On Middle Slice'])
	gd.addNumericField('Otherwise, Start Alignment On This Slice', gAlignOnThisSlice, 0)

	#5
	gd.addCheckboxGroup(1, 1, ['Save 8-bit'], [gSave8bit], ['Save 8-bit (at end)'])
	#gd.addCheckbox('Save 8-bit', gSave8bit)
	
	gd.showDialog()

	if gd.wasCanceled():
		print 'Options Was Cancelled by user'
		return 0
	else:
		print 'Reading values'
		gFileType = gd.getNextChoice()
		
		gNumChannels = int(gd.getNextNumber())

		gLinearShift = int(gd.getNextNumber())

		gCropLeft = int(gd.getNextNumber())
		gCropTop = int(gd.getNextNumber())
		gCropWidth = int(gd.getNextNumber())
		gCropHeight = int(gd.getNextNumber())

		gAlignThisChannel = int(gd.getNextNumber())
		gAlignOnThisSlice = int(gd.getNextNumber())

		checks = gd.getCheckboxes()
		checkIdx = 0
		for check in checks:
			#print check.getState()
			if checkIdx==0:
				gGetNumChanFromScanImage = check.getState()
			if checkIdx==1:
				gRemoveCalibration = check.getState()
			if checkIdx==2:
				gDoCrop = check.getState()
			if checkIdx==3:
				gDoAlign = check.getState()
			if checkIdx==4:
				gAlignOnMiddleSlice = check.getState()

			if checkIdx==5:
				gSave8bit = check.getState()
			checkIdx += 1

		# print to fiji console
		bPrintLog('These are your global options:', 0)
		bPrintLog('gFileType=' + gFileType, 1)
		bPrintLog('gGetNumChanFromScanImage=' + str(gGetNumChanFromScanImage), 1)
		bPrintLog('gNumChannels=' + str(gNumChannels), 1)
		bPrintLog('gRemoveCalibration=' + str(gRemoveCalibration), 1)
		bPrintLog('gLinearShift=' + str(gLinearShift), 1)
		bPrintLog('gDoCrop=' + str(gDoCrop), 1)
		bPrintLog('gDoAlign=' + str(gDoAlign), 1)
		bPrintLog('gAlignThisChannel=' + str(gAlignThisChannel), 1)
		bPrintLog('gSave8bit=' + str(gSave8bit), 1)
		
		return 1
		
class Filter(FilenameFilter):
	def accept(self, dir, name):
		reg = re.compile('\.tif$')
		regMax = re.compile('\max.tif$')
		m = reg.search(name)
		m2 = regMax.search(name)
		if m and not m2:
			return 1
		else:
			return 0

class Filter_LSM(FilenameFilter):
	def accept(self, dir, name):
		reg = re.compile('\.lsm$')
		regMax = re.compile('\max.lsm$')
		m = reg.search(name)
		m2 = regMax.search(name)
		if m and not m2:
			return 1
		else:
			return 0

def bPrintLog(text, indent):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)
	
def bSaveStack(imp, fullPath):
	fs = FileSaver(imp)
	#print 'bSaveStack()', fullPath, 'nslices=', imp.getNSlices()
	bPrintLog('bSaveStack():' + fullPath + ' slices=' + str(imp.getNSlices()), 1)
	if imp.getNSlices()>1:
		fs.saveAsTiffStack(fullPath)
	else:
		fs.saveAsTiff(fullPath)

def bSaveZProject(imp, dstFolder, shortname):
	#bring to front
	impWinStr = imp.getTitle()
	IJ.selectWindow(impWinStr)
	
	bPrintLog('Making Z-Project from ' + impWinStr, 2)
	madez = 0
	z1 = 1
	z2 = imp.getNSlices()
	if z2>1:
		paramStr = 'start=%s stop=%s projection=[Max Intensity]' % (z1, z2)
		IJ.run('Z Project...', paramStr) #makes 'MAX_' window
		zWinStr = 'MAX_' + impWinStr
		zImp = WindowManager.getImage(zWinStr)
		madez = 1
	else:
		zImp = imp
			
	if dstFolder != None:
		dstFile = dstFolder + 'max_' + shortname + '.tif'
		bPrintLog('Saving Z-Project: ' + dstFile, 2)
		bSaveStack(zImp, dstFile)

	if madez:
		zImp.changes = 0
		zImp.close()
	
def runOneFolder(sourceFolder):
	global gFileType
	
	if not os.path.isdir(sourceFolder):
		bPrintLog('\nERROR: runOneFolder() did not find folder: ' + sourceFolder + '\n',0)
		return 0
		
	print 'xxx', gFileType
	if gFileType=='tif':
		tifNames = [file.name for file in File(sourceFolder).listFiles(Filter())]
	else:
		tifNames = [file.name for file in File(sourceFolder).listFiles(Filter_LSM())]
	numTifs = len(tifNames)

	bPrintLog(' ',0)
	bPrintLog('=================================================',0)
	bPrintLog('Align Batch 7',0)
	bPrintLog('File type is ' + gFileType,1)
	bPrintLog('sourceFolder: ' + sourceFolder,1)
	bPrintLog('Number of files of file type: ' + str(numTifs),1)

	count = 1
	for tifName in tifNames:
		msgStr = '--->>> Opening ' + str(count) + ' of ' + str(numTifs)
		bPrintLog(msgStr, 0)	
		runOneFile(sourceFolder + tifName)
		count += 1

	bPrintLog('Done runOneFolder', 1)

def runOneFile(fullFilePath):
	global gFileType
	global gNumChannels
	global gAlignBatchVersion
	
	if not os.path.isfile(fullFilePath):
		bPrintLog('\nERROR: runOneFile() did not find file: ' + fullFilePath + '\n',0)
		return 0

	bPrintLog(time.strftime("%H:%M:%S") + ' starting runOneFile(): ' + fullFilePath, 1)
	
	enclosingPath = os.path.dirname(fullFilePath)
	head, tail = os.path.split(enclosingPath)
	enclosingPath += '/'
	
	#make output folders
	destFolder = enclosingPath + tail + '_channels/'
	if not os.path.isdir(destFolder):
		os.makedirs(destFolder)
	destMaxFolder = destFolder + 'max/'
	if not os.path.isdir(destMaxFolder):
		os.makedirs(destMaxFolder)

	if gDoAlign:
		destAlignmentFolder = destFolder + 'alignment/'
		if not os.path.isdir(destAlignmentFolder):
			os.makedirs(destAlignmentFolder)
			
	if gSave8bit:
		eightBitFolder = destFolder + 'channels8/'
		if not os.path.isdir(eightBitFolder):
			os.makedirs(eightBitFolder)
		eightBitMaxFolder = eightBitFolder + 'max/'
		if not os.path.isdir(eightBitMaxFolder):
			os.makedirs(eightBitMaxFolder)
	
	if gFileType=='tif':
		# open .tif image
		imp = Opener().openImage(fullFilePath)
	else:
		'''
		This will make a window 'OME Metadata - <file>.lsm'
		But then IJ.rundo not know how to access the contents of the window to get date/time
		(CreationDate, PhysicalSizeX, PhysicalSizeY, PhysicalSizeZ)
		IJ.run(imp, "Bio-Formats Importer", "open=/Users/cudmore/Desktop/lsm/C1_MC2_1.lsm autoscale color_mode=Default display_metadata display_ome-xml view=Hyperstack stack_order=XYCZT");
		'''
		# open .lsm
		cmdStr = 'open=%s autoscale color_mode=Default view=Hyperstack stack_order=XYCZT' % (fullFilePath,)
		IJ.run('Bio-Formats Importer', cmdStr)
		lsmpath, lsmfilename = os.path.split(fullFilePath)
		lsWindow = lsmfilename
		imp = WindowManager.getImage(lsWindow)
		
		#20160630, try and get voxel size, CALIBRATION DOES NOT FUCKING WORK !!!
		'''
		print '1'
		calibration = imp.getCalibration()
		if calibration:
			#print 'calibration:', calibration
			pixelWidth = calibration.pixelWidth()
			print '2'
			pixelHeight = calibration.pixelHeight()
			pixelDepth = calibration.pixelDepth()
			unitStr = imp.DEFAULT_VALUE_UNIT
			bPrintLog(str(pixelWidth) + str(pixelHeight) + str(pixelDepth) + str(unitStr), 2)
		else:
			bPrintLog('ERROR: Getting image calibration from .lsm file', 2)
		'''
		
	# get parameters of image
	(width, height, nChannels, nSlices, nFrames) = imp.getDimensions()
	bitDepth = imp.getBitDepth()
	infoStr = imp.getProperty("Info") #get all .tif tags
	
	if not infoStr:
		infoStr = ''
	infoStr += 'bAlignBatch_Version=' + str(gAlignBatchVersion) + '\n'
	infoStr += 'bAlignBatch_Time=' + time.strftime("%Y%m%d") + '_' + time.strftime("%H%M%S") + '\n'
		
	msgStr = 'w:' + str(width) + ' h:' + str(height) + ' slices:' + str(nSlices) \
				+ ' channels:' + str(nChannels) + ' frames:' + str(nFrames) + ' bitDepth:' + str(bitDepth)
	bPrintLog(msgStr, 1)
	
	if gFileType=='lsm':
		numChannels, voxelx, voxely, voxelz = readlsmHeader(infoStr)
		infoStr += 'bvoxelx=' + str(voxelx) + '\n'
		infoStr += 'bvoxely=' + str(voxely) + '\n'
		infoStr += 'bvoxelz=' + str(voxelz) + '\n'
		
	path, filename = os.path.split(fullFilePath)
	shortName, fileExtension = os.path.splitext(filename)

	#
	# look for num channels in ScanImage infoStr
	if gGetNumChanFromScanImage:
		for line in infoStr.split('\n'):
			#scanimage.SI4.channelsSave = [1;2]
			scanimage4 = find(line, 'scanimage.SI4.channelsSave =') == 0
			#state.acq.numberOfChannelsSave=2
			scanimage3 = find(line, 'state.acq.numberOfChannelsSave=') == 0
			if scanimage3:
				#print 'line:', line
				equalIdx = find(line, '=')
				line2 = line[equalIdx+1:]
				if gGetNumChanFromScanImage:
					gNumChannels = int(line2)
					bPrintLog('over-riding gNumChannels with: ' + str(gNumChannels), 2)
			if scanimage4:
				#print '   we have a scanimage 4 file ... now i need to exptract the number of channel'
				#print 'line:', line
				equalIdx = find(line, '=')
				line2 = line[equalIdx+1:]
				for delim in ';[]':
					line2 = line2.replace(delim, ' ')
				if gGetNumChanFromScanImage:
					gNumChannels = len(line2.split())
					bPrintLog('over-riding gNumChannels with: ' + str(gNumChannels), 2)

	# show
	imp.show()
	# split channels if necc. and grab the original window names
	if gNumChannels == 1:
		origImpWinStr = imp.getTitle() #use this when only one channel
		origImpWin = WindowManager.getWindow(origImpWinStr) #returns java.awt.Window
	
	if gNumChannels == 2:
		winTitle = imp.getTitle()
		bPrintLog('Deinterleaving 2 channels...', 1)
		IJ.run('Deinterleave', 'how=2 keep') #makes ' #1' and ' #2', with ' #2' frontmost
		origCh1WinStr = winTitle + ' #1'
		origCh2WinStr = winTitle + ' #2'
		origCh1Imp = WindowManager.getImage(origCh1WinStr)
		origCh2Imp = WindowManager.getImage(origCh2WinStr)
		origCh1File = destFolder + shortName + '_ch1.tif'
		origCh2File = destFolder + shortName + '_ch2.tif'

	# work on a copy, mostly for alignment with cropping
	copy = Duplicator().run(imp)
	#copy.copyAttributes(imp) #don't copy attributes, it copies the name (which we do not want)
	copy.show()
	
	#
	# crop (on copy)
	if gDoCrop:
		bPrintLog('making cropping rectangle (left,top,width,height) ',1)
		bPrintLog(str(gCropLeft) + ' ' + str(gCropTop) + ' ' +str(gCropWidth) + ' ' +str(gCropHeight), 2)
		
		roi = Roi(gCropLeft, gCropTop, gCropWidth, gCropHeight) #left,top,width,height
		copy.setRoi(roi)
		
		time.sleep(0.5) # otherwise, crop SOMETIMES failes. WHAT THE FUCK FIJI DEVELOPERS, REALLY, WHAT THE FUCK
		
		#bPrintLog('cropping', 1)
		IJ.run('Crop')
		infoStr += 'bCropping=' + str(gCropLeft) + ',' + str(gCropTop) + ',' + str(gCropWidth) + ',' + str(gCropHeight) + '\n'
	
	#
	# remove calibration ( on original)
	if gRemoveCalibration:
		cal = imp.getCalibration()
		calCoeff = cal.getCoefficients()
		if calCoeff:
			msgStr = 'Calibration is y=a+bx' + ' a=' + str(calCoeff[0]) + ' b=' + str(calCoeff[1])
			bPrintLog(msgStr, 1)
			
			#remove calibration
			bPrintLog('\tRemoving Calibration', 2)
			imp.setCalibration(None)
				
			#without these, 8-bit conversion goes to all 0 !!! what the fuck !!!
			#bPrintLog('calling imp.resetStack() and imp.resetDisplayRange()', 2)
			imp.resetStack()
			imp.resetDisplayRange()

			#get and print out min/max
			origMin = StackStatistics(imp).min
			origMax = StackStatistics(imp).max
			msgStr = '\torig min=' + str(origMin) + ' max=' + str(origMax)
			bPrintLog(msgStr, 2)
			
			# 20150723, 'shift everybody over by linear calibration intercept calCoeff[0] - (magic number)
			if 1:
				# [1] was this
				#msgStr = 'Subtracting original min '+str(origMin) + ' from stack.'
				#bPrintLog(msgStr, 2)
				#subArgVal = 'value=%s stack' % (origMin,)
				#IJ.run('Subtract...', subArgVal)
				# [2] now this
				#msgStr = 'Adding calCoeff[0] '+str(calCoeff[0]) + ' from stack.'
				#bPrintLog(msgStr, 2)
				#addArgVal = 'value=%s stack' % (int(calCoeff[0]),)
				#IJ.run('Add...', addArgVal)
				# [3] subtract a magic number 2^15-2^7 = 32768 - 128
				magicNumber = gLinearShift #2^15 - 128
				msgStr = 'Subtracting a magic number (linear shift) '+str(magicNumber) + ' from stack.'
				bPrintLog(msgStr, 2)
				infoStr += 'bLinearShift=' + str(gLinearShift) + '\n'
				subArgVal = 'value=%s stack' % (gLinearShift,)
			IJ.run(imp, 'Subtract...', subArgVal)
				
			# 20150701, set any pixel <0 to 0
			if 0:
				ip = imp.getProcessor() # returns a reference
				pixels = ip.getPixels() # returns a reference
				msgStr = '\tSet all pixels <0 to 0. This was added 20150701 ...'
				bPrintLog(msgStr, 2)
				pixels = map(lambda x: 0 if x<0 else x, pixels)
				bPrintLog('\t\t... done', 2)
				
			#get and print out min/max
			newMin = StackStatistics(imp).min
			newMax = StackStatistics(imp).max
			msgStr = '\tnew min=' + str(newMin) + ' max=' + str(newMax)
			bPrintLog(msgStr, 2)
			
			#append calibration to info string
			infoStr += 'bCalibCoeff_a = ' + str(calCoeff[0]) + '\n'
			infoStr += 'bCalibCoeff_b = ' + str(calCoeff[1]) + '\n'
			infoStr += 'bNewMin = ' + str(newMin) + '\n'
			infoStr += 'bNewMax = ' + str(newMax) + '\n'

	#
	# set up
	if gNumChannels == 1:
		impWinStr = copy.getTitle() #use this when only one channel
		impWin = WindowManager.getWindow(impWinStr) #returns java.awt.Window
	
	if gNumChannels == 2:
		winTitle = copy.getTitle()
		bPrintLog('Deinterleaving 2 channels...', 1)
		IJ.run('Deinterleave', 'how=2 keep') #makes ' #1' and ' #2', with ' #2' frontmost
		ch1WinStr = winTitle + ' #1'
		ch2WinStr = winTitle + ' #2'
		ch1Imp = WindowManager.getImage(ch1WinStr)
		ch2Imp = WindowManager.getImage(ch2WinStr)
		ch1File = destFolder + shortName + '_ch1.tif'
		ch2File = destFolder + shortName + '_ch2.tif'
		
	#
	# alignment
	if gDoAlign and gNumChannels == 1 and copy.getNSlices()>1:
		infoStr += 'AlignOnChannel=1' + '\n'
		#snap to middle slice
		if gAlignOnMiddleSlice:
			middleSlice = int(math.floor(copy.getNSlices() / 2)) #int() is necc., python is fucking picky
		else:
			middleSlice = gAlignOnThisSlice
		copy.setSlice(middleSlice)
		
		transformationFile = destAlignmentFolder + shortName + '.txt'
		
		bPrintLog('MultiStackReg aligning:' + impWinStr, 1)
		stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(impWin,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)
		infoStr += 'AlignOnSlice=' + str(middleSlice) + '\n'

		#20150723, we just aligned on a cropped copy, apply alignment to original imp
		origImpTitle = imp.getTitle()
		stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(origImpTitle,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)		
		
	if gDoAlign and gNumChannels == 2 and ch1Imp.getNSlices()>1 and ch2Imp.getNSlices()>1:
		#apply to gAlignThisChannel
		alignThisWindow = ''
		applyAlignmentToThisWindow = ''
		if gAlignThisChannel == 1:
			infoStr += 'AlignOnChannel=1' + '\n'
			transformationFile = destAlignmentFolder + shortName + '_ch1.txt'
			alignThisWindow = ch1WinStr
			applyAlignmentToThisWindow = ch2WinStr
		else:
			infoStr += 'AlignOnChannel=2' + '\n'
			transformationFile = destAlignmentFolder + shortName + '_ch2.txt'
			alignThisWindow = ch2WinStr
			applyAlignmentToThisWindow = ch1WinStr
	
		alignThisImp = WindowManager.getImage(alignThisWindow)
		#snap to middle slice
		if gAlignOnMiddleSlice:
			middleSlice = int(math.floor(alignThisImp.getNSlices() / 2)) #int() is necc., python is fucking picky
		else:
			middleSlice = gAlignOnThisSlice
		alignThisImp.setSlice(middleSlice)

		infoStr += 'bAlignOnSlice=' + str(middleSlice) + '\n'
		
		bPrintLog('MultiStackReg aligning:' + alignThisWindow, 1)
		stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(alignThisWindow,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)
	
		# 20150723, we just aligned on a copy, apply alignment to both channels of original
		# ch1
		bPrintLog('MultiStackReg applying alignment to:' + origCh1WinStr, 1)
		stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(origCh1WinStr,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)		
		# ch2
		bPrintLog('MultiStackReg applying alignment to:' + origCh2WinStr, 1)
		stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(origCh2WinStr,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)		
		
		#apply alignment to other window
		#bPrintLog('MultiStackReg applying alignment to:' + applyAlignmentToThisWindow, 1)
		#applyAlignThisImp = WindowManager.getImage(applyAlignmentToThisWindow)
		#stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(applyAlignmentToThisWindow,transformationFile)
		#IJ.run('MultiStackReg', stackRegParams)		
	elif gDoAlign:
		bPrintLog('Skipping alignment, there may be only one slice?',3)
						
	#
	# save
	if gNumChannels == 1:
		imp.setProperty("Info", infoStr);
		impFile = destFolder + shortName + '.tif'
		#bPrintLog('Saving:' + impFile, 1)
		bSaveStack(imp, impFile)
		#max project
		bSaveZProject(imp, destMaxFolder, shortName)

	if gNumChannels == 2:
		#ch1
		origCh1Imp.setProperty("Info", infoStr);
		#bPrintLog('Saving:' + ch1File, 1)
		bSaveStack(origCh1Imp, ch1File)
		#max project
		bSaveZProject(origCh1Imp, destMaxFolder, shortName+'_ch1')

		#ch2
		origCh2Imp.setProperty("Info", infoStr);
		#bPrintLog('Saving:' + ch2File, 1)
		bSaveStack(origCh2Imp, ch2File)
 		#max project
		bSaveZProject(origCh2Imp, destMaxFolder, shortName+'_ch2')
		
 	#
	# post convert to 8-bit and save
	if gSave8bit:
		if bitDepth == 16:
			if gNumChannels == 1:
				bPrintLog('Converting to 8-bit:' + impWinStr, 1)
				IJ.selectWindow(impWinStr)
				#IJ.run('resetMinAndMax()')
				IJ.run("8-bit")
				impFile = eightBitFolder + shortName + '.tif'
				bPrintLog('Saving 8-bit:' + impFile, 2)
				bSaveStack(imp, impFile)
				#max project
				bSaveZProject(imp, eightBitMaxFolder, shortName)
				
			if gNumChannels == 2:
				#
				bPrintLog('Converting to 8-bit:' + origCh1WinStr, 1)
				IJ.selectWindow(origCh1WinStr)
				
				IJ.run("8-bit")
				impFile = eightBitFolder + shortName + '_ch1.tif'
				bPrintLog('Saving 8-bit:' + impFile, 2)
				bSaveStack(origCh1Imp, impFile)
				#max project
				bSaveZProject(origCh1Imp, eightBitMaxFolder, shortName+'_ch1')

				#
				bPrintLog('Converting to 8-bit:' + origCh2WinStr, 1)
				IJ.selectWindow(origCh2WinStr)
				#IJ.run('resetMinAndMax()')
				IJ.run("8-bit")
 				impFile = eightBitFolder + shortName + '_ch2.tif'
				bPrintLog('Saving 8-bit:' + impFile, 2)
				bSaveStack(origCh2Imp, impFile)
				#max project
				bSaveZProject(origCh2Imp, eightBitMaxFolder, shortName+'_ch2')
				
	#
	# close original window
	imp.changes = 0
	imp.close()
	#copy
	copy.changes = 0
	copy.close()

	#
	# close ch1/ch2
	if gNumChannels == 2:
		#original
		origCh1Imp.changes = 0
		origCh1Imp.close()
		origCh2Imp.changes = 0
		origCh2Imp.close()
		#copy
		ch1Imp.changes = 0
		ch1Imp.close()
		ch2Imp.changes = 0
		ch2Imp.close()

	bPrintLog(time.strftime("%H:%M:%S") + ' finished runOneFile(): ' + fullFilePath, 1)

def readlsmHeader(infoStr):
	voxelx = 1
	voxely = 1
	voxelz = 1
	numChannels = 1
	for line in infoStr.split('\n'):
		if line.find('VoxelSizeX') != -1:
			voxelx = str(line.split('=')[1])
		if line.find('VoxelSizeY') != -1:
			voxely = str(line.split('=')[1])
		if line.find('VoxelSizeZ') != -1:
			voxelz = str(line.split('=')[1])
		if line.find('SizeC') != -1:
			numChannels = str(line.split('=')[1])
			
	return numChannels, voxelx, voxely, voxelz
	
#
# called when invoked as a plugin via Fiji plugins menu
def run():
	bPrintLog(' ', 0)
	bPrintLog('=====================================', 0)
	bPrintLog('Running bAlign_Batch_v7', 0)
	bPrintLog('=====================================', 0)

	if len(sys.argv) < 2:
		print "   We need a hard-drive folder with .tif stacks as input"
		print "	  Usage: ./fiji-macosx bALign_Batch_7 <full-path-to-folder>/"
		# Prompt user for a folder
		sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
		if not sourceFolder:
			return 0
		strippedFolder = sourceFolder.replace(' ', '')
		if sourceFolder != strippedFolder:
			print 'found a space in specified path. Pease remove spaces and try again.'
			print 'path:', sourceFolder
			errorDialog = GenericDialog('Align Batch 7 Options')
			errorDialog.addMessage('bAlignBatch7 Error !!!')
			errorDialog.addMessage('There can not be any spaces in the path.')
			errorDialog.addMessage('Please remove spaces and try again.')
			errorDialog.addMessage('Offending path is:')
			errorDialog.addMessage(sourceFolder)
			errorDialog.showDialog()
			return 0
	else:
		sourceFolder = sys.argv[1] #assuming it ends in '/'
	
	if not os.path.isdir(sourceFolder):
		bPrintLog('\nERROR: run() did not find folder: ' + sourceFolder + '\n',0)
		return 0

	
	if (Options(sourceFolder)):
		runOneFolder(sourceFolder)

	bPrintLog('=====================================', 0)
	bPrintLog('Done bAlign_Batch_v7', 0)
	bPrintLog('=====================================', 0)
        bPrintLog(' ', 0)

#
if __name__ == '__main__': 
	run()
	