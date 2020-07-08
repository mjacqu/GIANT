#!/usr/bin/env python3
import os
import sys
import numpy as np
import lxml.objectify as OB
import stackSetup_alos_links as SS
import templateSetup as temp
import shutil
import argparse
import isce
import isceobj
from iscesys.Component.ProductManager import ProductManager as PM

def int2flt(dims, results_path):
    fid = open(os.path.join(results_path,'hgt.dem'),'rb')
    gid = open(os.path.join(results_path,'hgt.flt'),'wb')

    fwid = dims[0] #int(obj.bursts[0].image.width)     # width
    flen = dims[1] #int(obj.bursts[0].image.length)    # length

    for m in range(flen):
        line = np.fromfile(fid,dtype=np.int16,count=fwid)
        line = line.astype(np.float32)
        line.tofile(gid)

    fid.close()
    gid.close()
