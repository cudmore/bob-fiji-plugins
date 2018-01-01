#20160913
#Robert H. Cudmore

#imagej (java)
from ij import IJ
from ij import WindowManager, ImagePlus, ImageStack
from ij.io import DirectoryChooser, FileSaver
from ij.process import ImageConverter # default convert to 8-bit will scale. Turn it off. See: https://ilovesymposia.com/2014/02/26/fiji-jython/
from ij.gui import GenericDialog

#python
import os, sys, time
from os.path import basename
import xml.etree.ElementTree as ET

sys.path.append('/Users/cudmore/Dropbox/bob_fiji_plugins')
import bPrairie2tif_ as bPrairie2tif
import bAlignFolder_ as bAlignFolder

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

folderList = []
folderList.append('/Volumes/t3/data/2016/11/20161118/20161118_a190b/')
folderList.append('/Volumes/t3/data/2016/11/20161119/20161119_a188/')
folderList.append('/Volumes/t3/data/2016/11/20161119/20161119_a189/')
folderList.append('/Volumes/t3/data/2016/11/20161122/20161122_a189/')
folderList.append('/Volumes/t3/data/2016/11/20161123/20161123_a189b/')

'''
Main
'''
if __name__ == '__main__': 

	# to do, allow user to specify a folder of folders
	
	bPrintLog('\n=================')
	bPrintLog('Starting bPrairieBatch')

	startTime = time.time()
	numStackFolders = 0

	bPrairie2tif.globalOptions['medianFilter'] = 3
	bPrairie2tif.globalOptions['convertToEightBit'] = True

	bAlignFolder.globalOptions['alignThisChannel'] = 2
	bAlignFolder.globalOptions['medianFilter'] = 0 # set to 0 for no median filter

	i = 1
	
	for folder in folderList:

		bPrintLog('===',0)
		bPrintLog('   ' + time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()), 0)
		bPrintLog('   bPrairieBatch is processing ' + str(i) + ' of ' + str(len(folderList)) + 'folder:' + folder, 0)
		bPrintLog('===',0)

		# convert prairie to tif
		tmpNum, dstFolder = bPrairie2tif.runOneMetaFolder(folder)
		numStackFolders += tmpNum
		
		# align
		alignFolder = bAlignFolder.bAlignFolder(dstFolder, alignmentChannel=2)
		if alignFolder:
			alignFolder.run()

		i += 1
		
	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds / 60.0, 2)
	bPrintLog('Finished bPrairieBatch with ' + str(numStackFolders) + ' files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
	bPrintLog('=================\n')
	