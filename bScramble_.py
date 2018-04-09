#!/usr/bin/env python2.7

"""
Author: Robert H Cudmore
Date: 20170807
email: cudmore@jhu.edu

Purpose:

	- For each file in a folder, make a copy with a scrambled name.
	- Print out the mapping from each source file to its new scrambled file name
	- Save the mapping from source file to scrambled file in a .txt file
  
	IMPORTANT: Be sure to keep the output so you can reverse the scramble back to the original name.
	
	20170811: Converted from pure Python to Jython to be run in Fiji
	
"""

import os, datetime
from shutil import copyfile
from random import sample
#from  Tkinter import *
#import Tkinter, Tkconstants, tkFileDialog

from ij import IJ
from ij.io import DirectoryChooser #, OpenDialog, FileSaver

#
# options
#
dstFolderName = 'scrambled'
dstFilePrefix = 's_'
maximumFiles = 9999
zeroPadding = len(str(maximumFiles))
#
#
#

def do_scramble(srcPath):

	#
	# make the output directory
	dstFolder = os.path.join(srcPath,dstFolderName)
	if not os.path.exists(dstFolder):
		os.makedirs(dstFolder)

	bPrintLog('   srcPath:' + srcPath)
	bPrintLog('   dstFolder:' + dstFolder)

	#
	# make a list of files we will scramble, skipping directories and files that start with '.'
	files = []
	for file in os.listdir(srcPath):
		filepath = os.path.join(srcPath,file)
		if not os.path.isfile(filepath) or file.startswith('.'):
			continue
		files.append(file)
	numfiles = len(files)

	#
	if numfiles > maximumFiles:
		print "=== ERROR: This script only works with a maximum of", maximumFiles, "files. Please modify 'maximumFiles' and try again."
		return 0
	#
	# generate a list of numfiles random numbers [0..myRange] without repeats
	scramblednumbers = sample(range(maximumFiles), numfiles)

	#
	# make a string of length zeroPadding from scrambled numbers
	scrambledstrings = [str(scramblednumber).zfill(zeroPadding) for scramblednumber in scramblednumbers]

	outLines = []
	
	#
	# copy each file in srcPath to a new scrambled name in dstFolder
	for i, file in enumerate(files):
	
		# source file we will copy
		src = srcPath + '/' + file
	
		# make the random str length zeroPAdding
		#randomStr = str(scramblednumbers[i])
		#randomStr = randomStr.zfill(zeroPadding)
	
		# get the base file name and file extension of file
		basefilename, file_extension = os.path.splitext(file)
	
		# destination file (has scrambled name)
		dstFile = dstFilePrefix + scrambledstrings[i] + file_extension
		dst = os.path.join(dstFolder, dstFile)
	
		outLine = 'file ' + str(i+1) + ' of ' + str(numfiles) + ', src:' + src + ', dst:' + dst
		print outLine
		bPrintLog(outLine)
		outLines.append(outLine)
		
		#
		# do the copy
		copyfile(src, dst)
	
	#
	# save results in a file in srcPath
	outfilelog = os.path.join(srcPath, 'scrambled_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S') + '.txt')
	print 'Saving output log file to:', outfilelog
	bPrintLog('Saving output log file to: ' + outfilelog)
	with open(outfilelog, "w") as outputFile:
		for line in outLines:
			outputFile.write(line + '\n')
    
	print '=== Done ======================================================================'
	bPrintLog('=== Done ======================================================================')
	
##################################################################################################
# utility
##################################################################################################
def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)

##################################################################################################
# main
##################################################################################################
if __name__ in ['__main__', '__builtin__']: 

	#
	# get the source folder from user
	#root = Tk()
	#root.directory = tkFileDialog.askdirectory(title='Please select a directory with your source files to scramble')
	#sourceFolder = root.directory

	bPrintLog('=== Start ======================================================================')
	bPrintLog('bScrample_.py was run on:' + str(datetime.datetime.now()))

	sourceFolder = DirectoryChooser("Please Choose A Directory Of .lsm Files").getDirectory()

	if sourceFolder:
		do_scramble(sourceFolder)
	