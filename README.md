# pyDropletUtility
pyDropletUtility is a small GUI driven application for automatic characterization of the performance characteristics of droplet generating microfluidic chip geometry. Namely, the program takes a set of images captured at various flow rates following lab file naming conventions, extracts the flow rates for droplets, and creates calibration curves of droplet volumes at various flow rates.

File naming conventions follow the format: YYYY_MM_DD_INITIALS_BK#P#_PHOTO_Description-Flowrate1,Flowrate2-Replicate#.bmp

## Dependencies
pyDropletUtility is written entirely in Python 2. In addition to the base Python binaries, pyDropletUtility requires:
- numpy
- scipy
- matplotlib
- OpenCV version 3 or greater, with OpenCV-Python bindings installed
- GTK2 + PyGTK, libglade

pyDropletUtility should run on any platform where all of these prerequisites are met, but is only tested on Mac OSX and Windows Subsystem for Linux (Ubuntu, VcXsrv)
## Usage
The program requires some work to be done by the user to ensure accurate readings. Distances and volumes are calculated by mapping a known feature in photographs to a distance in pixels, and converting between these measurements. These distances in pixels can be found using ImageJ, Adobe Photoshop or comparable. In addition, the feature height of your microfluidic chips should be known to account for pancaking. Correctly configuring the parameters for Hough circle detection requires some trial and error. Hough Parameter 1 controls the thresholding for the edge detection, and Hough Parameter 2 controls the sensitivity of circle detection. Lower values on either can lead to false positives, the preview feature should be used to ensure that only a single circle is being detected in each image. Default values for the sample data set are already entered in the GUI.

Using the preview feature helps to set hough parameters before running the script for the entire data set and generating a calibration curve.
