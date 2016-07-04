###bob-fiji-plugins

These are [fiji](http://fiji.sc/Fiji) plugins written and maintained by [Robert Cudmore](http://robertcudmore.org). I am happy to fix bugs and make improvements to these plugins, just drop me an email. If you use these plugins for your work, I ask that you give me credit. If that is not possible, an email is always nice.

##Installation

Download a .py file and copy the file into your Fiji plugins folder. To download the code, navigate to the page that displays the plugins code, click the **Raw** button, and then copy/pase the code into a text file.

###bAlignBatch

bAlignBatch will convert a directory of .tif/.lsm stacks that can then be opened in [Map Manager][6]. It does the following:

 1. If stacks are two channels, it splits each stack into two .tif files: _ch1.tif and _ch2.tif
 2. Will optionally align slices within each stack using the MultistackReg plugin. If the stacks are two color channels, alignment can be done on one channel and then applied to the other.
 3. Will output a maximal z-projection for each stack
 4. Will output a text file with the .tif header for each stack.
 
If you are performing alignment, you need to have the [MultiStackReg v1.45](http://bradbusse.net/downloads.html) plugin installed.

If you are converting .lsm files, be sure to specify the correct number of channels. The plugin assumes all .lsm files in a folder have the same number of channels.

#### Troubleshooting

If the plugin doesn't work, first thing is to try and use an older [lifeline version of Fiji](http://fiji.sc/Downloads). Try the Fiji Life-Line version, 2013 July 15 on the main [FIJI download page](http://fiji.sc/Downloads).
  - Mac: http://fiji.sc/downloads/Life-Line/fiji-macosx-20130715.dmg
  - Windows (64-bit): http://fiji.sc/downloads/Life-Line/fiji-win64-20130715.zip
  - Windows (32-bit): http://fiji.sc/downloads/Life-Line/fiji-win32-20130715.zip


###Batch Convert To 8bit

Convert a folder of .tif files to 8-bit. Will also split 2 channel .tif files into 2 seperate files.

Useful if ...


###Sliding Z-Projection

Convert an image stack (opened in Fiji) to a sliding Z-PRojection. What is a sliding Z-Projection? See [here](http://www.robertcudmore.org/software/bSliding_Z_Projection.html).

###Bob Neurite Tracer

This is a FIJI plugin to automate fitting lines in 3D image stack from within [Map Manager 3](http://cudmore.github.io/mapmanager). This plugin is written in Java and is derived from [Simple Neurite Tracer](http://fiji.sc/Simple_Neurite_Tracer). It runs 'headless' within Fiji and is designed to be called from a command line, thus, manually selecting it from the Fiji plugins menu will not work.

##Links
- [1] : http://fiji.sc/Fiji
- [2] : http://fiji.sc/Downloads
- [3] : http://bradbusse.net/downloads.html
- [4] : http://www.robertcudmore.org/software/bSliding_Z_Projection.html
- [5] : http://fiji.sc/Simple_Neurite_Tracer
- [6] : http://cudmore.github.io/mapmanager