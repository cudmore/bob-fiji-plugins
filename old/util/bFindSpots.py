# Load an image of the Drosophila larval fly brain and segment
# the 5-micron diameter cells present in the red channel.

from ij import WindowManager #to get front window
from script.imglib.analysis import DoGPeaks
from script.imglib.color import Red
from script.imglib.algorithm import Scale2D
from script.imglib.math import Compute
from script.imglib import ImgLib
from ij3d import Image3DUniverse
from javax.vecmath import Color3f, Point3f

cell_diameter = 5  # in microns
minPeak = 40 # The minimum intensity for a peak to be considered so.

cell_diameter = 100
minPeak = 200

imp = WindowManager.getCurrentImage()
#imp = IJ.openImage("http://pacific.mpi-cbg.de/samples/first-instar-brain.zip")

#imageStats = imp.getStatistics()
#imageMin = imageStats.min()
imageMin = imp.MIN_MAX
print 'min:', imageMin

# Scale the X,Y axis down to isotropy with the Z axis
cal = imp.getCalibration()
print '   x/y/z calibration is: ', cal.pixelWidth, cal.pixelHeight, cal.pixelDepth

scale2D = cal.pixelWidth / cal.pixelDepth
print '   calling scale2d'
#iso = Compute.inFloats(Scale2D(Red(ImgLib.wrap(imp)), scale2D))
iso = Compute.inFloats(Scale2D(ImgLib.wrap(imp), scale2D))

# Find peaks by difference of Gaussian
sigma = (cell_diameter  / cal.pixelWidth) * scale2D
print '   starting dogpeaks...'
peaks = DoGPeaks(iso, sigma, sigma * 0.5, minPeak, 1)
print "   Found", len(peaks), "peaks"

# Convert the peaks into points in calibrated image space
if len(peaks)>0:
  ps = []
  for peak in peaks:
    p = Point3f(peak)
    p.scale(cal.pixelWidth * 1/scale2D)
    ps.append(p)

  print '   making 3d view...'
  
  # Show the peaks as spheres in 3D, along with orthoslices:
  univ = Image3DUniverse(512, 512)
  univ.addIcospheres(ps, Color3f(1, 0, 0), 2, cell_diameter/2, "Cells").setLocked(True)
  univ.addOrthoslice(imp).setLocked(True)
  univ.show()

print 'done'
