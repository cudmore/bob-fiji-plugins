"""
	Author: RObert H. Cudmore
	Date: 20160915
	Email: robert.cudmore@gmail.com
	Web: http://robertcudmore.org
	Github: https://github.com/cudmore/bob-fiji-plugins

	This script will allign 3D .tif stacks.
	The output is placed in /src/src_aligned where /src/ is the directory you specify.
	All alignmnet is done w.r.t. the middle slice.
	For 1 channel .tif files, this will align the file
	For 2 channel .tif files
		- We assume channels are in their own file _ch1.tif and _ch2.tif (See bFolder2MapManager_.py to achieve this).
		- Use globalOptions['alignThisChannel'] to specify the channel to do the alignment on.
	For 3 channel .tif file -->> THIS DOES NOT WORK.

	Requirements:
		This plugin requires 2 additional plugins to run:
			1) MultiStackReg: http://bradbusse.net/sciencedownloads.html
			2) TurboReg: http://bigwww.epfl.ch/thevenaz/turboreg/
		
	To Do:
		Rewrite this to align one file. Then use commandlinebatch.py to call it on multiple images.
"""

import os
import sys, time, math

from ij import IJ
from ij.io import DirectoryChooser, OpenDialog, FileSaver

globalOptions = {}
globalOptions['alignThisChannel'] = 2
globalOptions['medianFilter'] = 0 # set to 0 for no median filter

run_alignment = True # set to False to not run alignment for debuggin

