#!/usr/bin/env python
# -*- coding:utf8 -*-
"""
Scripts used to trim earthquake event waveform from continues waveform

Files of miniSEED should be organized as <net>.<sta>.<loc>.<cha>.<starttime>.mseed
 eg. JX.WAA.00.BHZ.20160501000004.mseed

All these files collected in one day folder named as YYYYMMDD
 eg. 20160501
"""
from obspy import UTCDateTime
import datetime as dt
from obspy import read
import os
from obspy.io.sac import SACTrace

import logging


# ===============
# Setup the logger
# ===============
FORMAT = "[%(asctime)s]  %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Client(object):
    def __init__(self, stationinfo, mseeddir, sacdir):
        self.mseeddir = mseeddir
        self.sacdir = sacdir

        self.stations = self._read_stations(stationinfo)

    def _read_stations(self, stationinfo):
        """
        Read station information from station metadata file.
        """
        stations = []
        with open(stationinfo, "r") as f:
            for line in f:
                name, stla, stlo, stel, stdp = line.split()[0:5]
                station = {"name": name,
                           "stla": float(stla),
                           "stlo": float(stlo),
                           "stel": float(stel),
                           "stdp": float(stdp),
                           }
                stations.append(station)
        return stations

    def _get_dirname(self, starttime, endtime):
        """
        Get directory names based on starttime and endtime.
        """
        # mseed data are stored according to BJT not UTC
        starttime_in_bjt = starttime + dt.timedelta(hours=8)
        endtime_in_bjt = endtime + dt.timedelta(hours=8)

        if starttime_in_bjt.date == endtime_in_bjt.date:  # one day
            return [starttime_in_bjt.strftime("%Y%m%d")]
        else:  # two days
            return [starttime_in_bjt.strftime("%Y%m%d"),
                    endtime_in_bjt.strftime("%Y%m%d")]

    def _read_mseed(self, station, dirnames, starttime, endtime):
        """
        Trim waveform for particular event.
        """
        # return none if dirnames is empty
        if not dirnames:
            return

        # obtain event waveform
        if len(dirnames) == 1:  # one day
            pattern = ".".join([list(station.keys())[0], "*"])
            fl_dr_nm = os.path.join(self.mseeddir, dirnames[0], pattern)
            try:
                st = read(fl_dr_nm)
            except Exception:
                msg = "Error in Reading {} !".format(list(station.keys())[0])
                logger.error(msg)
                return None
        elif len(dirnames) == 2:  # two days
            pattern = ".".join([list(station.keys())[0], "*"])
            fl_dr_nm0 = os.path.join(self.mseeddir, dirnames[0], pattern)
            fl_dr_nm1 = os.path.join(self.mseeddir, dirnames[1], pattern)
            try:
                st = read(fl_dr_nm0) + read(fl_dr_nm1)
            except Exception:
                msg = "Error in Reading {} !".format(list(station.keys())[0])
                logger.error(msg)
                return None
        # Merge data
        try:
            st.merge(fill_value=0)
        except Exception:
            msg = "Error in Reading {} !".format(list(station.keys())[0])
            logger.error(msg)
            return None
        st.trim(starttime, endtime)
        return st

    def _writesac(self, stream, event, station):
        """
        Write data with SAC format with event and station information.
        """
        for trace in stream:
            key = ".".join([trace.stats.network, trace.stats.station])

            # write missed station info into miss_station.list
            if key not in station:
                logger.warning(" No Station info for %s", key)
                return
            # transfer obspy trace to sac trace
            sac_trace = SACTrace.from_obspy_trace(trace=trace)

            # change some headers about station
            sac_trace.stla = station["stla"]
            sac_trace.stlo = station["stlo"]
            sac_trace.stel = station["stel"]
            sac_trace.stdp = station["stdp"]

            if trace.stats.channel[-1] == "E":
                sac_trace.cmpaz = 90
                sac_trace.cmpinc = 90
            elif trace.stats.channel[-1] == "N":
                sac_trace.cmpaz = 0
                sac_trace.cmpinc = 90
            elif trace.stats.channel[-1] == "Z":
                sac_trace.cmpaz = 0
                sac_trace.cmpinc = 0
            else:
                logger.warning("Not E|N|Z component")

            # change some headers about event
            sac_trace.evla = event["latitude"]
            sac_trace.evlo = event["longitude"]
            sac_trace.evdp = event["depth"]
            sac_trace.mag = event["magnitude"]
            # change reference time
            origin = event["origin"]
            sac_trace.nzyear = origin.year
            sac_trace.nzjday = origin.julday
            sac_trace.nzhour = origin.hour
            sac_trace.nzmin = origin.minute
            sac_trace.nzsec = origin.second
            sac_trace.nzmsec = origin.microsecond / 1000
            sac_trace.o = 0
            sac_trace.iztype = 'io'

            # SAC file location
            sub_fldr_nm = origin.strftime("%Y%m%d%H%M%S")
            sac_loc = os.path.join(self.sacdir, sub_fldr_nm)
            if not os.path.exists(sac_loc):
                os.mkdir(sac_loc)
            sac_flnm = ".".join([origin.strftime("%Y.%j.%H.%M.%S"),
                                 "0000", trace.id, "M", "SAC"])
            sac_fullname = os.path.join(sac_loc, sac_flnm)
            sac_trace.write(sac_fullname)
        return

    def get_waveform(self, event, duration):
        dirnames = self._get_dirname(event["origin"], duration)
        # check if folders exists
        for dirname in dirnames:
            if not os.path.exists(os.path.join(self.mseeddir, dirname)):
                msg = "{} not exist".format(dirname)
                logger.error(msg)
                return
        for station in self.stations:    # loop over all stations
            st = self._read_mseed(
                station, dirnames, event["origin"], event["origin"]+duration)
            # Reading error
            if not st:
                continue
            self._writesac(st, event, station)


def read_catalog(catalog):
    '''
    Read event catalog.
    '''

    events = []
    with open(catalog) as f:
        for line in f:
            origin, latitude, longitude, depth, magnitude = line.split()[0:5]
            event = {
                "origin": UTCDateTime(origin),
                "latitude": float(latitude),
                "longitude": float(longitude),
                "depth": float(depth),
                "magnitude": float(magnitude),
            }
            events.append(event)
    return events


if __name__ == '__main__':
    client = Client(stationinfo="../station.info.norm",
                    mseeddir="/run/media/seispider/Seagate Backup Plus Drive/",
                    sacdir="../test/")
    duration = 6000

    events = read_catalog("../bg6.5.csv")
    for event in events:
        client.get_waveform(event, duration)
