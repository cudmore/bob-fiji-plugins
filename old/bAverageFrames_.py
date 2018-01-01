#20161121
#Robert H. Cudmore

# this does not work, i don't want to iterate pixels in python
#
# use a macro instead
#
# selectWindow("20161119_a189-228_ch2.tif");
# run("Grouped Z Project...", "projection=[Average Intensity] group=2"); # outputs window named AVG_<orig window name>

# to do 20161123 to do
# see: https://www.ini.uzh.ch/~acardona/fiji-tutorial/
# 1
# this math does not seem neccessary? Priarie images are NOT 2^13 bit? They have intensities slightly over 2^13
#to convert 13 bit to 8 bit (i) divive all pixels by 2^16 / 2^13 = 8 (ii) convert to 8-bit
# run("Divide...", "value=8 stack");
#
# fiji menu/macro assumes values fill 2^16 !!!! they don't
# run(8-bit")

# 2
# then median filter

'''
todo: i need to parse my info str and replace values
'''

#imagej (java)
from ij import IJ
from ij import WindowManager, ImagePlus, ImageStack
from ij.process import FloatProcessor
from ij.io import DirectoryChooser, FileSaver
from ij.process import ImageConverter # by default convert to 8-bit will scale, i need to turn ot off. See: https://ilovesymposia.com/2014/02/26/fiji-jython/

#python
import os
import time, math
from os.path import basename

'''
Globals
'''
globalOptions = {}
globalOptions['gNumToAverage'] = 0
globalOptions['medianFilter'] = 0 # set to 0 for no median filter
globalOptions['gConvertToEightBit'] = True # set to 0 for no median filter

#gNumToAverage = 2
#gMedianFilterPixels = 3 # 0 to turn off
#gConvertToEightBit = True

class fakeClass():
	pass
	
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

def bTifList(srcFolder):
	tifList = []
	for child in os.listdir(sourceFolder):
		if child.endswith('.tif'):
			tifList.append(sourceFolder + child)
	return tifList

def bParseHeader(imp):
	'''
	for each line in imp header, return a dict with key/value pairs
	  will only parse lines with '=' in them
	'''
	  
	header = {}
	infoStr = imp.getProperty("Info") #get all tags
	if infoStr is None:
		infoStr = ''
	for line in infoStr.split('\n'):
		#print 'line:', line
		if line.find('=') != -1:
			lhs, rhs = line.split('=')
			header[lhs] = rhs
		
	return header

