#Robert H Cudmore
#20161213

'''
1) load tif
   Remove scale, tracing assumes we have 1x1x1 voxels
2) load list of 3d points
3) for each pnt i, trace from pnt i to pnt i+1
     collect the tracing in a list
5) save the list
...
...
6) import back into igor

Notes=====

- run this with command line

/Users/cudmore/Fiji_20170810.app/Contents/MacOS/ImageJ-macosx /Users/cudmore/Dropbox/bob_fiji_plugins/BobNeuriteTracer_v1_.py
or
/Users/cudmore/Fiji_20170810.app/Contents/MacOS/ImageJ-macosx --headless --run /Users/cudmore/Dropbox/bob_fiji_plugins/BobNeuriteTracer_v1_.py

- try to run in already running instance
see: https://imagej.nih.gov/ij/docs/guide/146-18.html
/Users/cudmore/Fiji_20170810.app/Contents/MacOS/ImageJ-macosx --port1 /Users/cudmore/Dropbox/bob_fiji_plugins/BobNeuriteTracer_v1_.py

/Volumes/vasculature/Users/cudmore/Fiji_20170810.app/Contents/MacOS/ImageJ-macosx --headless --run /Users/cudmore/jhu/bJHU/Tracing/BobNeuriteTracer_v1_.py 'tiffilename="/Volumes/vasculature/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/s_0071_ch1.tif", controlfilename="/Volumes/vasculature/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/stackdb/line/s_0071_c0.txt"'
'''

import os, sys

from ij import IJ

from tracing import PathAndFillManager
from tracing import TracerThread

#TracerThread tracer = new TracerThread(imagePlus, 0, 255, timeoutSeconds, reportEveryMilliseconds, x1, y1, z1, x2, y2, z2, reciprocal, depth == 1, hessian, ((hessian == null) ? 1 : 4), null, hessian != null );

defaultTiff = '/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/s_0071_ch1.tif'
defaultControl = '/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/stackdb/line/s_0071_c0.txt'

#@String(value=defaultTiff) tiffilename
#@String(value=defaultControl) controlfilename

def runmain():

	#
	# Load tif
	#
	#tiffilename = '/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/s_0071_ch1.tif'
	
	imp = IJ.openImage(tiffilename)  
	if imp is None:
		print 'error opening file'
	print 'opened tiffilename:', tiffilename
	
	#print 'showing image'
	#imp.show()
	
	width = imp.getWidth();
	height = imp.getHeight();
	depth = imp.getStackSize();
	
	#
	# load .txt file with control points
	#
	#controlfilename = '/Users/cudmore/Dropbox/MapManagerData/batch_test/batch_test_tif/stackdb/line/s_0071_c0.txt'
	pnt = {'x', 'y', 'z'}
	pnts = []
	with open(controlfilename, 'rU') as f:
		for line in f:
			line = line.rstrip()
			x, y, z = line.split(',')
			x = int(x)
			y = int(y)
			z = int(z)
			pnts.append([x,y,z])
	print 'read control points file:', controlfilename
	
	#
	# for each control point, accumulate tracing points into finalPntList
	finalPntList = []
	for i, pnt in enumerate(pnts):
		#print 'step:', i, len(pnts), pnt
		#print pnt
		
		if i < len(pnts)-1:
			pass
		else:
			continue
		
		# trace from pnt i to pnt j (i+1)
		ix = pnts[i][0]
		iy = pnts[i][1]
		iz = pnts[i][2]
		
		jx = pnts[i+1][0]
		jy = pnts[i+1][1]
		jz = pnts[i+1][2]
		
		#Use the reciprocal of the value at the new point as the cost
		#in moving to it (scaled by the distance between the points).
		reciprocal = True;
		
		timeoutSeconds = 5
		reportEveryMilliseconds = 3000
		
		#hessian = None
			
		tracer = TracerThread(imp, 0, 255, timeoutSeconds, reportEveryMilliseconds, ix,iy,iz,jx,jy,jz, reciprocal, depth == 1, None, 1, None, False )
		tracer.run()
		result = tracer.getResult().getPoint3fList()
	
		for resultPnt in enumerate(result):
			#print 'resultPnt:', resultPnt[1].x
			#print type(resultPnt[1])
			x = resultPnt[1].x
			y = resultPnt[1].y
			z = resultPnt[1].z
			finalPntList.append([x, y, z])


	#
	# save tracing in xxx to output file <in>.mast
	#path, name = os.path.split(controlfilename)
	outfile = controlfilename + '.master'
	with open(outfile, "w") as of:
		for pnt in finalPntList:
			#print pnt
			outline = '(' + str(pnt[0]) + ',' + str(pnt[1]) + ',' + str(pnt[2]) + ')'
			of.write(outline + '\n')
	print 'saved tracing to', outfile
	
	#
	# make a .finished file
	finishfile = controlfilename + '.finished'
	with open(finishfile, "w") as of:
		of.write('finished' + '\n')
	print 'saved finished file to', finishfile
		
print '__name__:', __name__
if __name__ in ['__main__', '__builtin__']:
	# these don't work when called from command line
	#print 'Number of arguments:', len(sys.argv), 'arguments.'
	#print 'Argument List:', str(sys.argv)
	runmain()