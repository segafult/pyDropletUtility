#!/usr/bin/env python
import os
import cv2 as cv
import numpy as np
import pylab
from scipy import *
import gtk, gtk.glade


# FLAGS AND DEFAULTS --------------------------------------------------------------------------

DEBUG_ENABLE = False

HOUGH_PARAM_1 = 140
HOUGH_PARAM_2 = 100
HOUGH_MINRAD = 0
HOUGH_MAXRAD = 0

CONVERT_UNITS = True
CONVERT_TO_MICROLITRES = True
REFERENCE_DISTANCE_MICRON = 100.
REFERENCE_DISTANCE_PIXEL = 224.1
CHANNEL_HEIGHT = 60.

DIRECTORY = 'input/'
FILTER = 'TaperJunction'

SHOW_RAW = True
SHOW_ERROR = True

# FUNCTION DECLARATIONS ------------------------------------------------------------------------

# debug function, show a window containing drawn out circle - deprecated with addition of GUI
def debug_showFoundCircle(img, circle_output):
    circle_cleanedup = np.uint16(np.around(circle_output))
    cimg = cv.cvtColor(img, cv.COLOR_GRAY2BGR)
    for i in circle_cleanedup[0,:]:
        cv.circle(cimg,(i[0],i[1]),i[2],(0,255,0),2)
    cv.imshow('DEBUG', cimg)
    cv.waitKey(0)
    cv.destroyAllWindows()


# getFileList - takes a directory and extension and returns a list of paths to files with that extension
def getFileList(path, extension):
    files = os.listdir(path)
    filtered_files = []
    for f in files:
        if f.endswith(extension):
            filtered_files.append(f)
    return filtered_files

# getFilteredFiles - takes a list of files and returns a list 
def getFilteredFiles(search_term, filenames):
    filtered = []
    for filename in filenames:
        if search_term in filename:
            filtered.append(filename)
    return filtered

# getImageList - takes a directory and a list of files, and returns a list of image handles
def getCVImageList(path, filenames):
    images = []
    for fname in filenames:
        images.append(cv.imread(path + fname, 1))
    return images

# getCVCircles - takes a list of image handles, and returns a list of raw circles as outputted by CV
def getCVCircles(images):
    circles = []
    for image in images:
        # create grayscale image for Hough transform and append list of found circles
        image_bw = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
        circles.append(cv.HoughCircles(image_bw, cv.HOUGH_GRADIENT, 1, 20, param1 = HOUGH_PARAM_1, param2 = HOUGH_PARAM_2, minRadius = HOUGH_MINRAD, maxRadius = HOUGH_MAXRAD))
#        if DEBUG_ENABLE:
#            debug_showFoundCircle(image, circles[-1])

    return circles

# extractFileNameToken - takes a filename of format:
# YYYY_MM_DD_INITIAL_bkNumpgNum_PHOTO_CHIP-Label-OilFlow,AqFlow-Replicate.ext
# and splits delimeters to return a list of OilFlow,AqFlow
def extractFileNameToken(filenames):
    flow_tokens = []
    for filename in filenames:
        # remove experimental and date info
        no_exp_info = filename.split('_')[-1]
        # flowrates should be second last token, before replicate number
        flow_tokens.append(no_exp_info.split('-')[-2])
    return flow_tokens

# extractDropletFlowrate - returns carrier phase flow rate from a string of format cc,dd
def extractDropletFlowrate(flowpair):
    return float(flowpair.split(',')[1])

# extractCarrierFlowrate - returns carrier phase flow rate from a string of format cc,dd
def extractCarrierFlowrate(flowpair):
    return float(flowpair.split(',')[0])

# performPixelVolumeConversion - takes a distance in pixels and returns the volume of a droplet in either cubic meters or microliters, depending on channel height
def performPixelVolumeConversion(distance_in_pixels):
    # convert to microns
    distance_in_microns = distance_in_pixels * (REFERENCE_DISTANCE_MICRON / REFERENCE_DISTANCE_PIXEL)
    
    # scale to meters
    xy_vals = distance_in_microns * 1e-6

    # account for droplet being pancaked in the channel, approximate as an ovular shape
    if(distance_in_microns > CHANNEL_HEIGHT):
        z_val = CHANNEL_HEIGHT * 10e-6
    else:
        z_val = xy_vals

    # volume calculation
    volume = (4./3.) * np.pi * xy_vals * xy_vals * z_val
    if CONVERT_TO_MICROLITRES:
        volume = volume * 1e9
    return volume

# GUI declaration: Done here for forward declaration
MainGUI = gtk.glade.XML('Application.glade')

# GUI HANDLER DECLARATIONS ------------------------------------------------------------------------------------

