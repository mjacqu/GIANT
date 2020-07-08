#!/usr/bin/python
import numpy as np
import h5py
import matplotlib.pyplot as plt
import geocode
import matplotlib.dates

#load data
hfile = h5py.File('/home/myja3483/Landslides/Bigsur/Results/Giant_desc_manualremoval/Stack/NSBAS-PARAMS.h5', 'r')
list(hfile.keys())
data = hfile['rawts']
dates = hfile['dates']
np.savetxt('dates.txt', dates)

for d in range(0,len(dates)):
    np.savetxt(str(matplotlib.dates.num2date(dates)[d].date())+'.txt', data[d,:,:]) #save to text file for reading into python3



#############
#save to geotiff
#not verified to work currently

xmin,ymin,xmax,ymax = [lons.min(),lats.min(),lons.max(),lats.max()]
nrows,ncols = np.shape(gc_data)
xres = (xmax-xmin)/float(ncols)
yres = (ymax-ymin)/float(nrows)
geotransform=(xmin,xres,0,ymax,0, -yres)
# That's (top left x, w-e pixel resolution, rotation (0 if North is up),
#         top left y, rotation (0 if North is up), n-s pixel resolution)
# I don't know why rotation is in twice???
from osgeo import gdal
from osgeo.gdalconst import *
from osgeo import osr
output_raster = gdal.GetDriverByName('GTiff').Create('2015_raw.tif',ncols, nrows, 1 ,gdal.GDT_Float32)  # Open the file
output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
srs = osr.SpatialReference()                 # Establish its coordinate encoding
srs.ImportFromEPSG(4326)                     # This one specifies WGS84 lat long.
                                             # Anyone know how to specify the
                                             # IAU2000:49900 Mars encoding?
output_raster.SetProjection( srs.ExportToWkt() )   # Exports the coordinate system
                                                   # to the file
output_raster.GetRasterBand(1).WriteArray(gc_data)   # Writes my array to the raster

output_raster.FlushCache()

'''
