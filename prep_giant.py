#!/usr/bin/env python
import os
import re
import sys
sys.path.append('/home/myja3483/isce_tools/ISCE')
from lxml import etree
import tops
import numpy as np
import lxml.objectify as OB
import stackSetup_alos_links as SS
import templateSetup as temp
import shutil
import argparse
import isce
from zerodop.geozero import createGeozero
import isceobj
from iscesys.Component.ProductManager import ProductManager as PM
#from isceobj.TopsProc import runGeocode

#This code is primarily provided by Magali Barba @ CU Boulder and edited for use
#as functions my Mylène Jacquemart (CU Boulder)

############
# Functions
############

# get width and length of interferograms to pass to prep_Giant
def get_width_length(file_path, dir_paths):
    xml_fn = os.path.join(dir_paths[0], 'merged/phsig.cor.geo.xml')
    root = etree.parse(xml_fn).getroot()
    length = root.xpath('property[@name="length"]/value')[0].text
    width = root.xpath('property[@name="width"]/value')[0].text
    return [int(width), int(length)]

# Create ref_point.txt
def make_ref_point(ref_pts, file_path, refpoint_file):
    with open(os.path.join(file_path, refpoint_file),'w') as pointFile:
        for item in ref_pts:
            pointFile.write('%s\n' % item)


# Create pair_list.txt
'''
Write pair_list.txt to file_path
'''
def make_pair_file(file_path, pairs_file, dirs):
    with open(os.path.join(file_path, pairs_file),'w') as pairFile:
        for item in dirs:
            pairFile.write('%s\n' % item)

# Make results directory
def results_dir(result_dir, result_path, overwrite):
    check = os.path.isdir(os.path.join(result_path, result_dir))
    result_dir = os.path.join(result_path, result_dir)
    if check == True:
        if overwrite == False:
            print ('Results directory exists. Rename or set overwrite to False')
        else:
            print('Overwriting previous results')
    if check == False:
        os.mkdir(os.path.join(result_path, result_dir))
        print('Created ' + result_dir + ' directory')
    return result_dir

# Make list of all pair directories
def make_dir_list(file_path):
    list_dir = os.listdir(file_path)
    regex = re.compile(r'\d{8}_\d{8}')
    dirs = np.sort(list(filter(regex.search, list_dir)))
    dir_paths = [os.path.join(file_path, d) for d in dirs]
    return dirs, dir_paths


def Seconds(instr):
    vals = instr.split(':')
    secs = float(vals[0]) * 3600 + float(vals[1]) * 60 + float(vals[2])
    return secs