### Main
def runOneTif(tifPath, dstTifPath):
	bPrintLog('=== runOneTif processing tif:' + tifPath, 3)

	bPrintLog('Loading file...', 3)
	imp = IJ.openImage(tifPath)  

	if imp is None:  
		bPrintLog('ERROR: could not open image from file:' + tifPath, 3)
		return 0  

	logStr = 'done loading file: ' + str(imp.width) + ' ' + str(imp.height) + ' ' + str(imp.getNSlices())
	bPrintLog(logStr, 3)

	numSlices = imp.getNSlices()
	if numSlices>1:
		pass
	else:
		bPrintLog('ERROR: number of slices must be more than one, file: ' + tifPath)
		return 0
	bPrintLog('numSlices: ' + str(numSlices), 3)
	
	infoStr = imp.getProperty("Info") #get all tags
	#print infoStr
	if infoStr is None:
		infoStr = ''
	infoStr += 'bAverageFrames=v0.1\n'
	imp.setProperty("Info", infoStr)

	imp.show()
	impWin = imp.getTitle()

	#
	# start body
	
	#infer type of file from
	# get the actual bit depth used (e.g. ScanImage is 11 bit, Prairie is 13 bit)
	header = bParseHeader(imp)
	b_sequence = ''
	if 'b_sequence' in header:
		b_sequence = str(header['b_sequence'])

	bPrintLog('b_sequence: ' + b_sequence, 3)
	
	madeAverage = 0

	
	# if numSlices is not divisable by gNumToAverage then chop a few slices off bottom/end
	if b_sequence.startswith('TSeries'):
		if globalOptions['gNumToAverage'] > 1:
			numToRemove = numSlices % globalOptions['gNumToAverage']
			if numToRemove > 0:
				bPrintLog('Removing bottom slices: ' + str(numToRemove), 3)
				# run("Slice Remover", "first=3 last=5 increment=1");
				removeArgs = 'first=' + str(numSlices-numToRemove+1) + ' last=' + str(numSlices) + ' increment=1'
				IJ.run('Slice Remover', removeArgs)
				numSlices = imp.getNSlices()
				bPrintLog('numSlices: ' + str(numSlices), 3)
				
			#fix this: if stack is really short this will not be taken
			if (numSlices > globalOptions['gNumToAverage']):
				bPrintLog('Taking average of ' + str(globalOptions['gNumToAverage']) + ' slices from ' + str(numSlices), 3)
				stackRegParams = 'projection=[Average Intensity] group=' + str(globalOptions['gNumToAverage'])
				IJ.run('Grouped Z Project...', stackRegParams) # makes window AVG_
		
				madeAverage = 1
				
				avgWindow = 'AVG_' + impWin
				avgImp = WindowManager.getImage(avgWindow)
				avgSlices = avgImp.getNSlices()
	
				# Grouped Z PRoject swaps slices for frames?
				tmpSlices = avgImp.getNSlices()
				tmpFrames = avgImp.getNFrames()
				if tmpFrames > 1:
					newSlices = tmpFrames
					newFrames = tmpSlices
					nChannels = 1
					bPrintLog('Swaping frames for slices after grouped z',3)
					bPrintLog('newSlices=' + str(newSlices) + ' newFrames='+str(newFrames), 4)
					avgImp.setDimensions(nChannels, newSlices, newFrames)
				
				infoStr += 'gNumToAverage=' + str(globalOptions['gNumToAverage']) + '\n'
				# I want to adjust the framePeriod, prairie would be 'b_framePeriod'
				avgImp.setProperty("Info", infoStr)
		else:
			avgImp = imp
			avgSlices = numSlices
		
	else:
		bPrintLog('Not taking average of sequence: ' + b_sequence,3)
		avgImp = imp
		avgSlices = numSlices

		
	if globalOptions['medianFilter']>0:
		bPrintLog('Running median filter: ' + str(globalOptions['medianFilter']), 3)
		medianArgs = 'radius=' + str(globalOptions['medianFilter']) + ' stack'
		IJ.run(avgImp, "Median...", medianArgs);
		infoStr += 'bMedianFilter=' + str(globalOptions['medianFilter']) + '\n'
		avgImp.setProperty("Info", infoStr)

	# convert to 8 bit
	# 1) read bit depth from header (e.g. 2^13)
	# 2) do math on image and convert to 8-bit
	# run("Divide...", "value=32 stack");
	if globalOptions['gConvertToEightBit']:
		bPrintLog('converting to 8-bit by dividing image down and then convert to 8-bit with ImageConverter.setDoScaling(False)', 3)
		bitDepth = 2^13
		divideBy = bitDepth / 2^8
		# divide the 13 bit image down to 8 bit
		#run("Divide...", "value=32 stack");
		bPrintLog('divideBy:' + str(divideBy), 3)
		divideArgs = 'value=' + str(divideBy) + ' stack'
		IJ.run(avgImp, "Divide...", divideArgs);
		# convert to 8-bit will automatically scale, to turn this off use
		# eval("script", "ImageConverter.setDoScaling(false)"); 
		ImageConverter.setDoScaling(False)
		# run("8-bit");
		bPrintLog('converting to 8-bit with setDoScaling False', 3)
		IJ.run(avgImp, "8-bit", '');
	
	bPrintLog('Saving stack with ' + str(avgSlices) + ' slices:' + dstTifPath, 3)
	fs = FileSaver(avgImp)
	if avgSlices>1:
		fs.saveAsTiffStack(dstTifPath)
	else:
		fs.saveAsTiff(dstTifPath)

	if madeAverage:
		avgImp.changes = 0
		avgImp.close()
	
	imp.changes = 0
	imp.close()
	
	# end body
	#
	
	# why was this here
	#imp.changes = 0
	#imp.close()

	return 1

def runOneFolder(sourceFolder):

	bPrintLog('runOneFolder() ' + sourceFolder, 1)
	if not os.path.isdir(sourceFolder):
		bPrintLog('ERROR: runOneFolder() did not find folder: ' + sourceFolder)
		return 0

	# make output folder
	tmp = os.path.split(sourceFolder)[0]
	enclosingFolderName = os.path.split(tmp)[1]
	dstFolder = sourceFolder + enclosingFolderName + '_average' + '/'
	if not os.path.isdir(dstFolder):
		os.makedirs(dstFolder)

	# go through all tif in sourceFOlder
	tifList = bTifList(sourceFolder) # list of folder we will process (Each folder has list of .tif)
	numTif = 0
	for i, tifFilePath in enumerate(tifList):
		# debug
		#if i > 6:
		#	continue
		
		#print 'runOneFolder found tif:', tifFile
		tifFileName = os.path.split(tifFilePath)[1]
		dstTifPath = dstFolder + tifFileName
		runOneTif(tifFilePath, dstTifPath)

		numTif += 1

	return numTif, dstFolder

if __name__ == '__main__': 
	startTime = time.time()
	
	bPrintLog('\n=================')
	bPrintLog('Starting bAverageFrames')

	#ask user for folder, this is a folder that contains folders with single image .tif files
	sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()

	numTif = 0
	if (sourceFolder):
		numTif, dstFolder = runOneFolder(sourceFolder)
	else:
		bPrintLog('Canceled by user', 0)
	
	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds / 60.0, 2)
	bPrintLog('Finished bAverageFrames with ' + str(numTif) + ' tif files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
	bPrintLog('=================\n')

