#! /usr/bin/env python
# -*- coding:utf8 -*-

import os
import glob
import sys
import subprocess as sp

os.putenv("SAC_DISPLAY_COPYRIGHT", '0')

if len(sys.argv) == 1:
    sys.exit("Usage: python dirname")

for event in sys.argv[1:]:
    p = sp.Popen(['sac'], stdin=sp.PIPE)
    s = ""
    filelist = glob.glob(os.path.join(event, "*.SAC"))
    for fname in filelist:
        s += "rh {}\n".format(fname)
        s += "wh\n"
    s += "q\n"
    p.communicate(s.encode())
