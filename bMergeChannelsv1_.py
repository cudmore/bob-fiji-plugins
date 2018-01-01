#import os, sys
from ij import IJ, ImagePlus, ImageStack, CompositeImage
from ij3d import Image3DUniverse, Content
from java.lang.System import getProperty
#import vib.PointList

from org.scijava.vecmath import Color3f, Point3f

from ij.measure import Calibration
from ij.plugin.frame import RoiManager
from ij.gui import GenericDialog, OvalRoi #PointRoi
from ij.io import OpenDialog

def options():
	gd = GenericDialog('bMergeChannelsv1 Options')
	defaultVal = 1
	gd.addCheckbox('Add points to ROI Manager', defaultVal)
	defaultVal = 1
	gd.addCheckbox('Add points to 3D Universe', defaultVal)

	gd.showDialog()

	if gd.wasCanceled():
		print 'Options Was Cancelled by user'
		return None
	else:
		print 'Reading values'
		doROI = gd.getNextBoolean()
		do3d = gd.getNextBoolean()

		theRet = {}
		theRet['doroi'] = doROI
		theRet['do3d'] = do3d
		return theRet
		
def myRun():
	print "===Starting bMergeChannels_"

	theOptions = options()
	if theOptions is None:
		return 0
	
	fileObj = OpenDialog("")
	userFileName = fileObj.getFileName()
	userFileDir = fileObj.getDirectory()
	userFilePath = fileObj.getPath()
	print 'userFilePath:', userFilePath
	
	file = open(userFilePath, "r")
	
	#open text file that gives us a list of images (for now it will be 2)
	#pluginDir = getProperty("fiji.dir") + "/plugins/bob-fiji-plugins/"
	#file = open(pluginDir + "bMergeChannels.txt", "r")
	
	do3d = 0
	doComposite = 0
	pointList = [] #list of spine points
	cPointList = [] #list of connection points
	lPointList = [] #list of backbone centerline points
	doROI = 0
	
	for line in file.readlines():
		currLine = line.strip()
		#print currLine
		token, value = currLine.split("=")
		
		if currLine.startswith('file1'):
			filepath1 = value
		if currLine.startswith('file2'):
			filepath2 = value
		if currLine.startswith('x'):
			voxelx = value
		if currLine.startswith('y'):
			voxely = value
		if currLine.startswith('z'):
			voxelz = value
		if currLine.startswith('do3d'):
			do3d = int(value)
		if currLine.startswith('doComposite'):
			doComposite = int(value)
		if currLine.startswith('doROI'):
			doROI = int(value)
		if currLine.startswith('sPoint'):
			#x, y, z = value.split(",")
			pointList.append(value)
		if currLine.startswith('cPoint'):
			#x, y, z = value.split(",")
			cPointList.append(value)
		if currLine.startswith('lPoint'):
			#x, y, z, ID = value.split(",")
			lPointList.append(value)
			
	file.close()
	
	doROI = theOptions['doroi']
	do3d = theOptions['do3d']
	
	print "\tfilepath1: " + filepath1
	print "\tfilepath2: " + filepath2
	print "\tVoxel Size: " + str(voxelx) + " " + str(voxely) + " " + str(voxelz)
	print "\tdo3d: " + str(do3d)
	print "\tdoComposite: " + str(doComposite)
	
	#calibrate the image we are making
	myCalibration = Calibration()
	myCalibration.setUnit("um")
	myCalibration.pixelWidth = float(voxelx)
	myCalibration.pixelHeight = float(voxely)
	myCalibration.pixelDepth = float(voxelz)
	
	if doComposite==1:
		print "Opening 2-channel composite"
		print "\t" + filepath1
		print "\t" + filepath1
		#open the images
		imp1 = IJ.openImage(filepath1)
		imp2 = IJ.openImage(filepath2)
		
		#get their stacks (not sure why Fiji makes us do this?)
		stack1 = imp1.getImageStack()
		stack2 = imp2.getImageStack()
		
		#this is te destination (we will display as composite)
		newStack = ImageStack(imp1.width, imp1.height)
		
		#fuse the 2 stacks inter intwoven stack
		for i in xrange(1, imp1.getNSlices()+1):
		  # Get the ColorProcessor slice at index i
		  cp1 = stack1.getProcessor(i)
		  cp2 = stack2.getProcessor(i)
		  # Add both to the new stack
		  newStack.addSlice(None, cp1)
		  newStack.addSlice(None, cp2)
		
		# Create a new ImagePlus with the new stack newStack
		newImp = ImagePlus("my composite", newStack)
		newImp.setCalibration(imp1.getCalibration().copy())
		
		# Tell the ImagePlus to represent the slices in its stack
		# in hyperstack form, and open it as a CompositeImage:
		nChannels = 2             # two color channels
		nSlices = stack1.getSize() # the number of slices of the original stack
		nFrames = 1               # only one time point 
		newImp.setDimensions(nChannels, nSlices, nFrames)
		comp = CompositeImage(newImp, CompositeImage.COMPOSITE)
		comp.show()
	
		imp1 = comp
	else:
		print "Opening single channel:"
		print "\t" + filepath1
		imp1 = IJ.openImage(filepath1)
				
		imp1.show()
	
		# addvoltex was complainnig about imp?
		print "converting to 8-bit. addvoltex was complaining. This is not acceptable. This is why we don't use Fiji"
		IJ.run("8-bit")
	
	imp1.setCalibration(myCalibration)
	
	if imp1 is None:
		print "ERROR: BAD imp1, nothing else will work."
	
	#add sPoint list to ROI (don't add cPoint list for now)
	if doROI==1:
		#see: http://fiji.sc/Tips_for_developers#Interact_with_the_ROI_manager
		print "building roi list from stackdb object"
		manager = RoiManager.getInstance()
		if (manager == None):
			manager = RoiManager()
		RoiManager(False) #show the roi manager window, wierd interface
		i = 1
		for currPoint in pointList:
			#print "point " + str(i)
			x, y, z = currPoint.split(",")
			
			#composite is interleaved with ch1/ch2
			#if doComposite==1:
			#	z *= 2
			
			#a point roi (This seems to be in pixels???)
			#pROI = PointRoi(int(x), int(y), imp1)
			width = 5
			height = 5
			pROI = OvalRoi(int(x), int(y), width, height, imp1)
			
			imp1.setSliceWithoutUpdate(int(z))
			manager.add(imp1, pROI, int(z)) #add WITH slice, I want the pROI to be a 3D point
			#manager.addRoi(pROI) #add WITHOUT slice
			i += 1
		print "added " + str(i) + " pnts to roi manager"
		
	if do3d==1:
		#see: http://www.ini.uzh.ch/~acardona/fiji-tutorial/
		ps = [] #list of Point3f (pointList)
		cps = [] #list of Point3f of connection points (cPointList)
		lps = [] #list of backbone centerline points (lPointList)
		
		#print "Setting Spine Points..."
		for currPoint in pointList:
			x, y, z = currPoint.split(",")
			x = float(x) * float(voxelx)
			y = float(y) * float(voxely)
			z = float(z) * float(voxelz)
			p = Point3f(x, y, z)
			#p.scale(cal.pixelWidth * 1/scale2D)
			ps.append(p)
	
		#print "Setting Connection Points..."
		for currPoint in cPointList:
			x, y, z = currPoint.split(",")
			x = float(x) * float(voxelx)
			y = float(y) * float(voxely)
			z = float(z) * float(voxelz)
			p = Point3f(x, y, z)
			#p.scale(cal.pixelWidth * 1/scale2D)
			cps.append(p)
			
		#print "Setting Backbone Line Points..."
		lastID = 0
		lps.append([]) # lps is a list of lists, first list of ID
		for currPoint in lPointList:
			x, y, z, currID = currPoint.split(",")
			currID = int(currID)
			x = float(x) * float(voxelx)
			y = float(y) * float(voxely)
			z = float(z) * float(voxelz)
			p = Point3f(x, y, z)
			if currID != lastID:
				lps.append([])
			#p.scale(cal.pixelWidth * 1/scale2D)
			lps[currID].append(p)
	
		print "Building 3d..."
		
		cell_diameter = 0.6 #right now in pixels, eventually in um

		#we will fail here if imp1 is NOT 8 bit
		univ = Image3DUniverse()
		imageContent = univ.addVoltex(imp1) #.setLocked(True)
		imageContent.setLocked(True)
		
		#spine
		pointContent = univ.addIcospheres(ps, Color3f(1, 1, 0), 2, cell_diameter, "Spines")
		pointContent.setLocked(True)
	
		#put back in
		#connection
	    	#cPointContent = univ.addIcospheres(cps, Color3f(1, 0, 0), 2, cell_diameter, "cPoints")
		#cPointContent.setLocked(True)
		
		#pointContent = univ.addPointMesh(ps, Color3f(1, 1, 0), cell_diameter, "Spines")
		#univ.addOrthoslice(imp1).setLocked(True)
	
		#put back in
		#centerline
		for i, segment in enumerate(lps):
			meshName = 'lPoint_' + str(i)
			lPointContent = univ.addLineMesh(segment, Color3f(1, 0, 0), meshName, True) # True specifies a 'strip line'
			lPointContent.setLocked(True)
		#lPointContent.setLandmarkPointSize(20)
		
		univ.show()
	
		#set image transparency to 40% so we can see our pointContent
		imageContent.setTransparency(0.4)
		
		#see: http://fiji.sc/Jython_Scripting
		
	print '=== bMergeChannels_ is finished.'

if __name__ == '__main__':
	myRun()
	