#####################################################################################
class bAlignFile:
	def __init__(self, srcFile, alignmentChannel=globalOptions['alignThisChannel']):

		if not os.path.isfile(srcFile):
			bPrintLog('ERROR: bAlignFile() did not find file: ' + srcFile,0)
			return 0

		self.alignmentChannel = alignmentChannel
		self.medianFilter = globalOptions['medianFilter']

		self.tifFilePath = srcFile

		tmp = os.path.split(srcFile)[0]
		self.enclosingFolderName = os.path.split(tmp)[1]
		#self.dstFolder = tmp + '/' + self.enclosingFolderName + '_aligned' + '/'
		self.dstfolder = os.path.join(tmp, self.enclosingFolderName + '_aligned') + '/'

		
		print 'bAlignFile srcFile:', srcFile
		print 'enclosingFolderName:', self.enclosingFolderName
		print 'dstFolder:', self.dstFolder

	def run (self):
		# make output folder
		if not os.path.isdir(self.dstFolder):
			os.makedirs(self.dstFolder)

		tifFileName = os.path.split(self.tifFilePath)[1]
		isCh1 = self.tifFilePath.endswith('_ch1.tif')
		isCh2 = self.tifFilePath.endswith('_ch2.tif')

		doThisFilePath = ''
		if self.alignmentChannel==1 and isCh1:
			doThisFilePath = self.tifFilePath
		elif self.alignmentChannel==2 and isCh2:
			doThisFilePath = self.tifFilePath
		
		if (doThisFilePath):
			###
			###
			bPrintLog('Loading file: ' + doThisFilePath, 3)
			imp = IJ.openImage(doThisFilePath)  

			if imp is None:  
				print "ERROR: could not open image from file:", doThisFilePath
				return -1  

			d = imp.getDimensions() # Returns the dimensions of this image (width, height, nChannels, nSlices, nFrames) as a 5 element int array.
			logStr = 'dimensions are w:' + str(d[0]) + ' h:' + str(d[1]) + ' channels:' + str(d[2]) + ' slices:' + str(d[3]) + ' frames:' + str(d[4])
			bPrintLog(logStr, 3)
			
			'''
			this is not designed to handle stacks that have frames !!!
			'''
			##
			numSlices = imp.getNSlices()
			if numSlices>1:
				pass
			else:
				numFrames = imp.getNFrames()
				
				if numFrames > 1:
					# swap nFrames with nSLices
					numSlices = numFrames
					numFrames = 1
					nChannels = 1
					
					bPrintLog('Swapping frames for slices. numSlices=' + str(numSlices) + ' numFrames=' + str(numFrames), 3)
					imp.setDimensions(nChannels, numSlices, numFrames)
				else:
					bPrintLog('ERROR: number of slices must be more than one, file: ' + tifFileName)
					return -1
			##
			
			# get the stack header (e.g. infoStr)
			infoStr = imp.getProperty("Info") #get all tags
			if infoStr is None:
				infoStr = ''

			## median filter
			if self.medianFilter > 0:
				bPrintLog('Running median filter: ' + str(self.medianFilter), 3)
				medianArgs = 'radius=' + str(self.medianFilter) + ' stack'
				IJ.run(imp, "Median...", medianArgs);
				infoStr += 'bMedianFilter=' + str(self.medianFilter) + '\n'
				imp.setProperty("Info", infoStr)
			
			#add to stack header
			infoStr += 'b_AlignFolder=v0.0\n'
			imp.setProperty("Info", infoStr)
			
			imp.show()
			impWin = imp.getTitle()

			#show the slice we start alignment on
			middleSlice = int(math.floor(numSlices / 2))
			imp.setSlice(middleSlice)
			
			transformationFile = self.dstFolder + tifFileName + '.txt'
		
			if run_alignment:
				bPrintLog('Running MultiStackReg for: ' + tifFileName, 3)
				stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(impWin,transformationFile)
				IJ.run('MultiStackReg', stackRegParams)
			else:
				bPrintLog('DEBUG: NOT running MultiStackReg for: ' + tifFileName, 3)

			# save alignment
			bPrintLog('Saving aligned stack():' + self.dstFolder + tifFileName, 3)
			fs = FileSaver(imp)
			if numSlices>1:
				fs.saveAsTiffStack(self.dstFolder + tifFileName)
			else:
				fs.saveAsTiff(self.dstFolder + tifFileName)
			
			imp.changes = 0
			imp.close()

			###
			###
			#open and run alignment on other channel
			if isCh1:
				otherFilePath = self.tifFilePath.strip('_ch1.tif') + '_ch2.tif'
			elif isCh2:
				otherFilePath = self.tifFilePath.strip('_ch2.tif') + '_ch1.tif'

			if os.path.isfile(otherFilePath):
				otherFileName = os.path.split(otherFilePath)[1]
				
				bPrintLog('Loading [OTHER] file: ' + doThisFilePath, 3)
				imp = IJ.openImage(otherFilePath)  

				if imp is None:  
					print "ERROR: could not open other image from file:", otherFilePath
					return -1  

				##
				numSlices = imp.getNSlices()
				if numSlices>1:
					pass
				else:
					numFrames = imp.getNFrames()
					
					if numFrames > 1:
						# swap nFrames with nSLices
						numSlices = numFrames
						numFrames = 1
						nChannels = 1
						
						bPrintLog('Swapping frames for slices. numSlices=' + str(numSlices) + ' numFrames=' + str(numFrames), 3)
						imp.setDimensions(nChannels, numSlices, numFrames)
					else:
						bPrintLog('ERROR: number of slices must be more than one, file: ' + tifFileName)
						return -1
				##
				
				#add to stack header
				infoStr = imp.getProperty("Info") #get all tags
				if infoStr is None:
					infoStr = ''
				infoStr += 'b_AlignFolder=v0.0' + '\n'
				imp.setProperty("Info", infoStr)

				imp.show()
				impWin = imp.getTitle()

				if run_alignment:
					bPrintLog('Running MultiStackReg for: ' + otherFileName, 3)
					stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(impWin,transformationFile)
					IJ.run('MultiStackReg', stackRegParams)		
				else:
					bPrintLog('DEBUG: Not running MultiStackReg for: ' + otherFileName, 3)

				#save alignment
				bPrintLog('Saving aligned stack():' + self.dstFolder + otherFileName, 3)
				fs = FileSaver(imp)
				if numSlices>1:
					fs.saveAsTiffStack(self.dstFolder + otherFileName)
				else:
					fs.saveAsTiff(self.dstFolder + otherFileName)

				imp.changes = 0
				imp.close()
	
