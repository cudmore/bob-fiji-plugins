#20161206
#Robert H. Cudmore

import bPrairie2Tif_
import bAlignFolder_
import bAverageFrames_
import bConvertTo8Bit_v5_
import bMaxProject_

if __name__ == '__main__': 
	startTime = time.time()
	
	bPrintLog('\n=================')
	bPrintLog('Starting bPrairieBatch')

	#ask user for folder, this is a folder that contains folders with single image .tif files
	sourceFolder = DirectoryChooser("Please Choose A Directory Of Prairie .tif Folders").getDirectory()

	# convert folders of single .tif images to single .tif file for each stack or time series
	numStackFolders, outFolder = prairie2tif.runOneMetaFolder(sourceFolder)

	# align
	alignFolder = bAlignFolder. bAlignFolder(outFolder)
	if alignFolder:
		alignFolder.run()
	outFolder = alignFolder.dstFolder

	# average
	tmpNum, outFolder = bAverageFrames.runOneFolder(outFolder)

	# convert to 8 bit
	#bConvertTo8Bit.gUseEnclosingFolderNameInOutputFolder = False
	tmpNum, outFolder = bConvertTo8Bit.runOneFolder(outFolder)

	# max project
	bMaxProject.gUseEnclosingFolderNameInOutputFolder = False
	tmpNum, outFolder = bMaxProject.runOneFolder(outFolder)
	
	# max project
	
	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds / 60.0, 2)
	bPrintLog('Finished bPrairieBatch with ' + str(numTif) + ' tif files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
	bPrintLog('=================\n')
