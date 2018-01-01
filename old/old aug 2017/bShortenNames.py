#Author: RObert H Cudmore
#Date: 20160419
#
#Purpose: Shorten name in a directory of .tif or .lsm 
#

from ij import IJ, ImagePlus, WindowManager
from ij.gui import GenericDialog, Roi
from ij.process import StackStatistics
from ij.io import Opener, FileSaver, DirectoryChooser
from java.io import File, FilenameFilter
import sys, os, re, math
from string import find
import time # for yyyymmdd, for wait
#from ij.plugin import Duplicator # for Duplicator().run(imp)

#globals
global gShortenVersion
global gFileType # tif or lsm
global fileIndex

gShortenVersion = '1.0'
gFileType = 'tif'
fileIndex = 0

#return a list of .tif file, skip files that end in 'max.tif'
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

#return a list of .lsm file, skip files that end in 'max.tif'
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

#print to the fiji log window
def bPrintLog(text, indent):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)
	
#save a single stack
def bSaveStack(imp, fullPath):
	fs = FileSaver(imp)
	#print 'bSaveStack()', fullPath, 'nslices=', imp.getNSlices()
	bPrintLog('bSaveStack():' + fullPath + ' slices=' + str(imp.getNSlices()), 1)
	if imp.getNSlices()>1:
		fs.saveAsTiffStack(fullPath)
	else:
		fs.saveAsTiff(fullPath)

#run on a hard-drive folder
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
	bPrintLog('Shorten Names',0)
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

#run on one file
def runOneFile(fullFilePath):
	global gFileType
	global fileIndex
	
	if not os.path.isfile(fullFilePath):
		bPrintLog('\nERROR: runOneFile() did not find file: ' + fullFilePath + '\n',0)
		return 0

	bPrintLog(time.strftime("%H:%M:%S") + ' starting runOneFile(): ' + fullFilePath, 1)
	bPrintLog('inputfile is:' + fullFilePath, 1)
	
	enclosingPath = os.path.dirname(fullFilePath)
	head, tail = os.path.split(enclosingPath) #tail is name of enclosing folder
	enclosingPath += '/'
	
	# make output folders
	destFolder = enclosingPath + tail + '_short/'
	if not os.path.isdir(destFolder):
		os.makedirs(destFolder)

	# open
	if gFileType=='tif':
		# open .tif image
		imp = Opener().openImage(fullFilePath)
	else:
		# open .lsm
		cmdStr = 'open=%s autoscale color_mode=Default view=Hyperstack stack_order=XYCZT' % (fullFilePath,)
		IJ.run('Bio-Formats Importer', cmdStr)
		lsmpath, lsmfilename = os.path.split(fullFilePath)
		lsWindow = lsmfilename
		imp = WindowManager.getImage(lsWindow)

	# get parameters of image
	(width, height, nChannels, nSlices, nFrames) = imp.getDimensions()
	bitDepth = imp.getBitDepth()
	infoStr = imp.getProperty("Info") #get all .tif tags
	#print 'original infoStr:', infoStr
	if not infoStr:
		infoStr = ''
	infoStr += 'ShortenNames_Version=' + str(gShortenVersion) + '\n'
	infoStr += 'ShortenNames_Time=' + time.strftime("%Y%m%d") + '_' + time.strftime("%H%M%S") + '\n'
		
	msgStr = 'w:' + str(width) + ' h:' + str(height) + ' slices:' + str(nSlices) \
				+ ' channels:' + str(nChannels) + ' frames:' + str(nFrames) + ' bitDepth:' + str(bitDepth)
	bPrintLog(msgStr, 1)
	
	path, filename = os.path.split(fullFilePath)
	shortName, fileExtension = os.path.splitext(filename)

	#output file name
	outFile = destFolder + tail + '_' + str(fileIndex) + '.tif'
	fileIndex += 1
	bPrintLog('output file is:' + outFile, 1)
	
	# put original name in header
	infoStr += 'ShortenNames_OriginalFile=' + fullFilePath + '\n'
	
	# put scanimage header back in
	imp.setProperty("Info", infoStr);

	#save
	bSaveStack(imp, outFile)

	#
	# close original window
	imp.changes = 0
	imp.close()

#
# called when invoked as a plugin via Fiji plugins menu
def run():
	bPrintLog(' ', 0)
	bPrintLog('=====================================', 0)
	bPrintLog('Running ShortenNames', 0)
	bPrintLog('=====================================', 0)

	if len(sys.argv) < 2:
		print "   We need a hard-drive folder with .tif stacks as input"
		print "	  Usage: ./fiji-macosx bShortenName <full-path-to-folder>/"
		# Prompt user for a folder
		sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
		if not sourceFolder:
			return 0
	else:
		sourceFolder = sys.argv[1] #assuming it ends in '/'
	
	if not os.path.isdir(sourceFolder):
		bPrintLog('\nERROR: run() did not find folder: ' + sourceFolder + '\n',0)
		return 0

	runOneFolder(sourceFolder)

	bPrintLog('=====================================', 0)
	bPrintLog('Done ShortenNames', 0)
	bPrintLog('=====================================', 0)
        bPrintLog(' ', 0)

#
if __name__ == '__main__': 
	run()

