/* -*- mode: java; c-basic-offset: 8; indent-tabs-mode: t; tab-width: 8 -*- */

/*
 * Bob_Test.java
 *
 * Created on 20101212 by Bob Cudmore
 * Modified from Albert_Test.java
 */

//201412, rewriting this for new version of bStack
//goals:
//	1) simplify command line interface, basically get rid of everyhting
//	2) determine if my fitting with x/y/z == 1/1/1 is good
//		my contorl pnt file has to be int
//	3) just spit out a .swc file for each SEGMENT
//	4) have bStack load a number of swc files

//useful fiji wiki page
//   http://pacific.mpi-cbg.de/wiki/index.php/Developing_Fiji
//this file sits in:
//   fiji/src-plugin/Simple_Neurite_Tracer/tracing/Bob_Test.java
//20110311, first time build
//   sh Build.sh run
//   20110311, the line above is one time (After downloading with git)
//incremental build (after I make changes to Bob_test.java):
//   cd ./fiji
//   ./fiji --build
//be sure to modify, fiji/src-plugin/Simple_Neurite_Tracer/ with
// Plugins, "Bob Test", tracing.Bob_Test
//be sure to increae the memory of the compiled fiji app (edit:options:memory)
// be sure to make Contents folder in ./fiji/Contents
//
//once compiled, copy ~/cudmore/fiji/plugins/Simple_Neurite_Tracer.jar
// into stock fiji (downloaded/updated version)
//   Applications/Fiji.app/plugins
//
//to update git repository
// cd fiji/
// git pull

//20110408, Mark updated simple neurite tracer to handle 16bit images (on 'fit')
//20110817, adding new argument to open image on first plugin call
//	now we call with fiji [tif] [line] ...
//20111126, added gSaveNormStack to turn off finding the normal plane
//		with this we can now run plugin by dropping it into an axisting Fiji install
//		because we no longer need a new version of Path.java
//

//20111126, removed when detaching from Path and 'Simple NEurite Tracer'
//package tracing;

import ij.*;				
import features.ComputeCurvatures;
import ij.IJ;
import ij.ImagePlus;
import ij.WindowManager;
import ij.plugin.PlugIn;
import ij.measure.Calibration;
import ij.gui.*;			
import ij.io.*;			
//import ij.process.ImageConverter; //to convert to 8-bit i necc
import ij.process.StackConverter; //to convert to 8-bit i necc

import java.io.*;			
import java.util.StringTokenizer;	
import java.util.ArrayList;

import ij.process.ImageConverter;	//to include method convert(ImagePlus image)
import ij.process.StackConverter;
import ij.process.FloatProcessor;

//import ij.io.FileSaver; //to save the normal plane stack (one at a time for now)
import java.io.PrintWriter; //to save a text file (of valid stack slices)

//to use list 20141214
import java.util.List;
import javax.vecmath.Point3f;

//20141214, to save my list in serialized form
//import java.io.FileOutputStream;
//import java.io.PrintWriter

//20111126
import tracing.*;

public class Bob_Neurite_Tracer_v3 implements PlugIn {

