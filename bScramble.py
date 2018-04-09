#!/usr/bin/env python2.7

"""
Author: Robert H Cudmore
Date: 20170807
email: cudmore@jhu.edu

Purpose:
 - For each file in a folder, make a copy with a scrambled name.
 - Print out the mapping from each source file to its new scrambled file name
 - Save the mapping from source file to scrambled file in a .txt file

Important:
 - Be sure to keep the output .txt file so you can reverse the scramble back to the original name.
 - This does not modify source files, it makes COPIES in a new folder
 - File names may be duplicated when you run multiple times (on multipe folders).
    If you are going to try and merge the output later, some files may have the same name.
    It is best to merge files into one folder BEFORE running bScramble.py
	
Changes:
 - 20170811: Converted from pure Python to Jython to be run in Fiji
 - 20180110: switched back to pure Python

Todo:
 - Make the script take a folder at the command line
     Currently, we are having user select a folder manually with a dialog.
 - [Done] Change code so we save output .txt file as we go.
     Currently, if user aborts with ctrl+c the output .txt file is NOT saved.
 - [Done] Make output .txt file name contain name of enclosing folder
     Currently, output .txt file is always named scrambled_<YYMMDD_HHMMSS>.txt
 - [Done] Make output folder have name of source folder in it
     Currently, output folder is always named 'scrambled'
     
 
"""

from __future__ import print_function
import sys # for command lines in sys.argv
import os, datetime
from shutil import copyfile
from random import sample
from  Tkinter import *
import Tkinter, Tkconstants, tkFileDialog

#
# options
#
dstFilePrefix = 's_'
maximumFiles = 9999
includeSourceFolderInOutputName = False
#
#
#

zeroPadding = len(str(maximumFiles))

def do_scramble(srcPath):

	enclosingFolder = os.path.basename(srcPath)
	if includeSourceFolderInOutputName:
		dstFolderName = enclosingFolder + "-scrambled"
	else:
		dstFolderName = 'scrambled'
		
	#
	# make the output directory
	dstFolder = os.path.join(srcPath,dstFolderName)
	if not os.path.exists(dstFolder):
		os.makedirs(dstFolder)

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
		print("=== ERROR: This script only works with a maximum of", maximumFiles, "files. Please modify 'maximumFiles' and try again.")
		return 0
		
	#
	# generate a list of numfiles random numbers [0..myRange] without repeats
	# When this script is run multiple times, this list will sometimes have names from previous run
	scramblednumbers = sample(range(maximumFiles), numfiles)

	#
	# make a string of length zeroPadding from scrambled numbers
	scrambledstrings = [str(scramblednumber).zfill(zeroPadding) for scramblednumber in scramblednumbers]

	if includeSourceFolderInOutputName:
		outfilelog = os.path.join(srcPath, enclosingFolder + '-scrambled-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.txt')
	else:
		outfilelog = os.path.join(srcPath, 'scrambled-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + '.txt')
	
	#
	# copy each file in srcPath to a new scrambled name in dstFolder
	for i, file in enumerate(files):		
		# source file we will copy
		src = srcPath + '/' + file
	
		# get the base file name and file extension of file
		basefilename, file_extension = os.path.splitext(file)
	
		# destination file (has scrambled name)
		dstFile = dstFilePrefix + scrambledstrings[i] + file_extension
		dst = os.path.join(dstFolder, dstFile)
	
		outLine =  'src:' + src + ', dst:' + dst
		feedback = 'file ' + str(i+1) + ' of ' + str(numfiles) + ', ' + outLine
		print(feedback)
		
		# save output .txt file as we go
		with open(outfilelog, "a") as outputFile:
			outputFile.write(outLine + '\n')
		#
		# do the copy
		copyfile(src, dst)
	
##################################################################################################
# main
##################################################################################################
if __name__ in ['__main__', '__builtin__']: 

	#
	# get the source folder from user
	root = Tk()
	root.withdraw()
	root.directory = tkFileDialog.askdirectory(title='Please select a directory with your source files to scramble')
	root.update()
	sourceFolder = root.directory

	do_scramble(sourceFolder)
	
	print('=== Done ======================================================================')
	