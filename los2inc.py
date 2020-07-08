#!/usr/bin/env python
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot
import os
import isce
import sys
import numpy as np
import lxml.objectify as OB
import time
import sys
import logging
import re
import collections
import lxml.objectify as ob

###Create a memory map using numpy's memmap module.
def load_mmap(fname, nxx, nyy, map='BSQ', nchannels=1, channel=1, datatype=np.float32, quiet=False, conv=False):
    '''Create a memory map to data on file.

    Args:

        * fname   -> File name
        * nxx     -> Width
        * nyy     -> length

    KwArgs:
        * map       -> Can be 'BIL', 'BIP', 'BSQ'
        * nchannels -> Number of channels in the BIL file.
        * channel   -> The channel needed in the multi-channel file
        * datatype  -> Datatype of data in file
        * quiet     -> Suppress logging outputs
        * conv      -> Switch endian

    Returns:

        * fmap     -> The memory map.'''

    if quiet==False:
        logging.info('Reading input file: %s'%(fname))

    ####Get size in bytes of datatype
    ftemp = np.zeros(1, dtype=datatype)
    fsize = ftemp.itemsize

    if map.upper() == 'BIL':  #Band Interleaved by Line
        nshape = (nchannels*nyy-channel+1, nxx)
        noffset = (channel-1)*nxx*fsize

        try:
            omap = np.memmap(fname, dtype=datatype, mode='r', shape=nshape, offset = noffset)
        except:
            raise Exception('Could not open BIL style file or file of wrong size: ' + fname)

        if conv:
            gmap = omap.byteswap(False)
        else:
            gmap = omap

        nstrides = (nchannels*nxx*fsize, fsize)

        fmap = np.lib.stride_tricks.as_strided(gmap, shape=(nyy,nxx), strides=nstrides)

    elif map.upper() == 'BSQ': #Band Sequential
        noffset = (channel-1)*nxx*fsize*nyy
        try:
            gmap = np.memmap(fname, dtype=datatype, mode='r', shape=(nyy,nxx), offset=noffset)
        except:
            raise Exception('Could not open BSQ style file or file of wrong size: ' + fname)

        if conv:
            fmap = gmap.byteswap(False)
        else:
            fmap = gmap

    elif map.upper() == 'BIP': #Band interleaved by pixel
        nsamps = nchannels * nyy * nxx  - (channel-1)
        noffset = (channel-1)*fsize

        try:
            gmap = np.memmap(fname, dtype=datatype,mode='r', shape = (nsamps), offset = noffset)
        except:
            raise Exception('Could not open BIP style file or file of wrong size: ' + fname)

        if conv:
            omap = gmap.byteswap(False)
        else:
            omap = gmap

        nstrides = (nchannels*nxx*fsize, nchannels*fsize)
        fmap = np.lib.stride_tricks.as_strided(omap, shape=(nyy,nxx), strides=nstrides)

    return fmap


def los2inc(dir_paths, dims, results_path, ch = 1):
    #ch=1 #1=inc
    #ch=2 #2=az

    flt_in = (os.path.join(dir_paths[0],'merged/los.rdr.geo'))
    fwid = dims[0] #int(obj.bursts[0].image.width)     # width
    flen = dims[1] #int(obj.bursts[0].image.length)    # length
    flt= load_mmap(flt_in,fwid,flen,quiet=True,map='BIL',nchannels=2,channel=ch)
    outf = open(os.path.join(results_path,'inc.flt'),'wb')


    flt.tofile(outf)
    outf.close()