	public void run(String ignored) {
		int showOutput = 0; //added 20141217

		//if we turn this on we can save a normalized stack
		//requires us to rewrite Path.java to make xxx public
		boolean gSaveNormStack = false;
		
		if (showOutput==1) {
			System.out.println(" ");
			System.out.println("Start: Bob_Neurite_Tracer_v1");
		}
		int destinationSize = 40; //destination height/width of normal plane stack

		//
		//parse the macro options, getting a filename of control points
		//macro options are: controlfilename=<FILENAME>
		//
		String macroOptions = Macro.getOptions();
		
		if (showOutput==1) {
			IJ.log(macroOptions);
		}
		
		String macroTiffFilename = null;

		String macroControlFilename = null;
		//String macroDoNormalStack = null;
		
		String bConvertTo8Bit = null;
		String bDoCurvature = null;
		String bQuitAtEnd = null;
		
		if( macroOptions != null ) {
			macroTiffFilename = Macro.getValue(macroOptions, "tiffilename", null );
			macroControlFilename = Macro.getValue(macroOptions, "controlfilename", null );
			bConvertTo8Bit = Macro.getValue(macroOptions, "convertto8bit", null );
			bDoCurvature = Macro.getValue(macroOptions, "docurvature", null );
			bQuitAtEnd = Macro.getValue(macroOptions, "quitatend", null );
		}

		if (showOutput==1) {
			System.out.println("   Options are:");
			System.out.println("      macroTiffFilename = '" + macroTiffFilename + "'");
			System.out.println("      macroControlFilename = '" + macroControlFilename + "'");
			System.out.println("      bConvertTo8Bit = '" + bConvertTo8Bit + "'");
			System.out.println("      bDoCurvature = '" + bDoCurvature + "'");
			System.out.println("      bQuitAtEnd = '" + bQuitAtEnd + "'");
			
			//this is wierd here, i import ij.IJ and then use IJ (CASE SESNSITIVE)
			IJ.log("starting class Bob_Neurite_Tracer_v3");
			IJ.log("   Options are:");
			IJ.log("      macroTiffFilename = '" + macroTiffFilename + "'");
			IJ.log("      macroControlFilename = '" + macroControlFilename + "'");
			IJ.log("      bConvertTo8Bit = '" + bConvertTo8Bit + "'");
			IJ.log("      bDoCurvature = '" + bDoCurvature + "'");
			IJ.log("      bQuitAtEnd = '" + bQuitAtEnd + "'");
		}
		
		//boolean doNorm = false;
		//if( macroDoNormalStack != null ) {
		//	doNorm = true;
		//}

		//headless
		//IJ.log("trying to recycle .tif file");
		//ImagePlus imp = WindowManager.getCurrentImage();
		//if (imp==null) {
		//open the tif, this will then be used below via WindowManager.getCurrentImage()
		if (showOutput==1) {
			System.out.println("Opening .tif file");
			IJ.log("Opening .tif file");
		}
		//headless
		ImagePlus imp = IJ.openImage(macroTiffFilename);
		//imp = IJ.openImage(macroTiffFilename);
		if (imp == null) {
			IJ.error("Could not open image from file: " + macroTiffFilename); 
		}
		//}

		// Remove scale, tracing assumes we have 1x1x1 voxels
		//run("Properties...", "channels=1 slices=120 frames=1 unit=um pixel_width=.1 pixel_height=.1 voxel_depth=1 frame=[0 sec] origin=0,0");
		//20140521, taken from
		//http://stackoverflow.com/questions/15658954/imagej-calibrating-an-image-to-a-physical-scale-using-calibration
		if (showOutput==1) {
			IJ.log("   Removing calibration, we always trace in 1x1x1 pixels");
		}
		Calibration cal = imp.getCalibration();
		cal.setUnit("pixels");
		cal.pixelWidth = 1;
		cal.pixelHeight = 1;
		cal.pixelDepth = 1;
		cal.xOrigin = 0;
		cal.yOrigin = 0;
		cal.zOrigin = 0;
		imp.setCalibration(cal);

		//headless?
		//imp.show();
		
		//open the text file with 3D control points
		File controlFileToLoad = null;
		if( macroControlFilename != null ) {
			controlFileToLoad = new File( macroControlFilename );
			if( controlFileToLoad.exists() ) {
				//pathAndFillManager.loadGuessingType( controlFileToLoad.getAbsolutePath() );
				//System.out.println("Loading File: " + macroControlFilename);
			}
			else
				IJ.error("The control file suggested by the macro parameters ("+macroControlFilename+") does not exist");
		}
		else {
			if (showOutput==1) {
				System.out.println("Prompting User For File...");
			}
		}
		//if we still do not have a file, prompt for one
		String directory = ""; //don't assign default, see how it works
		if ( controlFileToLoad == null ) {
			OpenDialog od;
			od = new OpenDialog("Select .traces or .swc file...", directory, null );
			macroControlFilename = od.getFileName();
			directory = od.getDirectory();
			if( macroControlFilename != null ) {
				File chosenFile = new File( directory, macroControlFilename );
				if( ! chosenFile.exists() ) {
					if (showOutput==1) {
						IJ.error("The file '"+chosenFile.getAbsolutePath()+"' didn't exist");
					}
					return;
				}
			}
		}
		//
		//Read a file with control points for line into an array and then loop on TracerThread, 
		if (showOutput==1) {
			System.out.println("Reading control point file...");
			IJ.log("Reading control point file...");
		}
		
//HARD LIMIT
//stupid to use int but the tracing engine TracerThread() seems to only work with int???
		int numRowsInArray = 50; //hard limit, fix this later and make it dynamic
		int[][] myArray = new int[numRowsInArray][3]; //I need to get the number of rows from the file
		StringTokenizer st = null;
		int currRow = 0;
		int rowCount = 0; //remove this, it is redundant
		BufferedReader inFile = null;
		String str;
		
		try {
 		   //inFile = new BufferedReader(new FileReader("/Users/cudmore/jhu/anal/simple_neurite_tracer/a20100621_a71_s1z1_controlPnt_d1.marker"));
 		   inFile = new BufferedReader(new FileReader(macroControlFilename));
 		   while ((str = inFile.readLine()) != null) {
 		       st = new StringTokenizer(str, ","); //break comma separated line using ","
	 		       myArray[currRow][0] = Integer.parseInt(st.nextToken());
	 		       myArray[currRow][1] = Integer.parseInt(st.nextToken());
	 		       myArray[currRow][2] = Integer.parseInt(st.nextToken());
 		       currRow++;
 		       rowCount++;
 		   }
 		   inFile.close();
		} catch (IOException e) {
			IJ.error("IOException while trying to read text file: " + e);
			return;
		}
		
		// This is an example of tracing between two random
		// points in an image synchronously.  For an
		// example of how to use these classes in a asynchronous
		// way, see the Simple_Neurite_Tracer plugin.
		//headless	
		//original
		//ImagePlus imagePlus = WindowManager.getCurrentImage();
		//ImagePlus imagePlus = WindowManager.getImage(macroTiffFilename) ;
		ImagePlus imagePlus = imp;
		if (imagePlus == null) {
			IJ.error("No current image to use.");
			return;
		}

		int width = imagePlus.getWidth();
		int height = imagePlus.getHeight();
		int depth = imagePlus.getStackSize();

		if (bConvertTo8Bit.equals("1")) {
			if( ! (imagePlus.getType() == ImagePlus.GRAY8 ||
			       imagePlus.getType() == ImagePlus.COLOR_256) ) {
				//before I added convert()
				//IJ.error("This plugin only works on 8 bit images");
				if (showOutput==1) {
					System.out.println("Converting to 8 bit image...");
					IJ.log("Converting to 8 bit image...");
				}
				convert(imagePlus);
				//return;
			}
			if( ! (imagePlus.getType() == ImagePlus.GRAY8 ||
				imagePlus.getType() == ImagePlus.COLOR_256) ) {
				IJ.error("Still not 8 bit: This plugin only works on 8 bit images");
				return;
			}
		} // if (bConvertTo8Bit)

		//start
		int x1; int y1; int z1;
		//goal
		int x2; int y2; int z2;

		// Use the reciprocal of the value at the new point as the cost
		// in moving to it (scaled by the distance between the points.
		boolean reciprocal = true;

		Calibration calibration = imagePlus.getCalibration();
		double minimumSeparation = 1;
		if( calibration != null )
			minimumSeparation = Math.min(Math.abs(calibration.pixelWidth),
						     Math.min(Math.abs(calibration.pixelHeight),
							      Math.abs(calibration.pixelDepth)));

                ComputeCurvatures hessian=null;
		//if (showOutput==1) {
		//	IJ.log("2 Reading control point file...");	
                //}
                if (bDoCurvature.equals("1")) {
                        if (showOutput==1) {
                        	System.out.println("Calculating Curvatures...");
				IJ.log("Calculating Curvatures...");
                        }
                        // In most cases you'll get better results by using the Hessian
                        // based measure of curvatures at each point, so calculate that
                        // in advance.
                        hessian = new ComputeCurvatures(imagePlus, minimumSeparation, null, calibration != null);
                        hessian.run();

			if  (showOutput==1) {
				System.out.println("   Finished calculating Curvatures.");
				IJ.log("   Finished calculating Curvatures.");
        		}
                }

		// Give up after 3 minutes.
		// int timeoutSeconds = 3 * 60;
                int timeoutSeconds = 5 * 60;

		// This doesn't matter in this case, since there's no
		// interface that'll need updating.  However, it'll only
                // check whether the timeout has expired every time this
                // interval is up, so don't set it too high.
		long reportEveryMilliseconds = 3000;

		//moved from below
		PathAndFillManager manager = new PathAndFillManager(imagePlus);

		//destination stack, save after loop
		ImageStack destStack = null;
		if (gSaveNormStack) {
			destStack = new ImageStack( destinationSize, destinationSize );
		}
		
		//strip off '.txt'
		String outNormalStackName = macroControlFilename.substring(0,macroControlFilename.length()-4);

		ArrayList bValidArray = new ArrayList();
		
		if (showOutput==1) {
			System.out.println("Starting to trace");
			IJ.log("Starting to trace");
		}
		
		//20141214
		//as we connect points, put all pnts into this array
		ArrayList<Point3f> masterPointList = new ArrayList<Point3f>();

		//sequentially connect points [0,1], [1,2], [2,3], ... [rowCount-2,rowCount-1]
		//how do I make this one long path rather than a sequence of paths???
		for (int i=0; i<rowCount-1; i++) {
			//current start
			x1 = myArray[i][0];	
			y1 = myArray[i][1];	
			z1 = myArray[i][2];	
			//current goal
			x2 = myArray[i+1][0];	
			y2 = myArray[i+1][1];	
			z2 = myArray[i+1][2];	
			TracerThread tracer = new TracerThread(imagePlus, 0, 255, timeoutSeconds, reportEveryMilliseconds, x1, y1, z1, x2, y2, z2, reciprocal, depth == 1, hessian, ((hessian == null) ? 1 : 4), null, hessian != null );

			if (showOutput==1) {
				System.out.println("Running tracer " + (i+1) + " of " + (rowCount-1) + " ...");
				System.out.println("   Start: (" + x1 + "," + y1 + "," + z1 + "), Goal: (" + x2 + "," + y2 + "," + z2 + ")");
				IJ.log("Running tracer " + (i+1) + " of " + (rowCount-1) + " ...");
				IJ.log("   Start: (" + x1 + "," + y1 + "," + z1 + "), Goal: (" + x2 + "," + y2 + "," + z2 + ")");
			}
				
			//
			tracer.run();
			//
			
			if (showOutput==1) {
				System.out.println("   Finished running tracer...");
			}
			
			Path result = tracer.getResult();
			if (result == null) {
				IJ.error("ERROR: Finding a path failed: ");
				return;
			}

			//'fit volume' on the path we just found
			//this was from PathWindow.java
			//Path fitted = p.fitCircles( 40, plugin.getImagePlus(), (e.getModifiers() & ActionEvent.SHIFT_MASK) > 0, plugin );

			//Path fitted = result.fitCircles( 40, imagePlus, false, null );
			//added 201412
			int doFitRadii = 0;
			if (doFitRadii==1) {
				if (showOutput==1) {
					System.out.println("   Fitting circles and computing normal plane stack (wait awhile) ...");
					IJ.log("   Fitting circles and computing normal plane stack (wait awhile) ...");
				}
				Path fitted = result.fitCircles( destinationSize, imagePlus, false );
				if (fitted == null) {
					IJ.error("Finding a fitted path failed (fitCircles): ");
					return;
				}
				System.out.println("      Finished");
				manager.addPath(fitted);
			} else {
				manager.addPath(result);
	
				//20141214, try and save each sequential fiji path (the list of points between each contorl point)
				//20141214 we can get a list of points from the path
				//List<Point3f> getPoint3fList()
	
				//ArrayList<Point3f> masterPointList = new ArrayList<Point3f>(); //declared above
				List<Point3f> pathPointList; //get the path as a list of points (THIS)
				pathPointList = result.getPoint3fList();
	
				//System.out.println(pathPointList);
				//float[] myFloat = new float[3];
				for (Point3f myPnt : pathPointList) {
					masterPointList.add(myPnt); //append to my list of 3d points
					//myPnt.get(myFloat);
					//System.out.println(myFloat[0] + "," + myFloat[0] + "," + myFloat[0]);
				}
			}
		
			
		} //i, point to search between

		//
		//write masterPointList to a file
		//naive version
		PrintWriter myMasterFile;
		String myMasterFileName = macroControlFilename + ".master";
		try {
			myMasterFile = new PrintWriter( myMasterFileName );
			//System.out.println("Writing file to:" + myOutFile.getAbsolutePath());
			//IJ.log("Writing file to:" + myOutFile.getAbsolutePath());
		
			float[] myFloat = new float[3];
			for (Point3f myPnt : masterPointList) {
				myPnt.get(myFloat);
				//System.out.println(myFloat[0] + "," + myFloat[0] + "," + myFloat[0]);
				myMasterFile.println(myPnt.toString());
			}
			myMasterFile.close();

			//for Windows, write a .finished file
			String myFinishedFileName = macroControlFilename + ".finished";
			PrintWriter myFinishedFile;
			myFinishedFile = new PrintWriter( myFinishedFileName );
			myFinishedFile.close();
			
		} catch (IOException e) {
			IJ.error("IOException while trying to write myMasterFile with all points: " + e);
		}

		//serialized version, this does not work as i can only seem to write binary file object, not the values in the list???
		//try {
		//	FileOutputStream fos = new FileOutputStream("t.tmp");
		//	ObjectOutputStream oos = new ObjectOutputStream(fos);
		//	oos.writeObject(masterPointList);
		//	oos.close();
		//} catch (IOException e) {
		//	IJ.error("Error while writing all points to a single file: " + e);
		//}
		
		if (showOutput==1) {
			System.out.println("Finish: Bob_Neurite_Tracer_v3");
			IJ.log("Finish: Bob_Neurite_Tracer_v3");
		}
		
		if (bQuitAtEnd.equals("1")) {
			IJ.doCommand("Quit");		
		}
	} //run
	
	//////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////
	//taken from Fiji 3d viewer plugin (ContentCreator.java)
	//////////////////////////////////////////////////////////////////
	//////////////////////////////////////////////////////////////////
	public static void convert(ImagePlus image) {
		int imaget = image.getType();
		if(imaget == ImagePlus.GRAY8 || imaget == ImagePlus.COLOR_256)
			return;
		int s = image.getStackSize();
		switch(imaget) {
			case ImagePlus.GRAY16:
			case ImagePlus.GRAY32:
				if(s == 1)
					new ImageConverter(image).convertToGray8();
				else
					new StackConverter(image).convertToGray8();
				break;
		}
	} //convert

}
