#Author: Robert H. Cudmore
#Date: June 2012
#
#Purpose: Prompt user for a source directory of .tif files
#make a destination directory 'channels8'
#save a copy of each .tif in source as 8-bit in destination
#

import os
from ij import IJ, ImagePlus
from ij.io import FileSaver  
import sys

# Expecting one argument: the file path
if len(sys.argv) < 2:
	print "ERROR: simple_batch.py error, we need at least one folder as input"
	print "   Usage: ./fiji-macosx <script-name> <file-path>"
	
	# PRompt the user for a folder
	sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()

	print "sourcefolder=" + sourceFolder

else:
	sourceFolder = sys.argv[1] #assuming it ends in '/' AND contains 'channels' folder

doDeinterleave = 1

destFolder = sourceFolder + "channels8/"

if not os.path.isdir(destFolder):
    os.makedirs(destFolder)

print "Processing folder=", sourceFolder  

for filename in os.listdir(sourceFolder):    
    if not filename.startswith("."):
    	if filename.endswith(".tif"):  
	    shortName, fileExtension = os.path.pslittext(filename)
	    outPath1 = destFolder + "/" + shortName + "_ch1" + ".tif"
	    outPath2 = destFolder + "/" + shortName + "_ch2" + ".tif"
	    
	    #before we open, check if eventual dest exists
	    #if os.path.exists(outPath):
	    #	print "Skipping file", filename, "eventual destination already exists"
	    #	continue #with next iteration
			
	    print "===================================="
	    print "Opening", sourceFolder+filename  
	    imp = IJ.openImage(sourceFolder + filename)
	    if imp is None:  
	        print "   Could not open image from file:", filename  
		continue   #with next iteration
		
	    imp.show()
		
	    print imp.getProperties()
		
	    print "   Image is: " + str(imp.width) + " X " + str(imp.height) + " X " + str(imp.getNSlices())
	    if imp.getBitDepth() == 16:
			
		print "   Converting to 8-bit..."
		IJ.run("8-bit")

		if doDeinterleave:
		    IJ.run("Deinterleave", "how=2"); #makes 2 window
		    
		#ch2
		if os.path.exists(outPath2):  
		    print "ch2 8 Bit File exists! Not saving the image!"  
		else:
		    imp2 = IG.getImage()
		    fs = FileSaver(imp2)
		    fs.saveAsTiffStack(outPath2):
		    print "8bit File saved to", outPath2
		    #
		    imp2.changes = 0
		    imp2.close()
			
	    else:
		print "File was not 16 bit???"
		
	    imp.hide()

    	else:  
	    print "Ignoring:", filename

print "batchConvertTo8Bitv2.py is Done"
