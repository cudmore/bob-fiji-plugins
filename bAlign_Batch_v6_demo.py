#
#   Author: Robert H Cudmore
#   web: http://www.robertcudmore.org
#
#   - This is a tutorial on how to write your own Fiji Jython code and call bAlign_Batch_v6.py
#   - You need to turn different sections on/off with
#       'if 0:' to turn section off
#       'if 1:' to turn section on
#   - This is Jython code to be run as a Fiji plugin.
#

import bAlign_Batch_v6 as bab

print 'starting bAlign_Batch_v6_demo'

#
#run on one folder
if 0:
	sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
	if not sourceFolder:
		exit(1)
	if bab.Options(sourceFolder):
		bab.runOneFolder(sourceFolder)

#
#run on one file
if 0:
	od = OpenDialog("Choose image file", None)
	srcDirectory = od.getDirectory()
	srcFile = od.getFileName()
	if srcFile != None:
		if bab.Options(srcDirectory):
			bab.runOneFile(srcDirectory + srcFile)

#
#run on all folders in a folder (very useful)
#you should write this as an exercise

#
#set global options by hand and run on one folder (bypasses the dialog !)
if 1:
    #globals, #1...#5 are the order of operation
    #1
    bab.gGetNumChanFromScanImage = 1 # 0 is off, 1 is on
    bab.gNumChannels = 2
    #2
    bab.gDoCrop = 0 # 0 is off, 1 is on
    bab.gCropLeft = 100 #default left of cropping rectangle
    bab.gCropTop = 0 #default top of cropping rectangle
    bab.gCropWidth = 850 #default width of cropping rectangle
    bab.gCropHeight = 1024 #default height of cropping rectangle
    #3
    bab.gRemoveCalibration = 0 # 0 is off, 1 is on
    #4
    bab.gDoAlign = 1 # 0 is off, 1 is on
    bab.gAlignThisChannel = 1
    bab.gAlignOnMiddleSlice = 1
    bab.gAlignOnThisSlice = 0 
    #5
    bab.gSave8bit = 0 # 0 is off, 1 is on

    #bab.run() #run() will (i) ask for folder and (ii) allow you to set options

    sourceFolder = DirectoryChooser("Please Choose A Directory Of .tif Files").getDirectory()
    if not sourceFolder:
        exit(1)
    #if bab.Options():
    bab.runOneFolder(sourceFolder)

print 'finished bAlign_Batch_v6_demo'


