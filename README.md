## bob-fiji-plugins

A collection of Fiji/ImageJ plugins we use for our image analysis pipelines. These plugins convert proprietary image formats to Tiff, split color channels, reduce bit depth, and perform correlation based stack alignment.

Most of these plugins will attempt to preserve .tif headers and in most cases will append new ones for import into [Map Manager](http://blog.cudmore.io/mapmanager). Common .tif headers that will be appended are date, time, voxel size, and scan parameters such as dwell time, scan line period, laser power, detector gains, etc. etc.

In general, the output .tif stacks are placed in a new folder inside the specified source folder.

**bAlignFolder**. Align a folder of .tif images. For 2-3 color channel images, alowss the user to choose the channel for alignment and will apply this alignment to other color channels. This plugin requires:
 1. MultiStackReg: http://bradbusse.net/sciencedownloads.html
 2. TurboReg: http://bigwww.epfl.ch/thevenaz/turboreg/

**bConvertTo8Bit_v5_**. Convert a folder of .tif images into 8-bit. By default this will expand the histogram of each .tif file to fill 8-bit intensities. This **should not** be used if you want to compare intensity between stacks (e.g. time-points). 

**bFolder2MapManager.v0.0_**. Convert a directory of image files into single channel .tif files. This will convert Zeiss LSM/CZI, and Scan Image 3.8/4.x.

**bMaxProject_**. Create maximal intensity projection images from each .tif stack in a folder.

**bPrairie2tif.v0.0_*. Convert the native Bruker Prairie View .tif format which is a folder of single image plane .tif files into a single .tif image volume/time-series.

**bScramble_**. Make a scrambled name copy of each file in a folder. This is used for pre-processing files before performing **blind** analysis. The mapping between the original file and the scrambled file are saved in a text file. Don't cheat.


The software is provided "as is" without warranty of any kind.