# UpdateValsFromGUI is called before every preview and run, updates all flags with their values in the GUI
def UpdateValsFromGUI():
    global DEBUG_ENABLE
    global HOUGH_PARAM_1
    global HOUGH_PARAM_2
    global HOUGH_MINRAD
    global HOUGH_MAXRAD
    global CONVERT_UNITS
    global CONVERT_TO_MICROLITRES
    global REFERENCE_DISTANCE_MICRON
    global REFERENCE_DISTANCE_PIXEL
    global CONVERT_UNITS
    global CONVERT_TO_MICROLITRES
    global REFERENCE_DISTANCE_MICRON
    global REFERENCE_DISTANCE_PIXEL
    global CHANNEL_HEIGHT
    global DIRECTORY
    global FILTER
    global SHOW_RAW
    global SHOW_ERROR

    DEBUG_ENABLE = MainGUI.get_widget('val_Debug').get_active()
    HOUGH_PARAM_1 = MainGUI.get_widget('val_HoughParam1').get_value()
    HOUGH_PARAM_2 = MainGUI.get_widget('val_HoughParam2').get_value()
    HOUGH_MINRAD = (int)(MainGUI.get_widget('val_MinRad').get_value())
    HOUGH_MAXRAD = (int)(MainGUI.get_widget('val_MaxRad').get_value())
    
    # Switching for radio buttons
    if MainGUI.get_widget('val_UnitPixels').get_active():
        CONVERT_UNITS = False
    else:
        CONVERT_UNITS = True
        if MainGUI.get_widget('val_UnitMicro').get_active():
            CONVERT_TO_MICROLITRES = True
        else:
            CONVERT_TO_MICROLITRES = False

    REFERENCE_DISTANCE_MICRON = (float)(MainGUI.get_widget('val_RefMicron').get_text())
    REFERENCE_DISTANCE_PIXEL = (float)(MainGUI.get_widget('val_RefPx').get_text())
    CHANNEL_HEIGHT = (float)(MainGUI.get_widget('val_ChannelHeight').get_text())

    DIRECTORY = MainGUI.get_widget('val_InputDir').get_text()
    FILTER = MainGUI.get_widget('val_FilterText').get_text()

    SHOW_RAW = MainGUI.get_widget('val_ShowRawData').get_active()
    SHOW_ERROR = MainGUI.get_widget('val_ShowMeanError').get_active()
    


# RunProg
# Formerly main body of program: executes upon clicking the run button and generates a plot
def RunProg(widget):
    # Fetch new values from the GUI widgets
    UpdateValsFromGUI()

    # Get list of all bitmaps in selected directory and filter by search term
    img = getFileList(DIRECTORY, '.bmp')
    fimg = getFilteredFiles(FILTER, img)

    # Open all files as CV images, and find circles in each image
    img_handles = getCVImageList(DIRECTORY, fimg)
    circles_raw = getCVCircles(img_handles)
    
    # Get a matched list of flow rates, and a shortened unique version of the flow rates (for dictionary)
    flowrate_hashes = extractFileNameToken(fimg)
    flowrates = list(set(flowrate_hashes))
    
    # create dictionary of detected flow rates, create an empty list at each index to populate
    flowHashTable = {}
    for flowrate in flowrates:
        flowHashTable[flowrate] = []
    
    # populate hashtable with detected circle radii - only use one of the circles for each data point
    for index in range(0, len(circles_raw)):
        tmp_circ = circles_raw[index][0][0]
        flowHashTable[flowrate_hashes[index]].append(tmp_circ[2])
    
    # convert to array data type for data processing and perform unit conversions
    for flowrate in flowrates:
        # do unit conversion if requested - new in GUI version, not parallelized due to branching control
        if CONVERT_UNITS:
            for index in range(0,len(flowHashTable[flowrate])):
                flowHashTable[flowrate][index] = performPixelVolumeConversion(flowHashTable[flowrate][index])
        flowHashTable[flowrate] = np.array(flowHashTable[flowrate])
    
    # create new hashtable with mean and standard deviation data
    meanHashTable = {}
    stdDevHashTable = {}
    for flowrate in flowrates:
        meanHashTable[flowrate] = np.mean(flowHashTable[flowrate])
        stdDevHashTable[flowrate] = np.std(flowHashTable[flowrate])
    
    if DEBUG_ENABLE:
        print 'Flow rates: hash table'
        print flowHashTable
        print 'Means: hash table'
        print meanHashTable
        print 'Standard deviation: hash table'
        print stdDevHashTable
    
    # convert hashtable data into usable graphable x,y pairs
    scatter_x = []
    scatter_y = []
    average_x = []
    average_y = []
    errbar_y = []
    for flowrate in flowrates:
        # get the droplet phase flow rate
        x_val = extractDropletFlowrate(flowrate)
        # extend with identical x values for appropriate number of data points
        scatter_x.extend([x_val] * len(flowHashTable[flowrate]))
        # extend y data with y values
        scatter_y.extend(flowHashTable[flowrate])
        average_x.append(x_val)
        average_y.append(meanHashTable[flowrate])
        errbar_y.append(stdDevHashTable[flowrate])
    
    if DEBUG_ENABLE:
        print 'Scatter plot: x values'
        print scatter_x
        print 'Scatter plot: y values'
        print scatter_y
    
    title_text = ''
    plot = pylab.figure()
    subplot = plot.add_subplot(111)
    # Plot based on selected items to plot
    if SHOW_RAW:
        subplot.plot(scatter_x, scatter_y, 'xb')
    if SHOW_ERROR:
        subplot.errorbar(average_x, average_y, fmt='-r', yerr=errbar_y, marker='s', capsize=2, ecolor='black')
    subplot.set_xlabel(r'Droplet Phase Flow Rate ($\mu$L/min)')

    # Set y axis label based on the set flags
    if CONVERT_UNITS:
        title_text = 'Volume'
        if CONVERT_TO_MICROLITRES:
            subplot.set_ylabel(r'Droplet Volume ($\mu$L)')
        else:
            subplot.set_ylabel(r'Droplet Volume ($m^3$)')
    else:
        title_text = 'Radius'
        subplot.set_ylabel('Droplet Radius (px)')
    
    # extract carrier flowrate (assumed constant) to make title
    title_assembled = 'Droplet ' + title_text + ' as a Function of Droplet Phase Flow Rate at ' + str(extractCarrierFlowrate(flowrates[0])) + ' $\mu$L/min'
    subplot.set_title(title_assembled)
    # show graph
    plot.set_tight_layout(True)
    pylab.show()


