import os, sys
from ij import IJ, ImagePlus, ImageStack
from ij.plugin import ZProjector
from ij.gui import GenericDialog  

#Author: Robert H. Cudmore
#Web: http://robertcudmore.org
#Date: November 3, 2012
#
# Input: A 3D stack
# Output: A 3D stack (same size as input) where each slice
#         is a z-projection around the original slice
#
# Algorithm
#Step through all slices of a stack and make a small sliding z-projection at each slice
#
# Options
# The size of the sliding z-projection is set in a user dialog (userSlices)
# Specify userSlices=0 and the output shoulld be the same as the input

#function to get user options
def getOptions():
	gd = GenericDialog("Option")
	gd.addNumericField("Sliding Z Projection Slices", 5, 0) # show 0 decimals
	gd.addHelp("http://www.robertcudmore.org/software/bSliding_Z_Projection.html")
	gd.showDialog()

	if gd.wasCanceled():
		print "User cancelled dialog."
		return
	#read out options
	userSlices = gd.getNextNumber()
	return int(userSlices)


# get the current dispayed image by
imp = WindowManager.getCurrentImage()

if imp==None:
	print "We need a stack"
	IJ.log("'Sliding Z Projection' did not find an open stack.")
	sys.exit(1)

#get user input
options = getOptions()
if options is None:
	IJ.log("User aborted bzProject.")
	sys.exit(1)

if options is not None:
	userSlices = options
	
origStack = imp.getStack()
#stack = imp.getStack() # get the stack within the ImagePlus
nSlices = imp.getNSlices() # get the number of slices

currStart = 1
currStop = 1 + userSlices

#method = ZProjector.MAX_METHOD

#make the output stack
newStack = ImageStack(imp.width, imp.height)

#index starts at 1
for index in range(1, nSlices+1):
	ip = origStack.getProcessor(index)    
	
	#IJ.log(str(index) + " " + ip.toString()) # output info on current slice
	#IJ.run(imp, "Z Project...", "start=" + str(currStart) + " stop=" + str(currStop) + " projection=[Max Intensity]")

	#print "index=" + str(index) + "start=" + str(currStart) + " stop=" + str(currStop)
	
	if (currStart<1):
		currStart = 1
	if (currStop>nSlices):
		currStop = nSlices
	
	zp = ZProjector(imp)
	zp.setMethod(ZProjector.MAX_METHOD)
	zp.setStartSlice(currStart)
	zp.setStopSlice(currStop)
	#zp.doHyperStackProjection(True)
	
	zp.doProjection()
	tmpProject = zp.getProjection()
	zImageProcessor = tmpProject.getProcessor()
	
	if (tmpProject==None):
		print "\tNULL ZProject"
	else:
		newStack.addSlice(origStack.getSliceLabel(index), zImageProcessor)
		
	currStart = index - userSlices
	currStop = index + userSlices

#how the results as an image
imp2 = ImagePlus("Sliding Z Project: " + imp.title + " " + "[" + str(userSlices) + "]", newStack)
imp2.setCalibration(imp.getCalibration().copy()) 
imp2.show()

doHist = 0
if doHist==1:
	IJ.run(imp, "Histogram", "stack")

