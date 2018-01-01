from ij import IJ
import os
import sys

def run():

    print '======================'
    print 'running'

    if len(sys.argv)<2:
        print 'bAlignCrop will align a stack.'
        print 'Usage: ./fiji'
        filePath = '/Users/cudmore/Desktop/X20150214_a156_010_ch1_c.tif'
        #return
    else:
        filePath = sys.argv[1]
    
    #check that file exists
    if not os.path.isfile(filePath):
        print 'Error: did not find file ', filePath
        return
        
    #open file
    print 'opening file:', filePath
    imp = IJ.openImage(filePath)

    if imp is None:
        print 'Error opening file'
        return

    imp.show()
    winTitle = imp.getTitle()

    transformationFile = filePath + '.txt'
    
    print 'running multistack reg'
    #IJ.run(imp, "MultiStackReg", "stack_1=X20150214_a156_010_ch1_c.tif action_1=Align file_1=[] stack_2=None action_2=Ignore file_2=[] transformation=Translation save");
    stackRegParams = 'stack_1=%s action_1=[Align] file_1=[%s] transformation=[Translation] save' %(winTitle, transformationFile)
    IJ.run('MultiStackReg', stackRegParams)

print 'running bALign_Crop'
run()
print 'finished'