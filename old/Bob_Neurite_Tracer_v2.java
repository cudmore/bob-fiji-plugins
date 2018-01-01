/* -*- mode: java; c-basic-offset: 8; indent-tabs-mode: t; tab-width: 8 -*- */

/*
 * Bob_Test.java
 *
 * Created on 20101212 by Bob Cudmore
 * Modified from Albert_Test.java
 */

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
//20140405, trying to save .csv with manager.exportToCSV

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

import ij.io.FileSaver; //to save the normal plane stack (one at a time for now)
import java.io.PrintWriter; //to save a text file (of valid stack slices)

//20111126
//import tracing.PathAndFillManager;
import tracing.*;

public class Bob_Neurite_Tracer_v2 implements PlugIn {

	String macroTiffFilename = "";

	String macroControlFilename = "";
		
	Integer bConvertTo8Bit = 0;
	Integer bDoCurvature = 0;
	Integer bQuitAtEnd = 0;

	//read in Bob_Neurite_Tracer_v2.param file
	public void readParams() {

		String paramFilename = IJ.getDirectory("plugins") + "bob-fiji-plugins/Bob_Neurite_Tracer_v2.param";
		
		IJ.log("Reading .param file: " + paramFilename);
		
		File paramFileToLoad = new File( paramFilename );

		//
		//Read a .param file with token=value: {tiffilename, controlfilename, convertto8bit, docurvature, quitatend} 
		
		int numParams = 5; //hard limit, number of params
		BufferedReader inFile = null;
		String str;
		
		try {
 		   //inFile = new BufferedReader(new FileReader("/Users/cudmore/jhu/anal/simple_neurite_tracer/a20100621_a71_s1z1_controlPnt_d1.marker"));
 		   inFile = new BufferedReader(new FileReader(paramFilename));
 		   while ((str = inFile.readLine()) != null) {
 		       String[] parts = str.split("=");
 		       String lhs = parts[0];
 		       String rhs = parts[1];

 		       //IJ.log("lhs:"+lhs);
 		       //IJ.log("rhs:"+rhs);
 		       //IJ.log(str);

 		       if (lhs.equals("tiffilename")) {
 		       		this.macroTiffFilename = rhs;
 		       }
 		       if (lhs.equals("controlfilename")) {
 		       		this.macroControlFilename = rhs;
 		       }
 		       if (lhs.equals("convertto8bit")) {
 		       		this.bConvertTo8Bit = Integer.parseInt(rhs);
 		       }
 		       if (lhs.equals("docurvature")) {
 		       		this.bDoCurvature = Integer.parseInt(rhs);
 		       }
 		       if (lhs.equals("quitatend")) {
 		       		this.bQuitAtEnd = Integer.parseInt(rhs);
 		       }
 		       } //while

 		   inFile.close();
		} catch (IOException e) {
			IJ.error("IOException while trying to read text file: " + e);
			return;
		}
		IJ.log("   Done Reading .param file.");

	}
	
