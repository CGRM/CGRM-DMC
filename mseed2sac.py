#!/usr/bin/env python
# -*- coding:utf8 -*-
"""
Scripts used to trim earthquake event waveform from continues waveform.

miniSEED should be organized as:

    |--- YYYYMMDD
    |    |-- <net>.<sta>.<loc>.<cha>.<starttime>.mseed
    |    |-- <net>.<sta>.<loc>.<cha>.<starttime>.mseed
    |    `-- ...
    |--- YYYYMMDD
    |    |-- <net>.<sta>.<loc>.<cha>.<starttime>.mseed
    |    |-- <net>.<sta>.<loc>.<cha>.<starttime>.mseed
    |    `-- ...
    |--- ...

For example:

    |--- 20160101
    |    |-- NET1.STA1.00.BHE.20160101000000.mseed
    |    |-- NET1.STA1.00.BHN.20160101000000.mseed
    |    |-- NET1.STA1.00.BHZ.20160101000000.mseed
    |    `-- ...
    |--- 20160102
    |    |-- NET1.STA1.00.BHE.20160102000000.mseed
    |    |-- NET1.STA1.00.BHN.20160102000000.mseed
    |    |-- NET1.STA1.00.BHZ.20160102000000.mseed
    |    `-- ...
    |--- ...
"""
import os
import logging
from datetime import timedelta

from obspy import read, UTCDateTime
from obspy.io.sac import SACTrace


# Setup the logger
FORMAT = "[%(asctime)s]  %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
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

        Format of station information:

            NET.STA  latitude  longitude  elevation
        """
        stations = []
        with open(stationinfo, "r") as f:
            for line in f:
                name, stla, stlo, stel = line.split()[0:4]
                station = {"name": name,
                           "stla": float(stla),
                           "stlo": float(stlo),
                           "stel": float(stel),
                          }
                stations.append(station)
        logger.info("%d stations found.", len(stations))
        return stations

    def _get_dirname(self, starttime, endtime):
        """
        Get directory names based on starttime and endtime.
        """
        # mseed data are stored according to BJT not UTC
        starttime_in_bjt = starttime + timedelta(hours=8)
        endtime_in_bjt = endtime + timedelta(hours=8)

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
        pattern = station['name'] + ".*"
        if len(dirnames) == 1:  # one day
            fl_dr_nm = os.path.join(self.mseeddir, dirnames[0], pattern)
            try:
                st = read(fl_dr_nm)
            except Exception:
                logger.error("Error in reading %s", station['name'])
                return None
        elif len(dirnames) == 2:  # two days
            fl_dr_nm0 = os.path.join(self.mseeddir, dirnames[0], pattern)
            fl_dr_nm1 = os.path.join(self.mseeddir, dirnames[1], pattern)
            try:
                st = read(fl_dr_nm0) + read(fl_dr_nm1)
            except Exception:
                logger.error("Error in reading %s", station['name'])
                return None
        # Merge data
        try:
            st.merge(fill_value=0)
        except Exception:
            logger.error("Error in merging %s", station['name'])
            return None
        st.trim(starttime, endtime)
        return st

    def _writesac(self, stream, event, station, outdir):
        """
        Write data with SAC format with event and station information.
        """
        for trace in stream:  # loop over 3-component traces
            # transfer obspy trace to sac trace
            sac_trace = SACTrace.from_obspy_trace(trace=trace)

            # change some headers about station
            sac_trace.stla = station["stla"]
            sac_trace.stlo = station["stlo"]
            sac_trace.stel = station["stel"]

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
            sac_flnm = ".".join([origin.strftime("%Y.%j.%H.%M.%S"),
                                 "0000", trace.id, "M", "SAC"])
            sac_fullname = os.path.join(outdir, sac_flnm)
            sac_trace.write(sac_fullname)
        return

    def get_waveform(self, event, starttime, endtime):
        dirnames = self._get_dirname(starttime, endtime)
        logger.debug("dirnames: %s", dirnames)
        # check if folders exists
        for dirname in dirnames:
            if not os.path.exists(os.path.join(self.mseeddir, dirname)):
                msg = "{} not exist".format(dirname)
                logger.error(msg)
                return

        eventdir = event['origin'].strftime("%Y%m%d%H%M%S")
        outdir = os.path.join(self.sacdir, eventdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)

        # loop over all stations
        for station in self.stations:
            st = self._read_mseed(station, dirnames, starttime, endtime)
            # Reading error
            if not st:
                continue
            self._writesac(st, event, station, outdir)


def read_catalog(catalog):
    '''
    Read event catalog.

    Format of event catalog:

        origin  latitude  longitude  depth  magnitude  magnitude_type

    Example:

        2016-01-03T23:05:22.270  24.8036   93.6505  55.0 6.7  mww
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
    client = Client(stationinfo="station.info",
                    mseeddir="MSEED",
                    sacdir="SAC")

    events = read_catalog("events.csv")
    for event in events:
        logger.info("origin: %s", event['origin'])
        starttime = event['origin']
        endtime = starttime + 6000
        client.get_waveform(event, starttime, endtime)
