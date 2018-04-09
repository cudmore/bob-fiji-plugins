## bob-fiji-plugins

This repository is a collection of Fiji/ImageJ plugins we use for our image analysis pipelines. These plugins convert proprietary image formats to Tiff, split color channels, reduce bit depth, and perform correlation based stack alignment. We use these plugins as a preprocessing step before importing into [Map Manager](http://mapmanager.github.io).

Please let us know if you use any of these plugins. We are providing this code as a service to the community and expect to be told when they are useful. As always, email Robert Cudmore with questions, comments, or bugs.

## Install

Click on the green 'Clone or download' button and select 'Download ZIP'. Once you have the .zip file, extract it and drag and drop desired plugin onto the main Fiji window. Run the plugin from the Fiji editor with the 'Run' menu or using keyboard ctrl+r.

## Usage

 - **bFolder2MapManager.** For Zeiss LSM/CZI or ScanImage files.
 - **bPrairie2tif.** For Brucker Prairie View files.
 
### bAlignFolder_v0.0_

Align a folder of .tif images. For 2-3 color channel images, allows the user to choose the channel for alignment and will apply this alignment to other color channels. This plugin requires:
 1. MultiStackReg: http://bradbusse.net/sciencedownloads.html
 2. TurboReg: http://bigwww.epfl.ch/thevenaz/turboreg/

### bConvertTo8Bit_v5_

Convert a folder of .tif images into 8-bit. By default this will expand the histogram of each .tif file to fill 8-bit intensities. This **should not** be used if you want to compare intensity between stacks (e.g. time-points). 

### bFolder2MapManager.v0.0_

Convert a folder of image files into single channel .tif files. This will convert **Zeiss LSM/CZI**, and **Scan Image 3.8/4.x**.

### bMaxProject_

Create maximal intensity projection images from each .tif stack in a folder.

### bPrairie2tif.v0.0_

Convert the native **Bruker Prairie View** .tif format which is a folder of single image plane .tif files into a single .tif image volume/time-series.

### bScramble_

Make a scrambled name copy of each file in a folder. This is used for pre-processing files before performing **blind** analysis. The mapping between the original file and the scrambled file are saved in a text file. Don't cheat.


## Notes

The code in each plugin is fairly well commented to make it easier to modify.

When new files are created, they will be placed in a new folder within the original folder. 

Most of these plugins will attempt to preserve .tif headers and in most cases will append new ones for import into [Map Manager](http://mapmanager.github.io). Common .tif headers that will be appended are date, time, voxel size, and scan parameters such as dwell time, scan line period, laser power, detector gains, etc. etc.

As time marches on, so does new software versions. New versions of software that is out of our control including Zeiss/Zen, Scan Image, and Prairie View will sometimes break the code provided here. We are constantly updating these plugins to keep up with new software versions.

The software is provided "as is" without warranty of any kind.