	public void run(String ignored) {

		//if we turn this on we can save a normalized stack
		//requires us to rewrite Path.java to make xxx public
		boolean gSaveNormStack = false;
		
		IJ.log("============================");
		IJ.log("Start: Bob_Neurite_Tracer_v2");
		int destinationSize = 40; //destination height/width of normal plane stack

		readParams();
		
		//this is wierd here, i import ij.IJ and then use IJ (CASE SESNSITIVE)
		IJ.log("starting class Bob_Neurite_Tracer");
		IJ.log("   Options are:");
		IJ.log("      macroTiffFilename = '" + this.macroTiffFilename + "'");
		IJ.log("      macroControlFilename = '" + macroControlFilename + "'");
		IJ.log("      bConvertTo8Bit = '" + bConvertTo8Bit + "'");
		IJ.log("      bDoCurvature = '" + bDoCurvature + "'");
		IJ.log("      bQuitAtEnd = '" + bQuitAtEnd + "'");

		//boolean doNorm = false;
		//if( macroDoNormalStack != null ) {
		//	doNorm = true;
		//}

	
	//headless
	//IJ.log("trying to recycle .tif file");
	//ImagePlus imp = WindowManager.getCurrentImage();
	//if (imp==null) {
		//open the tif, this will then be used below via WindowManager.getCurrentImage()
		IJ.log("Opening .tif file");
//headless
		ImagePlus imp = IJ.openImage(macroTiffFilename);
		//imp = IJ.openImage(macroTiffFilename);
		if (imp == null) {
			IJ.error("Could not open image from file: " + macroTiffFilename);  
		}
	//}
		
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
			System.out.println("Prompting User For File...");
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
					IJ.error("The file '"+chosenFile.getAbsolutePath()+"' didn't exist");
					return;
				}
			}
		}
		//
		//Read a file with control points for line into an array and then loop on TracerThread, 
		System.out.println("Reading control point file...");
		IJ.log("Reading control point file...");
		
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

		IJ.log("   read " + Integer.toString(currRow) + " points");
		
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
				System.out.println("Converting to 8 bit image...");
				IJ.log("Converting to 8 bit image...");
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
//IJ.log("2 Reading control point file...");
		if (bDoCurvature.equals("1")) {
                        System.out.println("Calculating Curvatures...");
			IJ.log("Calculating Curvatures...");
                        // In most cases you'll get better results by using the Hessian
                        // based measure of curvatures at each point, so calculate that
                        // in advance.
                        hessian = new ComputeCurvatures(imagePlus, minimumSeparation, null, calibration != null);
                        hessian.run();

			System.out.println("   Finished calculating Curvatures.");
			IJ.log("   Finished calculating Curvatures.");
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
		
		IJ.log("Starting to trace...");

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
			
			//this will give a long Java error if x1,y1,z1 or x2,y2,z2 are out of image bound
			TracerThread tracer = new TracerThread(imagePlus, 0, 255, timeoutSeconds, reportEveryMilliseconds, x1, y1, z1, x2, y2, z2, reciprocal, depth == 1, hessian, ((hessian == null) ? 1 : 4), null, hessian != null );

			IJ.log("Running tracer " + (i+1) + " of " + (rowCount-1) + " ...");
			IJ.log("   Start: (" + x1 + "," + y1 + "," + z1 + "), Goal: (" + x2 + "," + y2 + "," + z2 + ")");
				
				tracer.run();
			
			IJ.log("   Finished running tracer");
	
			Path result = tracer.getResult();
			if (result == null) {
				IJ.log("ERROR in 'result'");
				IJ.error("ERROR: Finding a path failed: ");
				return;
			}

			//'fit volume' on the path we just found
			//this was from PathWindow.java
			//Path fitted = p.fitCircles( 40, plugin.getImagePlus(), (e.getModifiers() & ActionEvent.SHIFT_MASK) > 0, plugin );

			//Path fitted = result.fitCircles( 40, imagePlus, false, null );
			IJ.log("   Fitting circles and computing normal plane stack (wait awhile) ...");
			Path fitted = result.fitCircles( destinationSize, imagePlus, false );
			if (fitted == null) {
				IJ.error("Finding a fitted path failed (fitCircles): ");
//				IJ.error("Finding a fitted path failed (fitCircles): "+
//				SearchThread.exitReasonStrings[tracer.getExitReason()]);
				return;
				}
			IJ.log("   Finished");
		
			//append valid entries
			if (gSaveNormStack) {
			//	int bTotalPoints = result.size();
			//	boolean [] valid = result.bGetValid();
			//	for (int validi=0; validi<bTotalPoints ; validi++) {
			//	if( valid[validi] )
			//		bValidArray.add(new Integer(1));
			//		//pr.println(1);
			//	else
			//		bValidArray.add(new Integer(0));
			//		//pr.println(0);
			//	}
			//
			//	//append the normalized planes
			//	System.out.println("   Appending images to stack.");
			//	ImageStack bStack = result.bGetImageStack();
			//	int currStackSize = bStack.getSize();
			//	for (int currSlice=0; currSlice<currStackSize; currSlice++) {
			//		FloatProcessor tmpFloatProcessor = new FloatProcessor( destinationSize, destinationSize );
			//		tmpFloatProcessor.setPixels(bStack.getPixels(currSlice+1));
			//		destStack.addSlice(null, tmpFloatProcessor);
			//	}
			} //if gSaveNormStack
			
			//put this before the start of the loop
			//PathAndFillManager manager = new PathAndFillManager(imagePlus);
			
			//manager.addpath makes multiple paths, not one long one
			//we need to use one or both of the following
			//			setTemporaryPath( result );
			//			confirmTemporary( )

			//add the 'fitted' path we just found
			manager.addPath(fitted);
//this will add each path as a seperate line
//use it to make a sequence of lines that are the spine lines
//manager.addPath(fitted,true);
		
		} //i

		//we need this out here with some combination of set/confirm temporary
		//manager.addPath(fitted);
		
		//
		//Write out XML with full path x/y/z, tangent, and radius
		//
		File myOutFile;
		String outFileName = macroControlFilename + ".traces";
		try {
			myOutFile = new File( outFileName );
			IJ.log("Writing file to: " + myOutFile.getAbsolutePath());
			manager.writeXML(myOutFile.getAbsolutePath(), false);
			
			//03/2014
			String outFileName2 = macroControlFilename + ".csv";
			myOutFile2 = new File( outFileName2 );
			manager.exportToCSV(myOutFile2.getAbsolutePath());
		} catch (IOException e) {
			IJ.error("IOException while trying to write the path to a temporary file: " + e);
			return;
		}

		//
		//write out stack
		//
		if (gSaveNormStack) {
		//	String outStackFile = outNormalStackName + ".tif";
		//	ImagePlus outputImagePlus = new ImagePlus( "", destStack );
		//	FileSaver outputFS = new FileSaver(outputImagePlus);
		//	System.out.println("   Saving stack of normal planes as:" + outStackFile);
		//	outputFS.saveAsTiffStack(outStackFile);
		
		//	//
		//	//write out vector of valid
		//	//
		//	String validFile = outNormalStackName;
		//	validFile += "_valid" + ".txt";
		//	System.out.println("   Saving valid array");
		//	try
		//	{
		//		PrintWriter pr = new PrintWriter(validFile);    
		//		int bFinalSize = bValidArray.size();
		//		for (int validi=0; validi<bFinalSize ; validi++)
		//		{
		//			Integer currItem = (Integer) bValidArray.get(validi);
		//			if( currItem==1 )
		//				pr.println(1);
		//			else
		//				pr.println(0);
		//		}
		//		pr.close();
		//	}
		//	catch (Exception e)
		//	{
		//	    e.printStackTrace();
		//	    System.out.println("No such file exists:" + validFile);
		//	}
		} //gSaveNormStack
		
		//IJ.open(myOutFile.getAbsolutePath());

		System.out.println("Finish: Bob_Neurite_Tracer");
		IJ.log("Finish: Bob_Neurite_Tracer");
		IJ.log("============================");
		
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
