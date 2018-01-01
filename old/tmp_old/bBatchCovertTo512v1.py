#Author: Robert H. Cudmore
#Web: http://robertcudmore.org
#Date: August 2013
#
#Purpose: Prompt user for a source directory of .tif files
#make a destination directory 'channels8'
#save a copy of each .tif in source as 8-bit in destination
#
#Set numberOfChannels=2 and we will deinterleave and make _c1/_ch2 pair
#
#to do:
#(3) i can get tif tags with imp.getProperties(), how do i set them?
#	  only way i can see is looping through all {key,value} pairs?
#
# this is now part of bob-fiji-plugin GitHub repository
#

import os
from ij import IJ, ImagePlus
from ij.io import FileSaver  
import sys

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
	print "===== bBatchConvertTo8Bitv3 ====="

	# Expecting one argument: the file path
	if len(sys.argv) < 2:
		print "   We need at least one folder as input"
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

	destFolder = sourceFolder + "channels8_256/"

	#make destination directory
	if not os.path.isdir(destFolder):
		os.makedirs(destFolder)

	print "   Processing source folder: ", sourceFolder  
	print "   Saving to destination folder: ", destFolder  

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
			
			#before we open, check if eventual dest exists
			if not replaceExisting:
				if numberOfChannels == 2 and os.path.exists(outPath1) and os.path.exists(outPath2):
					print "   512 Destination file exists, not saving the image.", filename
					continue #with next iteration
				if numberOfChannels == 1 and os.path.exists(outPath):
					print "   512 Destination file exists, not saving the image.", filename
					continue #with next iteration
			
			print "   ===================================="
			print "   -> Opening", sourceFolder+filename  
			imp = IJ.openImage(sourceFolder + filename)
			if imp is None:  
				print "	     Could not open image from file:", filename  
				continue   #with next iteration
			
			imp.show()
			numOpened +=1
			
			#i can get properties as long list of {key=value}
			#how do i then set each property in new imp1/imp2? Do IJ.openImagehave ot loop?
			#print imp.getProperties()

			#in the future IJ.openImagehavewant to have option to scale down to 512X512
			#run("Scale...", "x=- y=- z=1.0 width=512 height=512 depth=196 interpolation=Bilinear average process create title=20131007_a144_008_ch1-1.tif");

			print "      Image is: " + str(imp.width) + " X " + str(imp.height) + " X " + str(imp.getNSlices())
			#if imp.getBitDepth() == 16:
			if imp.width>512 and imp.height>512:
				print "      Converting to 512X512 with 'Scale'"
				#IJ.run("8-bit")
				theTitle = "tmpOutput"
				IJ.run(imp, "Scale...", "x=- y=- z=1.0 width=512 height=512 depth=" + str(imp.getNSlices()) + " interpolate=Bilinear average process create title=" + theTitle)
				imp = IJ.getImage() 

				#bug: original window is left open
				
				if numberOfChannels == 2:
					print "      deinterleaving"
					IJ.run("Deinterleave", "how=2"); #makes 2 window
					
					#ch2
					imp2 = IJ.getImage()
					fs = FileSaver(imp2)
					print "      Saving 8bit File to", outPath2
					fs.saveAsTiffStack(outPath2)
					numSaved += 1
					imp2.changes = 0
					imp2.close()
					
					#ch1
					imp1 = IJ.getImage()
					fs = FileSaver(imp1)
					print "      Saving 8bit File to", outPath2
					fs.saveAsTiffStack(outPath1)
					numSaved += 1
					imp1.changes = 0
					imp1.close()
				elif numberOfChannels == 1: #single channel
					fs = FileSaver(imp)
					print "      Saving 8bit File to", outPath
					fs.saveAsTiffStack(outPath)
					numSaved += 1
					imp.changes = 0
					imp.close()

			else:
				print "   File was not larger than 512X512???"
			
			imp.close() #close original

		else:  
			if isTif:
				#print "   ===================================="
				print "   -> Ignoring .tif:", filename

	print "   ==="
	print "   bBatchConvertTo8Bitv3.py is Done, Number Opened " + str(numOpened) + ", Number Saved ", str(numSaved)
	print "   ==="

run()