#####################################################################################
class bAlignFolder:
	def __init__(self, srcFolder, alignmentChannel=globalOptions['alignThisChannel']):

		if not os.path.isdir(srcFolder):
			bPrintLog('ERROR: bAlignFolder() did not find folder: ' + srcFolder,0)
			return 0

		self.alignmentChannel = alignmentChannel
		self.medianFilter = globalOptions['medianFilter']
		
		# list of full path to each .tif
		self.tifList = []
		for child in os.listdir(srcFolder):
			childPath = os.path.join(srcFolder, child)
			if childPath.endswith('.tif'):
				self.tifList.append(childPath)
		#print 'tifList:', self.tifList

		tmp = os.path.split(srcFolder)[0]
		self.enclosingFolderName = os.path.split(tmp)[1]
		#self.dstFolder = srcFolder + self.enclosingFolderName + '_aligned' + '/'
		self.dstFolder = os.path.join(srcFolder, self.enclosingFolderName + '_aligned') + '/'

		
	def run(self):
		# make output folder
		if not os.path.isdir(self.dstFolder):
			os.makedirs(self.dstFolder)
			
		numFiles = len(self.tifList)
		totalNumSlices = 0
		
		for i, tifFilePath in enumerate(self.tifList):
			#debug
			#if i>4:
			#	continue
			
			tifFileName = os.path.split(tifFilePath)[1]
			isCh1 = tifFilePath.endswith('_ch1.tif')
			isCh2 = tifFilePath.endswith('_ch2.tif')
			
			bPrintLog(str(i+1) + ' of ' + str(numFiles) + ' ' + tifFileName,2)

			doThisFilePath = ''
			if self.alignmentChannel==1 and isCh1:
				doThisFilePath = tifFilePath
			elif self.alignmentChannel==2 and isCh2:
				doThisFilePath = tifFilePath
			
			if (doThisFilePath):
				###
				###
				bPrintLog('Loading file: ' + doThisFilePath, 3)
				imp = IJ.openImage(doThisFilePath)  

				if imp is None:  
					print "ERROR: could not open image from file:", doThisFilePath
					continue  

				d = imp.getDimensions() # Returns the dimensions of this image (width, height, nChannels, nSlices, nFrames) as a 5 element int array.
				logStr = 'dimensions are w:' + str(d[0]) + ' h:' + str(d[1]) + ' channels:' + str(d[2]) + ' slices:' + str(d[3]) + ' frames:' + str(d[4])
				bPrintLog(logStr, 3)
				
				'''
				this is not designed to handle stacks that have frames !!!
				'''
				##
				numSlices = imp.getNSlices()
				if numSlices>1:
					pass
				else:
					numFrames = imp.getNFrames()
					
					if numFrames > 1:
						# swap nFrames with nSLices
						numSlices = numFrames
						numFrames = 1
						nChannels = 1
						
						bPrintLog('Swapping frames for slices. numSlices=' + str(numSlices) + ' numFrames=' + str(numFrames), 3)
						imp.setDimensions(nChannels, numSlices, numFrames)
					else:
						bPrintLog('ERROR: number of slices must be more than one, file: ' + tifFileName)
						continue
				##
				
				# get the stack header (e.g. infoStr)
				infoStr = imp.getProperty("Info") #get all tags
				if infoStr is None:
					infoStr = ''

				## median filter
				if self.medianFilter > 0:
					bPrintLog('Running median filter: ' + str(self.medianFilter), 3)
					medianArgs = 'radius=' + str(self.medianFilter) + ' stack'
					IJ.run(imp, "Median...", medianArgs);
					infoStr += 'bMedianFilter=' + str(self.medianFilter) + '\n'
					imp.setProperty("Info", infoStr)
				
				totalNumSlices += numSlices
				
				#add to stack header
				infoStr += 'b_AlignFolder=v0.0\n'
				imp.setProperty("Info", infoStr)
				
				imp.show()
				impWin = imp.getTitle()

				#show the slice we start alignment on
				middleSlice = int(math.floor(numSlices / 2))
				imp.setSlice(middleSlice)
				
				transformationFile = self.dstFolder + tifFileName + '.txt'
			
				if run_alignment:
					bPrintLog('Running MultiStackReg for: ' + tifFileName, 3)
					stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(impWin,transformationFile)
					IJ.run('MultiStackReg', stackRegParams)
				else:
					bPrintLog('DEBUG: Not running alignment for: ' + tifFileName, 3)

				# save alignment
				bPrintLog('Saving aligned stack():' + self.dstFolder + tifFileName, 3)
				fs = FileSaver(imp)
				if numSlices>1:
					fs.saveAsTiffStack(self.dstFolder + tifFileName)
				else:
					fs.saveAsTiff(self.dstFolder + tifFileName)
				
				imp.changes = 0
				imp.close()

				###
				###
				#open and run alignment on other channel
				if isCh1:
					otherFilePath = tifFilePath.strip('_ch1.tif') + '_ch2.tif'
				elif isCh2:
					otherFilePath = tifFilePath.strip('_ch2.tif') + '_ch1.tif'

				if os.path.isfile(otherFilePath):
					otherFileName = os.path.split(otherFilePath)[1]
					
					bPrintLog('Loading [OTHER] file: ' + doThisFilePath, 3)
					imp = IJ.openImage(otherFilePath)  

					if imp is None:  
						print "ERROR: could not open other image from file:", otherFilePath
						continue  

					##
					numSlices = imp.getNSlices()
					if numSlices>1:
						pass
					else:
						numFrames = imp.getNFrames()
						
						if numFrames > 1:
							# swap nFrames with nSLices
							numSlices = numFrames
							numFrames = 1
							nChannels = 1
							
							bPrintLog('Swapping frames for slices. numSlices=' + str(numSlices) + ' numFrames=' + str(numFrames), 3)
							imp.setDimensions(nChannels, numSlices, numFrames)
						else:
							bPrintLog('ERROR: number of slices must be more than one, file: ' + tifFileName)
							continue
					##
					
					#add to stack header
					infoStr = imp.getProperty("Info") #get all tags
					if infoStr is None:
						infoStr = ''
					infoStr += 'b_AlignFolder=v0.0' + '\n'
					imp.setProperty("Info", infoStr)

					imp.show()
					impWin = imp.getTitle()
	
					if run_alignment:
						bPrintLog('Running MultiStackReg for: ' + otherFileName, 3)
						stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(impWin,transformationFile)
						IJ.run('MultiStackReg', stackRegParams)		
					else:
						bPrintLog('DEBUG: NOT running MultiStackReg for: ' + otherFileName, 3)

					#save alignment
					bPrintLog('Saving aligned stack():' + self.dstFolder + otherFileName, 3)
					fs = FileSaver(imp)
					if numSlices>1:
						fs.saveAsTiffStack(self.dstFolder + otherFileName)
					else:
						fs.saveAsTiff(self.dstFolder + otherFileName)

					imp.changes = 0
					imp.close()

