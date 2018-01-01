#20161206
#Robert H. Cudmore

'''
For each .tif in a folder, generate a max project
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

gUseEnclosingFolderNameInOutputFolder = True

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
	if infoStr is None:
		infoStr = ''
	infoStr += 'bMaxProject=v0.1\n'
	imp.setProperty("Info", infoStr)

	imp.show()
	impWin = imp.getTitle()

	# BODY
	
	madeMax = 0
	if numSlices == 1:
		# don;t make max
		madeMax = 0
		maxSlices = numSlices
		maxImp = imp
	else:
		madeMax = 1
		# take max project
		#IJ.run(imp, "Z Project...", "projection=[Max Intensity]");
		maxProjectArgs = 'projection=[Max Intensity]'
		IJ.run(imp, "Z Project...", maxProjectArgs); # makes a new window MAX_
		
		maxWindow = 'MAX_' + impWin
		maxImp = WindowManager.getImage(maxWindow)
		maxImp.setProperty("Info", infoStr)
		maxSlices = maxImp.getNSlices() # should be 1
	
	# save
	bPrintLog('Saving stack with ' + str(maxSlices) + ' slices:' + dstTifPath, 3)
	fs = FileSaver(maxImp)
	if maxSlices>1:
		fs.saveAsTiffStack(dstTifPath)
	else:
		fs.saveAsTiff(dstTifPath)

	if madeMax:
		maxImp.changes = 0
		maxImp.close()

	# END BODY
	
	# close original
	imp.changes = 0
	imp.close()

def runOneFolder(sourceFolder):

	bPrintLog('runOneFolder() ' + sourceFolder, 1)
	if not os.path.isdir(sourceFolder):
		bPrintLog('ERROR: runOneFolder() did not find folder: ' + sourceFolder)
		return 0

	# make output folder
	tmp = os.path.split(sourceFolder)[0]
	if gUseEnclosingFolderNameInOutputFolder:
		enclosingFolderName = os.path.split(tmp)[1]
		dstFolder = sourceFolder + enclosingFolderName + '_max' + '/'
	else:
		dstFolder = sourceFolder  + 'max' + '/'

	if not os.path.isdir(dstFolder):
		os.makedirs(dstFolder)

	# go through all tif in sourceFOlder
	tifList = bTifList(sourceFolder) # list of folder we will process (Each folder has list of .tif)
	totalNumTif = len(tifList)
	numTif = 0
	for i, tifFilePath in enumerate(tifList):
		# debug
		#if i > 6:
		#	continue
		
		#print 'runOneFolder found tif:', tifFile
		bPrintLog(str(numTif) + ' of ' + str(totalNumTif), 2)
		tifFileName = os.path.split(tifFilePath)[1]
		tifFileName = 'max_' + tifFileName
		dstTifPath = dstFolder + tifFileName
		runOneTif(tifFilePath, dstTifPath)

		numTif += 1

	return numTif, dstFolder

if __name__ == '__main__': 
	startTime = time.time()
	
	bPrintLog('\n=================')
	bPrintLog('Starting bMaxProject')

	#ask user for folder, this is a folder that contains folders with single image .tif files
	sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()

	numTif = 0
	if (sourceFolder):
		numTif = runOneFolder(sourceFolder)
	else:
		bPrintLog('Canceled by user', 0)
	
	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds / 60.0, 2)
	bPrintLog('Finished bMaxProject with ' + str(numTif) + ' tif files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
	bPrintLog('=================\n')

