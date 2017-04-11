#! /usr/bin/env python
# -*- coding:utf8 -*-

import os
import glob
import sys
import subprocess as sp

os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

if len(sys.argv) != 2:
    print "Usage: python dirname"

p = sp.Popen(['sac'], stdin=sp.PIPE)
drnm = sys.argv[1]
fldnm_lst = glob.glob(os.path.join(drnm, "*"))
s = ""
for fldnm in fldnm_lst:
    # call sac
    flnm_lst = glob.glob(os.path.join(fldnm, "*.SAC"))
    for flnm in flnm_lst:
        s += "rh {}\n".format(flnm)
        s += "wh\n"
s += "q\n"
p.communicate(s.encode())

