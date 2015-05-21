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
#   Feb 23, 2015: fixed bug where max project did not have _ch1/_ch2 appended to max .tif file nmae
#

from ij import IJ, ImagePlus, WindowManager
from ij.gui import GenericDialog, Roi
from ij.process import StackStatistics
from ij.io import Opener, FileSaver, DirectoryChooser
from java.io import File, FilenameFilter
import sys, os, re, math
from string import find
import time # for yyyymmdd, for wait
#import re

#globals
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

# 1...#5 are the order of operation
# 1
gGetNumChanFromScanImage = 0 # 0 is off, 1 is on
gNumChannels = 2
# 2
gDoCrop = 0 # 0 is off, 1 is on
gCropLeft = 100 #default left of cropping rectangle
gCropTop = 0 #default top of cropping rectangle
gCropWidth = 850 #default width of cropping rectangle
gCropHeight = 1024 #default height of cropping rectangle
# 3
gRemoveCalibration = 0 # 0 is off, 1 is on
# 4
gDoAlign = 1 # 0 is off, 1 is on
gAlignThisChannel = 1
gAlignOnMiddleSlice = 1
gAlignOnThisSlice = 0
# 5
gSave8bit = 0 # 0 is off, 1 is on

# only call if we know for sure there is a sourceFolder
def Options(sourceFolder):
	#globals
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

	tifNames = [file.name for file in File(sourceFolder).listFiles(Filter())]
	numTifs = len(tifNames)

	gd = GenericDialog('Align Batch 6 Options')
	#gd.addStringField('Command: ', '')

	gd.addMessage('Source Folder: ' + sourceFolder)
	gd.addMessage('Number of .tif files: ' + str(numTifs))
	
	#gd.setInsets(5,0,3)
	#0
	gd.addCheckboxGroup(1, 1, ['Get Number Of Channels From ScanImage 3.x or 4.x header'], [gGetNumChanFromScanImage], ['Channels'])
	gd.addNumericField('Otherwise, Assume All Stacks Have This Number Of Channels: ', gNumChannels, 0)

	#1
	gd.addCheckboxGroup(1, 1, ['Remove Linear Calibration From ScanImage 4.x'], [gRemoveCalibration], ['ScanImage4'])
	
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
		gNumChannels = int(gd.getNextNumber())

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
		bPrintLog('gGetNumChanFromScanImage=' + str(gGetNumChanFromScanImage), 1)
		bPrintLog('gNumChannels=' + str(gNumChannels), 1)
		bPrintLog('gRemoveCalibration=' + str(gRemoveCalibration), 1)
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
	if not os.path.isdir(sourceFolder):
		bPrintLog('\nERROR: runOneFolder() did not find folder: ' + sourceFolder + '\n',0)
		return 0
		
	tifNames = [file.name for file in File(sourceFolder).listFiles(Filter())]
	numTifs = len(tifNames)

	bPrintLog(' ',0)
	bPrintLog('=================================================',0)
	bPrintLog('Align Batch 6',0)
	bPrintLog('sourceFolder: ' + sourceFolder,1)
	bPrintLog('Number of .tif files: ' + str(numTifs),1)

	count = 1
	for tifName in tifNames:
		msgStr = '--->>> Opening ' + str(count) + ' of ' + str(numTifs)
		bPrintLog(msgStr, 0)	
		runOneFile(sourceFolder + tifName)
		count += 1

	bPrintLog('Done runOneFolder', 1)

