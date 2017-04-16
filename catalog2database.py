#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from obspy import UTCDateTime
from datetime import datetime

BASE = "/data/Level1/CENC"
DIRROOT = "CENC"

if len(sys.argv) != 2:
    sys.exit("Usage: python {} events.csv".format(sys.argv[0]))

catalog = sys.argv[1]
print("id,date,time,evla,evlo,evdp,mag,imagtyp,dir")
with open(catalog, "r") as f:
    for line in f:
        origin, evla, evlo, evdp, mag, imagtyp = line.strip().split()
        date, time = origin.split('T')
        id = UTCDateTime(origin).strftime("%Y%m%d%H%M%S")
        entry = ",".join([id, date, time, evla, evlo, evdp, mag, imagtyp, os.path.join(DIRROOT, id)])
        if os.path.exists(os.path.join(BASE, id)):
            print(entry)
        else:
            print(line, end='', file=sys.stderr)
