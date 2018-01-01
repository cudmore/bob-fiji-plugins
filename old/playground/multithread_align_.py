from ij import IJ, ImagePlus, WindowManager
from ij.io import Opener, FileSaver, DirectoryChooser

from ij.plugin import ZProjector

import threading
import os, math, glob

maximumNumberOfThreads = 5
threadLimiter = threading.BoundedSemaphore(maximumNumberOfThreads)

class EncodeThread(threading.Thread):
    def __init__(self,path, num):
        threading.Thread.__init__(self)
        #print 'init path', path
        self.path = path
        self.num = num
        
    def run(self):
        threadLimiter.acquire()
        try:
            # your code here
            print 'start', self.path
            self.myrun()
        finally:
            print 'finished', self.path
            threadLimiter.release()

    def myrun(self):
        imp = IJ.openImage(self.path) #open imp
        if imp is None:
            print 'ERROR opening file:', self.path
            return 0
        numSlices = imp.getNSlices()
        if numSlices<2:
        	return 0
        
        middleSlice = int(math.floor(imp.getNSlices() / 2)) #int() is necc., python is fucking picky
        
        imp.show()
        imp.setSlice(middleSlice)
        impTitle = imp.getTitle()
        impWin = WindowManager.getWindow(impTitle) #returns java.awt.Window

        transformationFile = os.path.basename(self.path)
        transformationFile = os.path.splitext(transformationFile)[0] + '.txt'
        transformationFile = '/Users/cudmore/Desktop/out/' + transformationFile
        stackRegParams = 'stack_1=[%s] action_1=Align file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save' %(impWin,transformationFile)
        IJ.run('MultiStackReg', stackRegParams)
        
        imp.close()
        
        '''
        #20150723, we just aligned on a cropped copy, apply alignment to original imp
        origImpTitle = imp.getTitle()
        stackRegParams = 'stack_1=[%s] action_1=[Load Transformation File] file_1=[%s] stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]' %(origImpTitle,transformationFile)
        IJ.run('MultiStackReg', stackRegParams)        
        '''
        
        '''
        zp = ZProjector(imp)
        zp.setMethod(ZProjector.MAX_METHOD)
        zp.doProjection()
        zimp = zp.getProjection()

        savefile = os.path.basename(self.path)
        savefile = 'max_' + os.path.splitext(savefile)[0]
        savepath = '/Users/cudmore/Desktop/out/' + savefile
        IJ.saveAsTiff(zimp, savepath)
        imp.close()
        '''

def runrun():

    srcdir = '/Users/cudmore/jhu/hyperstack/rawRepo/a153_hs1/raw/channels8/'
    srcdir = '/Volumes/fourt/jhu/hyperstack/rawRepo/a153_hs1/raw/channels8/'
    filelist =  glob.glob(srcdir + '*.tif')

    # create a list of threads
    threadlist = []
    i = 1
    for file in filelist:
        et = EncodeThread(file, i)
        threadlist.append(et)
        i += 1
    
    # run all threads at once. threadLimiter will limit # running to maximumNumberOfThreads
    for thread in threadlist:
        thread.start()
    
    # wait for all threads to stop
    for thread in threadlist:
        thread.join()
        print 'done', thread.num

    print 'really finished'

def runtest():
    srcdir = '/Users/cudmore/jhu/hyperstack/rawRepo/a153_hs1/raw/channels8/'
    srcdir = '/Volumes/fourt/jhu/hyperstack/rawRepo/a153_hs1/raw/channels8/'
    filelist =  glob.glob(srcdir + '*.tif')
    file = filelist[0]

    et = EncodeThread(file, 1)
    et.myrun()

runrun()