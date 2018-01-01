#Author: Robert H. Cudmore
#Web: http://robertcudmore.org
#Date: February 2013
#
#Purpose
#Take a directory of .tif, load all files and append/concatenate all together into one stack
#
#run multistackreg on concatenated stack
#split files back into original
#save new copies of aligned files in /aligned
#
#(1) open a directory of .tif stack into one hyperstack
#

import os
import sys
from ij import IJ, ImagePlus
from ij.io import Opener
from ij.plugin import Concatenator #see: http://cmci.embl.de/documents/120206pyip_cooking/python_imagej_cookbook
from jarray import array

def myPrint(theStr):
	print theStr
	IJ.log(theStr)
	#return 1
	
def run():
	myPrint("=== bConcatALign ===")
	
	#get source folder
	if len(sys.argv) < 2:
		#from user
		sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
		if not sourceFolder:
			myPrint('   Aborted by user')
			return
	else:
		#from command line
		sourceFolder = sys.argv[1] #assuming it ends in '/'

	destFolder = sourceFolder + "channels8/"

	#a list of file names
	fileList = []
	sliceList = []
	
	timeseries = []
	
	#ccc = Concatenator()

	#i = 0
	
	for filename in os.listdir(sourceFolder):	
		startWithDot = filename.startswith(".")
		isMax = filename.endswith("max.tif")
		isTif = filename.endswith(".tif")

		if (not startWithDot) and (not isMax) and (isTif):
			myPrint(filename)
			fullPath = sourceFolder + filename
			shortName, fileExtension = os.path.splitext(filename)

			fileList.append(filename)
			#get x/y/z dims and append to list

			#imp = Opener.openUsingBioFormats(fullPath) #not working
			imp = IJ.openImage(sourceFolder + filename)
			imp.setOpenAsHyperStack(False)
			timeseries.append(imp)

			#if (i==0):
			#	mergedImp = imp
			#else:
			#	print i
			#	ccc.concatenate(mergedImp, imp, True)
			#
			#i += 1
			
	calib = timeseries[0].getCalibration()
	dimA = timeseries[0].getDimensions()
	#why doesn't this fucking work !!!!!!!!!!!!!!!!!!
	#infoProp = timeseries[0].getInfoProperty()
	
	#print calib
	#print dimA
	#print infoProp
	
	jaimp = array(timeseries, ImagePlus)
	ccc = Concatenator()
	allimp = ccc.concatenate(jaimp, False)
	#allimp.setDimensions(dimA[2], dimA[3], len(GRlist))
	allimp.setCalibration(calib)
	allimp.setOpenAsHyperStack(True)
	allimp.show()

run()