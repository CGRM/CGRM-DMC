#!/usr/bin/env python
# -*- coding:utf8 -*-
"""
Scripts used to trim earthquake event waveform from continues waveform

Files of miniSEED should be organized as <net>.<sta>.<loc>.<cha>.<starttime>.mseed
 eg. JX.WAA.00.BHZ.20160501000004.mseed

All these files collected in one day folder named as YYYYMMDD
 eg. 20160501

@Data_dir: string     ;Directory of Data
@Catalog_dirname: string  ;Directory+name of events Catalog_dir
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
        self.stationinfo = stationinfo
        self.mseeddir = mseeddir
        self.sacdir = sacdir

        self.stations = self._read_stations()

    def _read_stations(self):
        """
        Read station information from station metadata file.

        @stationinfo: dict     ;dict of station infos
        """
        with open(self.stationinfo, "r") as f:
            lines = f.readlines()

        stations = {}
        for line in lines:
            key, stla, stlo, stel, stdp = line.split()[0:5]
            value = {
                "stla": float(stla),
                "stlo": float(stlo),
                "stel": float(stel),
                "stdp": float(stdp),
            }
            stations[key] = value
        return stations

    def _get_dirname(self, starttime, duration):
        """
        Get dirname based on event starttime.

        @starttime: str           ;starttime of event in UTC
        @duration: int            ;duration of trimming [Unit = second]
        @folder_name: list        ;The folder name
        """
        # mseed data are stored according to BJT not UTC
        starttime_in_bjt = starttime + dt.timedelta(hours=8)
        endtime_in_bjt = starttime_in_bjt + duration

        starttime_in_bjt_str = starttime_in_bjt.strftime("%Y%m%d")
        endtime_in_bjt_str = endtime_in_bjt.strftime("%Y%m%d")

        folder_name = []
        if starttime_in_bjt_str == endtime_in_bjt_str:
            folder_name.append(starttime_in_bjt_str)
        else:
            folder_name.append(starttime_in_bjt_str)
            folder_name.append(endtime_in_bjt_str)

        return folder_name

    def _read_mseed(self, station, dirnames, starttime, duration):
        """
        Trim waveform for particular event.

        """
        # return none if dirnames is empty
        if not dirnames:
            return

        # obtain event waveform
        if len(dirnames) == 1:  # one day
            pattern = ".".join([station.keys()[0], "*"])
            fl_dr_nm = os.path.join(self.mseeddir, dirnames[0], pattern)
            try:
                st = read(fl_dr_nm)
            except Exception:
                msg = "Error in Reading {} !".format(station.keys()[0])
                logger.error(msg)
                return None
        elif len(dirnames) == 2:  # two days
            pattern = ".".join([station.keys()[0], "*"])
            fl_dr_nm0 = os.path.join(self.mseeddir, dirnames[0], pattern)
            fl_dr_nm1 = os.path.join(self.mseeddir, dirnames[1], pattern)
            try:
                st = read(fl_dr_nm0) + read(fl_dr_nm1)
            except Exception:
                msg = "Error in Reading {} !".format(station.keys()[0])
                logger.error(msg)
                return None
        # Merge data
        try:
            st.merge(fill_value=0)
        except Exception:
            msg = "Error in Reading {} !".format(station.keys()[0])
            logger.error(msg)
            return None
        st.trim(starttime, starttime + duration)
        return st

    def _writesac(self, st, station, event):
        """
        Write data with SAC format with event and station information.
        """
        for i in range(len(st)):
            Trace = st[i]
            key = ".".join([Trace.stats.network, Trace.stats.station])

            # write missed station info into miss_station.list
            if key not in station:
                logger.warn("Warning: No Station info for %s", key)
                with open(os.path.join("./Log.list"), "a") as f:
                    f.write(key + "no station info")
                return
            # transfer obspy trace to sac trace
            sac_trace = SACTrace.from_obspy_trace(trace=Trace)

            # change some headers about station
            sac_trace.stla = station[key]["stla"]
            sac_trace.stlo = station[key]["stlo"]
            sac_trace.stel = station[key]["stel"]
            sac_trace.stdp = station[key]["stdp"]

            if Trace.stats.channel[-1] == "E":
                sac_trace.cmpaz = 90
                sac_trace.cmpinc = 90
            if Trace.stats.channel[-1] == "N":
                sac_trace.cmpaz = 0
                sac_trace.cmpinc = 90
            if Trace.stats.channel[-1] == "Z":
                sac_trace.cmpaz = 0
                sac_trace.cmpinc = 0

            # change some headers about event
            sac_trace.evla = event["latitude"]
            sac_trace.evlo = event["longitude"]
            sac_trace.evdp = event["depth"]
            sac_trace.mag = event["magnitude"]
            # change reference time
            starttime = event["starttime"]
            sac_trace.nzyear = starttime.year
            sac_trace.nzjday = starttime.julday
            sac_trace.nzhour = starttime.hour
            sac_trace.nzmin = starttime.minute
            sac_trace.nzsec = starttime.second
            sac_trace.nzmsec = starttime.microsecond / 1000
            sac_trace.o = 0
            sac_trace.iztype = 'io'

            # SAC file lodation
            sub_fldr_nm = starttime.strftime("%Y%m%d%H%M%S")
            sac_loc = os.path.join(self.sacdir, sub_fldr_nm)
            if not os.path.exists(sac_loc):
                os.mkdir(sac_loc)
            sac_flnm = [starttime.strftime("%Y.%j.%H.%M.%S")]
            sac_flnm += ["0000"]
            sac_flnm += [
                str(sac_trace.knetwk), str(sac_trace.kstnm),
                "00", str(sac_trace.kcmpnm), "M", "SAC"
            ]
            sac_flnm_str = ".".join(sac_flnm)
            sac_pathname = os.path.join(sac_loc, sac_flnm_str)
            sac_trace.write(sac_pathname)
        return

    def get_waveform(self, event, duration):
        dirnames = self._get_dirname(event["starttime"], duration)
        # check if folders exists
        for i in range(len(dirnames)):
            if not os.path.exists(os.path.join(self.mseeddir, dirnames[i])):
                msg = "{} not exist".format(dirnames[i])
                logger.error(msg)
                return
        for key, value in self.stations.iteritems():    # loop over all stations
            station = {key: value}
            st = self._read_mseed(station, dirnames, event["starttime"], duration)
            # Reading error
            if not st:
                continue
            self._writesac(st, station, event)


def read_catalog(catalog):
    """
    Read event catalog.

    @events: list    ;list of dictionary which contain starttime, latitude,
                        longitude, depth, magnitude
    """

    with open(catalog) as f:
        lines = f.readlines()

    events = []
    for line in lines:
        starttime, latitude, longitude, depth, magnitude = line.split()[0:5]
        event = {
            "starttime": UTCDateTime(starttime),
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
