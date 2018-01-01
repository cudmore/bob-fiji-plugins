#Author: Robert H. Cudmore
#Web: http://robertcudmore.org
#Date: August 2014
#
#THIS IS A QUICK MODIFICATION TO 'Batch Convert To 8 Bit'
#IT HAS NOT BEEN TESTED AND IS BEING USED BY BOB FOR HIS WORK
#
#Purpose: Prompt user for a source directory of .tif files
#make a destination directory 'channels8'
#save a copy of each .tif in source as 8-bit in destination
#
#Usage:
#Set numberOfChannels=1 if each stack is a single channel
#Set numberOfChannels=2 and we will deinterleave and make _c1/_ch2 pair
#
#
#Bug Fixes:
#20140322: When saving a single slice, removed a dialog warning 'This is not a stack'
#20131212: This macro is now part of bob-fiji-plugin GitHub repository
#
#
#to do:
#(1) Get tif tags with imp.getProperties(), how do i set them?
#	  only way i can see is looping through all {key,value} pairs?
#
#

import os
from ij import IJ, ImagePlus
from ij.io import FileSaver  
from ij.process import StackStatistics
import math
import sys
import re

def run():
	print "===== Batch Convert Scan Image 4 ====="

	# Expecting one argument: the file path
	if len(sys.argv) < 2:
		print "   We need a hard-drive folder with .tif stacks as input"
		print "	  Usage: ./fiji-macosx bBatchConvertTo8Bitv3 <folder-path>/"

		# Prompt user for a folder
		sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
		if not sourceFolder:
			return
	else:
		sourceFolder = sys.argv[1] #assuming it ends in '/'

	destFolder = sourceFolder + "scanimage4/"
	destMaxFolder = destFolder + "max/"

	#make destination directory
	if not os.path.isdir(destFolder):
		os.makedirs(destFolder)

	#make max destination directory
	if not os.path.isdir(destMaxFolder):
		os.makedirs(destMaxFolder)
	
	print "   Processing source folder: ", sourceFolder  
	print "   Saving to destination folder: ", destFolder  
	IJ.log("   ====== Starting Batch Convert Scan Image 4 ======")
	IJ.log("   Processing source folder: " + sourceFolder)
	IJ.log("   Saving to destination folder: " + destFolder)

	numOpened = 0
	numSaved = 0

	for filename in os.listdir(sourceFolder):	
		startWithDot = filename.startswith(".")
		isMax = filename.endswith("max.tif")
		isTif = filename.endswith(".tif")

		if (not startWithDot) and (not isMax) and (isTif):
			shortName, fileExtension = os.path.splitext(filename)
			
			#source .tif output (after conversion)
			outPath = destFolder + filename

			#max projection output
			outMaxPath = destMaxFolder + "max_" + filename
			
			#before we open, check if eventual dest exists
			if os.path.exists(outPath):
				msgStr = "   Destination file exists, not processing the image:" + filename
				print msgStr
				IJ.log(msgStr)
				continue #with next iteration
			
			print "   ===================================="
			msgStr = "   -> Opening " + sourceFolder+filename  
			print msgStr
			IJ.log(msgStr)
			imp = IJ.openImage(sourceFolder + filename)
			if imp is None:  
				msgStr = "	     ERROR: Could not open image from file: " + filename  
				print msgStr
				IJ.log(msgStr)
				continue   #with next iteration
			
			imp.show()
			numOpened +=1

			msgStr = "      Original Image is: " + str(imp.width) + " X " + str(imp.height) + " X " + str(imp.getNSlices())
			print msgStr
			IJ.log(msgStr)
			if 1:
				msgStr = "      Removing Calibration From ScanImage 4 .tif"
				print msgStr
				IJ.log(msgStr)

				#20140810, I CAN'T BELIEVE I FINALLY FOUND THIS !!!
				infoStr = imp.getProperty("Info")
				#print infoStr

				#scanimage4 has a linear Calibration Function: y = a+bx
				#  a: -32768.000000
				#  b: 1.000000
				#  Unit: "Gray Value"
				#for some reason scanimage4 is setting a linear image calibration, we see negative values but there are NOT there
				cal = imp.getCalibration()
				calCoeff = cal.getCoefficients()
				msgStr = '        calibration is y=ax+b' + ' a=' + str(calCoeff[0]) + ' b=' + str(calCoeff[1])
				print msgStr
				IJ.log(msgStr)

				#append calibration to info string
				imp.setCalibration(None)
				infoStr += 'calibCoeff_a = ' + str(calCoeff[0]) + '\n'
				infoStr += 'calibCoeff_b = ' + str(calCoeff[1]) + '\n'

				#i have appended to Info, update it
				#found this burried here: http://code.google.com/p/fiji-bi/source/browse/ij/ImagePlus.java?repo=imageja&name=imagej
				imp.setProperty("Info", infoStr);

				#get and print out min/max
				theMin = StackStatistics(imp).min
				theMax = StackStatistics(imp).max
				msgStr = '        min=' + str(theMin) + ' max=' + str(theMax)
				print msgStr
				IJ.log(msgStr)

				#subtract the linear calibration slope 'a' (what about intercept 'b' ?)
				#coefficient 'a' is normally negative, this is what we are using 'Add'
				#run("Subtract...", "value=32768 stack");
				subArgVal = 'value=%s stack' % (calCoeff[0],)
				IJ.run('Add...', subArgVal)
				
				#save file
				fs = FileSaver(imp)
				msgStr = "      Saving File to" + outPath
				print msgStr
				IJ.log(msgStr)
					
				numSlices = imp.getNSlices() 

				if (numSlices>1):
					fs.saveAsTiffStack(outPath)
				else:
					fs.saveAsTiff(outPath)
				numSaved += 1

				#max
				if (numSlices>1):
					maxCmdParams = 'start=1' + ' stop=' + str(numSlices) + ' projection=[Max Intensity]'
					IJ.run("Z Project...", maxCmdParams)
				
				impMax = IJ.getImage()
				fs = FileSaver(impMax)
				print "      Saving Max File to", outMaxPath
				fs.saveAsTiff(outMaxPath)
				
				#close max
				impMax.changes = 0
				impMax.close()
				
				#close original
				imp.changes = 0
				imp.close()

			else:
				print "   File was not 16 bit???"
			
			imp.close() #close original

		else:  
			if (not startWithDot) and isTif:
				#print "   ===================================="
				print filename
				msgStr = "   -> Ignoring .tif:" + filename
				print msgStr
				IJ.log(msgStr)

	msgStr = "   Batch Convert Scan Image 4 is Done, Number Opened " + str(numOpened) + ", Number Saved " + str(numSaved)
	print "   ==="
	print msgStr
	print "   ==="
	IJ.log(msgStr)

run()
