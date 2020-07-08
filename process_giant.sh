#!/bin/bash
cd /home/myja3483/Landslides/Bigsur/Results/Giant_desc_manualremoval

python prepxml.py
python /usr/local/giant/GIAnT/SCR/PrepIgramStack.py
cp example.rsc Stack/hgt.flt.rsc
python /usr/local/giant/GIAnT/SCR/ProcessStack.py
python /usr/local/giant/GIAnT/SCR/NSBASInvert.py -nproc 8
python /usr/local/giant/GIAnT/SCR/plotts.py -f Stack/NSBAS-PARAMS.h5 -y -30 30 -raw