def prep_giant(file_path, result_dir, ilist, ref, swaths, dims, bbox, atmos = '', roi = None, coh_th = 0.2, tempDir = '', force = True):
    #Get current directory
    currdir = os.getcwd()

    ##Check if GIAnT dir exists. Create it if not.
    #if os.path.isdir(prepDir):
    #    print("{0} directory already exists".format(prepDir))
    #else:
    #    os.mkdir(prepDir)


    pairs = []
    #####Get list of IFGS
    if ilist in ['',None]:
        pairs = SS.getPairDirs(dirname=file_path)
    else:
        pairs = SS.pairDirs_from_file(ilist, base=file_path)

    #Create ifg.list
    master_xml = 'master/IW'+str(swaths[0])+'.xml'
    ifglist = os.path.join(result_dir, 'ifg.list')
    obj = None
    if (not os.path.exists(ifglist)) or force == True:
        fid = open(ifglist, 'w')
        for pair in pairs:
            dates=os.path.basename(pair).split('_')
            print(pair)
            xmlFile = os.path.join(file_path,pair, master_xml)
            pm = PM()
            pm.configure()
            obj = pm.loadProduct(xmlFile) #Example: fine_interferogram.xml

            try:
                bTop = obj.baseline.perp_baseline_top
                bBot = obj.baseline.perp_baseline_bottom
                bPerp = 0.5*(bTop + bBot)
                print(bPerp)
            except:
                print("Pair %s processed with TopsApp.py")
                print("Baseline not available")
                bPerp = 0.0

            fid.write('{0}   {1}   {2:5.4f}  SENTINEL-1A\n'.format(dates[0], dates[1], bPerp))
        fid.close()


    #####Create example.rsc  ### GP added xObj = None otherwise it could not find child object
    obj = None
    if obj is None:
        exampleXML = os.path.join(file_path, pairs[0], master_xml)
        mergedXML = os.path.join(file_path, pairs[0], 'merged','filt_topophase.unw.geo.xml')
        pm = PM()
        pm.configure()
        obj = pm.loadProduct(exampleXML)

    #mergedpm= PM()
    #mergedpm.configure()
    #mergedObj= pm.loadProduct(mergedXML)

    rdict = {}
    rdict['heading']= float(obj.bursts[0].orbit.getHeading()) #obj.bursts[0].orbit.getHeading()
    rdict['peg_heading']= float(obj.orbit.getENUHeading(obj.bursts[obj.numberOfBursts//2].sensingMid)) #peg_heading
    rdict['utc']= Seconds(str(obj.bursts[obj.numberOfBursts//2].sensingMid).split( ' ')[-1])
    rdict['wvl'] = float(obj.bursts[0].radarWavelength)
    rdict['deltarg']=float(obj.bursts[0].rangePixelSize)
    rdict['deltaaz'] = float(obj.bursts[0].rangePixelSize)

    rdict['width'] = dims[0]# 11301#int(mergedObj.width)
    rdict['length'] = dims[1] #11009#int(mergedObj.length)
    #rdict['utc'] = Seconds(str(xObj.master.frame.sensing_mid).split( ' ')[-1])

    #print(obj.orbit.getENUHeading(obj.bursts[obj.numberOfBursts//2].sensingMid))
    #####Get Lat / Lon information
    minLat, maxLat, minLon, maxLon = bbox

    rscfile = os.path.join(result_dir, 'example.rsc')
    if (not os.path.exists(rscfile)) or force == True:
        temp.templateSetup(rdict, source=tempDir,target=result_dir, filename='example.rsc')


    #####Create lat.flt, lon.flt, hgt.flt
    DEMfile = os.path.join(file_path,pairs[0],'merged/dem.crop')
    shutil.copyfile(DEMfile, os.path.join(result_dir, 'hgt.dem'))

    lat = np.linspace(maxLat, minLat, num=rdict['length']).astype(np.float32)
    lats = np.lib.stride_tricks.as_strided(lat,
	    shape=(rdict['length'], rdict['width']), strides=(4,0))
    lats.tofile(os.path.join(result_dir, 'lat.flt'))
    del lat, lats

    lon = np.linspace(minLon, maxLon, num=rdict['width']).astype(np.float32)
    lons = np.lib.stride_tricks.as_strided(lon,
	    shape=(rdict['length'],rdict['width']), strides = (0,4))
    lons.tofile(os.path.join(result_dir, 'lon.flt'))
    del lon,lons

    #######Create userfn.py
    rdict = {}
    rdict['relpath'] = file_path
    rdict['polyorder'] = 1
    ufnfile = os.path.join(result_dir, 'userfn.py')
    if (not os.path.exists(ufnfile)) or force == True:
        temp.templateSetup(rdict, source=tempDir, target=result_dir, filename='userfn.py')

    ##########Create prepxml.py
    rdict = {}
    rdict['looks']= 1
    rdict['nvalid'] = int(0.08 * len(pairs))
    rdict['inc'] = 'inc.flt' #float(xObj.master.instrument.incidence_angle)
    rdict['filt'] = 0.5
    rdict['cohth'] = coh_th
    rdict['atmos'] = atmos
    if roi is None:
        rdict['start_width']= 0
        rdict['end_width']= dims[0]
        rdict['start_length']= 0
        rdict['end_length']= dims [1]
        latlon = np.loadtxt(ref)
        rdict['rx0'] = latlon[0]-5
        rdict['rx1'] = latlon[0]+5
        rdict['ry0'] = latlon[1]-5
        rdict['ry1'] = latlon[1]+5
    if roi is not None:
        rdict['start_width']= roi[0]			#specify cropped area
        rdict['end_width']= roi[1]			#specify cropped area
        rdict['start_length']= roi[2]			#specify cropped area
        rdict['end_length']= roi[3]			#specify cropped area
        latlon = np.loadtxt(ref)
        rdict['rx0'] = (latlon[0]-5)-roi[0]
        rdict['rx1'] = (latlon[0]+5)-roi[0]
        rdict['ry0'] = (latlon[1]-5)-roi[2]
        rdict['ry1'] = (latlon[1]+5)-roi[2]
    print(rdict)
    pxmlfile = os.path.join(result_dir, 'prepxml.py')
    if (not os.path.exists(pxmlfile)) or force == True:
        temp.templateSetup(rdict, source=tempDir, target=result_dir, filename='prepxml.py')
