import numpy as np
import os
import re
import sys
sys.path.append('/home/myja3483/isce_tools/ISCE')
import tops
from ast import literal_eval
import prep_giant
import int2flt
import los2inc

# 1. Set parameters
results_directory = 'Giant_desc'
overwrite = True
file_path = '/net/tiampostorage/volume1/MyleneShare/Bigsur_desc/az1rng2'
ref_pts = [800, 1357] # [x, y]=[col, row]=[range, azimuth]
coh_th = 0.3

results_path = '/home/myja3483/Landslides/Bigsur/Results'
refpoint_file = 'ref_point.txt'
pairs_file = 'pair_list.txt'
roi = [640, 920, 1200, 1450] #[col_min, col_max, row_min, row_max]
#atmos = 'ECMWF'#no atmospheric correction.

# 2. Set up file structure and create initial files
dirs, dir_paths = prep_giant.make_dir_list(file_path)

result_dir = prep_giant.results_dir(results_directory, results_path, overwrite)
prep_giant.make_pair_file(file_path, pairs_file, dirs)
prep_giant.make_ref_point(ref_pts, file_path, refpoint_file)
dims = prep_giant.get_width_length(file_path, dir_paths)
ilist = os.path.join(file_path, pairs_file)
ref = os.path.join(file_path, refpoint_file)
swaths = literal_eval(tops.Pair.from_path(dir_paths[0]).swaths)
bbox = literal_eval(tops.Pair.from_path(dir_paths[0]).bbox)

# Run prep_Giant.py
prep_giant.prep_giant(file_path, result_dir, ilist, ref, swaths, dims, bbox, coh_th = coh_th, roi = roi, tempDir = '', force = True)

# Run int2flt + los2inc:
int2flt.int2flt(dims, os.path.join(results_path, results_directory))
los2inc.los2inc(dir_paths, dims, os.path.join(results_path, results_directory))
