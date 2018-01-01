#20161206
#Robert H. Cudmore

'''
Take a folder of .tif and convert all 16-bit tif to 8-bit
 - Scale pixels down using the source bit-depth (assuming we find b_bitDepth)
 -   The default behavior of Fiji/ImageJ 'convert to 8 bit' is to scale based on the max intensity in the image
 - If .tif is already 8-bit then just copy to destination
 '''

#python
import os
import time, math
from os.path import basename

 #imagej (java)
from ij import IJ
from ij import WindowManager, ImagePlus, ImageStack
from ij.process import FloatProcessor
from ij.io import DirectoryChooser, FileSaver
from ij.process import ImageConverter # by default convert to 8-bit will scale, i need to turn ot off. See: https://ilovesymposia.com/2014/02/26/fiji-jython/

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
	for child in os.listdir(srcFolder):
		#print 'srcFolder:', srcFolder, 'child:', child
		if child.endswith('.tif'):
			tifList.append(srcFolder + child)
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
	bPrintLog('numSlices: ' + str(numSlices), 3)
	
	infoStr = imp.getProperty("Info") #get all tags
	if infoStr is None:
		infoStr = ''
	infoStr += 'bMaxProject=v0.1\n'
	imp.setProperty("Info", infoStr)

	imp.show()
	impWin = imp.getTitle()

	# BODY
	
	# get the bit depth form opened imp
	impBitDepth = imp.getBitDepth()
	bPrintLog('image bit depth:' + str(impBitDepth), 3)

	# get the actual bit depth used (e.g. ScanImage is 11 bit, Prairie is 13 bit)
	header = bParseHeader(imp)
	actualBitDepth = impBitDepth
	if 'b_bitDepth' in header:
		actualBitDepth = int(header['b_bitDepth'])
	bPrintLog('actual bit depth:' + str(actualBitDepth), 3)
	
	made8bit = 0
	if impBitDepth == 8:
		made8bit = 1
	else:
		made8bit = 1
		if 0:
			divideBy = math.pow(2,actualBitDepth) / math.pow(2,8) # divide the 13 bit or 11 bit image down to 8 bit
			bPrintLog('diving by:' + str(divideBy), 3)
			bPrintLog('converting to 8-bit by dividing image by ' + str(divideBy) + ' and then convert to 8-bit with ImageConverter.setDoScaling(False)', 3)
			#run("Divide...", "value=32 stack");
			divideArgs = 'value=' + str(divideBy) + ' stack'
			IJ.run(imp, "Divide...", divideArgs);
		# convert to 8-bit will automatically scale, to turn this off use
		# eval("script", "ImageConverter.setDoScaling(false)"); 
		# 20170810 was this
		#ImageConverter.setDoScaling(False)
		ImageConverter.setDoScaling(True)
		# run("8-bit");
		bPrintLog('converting to 8-bit with setDoScaling False', 3)
		IJ.run(imp, "8-bit", ''); #does this in place, no new window

	# save
	bPrintLog('Saving stack with ' + str(numSlices) + ' slices:' + dstTifPath, 3)
	fs = FileSaver(imp)
	if numSlices>1:
		fs.saveAsTiffStack(dstTifPath)
	else:
		fs.saveAsTiff(dstTifPath)

	# END BODY
	
	# close original
	imp.changes = 0
	imp.close()

def runOneFolder(srcFolder):

	bPrintLog('runOneFolder() ' + srcFolder, 1)
	if not os.path.isdir(srcFolder):
		bPrintLog('ERROR: runOneFolder() did not find folder: ' + srcFolder)
		return 0

	# make output folder
	tmp = os.path.split(srcFolder)[0]
	enclosingFolderName = os.path.split(tmp)[1]
	if gUseEnclosingFolderNameInOutputFolder:
		dstFolder = srcFolder + enclosingFolderName + '_channels8' + '/'
	else:
		dstFolder = srcFolder + 'channels8' + '/'

	if not os.path.isdir(dstFolder):
		os.makedirs(dstFolder)

	# go through all tif in srcFolder
	tifList = bTifList(srcFolder) # list of folder we will process (Each folder has list of .tif)
	numTif = 0
	for i, tifFilePath in enumerate(tifList):
		# debug
		#if i > 6:
		#	continue
		
		#print 'runOneFolder found tif:', tifFile
		tifFileName = os.path.split(tifFilePath)[1]
		#tifFileName = 'max_' + tifFileName
		dstTifPath = dstFolder + tifFileName
		runOneTif(tifFilePath, dstTifPath)

		numTif += 1

	return numTif, dstFolder

print __name__

if __name__ in ('__main__','__builtin__'): 
	startTime = time.time()
	
	bPrintLog('\n=================')
	bPrintLog('Starting bConvertTo8Bit')

	#ask user for folder, this is a folder that contains folders with single image .tif files
	sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()

	numTif = 0
	if (sourceFolder):
		print 'sourceFolder:', sourceFolder # DOES end in
		
		doWalk = 0
		if doWalk:
			dirlist = []
			for dirpath, dirnames, filenames in os.walk(sourceFolder):
				foldername = dirpath.split('/')[-1]
				if foldername == 'raw':
					dirpath += '/'
					#print dirpath # does NOT end in /
					dirlist.append(dirpath)
	
			for thisdir in dirlist:
				print thisdir
				numTif, dstFolder = runOneFolder(thisdir)
		else:
			# user specified raw directory with .tif files
			numTif, dstFolder = runOneFolder(sourceFolder)
	else:
		bPrintLog('Canceled by user', 0)
	
	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds / 60.0, 2)
	bPrintLog('Finished bConvertTo8Bit with ' + str(numTif) + ' tif files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
	bPrintLog('=================\n')
