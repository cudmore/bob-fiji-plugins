# this is called from python script commandlinebatch

# see: http://imagej.net/Scripting_Headless

# to call this directly from command line
# /Users/cudmore/Fiji_20161212.app/Contents/MacOS/ImageJ-macosx --jython /Users/cudmore/Fiji_20161212.app/plugins/bob-fiji-plugins/testspawn_.py 'p1'

import os, sys, time, math

from ij import IJ, WindowManager

def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	#IJ.log(msgStr + text)

def myrun(filepath, thechannel):
	bPrintLog('myrun() start:' + str(thechannel) + ' ' + filepath)
	#time.sleep(2)
	#print 'myrun() done:', thechannel, filepath

	imp = IJ.openImage(filepath) #open imp
	if imp is None:
		print 'ERROR opening file:', filepath
		return 0
	numSlices = imp.getNSlices()
	if numSlices<2:
		return 0
	
	middleSlice = int(math.floor(imp.getNSlices() / 2)) #int() is necc., python is fucking picky
	
	imp.show()
	imp.setSlice(middleSlice)
	impTitle = imp.getTitle()
	impWin = WindowManager.getWindow(impTitle) #returns java.awt.Window

	debug = 1

	transformationFile = os.path.basename(filepath)
	transformationFile = os.path.splitext(transformationFile)[0] + '.txt'
	transformationFile = '/Users/cudmore/Desktop/out/' + transformationFile
	stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(impWin,transformationFile)

	if debug:
		print '   testspawn_.myrun()', stackRegParams
	else:
		IJ.run('MultiStackReg', stackRegParams)
	
	imp.close()
	
if __name__ == "__main__":
	#sys.argv[1] has to be 'file=full/path/to/file'
	
	bPrintLog('in testspawn_.py __main__',0)
	
	bPrintLog('len(sys.argv)='+str(len(sys.argv)),1)
	bPrintLog('sys.argv=',1)
	i = 0
	for item in sys.argv:
		bPrintLog(str(i) + " '" + item + "'", 2)
		i += 1
		
	filepath = sys.argv[1].split('=')[1]

	imp = IJ.openImage(filepath) #open imp
	imp.show()

	time.sleep(20)
	
	'''
	myrun(tiffile, channel)
	
	print '__main__ done\r'
	'''
	
	# this will quit
	#bPrintLog('calling quit',2)
	
	# this WORKS when macro is run from Fiji script editor
	#IJ.doCommand("Quit")
	
	# this does NOT work when macro is run from Fiji script editor
	sys.exit()
	
	bPrintLog('testspawn_.py should not be here',2)
	