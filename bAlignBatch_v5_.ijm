//
//
//Author: Robert H Cudmore
//Web: http://robertcudmore.org
//Affiliation: Department of Neuroscience, Johns Hopkins University, Linden Lab
//
//
//Convert a directory of .tif files, applying (1) median filter and/or (2) multistackreg on each file.
//save results into a new sub-directory <original_directory>/<original_directory>_aligned/
//
//if ch1Str=="_ch1" then only open _ch1 .tif files, save their transformations (in aligned/register/) and apply it to _ch2 .tif files
//
//20130224, 20130304, v5
//	Improved logic between: {ScanImage, lsm, generic .tif} processing
//	Now properly open files on windows (had \\ path error)
//	Now default to using Bio-Formats to open .tif on Windows (open() was not getting header info???)
//	Explicitly bail when trying to open ScanImage and we do not find the following in the header://
//		state.acq.numberOfChannelsSave
//		state.acq.numberOfZSlices
//	In this case, user should separate stacks into different folders based on channels and run plugin twice.
//
//
//20120916, v4
//	New: with 2 channel, don't put them back otgether, just save {_ch1,_ch2}
//
//0111102, v2
//	We now do the following to EACH original scan image .tif (assuming it has 2 channels)
//	(1) Take an original scan image file
//	(2) take it apart (into ch1 and ch2 stacks)
//	(3) median filter (radius=1)
//	(4) align ch2 (structure)
//	(4.5) use coordinates from alignment and apply to ch1 (ampa)
//	(5) put two channels back together into one stack
//	(6) save into a new folder with same name (one new file per original stack ..tif)
//
//	To Do: generalize which channel we align first (reference) and which channel follows
//	Done: We now handle one or 2 channels and reference stack alignment (ch1 or ch2)
//
////////////////////////////////////////////////////////////////////////////////////////////////
macro "bAlignBatch_v5 for .tif and .lsm" {
   prompt = 1;
   if (prompt == 1) {
	gSourceDir =getDirectory("Select SOURCE directory with Scan Image .tif or Zeiss .lsm");
	//on Windows, replace '\' with '/'. Come on Bill, fix this work !!!
	gSourceDir = bTransformPath(gSourceDir);

	//we put all results in a new directory inside gSourceDir
	enclosingSourceDir = File.getName(gSourceDir); //the name of the enclosing folder
	gDestDir = gSourceDir + enclosingSourceDir + "_aligned/";
	File.makeDirectory(gDestDir);
	
   } else {
	//
	gSourceDir = "/Volumes/Onslaught/jhu/[data]/two_photon_images/2011/02/20110208/grid/";
	gDestDir = "/Volumes/Onslaught/jhu/analTmp/20110208/grid/";
	//
	gSourceDir = "C:/Users/cudmore/[data]/2011/03/20110315/";
	gDestDir = "C:/Users/cudmore/analTemp/20110315/";
}

   //check that src and dst are DIFFERENT (we are saving with the same name as original!!!)
   if (matches(gSourceDir,gDestDir)) {
	print("SOURCE DIRECTORY AND DESTINATION DIRECTORY CANNOT BE THE SAME, try again...");
   } else {
   	//startMem = IJ.currentMemory();
   	//print("Calling bAlignBatch_v5");
   	bAlignBatch_v5(gSourceDir, gDestDir);
   
	   //bSave_SingleDetectionFile(destDir);
	   //bSutter_html(destDir);
	   //run("Close");   

   	//endMem = IJ.currentMemory();
	//print("Memory used at start = " + startMem);
	//print("Memory used at end =  " + endMem);
   }
}
////////////////////////////////////////////////////////////////////////
//convert a directory of .tif files, applying median filter and/or multistacreg on each file.
//save results into a new sub-directory aligned/
function bAlignBatch_v5(srcDir, dstDir) {

	//20130304, on windows, generic open() does not get us .tif header info !!!
	gForceBioFormats = 1;
	
	//
	// user options
	//
	gFileType = ".tif"; // {.tif, .lsm} sohuld work
	gMedianFilter = 0;
	gAlign = 1;
	gSaveStack = 1;
	gSaveDetectionParams = 1;

	gNumberOfChannels = 2; //==2 then we split, align, merge
				//==1 then we just align
	gAlignOnChannel = 2; //==2 we align channel 2 (channel 1 will follow)
			//o.w. we align channel 1 (channel 2 will follow)
				
	gAlignOtherChannel = 1; //added with _v4
	//gSaveStack = 1; //added with _v4
	gSaveMax = 1; //added with _v4

	gScanImageOriginal = 0;
	
	srcFileList = getFileList(srcDir);
	
	//count the number of .tif files
	numTIF = 0;
	for (i=0; i<srcFileList.length; i++) {
		path = srcDir + srcFileList[i];
		if (endsWith(path, gFileType)) {
			numTIF++;
		}	
	}

	//
	//allow user to select some global parameters
	//
	imagejVersionStr = getVersion();
	messageStr = "This macro was tested on Feb 24, 2013 and is verified to work with ImageJ version=1.45b";
	messageStr2 = "You are using ImageJ version=" + imagejVersionStr;

	Dialog.create("bAlignBatch_v4 Options");

	Dialog.addMessage("We will process " + numTIF + " '" + gFileType + "' files from the source directory and save the results in the destination directory");
	Dialog.addMessage("Source Directory: "+gSourceDir);
	Dialog.addMessage("Destination Directory: "+gDestDir);

	Dialog.addMessage("===================================================");
	Dialog.addMessage("Here are the options we will use:");
	
	Dialog.addChoice("File Type:", newArray(".tif", ".lsm"), ".tif");
	Dialog.addCheckbox("Median Filter", gMedianFilter);
	Dialog.addCheckbox("MultiStackReg Alignment", gAlign);
	Dialog.addChoice("Number of channels (if generic .tif):", newArray("1", "2"), "2");
	Dialog.addChoice("Align on channel:", newArray("1", "2"), "2");
	Dialog.addCheckbox("Apply alignment to other channel", gAlignOtherChannel);

	Dialog.addCheckbox("Save Stack", gSaveStack);
	Dialog.addCheckbox("Save Max", gSaveMax);
	Dialog.addCheckbox("ScanImage .tif (otherwise generic .tif)", gScanImageOriginal);

	Dialog.addHelp("http://robertcudmore.org/software/bAlignBatch_v3.html");

	Dialog.addMessage("===================================================");
	Dialog.addMessage(messageStr);
	Dialog.addMessage(messageStr2);
	Dialog.addMessage("If you have problems running this macro, please hit the 'Help' button.");
	
	Dialog.show();

	gFileType = Dialog.getChoice();
	gMedianFilter = Dialog.getCheckbox();
	gAlign = Dialog.getCheckbox();
	gNumberOfChannels = Dialog.getChoice();
	gAlignOnChannel = Dialog.getChoice();
	gAlignOtherChannel = Dialog.getCheckbox();

	gSaveStack = Dialog.getCheckbox();
	gSaveMax = Dialog.getCheckbox();

	gScanImageOriginal = Dialog.getCheckbox();

	//
	//start code
	//
	
	//turn this off to check we close all windows on each iteration
	//setBatchMode(true);
	setBatchMode(false); //deinterleave does not like batch mode !!!!! Come on people !!!!!

	//where we save the .tif files
	alignedPath = dstDir;   //the aligned stacks
print("alignedPath=" + alignedPath);
	File.makeDirectory(alignedPath);

	xmlPath = dstDir  + "detection_params/"; //for scanimage detection params
	File.makeDirectory(xmlPath);
	
	maxPath = dstDir  + "max/"; //for maximal z-projection
	File.makeDirectory(maxPath);
	
	registerPath = "" + dstDir  + "register/"; //this holds the ouput (the transformation) from MultiStackReg
	File.makeDirectory(registerPath);


	print("-----------------------------------------------------------------------------");
	print("Starting bAlignBatch_v5() at " + bGetDateTime());
	print("   We will process " + numTIF + " '" + gFileType + "' files");
	print("      srcDir="+srcDir);
	print("      dstDir="+dstDir);

	print("      gMedianFilter="+gMedianFilter);
	print("      gAlign="+gAlign);
	print("      gNumberOfChannels="+gNumberOfChannels);
	print("      gAlignOnChannel="+gAlignOnChannel);
	print("      gAlignOtherChannel="+gAlignOtherChannel);
	
	actualIdx = 0;
	for (i=0; i<srcFileList.length; i++) {
		path = srcDir + srcFileList[i];
		//isMaxProject = indexOf(srcFileList[i], "max") >= 0;
		isMaxProject = endsWith(path, "max.tif");
//print("" + isMaxProject);
		if (endsWith(path, gFileType) && !isMaxProject) {
			currFile = srcFileList[i];
			bModDate = File.dateLastModified(currFile);
			//strip .tif/.lsm
			strippedName = replace(currFile,gFileType,"");
			//strip any _ch1/_ch2 in original file name (this will cause problems)
			strippedName = replace(strippedName, "_ch1", "");
			strippedName = replace(strippedName, "_ch2", "");
			
			ch1File = strippedName + "_ch1";
			ch2File = strippedName + "_ch2";
			
			showProgress(actualIdx/numTIF);
			print("   -------------------------");
			print("   File " + actualIdx +1 + " of " + numTIF);
			
			//
			// open the original tif, bio-formats preserves the tif tags
			//
			if (gForceBioFormats || gFileType == ".lsm") {
				print("   Opening file with Bio-Formats: '" + path + "'");
				run("Bio-Formats Importer", "open="+path+" autoscale color_mode=Default view=[Standard ImageJ] stack_order=Default");
			} else {
				print("   Opening file with open(): '" + path + "'");
				open(path);
			}
			
			//get the detection params from the file we just opened
			origMetadata = getMetadata("Info");
			origMetadata += "\n" + "bAlignBatch_v5=1" + "\n";

			//put orig metadata into list and try to get state.acq.numberOfChannelsSave	2
			//20130304, added logic to be extra careful here (hopefully did not introduce further errors)
			if (gScanImageOriginal==1) {
				List.setList(origMetadata);
				tmpChannelStr = List.get("state.acq.numberOfChannelsSave"); //will be "" if not found
				tmpSlicesStr = List.get("state.acq.numberOfZSlices"); //will be "" if not found
				scanImageError = 0;
				if (lengthOf(tmpChannelStr) == 0) {
					print("ERROR READING SCANIMAGE HEADER. Please re-run bAlignBatch and uncheck ScanImage.");
					print("   Error reading: state.acq.numberOfChannelsSave");
					scanImageError = 1;
					return -999;
				}
				if (lengthOf(tmpSlicesStr) == 0) {
					print("ERROR READING SCANIMAGE HEADER. Please re-run bAlignBatch and uncheck ScanImage.");
					print("   Error reading: state.acq.numberOfZSlices");
					scanImageError = 1;
					return -999;
				}
				if (scanImageError==0) {
					scanImageChannels = List.getValue("state.acq.numberOfChannelsSave");
					scanImageSlices = List.getValue("state.acq.numberOfZSlices");	
				} 
			}

			//on windows, window names are FULL path
			newWindowName = srcFileList[i];

			//goal here is to just put some {name,value} pairs into stack header
			//check size of stack we just opened
			getDimensions(width, height, channels, slices, frames);
			
			if (gScanImageOriginal) {
				actualChannels = scanImageChannels; //from ScanImage header
				channels = scanImageChannels;
				slices = scanImageSlices;
				print("         ScanImage stack with " + actualChannels + " channels and " + scanImageSlices + " slices.");
			} else if (gFileType == ".lsm") {
				actualChannels = channels; //from getDimensions()
				print("         Zeiss LSM stack with " + actualChannels + " channels and " + slices + " slices.");
			} else {
				actualChannels = gNumberOfChannels; //from user input
				print("         Default .tif stack with " + actualChannels + " channels (User Entered) and " + slices + " slices.");
			}
			
			//channels
			origMetadata += "bNumChannels=" + gNumberOfChannels + "\n"; //20130224, this can be wrong !!!
			//width
			origMetadata += "bPixelsPerLine=" + width + "\n";
			origMetadata += "bPixelsx=" + width + "\n";
			//height
			origMetadata += "bLinesPerFrame=" + height + "\n";
			origMetadata += "bPixelsy=" + height + "\n";
			//depth
			origMetadata += "bNumSlices=" + slices + "\n";
			origMetadata += "bPixelsz=" + slices + "\n";
			
			getVoxelSize(width, height, depth, unit);
			origMetadata += "voxelx=" + width + "\n";
			origMetadata += "voxely=" + height + "\n";
			origMetadata += "voxelz=" + depth + "\n";

			//median filter (before we split the channels)
			if (gMedianFilter) {
			   print("         Applying median filter (to both channels)");
			   run("Median...", "radius=2 stack");
			   origMetadata += "bMedianFilter=1" + "\n";
			} else {
				origMetadata += "bMedianFilter=0" + "\n";
			}

			//de-interleave (split) ch1 and ch2
			if (actualChannels==2) {
				print("         Splitting into 2 stacks with Deinterleave");
				run("Deinterleave", "how=2"); //we destroy original, end up with ' #1' and ' #2'
			}
			
			//rename the 2 windows to something sane
			//in case the original file already has _ch1/_ch2
			strippedFileName = replace(currFile,"_ch1","");
			strippedFileName = replace(strippedFileName,"_ch2","");
			ch1Window = strippedFileName+"_ch1";
			ch2Window = strippedFileName+"_ch2";
			//channel 2
			if (actualChannels==2) {
				selectWindow(currFile+" #2"); //should be frontmost anyway
				rename(ch2Window);
				//channel 1
				selectWindow(currFile+" #1");
			}
			
			//this is for both 1 and 2 channels (for 2 channels, assuming it was selected in if {} above
			rename(ch1Window);
			
			if (gAlign) {
			   if (gAlignOnChannel==1) {
			   	firstWindow = ch1Window;
			   } else {
			   	if (gAlignOnChannel==2) {
			   		if (actualChannels==2) {
			   			firstWindow = ch2Window;
			   		} else {
			   			firstWindow = ch1Window;
			   		}
			   	}		
			   }
			   print("         Running MultiStackReg on " + firstWindow);
			   
			   //bring the channel to align to the front
			   selectWindow(firstWindow);
			   
			   nSlicesWeAreLookingAt = nSlices; // nSlices is a function call !!!
			   
			   //bail if this channel only has one channel (no alignment necc.)
			   if (nSlicesWeAreLookingAt>1) {
				middleSlice = floor(nSlices / 2);
				setSlice(middleSlice);
				print("            Num Slices="+nSlices+" middleSlice="+middleSlice);
	
			   	//run registration on ch2, saving the registration file
			   	//registration happens IN PLACE, no new window
			  	 fileStr = registerPath + replace(firstWindow,gFileType,"") + ".txt"; //"/Volumes/ONSLAUGHT/jhu/tst5.txt";
			  	 print("            Exporting registered stack coordinates to fileStr="+fileStr);
			  	 if (gAlignOtherChannel) {
			  	 	print("            Will apply these results to 'other' channel");
			  	 }
			   
			  	 run("MultiStackReg", "stack_1=" + firstWindow +" action_1=Align file_1=" + fileStr + " stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body] save");
			  	 origMetadata += "MultiStackReg=1" + "\n";

			  	 if (actualChannels==2) {
			  	 	//register ch1 using the .txt file we just created for ch2
					if (gAlignOnChannel==1)
						secondWindow = ch2Window;
					else
						secondWindow = ch1Window;

					//bring ch1 to front
					selectWindow(secondWindow);

					if (gAlignOtherChannel==1) {
						print("         Running MultiStackReg on 'other' channel, stack="+secondWindow);
						run("MultiStackReg", "stack_1=" + secondWindow +" action_1=[Load Transformation File] file_1=" + fileStr + " stack_2=None action_2=Ignore file_2=[] transformation=[Rigid Body]");
					}
					//save the 2nd channel
				   } //gNumberOfChannels==2
			   } //nSlicesWeAreLookingAt >= 1
			} //gAlign

			//make and save maximal z-projection
			selectWindow(ch1Window);
			if (gSaveMax) {
				run("Z Project...", "projection=[Max Intensity]"); //name is PREpended with MAX_
				if (actualChannels==2) {
					selectWindow(ch2Window);
					run("Z Project...", "projection=[Max Intensity]"); //name is PREpended with MAX_
				}
									   
				//ch1, save the max project
				selectWindow("MAX_" + ch1Window);
				tmpMaxFileName = "Max_" + ch1File + ".tif";
				print("         Saving MAX projection .tif file to: "+maxPath+tmpMaxFileName);
				saveAs("Tiff", maxPath+tmpMaxFileName);
	
				//ch2, save the max project
				if (actualChannels==2) {
					selectWindow("MAX_" + ch2Window);
					tmpMaxFileName = "Max_" + ch2File + ".tif";
					print("         Saving MAX projection .tif file to: "+maxPath+tmpMaxFileName);
					saveAs("Tiff", maxPath+tmpMaxFileName);
				}
				//close both max projections
				close();
				if (actualChannels==2) {
					close();
				}
			}

			//
			//save the result
			//
			
			//ch1
			selectWindow(ch1Window);
			//put the meta data back into the .tif
			setMetadata("Info", origMetadata);
			tmpFileName = ch1File + ".tif";
			if (gSaveStack) {
			   print("         Saving original .tif file to: "+alignedPath+tmpFileName);
			   saveAs("Tiff", alignedPath+tmpFileName);
			}
			//ch2
			if (actualChannels==2) {
				selectWindow(ch2Window);
				//put the meta data back into the .tif
				setMetadata("Info", origMetadata);
				tmpFileName = ch2File + ".tif";
				if (gSaveStack) {
				   print("         Saving original .tif file to: "+alignedPath+tmpFileName);
				   saveAs("Tiff", alignedPath+tmpFileName);
				}
			}
			//save detection params
			if (gSaveDetectionParams) {
			   //print("         Saving detection parameters");
			   bSave_DetectionParams(xmlPath, strippedName, origMetadata);
			}

			
			//close remaining windows
			if (actualChannels==2) close(); //close ch1

			close(); //close ch2
			
			actualIdx++;

		} //endsWith(tif)
	} //for i
	
	print("FINISH bAlignBatch_v5() at "+bGetDateTime());
	print("======================================");
	
} //bScanImageBatch
////////////////////////////////////////////////////////////////////////
function bGetDateTime() {
   getDateAndTime(year, month, dayOfWeek, dayOfMonth, hour, minute, second, msec);
   theRet = ""+year+"/"+month+1+"/"+dayOfMonth+" "+hour+":"+minute+":"+second;
   return theRet;
}
////////////////////////////////////////////////////////////////////////
//Windows: replace \ with /
//All Others: Do nothing
function bTransformPath(thePath) {
	theRet = thePath;
	theSep = "/";
	if (File.separator == "\\") { //special case on Windows (no change on Mac(Unix)/Linux)
		replaceThis = "\\\\";
		withThis = "\\\\\\\\";
		theRet = replace(thePath, replaceThis, withThis);
		//print("   bTransformPath() is returning theRet=" + theRet);
	}
	return theRet;
}
////////////////////////////////////////////////////////////////////////
//
// Get the last name ino a a path: this can be either(i) a file name or (ii) a folder
//
//function bGetLastInPath(str, osx_platform) {
//	if (osx_platform == 1) { // OS X
//		tmpList = split(str, "/");
//	}
//	if (osx_platform == 0) { // Windows
//		tmpList = split(str, "\\");
//	}
//	theRet = tmpList[tmpList.length-1];
//	return theRet;
//}
////////////////////////////////////////////////////////////////////////
//remove thisStr from the end of string
function bRemoveChannelPostfix(name, thisStr) {
	theRet = "":
	itEndsWith = endsWith(name, thisStr);
	if (itEndsWith==1) {
		theRet = replace(name, thisStr, "");	
	}
	return theRet
}
////////////////////////////////////////////////////////////////////////
//make global List with detection params
function sGetMetadata() {
	myMetadata = getMetadata("Info");
	List.setList(myMetadata);
	return List.getList();
}
////////////////////////////////////////////////////////////////////////
//save a text file
function bSave_DetectionParams(dstDir, name, detectionParams) {
	print ("         Saving Detection Parameters: " + dstDir +name+".txt");
	xmlDestDir = dstDir+name+".txt";
	xmlOutFile = File.open(xmlDestDir);
	print(xmlOutFile, detectionParams);
	File.close(xmlOutFile);
}


