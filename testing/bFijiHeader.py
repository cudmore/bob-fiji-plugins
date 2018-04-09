from ij import IJ

imp = IJ.getImage()

infoStr = imp.getProperty("Info") #get all tags

print 'infoStr:', infoStr

print imp.getInfoProperty()