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
import sys
import re

#function to get user options
def getOptions():
	gd = GenericDialog("Options")
	gd.addNumericField("Number of channel", 2, 0) # show 0 decimals
	gd.addCheckbox("Replace Destination .tif files", 0)
	gd.addHelp("http://robertcudmore.org/software_index.html")
	gd.showDialog()

	if gd.wasCanceled():
		print "User cancelled dialog."
		return -1
	#read out options
	numberOfChannels = gd.getNextNumber()
	replaceExisting = gd.getNextBoolean()
	
	global numberOfChannels
	global replaceExisting

	return 1 #int(numberOfChannels)

def run():
	print "===== Batch Convert To 512x512 ====="

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

	#get user options
	okGo = getOptions() # creates {numberOfChannels, replaceExisting}
	if okGo == -1:
		return 0

	destFolder = sourceFolder + "channels8_512/"
	destMaxFolder = sourceFolder + "max/"

	#make destination directory
	if not os.path.isdir(destFolder):
		os.makedirs(destFolder)

	#make max destination directory
	if not os.path.isdir(destMaxFolder):
		os.makedirs(destMaxFolder)
	
	print "   Processing source folder: ", sourceFolder  
	print "   Saving to destination folder: ", destFolder  
	IJ.log("   ====== Starting Batch Convert To 512x512 ======")
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
			outPath = destFolder + "/" + filename
			outPath1 = destFolder + "/" + shortName + "_ch1" + ".tif"
			outPath2 = destFolder + "/" + shortName + "_ch2" + ".tif"

			#max projection output
			outMaxPath = destMaxFolder + "/" + "max_" + filename
			outMaxPath1 = destMaxFolder + "/" + "max_" + shortName + "_ch1" + ".tif"
			outMaxPath2 = destMaxFolder + "/" + "max_" + shortName + "_ch2" + ".tif"
			
			#before we open, check if eventual dest exists
			if not replaceExisting:
				if numberOfChannels == 2 and os.path.exists(outPath1) and os.path.exists(outPath2):
					msgStr = "   8-Bit Destination file exists, not processing the image:" + filename
					print msgStr
					IJ.log(msgStr)
					continue #with next iteration
				if numberOfChannels == 1 and os.path.exists(outPath):
					msgStr = "   8-Bit Destination file exists, not processing the image:" + filename
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
			#if imp.getBitDepth() == 16:
			if 1:
				msgStr = "      Converting to 512x512..."
				print msgStr
				IJ.log(msgStr)
				#IJ.run("8-bit")

				IJ.run("Size...", "width=512 height=512 constrain average interpolation=Bilinear")

				if numberOfChannels == 2:
					msgStr = "      deinterleaving"
					print msgStr
					IJ.run("Deinterleave", "how=2"); #makes 2 window
					
					#
					#ch2
					imp2 = IJ.getImage()
					fs = FileSaver(imp2)
					msgStr = "      ch2: Saving deinterleaved 8bit File to: " + outPath2
					print msgStr
					IJ.log(msgStr)

					numSlices = imp2.getNSlices() 
					if (numSlices>1):
						fs.saveAsTiffStack(outPath2)
					else:
						fs.saveAsTiff(outPath2)
						
					#max, ch2
					if (numSlices>1):
						maxCmdParams = 'start=1' + ' stop=' + str(numSlices) + ' projection=[Max Intensity]'
						IJ.run("Z Project...", maxCmdParams)
						#impMax2 = IJ.getImage()
						
					print "      Saving 8bit Max File to", outMaxPath2
					impMax2 = IJ.getImage()
					fs = FileSaver(impMax2)
					fs.saveAsTiff(outMaxPath2)
					
					impMax2.changes = 0
					impMax2.close()
					
					numSaved += 1
					imp2.changes = 0
					imp2.close()
					
					#
					#ch1
					imp1 = IJ.getImage()
					fs = FileSaver(imp1)
					msgStr = "      ch1: Saving deinterleaved 8bit File to" + outPath1
					print msgStr
					
					numSlices = imp1.getNSlices() 
					if (numSlices>1):
						fs.saveAsTiffStack(outPath1)
					else:
						fs.saveAsTiff(outPath1)

					#max, ch1
					if (numSlices>1):
						maxCmdParams = 'start=1' + ' stop=' + str(numSlices) + ' projection=[Max Intensity]'
						IJ.run("Z Project...", maxCmdParams)
					
					impMax1 = IJ.getImage()
					fs = FileSaver(impMax1)
					msgStr = "      Saving 8bit Max File to" + outMaxPath1
					print msgStr
					IJ.log(msgStr)
					fs.saveAsTiff(outMaxPath1)
					impMax1.changes = 0
					impMax1.close()

					numSaved += 1
					imp1.changes = 0
					imp1.close()
				
				elif numberOfChannels == 1: #single channel
					fs = FileSaver(imp)
					msgStr = "      Saving 8bit File to" + outPath
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
					print "      Saving 8bit Max File to", outMaxPath
					fs.saveAsTiff(outMaxPath)
					impMax.changes = 0
					impMax.close()

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

	msgStr = "   Batch Convert To 512x512 is Done, Number Opened " + str(numOpened) + ", Number Saved " + str(numSaved)
	print "   ==="
	print msgStr
	print "   ==="
	IJ.log(msgStr)

run()