# RunPreview - Called when preview button is pressed. Gets input images and creates a preview image from one of these after finding circles with the selected parameters
def RunPreview(widget):
    # Fetch new values from the GUI widgets
    UpdateValsFromGUI()

    # Get list of all bitmaps in selected directory and filter by search term
    img = getFileList(DIRECTORY, '.bmp')
    fimg = getFilteredFiles(FILTER, img)

    img_handles = getCVImageList(DIRECTORY, fimg)
    image_bw = cv.cvtColor(img_handles[0], cv.COLOR_BGR2GRAY)

    # find circle in one (first) image
    circles = cv.HoughCircles(image_bw, cv.HOUGH_GRADIENT, 1, 20, param1 = HOUGH_PARAM_1, param2 = HOUGH_PARAM_2, minRadius = HOUGH_MINRAD, maxRadius = HOUGH_MAXRAD)
    
    # draw circles on preview image
    img_circles = img_handles[0]
    circles_cleanedup = np.uint16(np.around(circles))
    for i in circles_cleanedup[0,:]:
        cv.circle(img_circles,(i[0],i[1]),i[2],(255,0,0),2)
    
    # create pixel buffer from preview image, scale to an appropriate size with bilinear interpolation
    pixbuf = gtk.gdk.pixbuf_new_from_data(img_circles.tostring(), gtk.gdk.COLORSPACE_RGB, False, 8, 1280, 1024, 1280 * 3)
    # hard coded resolutions (for now)
    pixbuf = pixbuf.scale_simple(800,600,gtk.gdk.INTERP_BILINEAR)
    
    # update the preview image in the main window from pixel buffer
    img_gtk = MainGUI.get_widget('img_Preview')
    img_gtk.set_from_pixbuf(pixbuf)
    img_gtk.show()

# ShowAboutDialog - Shows the program info
def ShowAboutDialog(widget):
    MainGUI.get_widget('aboutdialog1').show()

def HideAboutDialog(widget, data):
    MainGUI.get_widget('aboutdialog1').hide()

# RunExit - 
def RunExit(widget):
    print 'exit'
    gtk.main_quit()

# MAIN PROGRAM BODY -------------------------------------------------------------------------------------------------

# bind signals and handlers and show GUI
dic = {'on_run_clicked':RunProg, 
        'on_preview_clicked':RunPreview, 
        'on_exit_clicked':RunExit,
        'on_window1_destroy':RunExit,
        'on_file_Exit_activate':RunExit,
        'on_help_About_activate':ShowAboutDialog,
        'on_aboutdialog1_response':HideAboutDialog}
MainGUI.signal_autoconnect(dic)
MainGUI.get_widget('window1').show()
gtk.main()