def runOneFile(fullFilePath):

	global gNumChannels
	
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
	
	# open image
	imp = Opener().openImage(fullFilePath)

	# get parameters of image
	(width, height, nChannels, nSlices, nFrames) = imp.getDimensions()
	bitDepth = imp.getBitDepth()
	infoStr = imp.getProperty("Info") #get all .tif tags
	if not infoStr:
		infoStr = ''
		
	msgStr = 'w:' + str(width) + ' h:' + str(height) + ' slices:' + str(nSlices) \
				+ ' channels:' + str(nChannels) + ' frames:' + str(nFrames) + ' bitDepth:' + str(bitDepth)
	bPrintLog(msgStr, 1)
	
	path, filename = os.path.split(fullFilePath)
	shortName, fileExtension = os.path.splitext(filename)

	#this is too much work for ScanImage4
	#try and guess channels if it is a scanimage file
	#scanImage3 = string.find(infoStr, 'scanimage') != -1
	#scanimage4 = find(infoStr, 'scanimage.SI4.channelSave = ')
	#print 'scanimage4:', scanimage4
	
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

	infoStr += 'bAlignBatch6=' + time.strftime("%Y%m%d") + '\n'
	#
	# crop
	if gDoCrop:
		bPrintLog('making cropping rectangle (left,top,width,height) ',1)
		bPrintLog(str(gCropLeft) + ' ' + str(gCropTop) + ' ' +str(gCropWidth) + ' ' +str(gCropHeight), 2)
		roi = Roi(gCropLeft, gCropTop, gCropWidth, gCropHeight) #left,top,width,height
		imp.setRoi(roi)
		
		#time.sleep(1)
		
		#bPrintLog('cropping', 1)
		IJ.run('Crop')
		infoStr += 'cropping=' + str(gCropLeft) + ',' + str(gCropTop) + ',' + str(gCropWidth) + ',' + str(gCropHeight) + '\n'
	#
	# remove calibration
	if gRemoveCalibration:
		cal = imp.getCalibration()
		calCoeff = cal.getCoefficients()
		if calCoeff:
			msgStr = 'Calibration is y=a+bx' + ' a=' + str(calCoeff[0]) + ' b=' + str(calCoeff[1])
			bPrintLog(msgStr, 1)
			
			#remove calibration
			bPrintLog('Removing Calibration', 2)
			imp.setCalibration(None)
				
			#get and print out min/max
			origMin = StackStatistics(imp).min
			origMax = StackStatistics(imp).max
			msgStr = 'orig min=' + str(origMin) + ' max=' + str(origMax)
			bPrintLog(msgStr, 2)
			
			#msgStr = 'adding calCoeff[0]='+str(calCoeff[0]) + ' to stack.'
			#bPrintLog(msgStr, 2)
			#subArgVal = 'value=%s stack' % (calCoeff[0],)
			#IJ.run('Add...', subArgVal)

			msgStr = 'Subtracting orig min '+str(origMin) + ' from stack.'
			bPrintLog(msgStr, 2)
			subArgVal = 'value=%s stack' % (origMin,)
			IJ.run('Subtract...', subArgVal)

			#get and print out min/max
			newMin = StackStatistics(imp).min
			newMax = StackStatistics(imp).max
			msgStr = 'new min=' + str(newMin) + ' max=' + str(newMax)
			bPrintLog(msgStr, 2)
			
			#without these, 8-bit conversion goes to all 0 !!! what the fuck !!!
			bPrintLog('calling imp.resetStack() and imp.resetDisplayRange()', 2)
			imp.resetStack()
			imp.resetDisplayRange()

			#append calibration to info string
			infoStr += 'calibCoeff_a = ' + str(calCoeff[0]) + '\n'
			infoStr += 'calibCoeff_b = ' + str(calCoeff[1]) + '\n'
			infoStr += 'origMin = ' + str(origMin) + '\n'
			infoStr += 'origMax = ' + str(origMax) + '\n'

	#
	# set up
	if gNumChannels == 1:
		impWinStr = imp.getTitle() #use this when only one channel
		impWin = WindowManager.getWindow(impWinStr) #returns java.awt.Window
	
	if gNumChannels == 2:
		winTitle = imp.getTitle()
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
	if gDoAlign and gNumChannels == 1 and imp.getNSlices()>1:
		infoStr += 'AlignOnChannel=1' + '\n'
		#snap to middle slice
		if gAlignOnMiddleSlice:
			middleSlice = int(math.floor(imp.getNSlices() / 2)) #int() is necc., python is fucking picky
		else:
			middleSlice = gAlignOnThisSlice
		imp.setSlice(middleSlice)
		
		transformationFile = destAlignmentFolder + shortName + '.txt'
		
		bPrintLog('MultiStackReg aligning:' + impWinStr, 1)
		stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(impWin,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)
		infoStr += 'AlignOnSlice=' + str(middleSlice) + '\n'
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

		infoStr += 'AlignOnSlice=' + str(middleSlice) + '\n'
		
		bPrintLog('MultiStackReg aligning:' + alignThisWindow, 1)
		stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(alignThisWindow,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)
	
		#apply alignment to other window
		bPrintLog('MultiStackReg applying alignment to:' + applyAlignmentToThisWindow, 1)
		applyAlignThisImp = WindowManager.getImage(applyAlignmentToThisWindow)
		stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(applyAlignmentToThisWindow,transformationFile)
		IJ.run('MultiStackReg', stackRegParams)		
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
		ch1Imp.setProperty("Info", infoStr);
		#bPrintLog('Saving:' + ch1File, 1)
		bSaveStack(ch1Imp, ch1File)
		#max project
		bSaveZProject(ch1Imp, destMaxFolder, shortName+'_ch1')

		#ch2
		ch2Imp.setProperty("Info", infoStr);
		#bPrintLog('Saving:' + ch2File, 1)
		bSaveStack(ch2Imp, ch2File)
 		#max project
		bSaveZProject(ch2Imp, destMaxFolder, shortName+'_ch2')
		
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
				bPrintLog('Converting to 8-bit:' + ch1WinStr, 1)
				IJ.selectWindow(ch1WinStr)
				#IJ.run('resetMinAndMax()')
				
				#ch1Imp.resetStack()
				#ch1Imp.resetDisplayRange()
				
				IJ.run("8-bit")
				impFile = eightBitFolder + shortName + '_ch1.tif'
				bPrintLog('Saving 8-bit:' + impFile, 2)
				bSaveStack(ch1Imp, impFile)
				#max project
				bSaveZProject(ch1Imp, eightBitMaxFolder, shortName+'_ch1')

				#
				bPrintLog('Converting to 8-bit:' + ch2WinStr, 1)
				IJ.selectWindow(ch2WinStr)
				#IJ.run('resetMinAndMax()')
				IJ.run("8-bit")
 				impFile = eightBitFolder + shortName + '_ch2.tif'
				bPrintLog('Saving 8-bit:' + impFile, 2)
				bSaveStack(ch2Imp, impFile)
				#max project
				bSaveZProject(ch2Imp, eightBitMaxFolder, shortName+'_ch2')
				
	#
	# close original window
	imp.changes = 0
	imp.close()

	#
	# close ch1/ch2
	if 1 and gNumChannels == 2:
		ch1Imp.changes = 0
		ch1Imp.close()
		ch2Imp.changes = 0
		ch2Imp.close()

	bPrintLog(time.strftime("%H:%M:%S") + ' finished runOneFile(): ' + fullFilePath, 1)
	
#
# called when invoked as a plugin via Fiji plugins menu
def run():
	bPrintLog(' ', 0)
	bPrintLog('=====================================', 0)
	bPrintLog('Running bAlign_Batch_v6', 0)
	bPrintLog('=====================================', 0)

	if len(sys.argv) < 2:
		print "   We need a hard-drive folder with .tif stacks as input"
		print "	  Usage: ./fiji-macosx bALign_Batch_6 <full-path-to-folder>/"
		# Prompt user for a folder
		sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
		if not sourceFolder:
			return 0
	else:
		sourceFolder = sys.argv[1] #assuming it ends in '/'
	
	if not os.path.isdir(sourceFolder):
		bPrintLog('\nERROR: run() did not find folder: ' + sourceFolder + '\n',0)
		return 0

	
	if (Options(sourceFolder)):
		runOneFolder(sourceFolder)

	bPrintLog('=====================================', 0)
	bPrintLog('Done bAlign_Batch_v6', 0)
	bPrintLog('=====================================', 0)
        bPrintLog(' ', 0)

#
if __name__ == '__main__': 
	run()
	