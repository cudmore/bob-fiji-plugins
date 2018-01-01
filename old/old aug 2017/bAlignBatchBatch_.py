#20161228
#Robert H Cudmore

# call bALignBatch on a number of folders
# requires a .txt file with each line is the full path to each folder

import os, sys, time
import glob

#imagej (java)
from ij import IJ
from ij.io import OpenDialog

sys.path.append('/Users/cudmore/Dropbox/bob_fiji_plugins')
import bAlignBatch_v7_2 as bAlignBatch


#
# the full hard-drive path to each folder
folders = []
folders.append('/Volumes/fourt/MapManager_Data/richard/Nancy/a73mm/raw/')
folders.append('/Volumes/fourt/xxx')
folders.append('/Volumes/fourt/MapManager_Data/richard/Nancy/rr50b/raw')


#
# the options for bALignBatch ( all .tif files in each folder MUST be the same !!!!)
bAlignBatch.gFileType = 'tif'
bAlignBatch.gGetNumChanFromScanImage = 0
bAlignBatch.gNumChannels = 2
bAlignBatch.gDoAlign = 0 # turn on to do alignment
bAlignBatch.gAlignThisChannel = 2

#utility
def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)

#
# load text file where each line is full path to folder to run

# open text file and populate list with full path to each folder
def openTextFile():
	pass

# open a text file and poluate a list of folder paths
def opentextfile(srcFile):
	# check that file exists
	
	file = open(srcFile, 'r')
	lines = file.readlines()
	bPrintLog('source file ' + srcFile + ' has ' + str(len(lines)) + ' lines', 0)
	print lines
	for line in lines:
		print line
	
# main
def run():
	# print out the options we will use
	bPrintLog('Option will be applied to ALL .tif stacks', 0)
	bPrintLog('bAlignBatch.gFileType=' + str(bAlignBatch.gFileType), 1)
	bPrintLog('bAlignBatch.gGetNumChanFromScanImage=' + str(bAlignBatch.gGetNumChanFromScanImage), 1)
	bPrintLog('bAlignBatch.gNumChannels=' + str(bAlignBatch.gNumChannels), 1)
	bPrintLog('bAlignBatch.gDoAlign=' + str(bAlignBatch.gDoAlign), 1)
	bPrintLog('bAlignBatch.gAlignThisChannel=' + str(bAlignBatch.gAlignThisChannel), 1)
	
	numFolders = len(folders)
	i = 1
	for folder in folders:
		# make sure folder ends in '/'
		if not folder.endswith('/'):
			folder += '/'
			
		# check if folder exists
		if not os.path.isdir(folder):
			# error
			bPrintLog('---',0)
			bPrintLog(time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),0)
			bPrintLog("Error: bAlignBatchBatch.run() did not find folder: '" + folder + "'", 0)
			bPrintLog('---',0)
			continue

		# print out all .tif files in folder
		tifList = glob.glob(folder + '*')
		numTif = len(tifList)
		bPrintLog(time.strftime('%a, %d %b %Y %H:%M:%S', time.localtime()),1)
		bPrintLog('[Folder ' + str(i) + ' of ' + str(numFolders) + '] with ' + str(numTif) + ' tif files in folder ' + folder, 1)
		for tif in tifList:
			bPrintLog(tif, 2)
			
		# do it
		bPrintLog('=== bALignBatchBatch is starting alignment on all stacks in folder: ' + folder, 2)
		#bALignBatch.runOneFolder(folder)

		i += 1

	bPrintLog('bAlignBatchBatch done at', 0)
#
if __name__ == '__main__': 

	srcDir = OpenDialog('Select a text file with your folders to batch process')
	print srcDir
	if srcDir:
		print srcDir.getDirectory()
		print srcDir.getFileName()
		fullPath = srcDir.getDirectory() + srcDir.getFileName()
		opentextfile(fullPath)
		# run()
	else:
		bPrintLog('Cancelled by user', 0)
		