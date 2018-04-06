import os
import cv2 as cv
import numpy as np
import pylab
from scipy import *

# CONSTANTS ----------------------------------------------------------------------------------

DEBUG_ENABLE = True

HOUGH_PARAM_1 = 140
HOUGH_PARAM_2 = 100
HOUGH_MINRAD = 0
HOUGH_MAXRAD = 0

CONVERT_UNITS = True
CONVERT_TO_MICROLITRES = True
REFERENCE_DISTANCE_MICRON = 100.
REFERENCE_DISTANCE_PIXEL = 224.1
CHANNEL_HEIGHT = 60.

# debug function, show a window containing drawn out circle
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
        images.append(cv.imread(path + fname, 0))
    return images

# getCVCircles - takes a list of image handles, and returns a list of raw circles as outputted by CV
def getCVCircles(images):
    circles = []
    for image in images:
        circles.append(cv.HoughCircles(image, cv.HOUGH_GRADIENT, 1, 20, param1 = HOUGH_PARAM_1, param2 = HOUGH_PARAM_2, minRadius = HOUGH_MINRAD, maxRadius = HOUGH_MAXRAD))
        if DEBUG_ENABLE:
            debug_showFoundCircle(image, circles[-1])

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

# extract droplet flowrate
def extractDropletFlowrate(flowpair):
    return float(flowpair.split(',')[1])

# extract carrier flowrate
def extractCarrierFlowrate(flowpair):
    return float(flowpair.split(',')[0])

def performPixelVolumeConversion(distance_in_pixels):
    # convert to microns
    distance_in_microns = distance_in_pixels * (REFERENCE_DISTANCE_MICRON / REFERENCE_DISTANCE_PIXEL)
    
    # scale to meters
    xy_vals = distance_in_microns * 1e-6

    # account for droplet being squished in the channel
    #if(distance_in_microns > CHANNEL_HEIGHT):
    #    z_val = CHANNEL_HEIGHT * 10e-6
    #else:
    z_val = xy_vals

    # volume calculation
    volume = (4./3.) * np.pi * xy_vals * xy_vals * z_val
    if CONVERT_TO_MICROLITRES:
        volume = volume * 1e9
    return volume

# MAIN PROGRAM BEGINS HERE -------------------------------------------------------------------

img = getFileList('input/', '.bmp')
fimg = getFilteredFiles('TaperJunction', img)

img_handles = getCVImageList('input/', fimg)
circles_raw = getCVCircles(img_handles)


flowrate_hashes = extractFileNameToken(fimg)
flowrates = list(set(flowrate_hashes))

# create dictionary of detected flow rates, create an empty list at each index to populate
flowHashTable = {}
for flowrate in flowrates:
    flowHashTable[flowrate] = []

# populate hashtable with detected circle radii
for index in range(0, len(circles_raw)):
    tmp_circ = circles_raw[index][0][0]
    flowHashTable[flowrate_hashes[index]].append(tmp_circ[2])

# convert to array data type for data processing
for flowrate in flowrates:
    flowHashTable[flowrate] = array(flowHashTable[flowrate])
    # do unit conversion if requested
    if CONVERT_UNITS:
        flowHashTable[flowrate] = performPixelVolumeConversion(flowHashTable[flowrate])

# create new hashtable with mean and standard deviation data
meanHashTable = {}
stdDevHashTable = {}
for flowrate in flowrates:
    meanHashTable[flowrate] = np.mean(flowHashTable[flowrate])
    stdDevHashTable[flowrate] = np.std(flowHashTable[flowrate])

if DEBUG_ENABLE:
    print flowHashTable
    print meanHashTable
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
    scatter_x.extend([x_val] * len(flowHashTable[flowrate]))
    scatter_y.extend(flowHashTable[flowrate])
    average_x.append(x_val)
    average_y.append(meanHashTable[flowrate])
    errbar_y.append(stdDevHashTable[flowrate])

if DEBUG_ENABLE:
    print scatter_x
    print scatter_y

# convert everything to arrays
#scatter_x = array(scatter_x)
#scatter_y = array(scatter_y)
#average_x = array(average_x)
#average_y = array(average_y)
#errbar_y = array(errbar_y)

# perform pixel to volume conversion?
#if CONVERT_UNITS:
#    scatter_y = performPixelVolumeConversion(scatter_y)
#    average_y = performPixelVolumeConversion(average_y)
#    errbar_y = performPixelVolumeConversion(errbar_y)

title_text = ''
plot = pylab.figure()
subplot = plot.add_subplot(111)
subplot.plot(scatter_x, scatter_y, 'xb')
subplot.errorbar(average_x, average_y, fmt='-r', yerr=errbar_y, marker='s', capsize=2, ecolor='black')
subplot.set_xlabel(r'Droplet Phase Flow Rate ($\mu$L/min)')
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
plot.set_tight_layout(True)
pylab.show()