'''
Utility
'''
def bPrintLog(text, indent=0):
	msgStr = ''
	for i in (range(indent)):
		msgStr += '    '
		print '   ',
	print text #to command line
	IJ.log(msgStr + text)

def bDebug():
	oneFile = '/Volumes/t3/data/2016/11/20161123/20161123_a189b/20161123_a189b_out/20161123_a189b-087_ch2.tif'
	alignFile = bAlignFile(oneFile)
	if alignFile:
		alignFile.run()
	
'''
Main
'''
# 20170811 including __builtin__ here for new versions of Fiji (this is BULLSHIT)
if __name__ in ['__main__', '__builtin__']: 
	startTime = time.time()
	
	bPrintLog('=== Starting bAlignFolder_.py')
	
	numObjs = 0
	path = ''
	
	debug = 0
	if debug:
		bDebug()
	else:
		# this is dumb, I need to expand this to take a command line (i) directory or (ii) file
		if len(sys.argv) > 1:
			type, path = sys.argv[1].split('=')
			bPrintLog('type:' + type)
			bPrintLog('path:' + path)
			if type == 'oneFile':
				alignFile = bAlignFile(path)
				if alignFile:
					alignFile.run()
			elif type == 'srcDir':
				alignFolder = bAlignFolder(path)
				if alignFolder:
					alignFolder.run()
		else:
			#ask user for folder, this is a folder that contains folders with single image .tif files
			
			# this asks for a folder
			path = DirectoryChooser("Please Choose A Directory Of .lsm Files").getDirectory()
			# this asks for a file
			#path = OpenDialog("xxx").getPath()
			
			if (path):
				print 'path:', path
				# '''
				if path.endswith('/'):
					alignFolder = bAlignFolder(path)
					if alignFolder:
						alignFolder.run()
				elif path.endswith('_ch2.tif'):
					alignFile = bAlignFile(path)
					if alignFile:
						alignFile.run()
				# '''
			else:
				bPrintLog('Canceled by user', 0)
	
	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds/60.0,2)
	bPrintLog('Finished bAlignFolder_.py in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)')
	bPrintLog('path:' + str(path), 2)
	bPrintLog('=================\n')
