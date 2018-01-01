# run this from OSX command line
# it will spawn fiji a number of times and run a plugin
# 
# start by running a multistack reg plagin for each spawned fiji instance

# to run a fiji plugin from command line
# plugin needs to be inside plugin folder (can't be external)
# /Users/cudmore/Fiji_20161212.app/Contents/MacOS/ImageJ-macosx -run testspawn

import threading
import os, math, glob
import time # debugging
import subprocess

gFijipath = '/Users/cudmore/Fiji_20161212.app/Contents/MacOS/ImageJ-macosx'
gFijiPath = '/Users/cudmore/Fiji_20161225.app/Contents/MacOS/ImageJ-macosx'

maximumNumberOfThreads = 5 #2
threadLimiter = threading.BoundedSemaphore(maximumNumberOfThreads)

class EncodeThread(threading.Thread):
	def __init__(self,path, num):
		threading.Thread.__init__(self)
		self.path = path
		self.num = num
		
	def run(self):
		threadLimiter.acquire()
		try:
			# your code here
			print 'Start EncodeThread.run()', self.num, self.path
			self.myrun()
		finally:
			print '   Stop EncodeThread.run()', self.num, self.path
			threadLimiter.release()

	def myrun(self):
		# production
		plugin = '/Users/cudmore/Dropbox/bob_fiji_plugins/bAlignFolder_.py'
		args = 'oneFile=' + self.path
		# debug
		#plugin = '/Users/cudmore/Dropbox/bob_fiji_plugins/playground/testspawn_.py'
		#args = 'path=' + self.path + ' num=' + str(self.num)

		cmd = gFijiPath + ' --allow-multiple --jython ' + plugin + ' ' + args
		print '=== EncodeThread.myrun() cmd:'
		print '   ', cmd
		try:
			#p = subprocess.Popen([cmd], shell=True, stdout=subprocess.PIPE)
			p = subprocess.Popen(cmd, shell=True)
			print '   === EncodeThread.myrun() got return num=', self.num
			for line in p.stdout.readlines():
				print '\t', line
		except:
			print '\r   *** EncodeThread.myrun()() got exception ***'
			print '      ', self.path
						
# run an entire directory
def runrun():

	startTime = time.time()

	srcdir = '/Volumes/t3/data/2016/11/20161123/20161123_a189b/20161123_a189b_out/'
	filelist =  glob.glob(srcdir + '*.tif')
	
	# create a list of threads
	threadlist = []
	numFile = 1
	for file in filelist:
		#if numFile>5: # limit to 5 files for debuggin
		#	continue
		print 'commandlinebatch.runrun() creating EncoderThread() file:', file, 'num:', numFile
		et = EncodeThread(file, numFile)
		threadlist.append(et)
		numFile += 1
	
	# run all threads at once. threadLimiter will limit # running to maximumNumberOfThreads
	for thread in threadlist:
		thread.start()
	
	# wait for all threads to stop
	print'commandlinebatch.runrun() looping and joining'
	for thread in threadlist:
		thread.join()
		print 'commandlinebatch.runrun() done and joined thread', thread.num

	print 'commandlinebatch.runrun() really finished'

	stopTime = time.time()
	elapsedSeconds = round(stopTime-startTime,2)
	elapsedMinutes = round(elapsedSeconds/60.0,2)
	print 'Finished commandlinebatch with ' + str(numFile) + ' files in ' + str(elapsedSeconds) + ' seconds (' + str(elapsedMinutes) + ' minutes)'

runrun()