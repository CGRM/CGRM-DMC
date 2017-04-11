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
        self.catalog = catalog
        self.stationinfo = stationinfo
        self.mseeddir = mseeddir
        self.sacdir = sacdir

        self.stations = self._read_stations()

    # =================
    # Load station info
    # =================
    def _read_stations(self):
        """
        function used to load the station info.

        @stationinfo: dict     ;dict of station infos
        """
        if not os.path.isfile(self.stationinfo):
            msg = "{} file not exist!\n".format(self.stationinfo)
            logger.error(msg)
            self.stationinfo = raw_input("Please input file location:\n")

        with open(self.stationinfo) as f:
            lines = f.readlines()

        stations = {}
        for line in lines:
            net, sta = (line.split()[0]).split(".")

            stla, stlo, stel, stdp = line.split()[-4:]
            key = ".".join([net, sta])
            value = {
                "stla": stla, "stlo": stlo, "stel": stel,
                "stdp": stdp, "sta": sta, "net": net
            }
            stations[key] = value
        return stations
    # =================
    # Obtain data folder name
    # =================

    def get_dirname(self, starttime, duration):
        """
        function used to obtain the folder name

        @starttime: str           ;starttime of event in UTC
        @duration: int            ;duration of trimming [Unit = second]
        @folder_name: list        ;The folder name
         """
        # change string starttime to UTCDateTime
        utcevent = UTCDateTime(starttime)
        # Change this UTC time to Beijing Time(BJT_Event)
        bjt_event = utcevent + dt.timedelta(hours=8)
        # obtain end time of Beijing time zone
        end_bjt_event = bjt_event + duration

        # transfer UTCDatetime to string
        bjt_event_str = bjt_event.strftime("%Y%m%d")
        end_bjt_event_str = end_bjt_event.strftime("%Y%m%d")

        folder_name = []
        if bjt_event_str == end_bjt_event_str:
            folder_name.append(bjt_event_str)
        else:
            folder_name.append(bjt_event_str)
            folder_name.append(end_bjt_event_str)

        return utcevent, folder_name

    def _read_mseed(self, station, dirnames, utcevent, duration):
        """
        trim waveform for particular event

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
        st.trim(utcevent, utcevent + duration)
        return st

    def writesac(self, st, station, event, utcevent):
        """
        function used to write data with SAC format
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
            sac_trace_init = SACTrace()
            sac_trace = sac_trace_init.from_obspy_trace(trace=Trace)

            # change some headers about station
            sac_trace.stla = float(station[key]["stla"])
            sac_trace.stlo = float(station[key]["stlo"])
            sac_trace.stel = float(station[key]["stel"])
            sac_trace.stdp = float(station[key]["stdp"])

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
            sac_trace.evla = float(event["latitude"])
            sac_trace.evlo = float(event["longitude"])
            sac_trace.evdp = float(event["depth"])
            sac_trace.mag = float(event["magnitude"])
            # change reference time
            sac_trace.nzyear = utcevent.year
            sac_trace.nzjday = utcevent.julday
            sac_trace.nzhour = utcevent.hour
            sac_trace.nzmin = utcevent.minute
            sac_trace.nzsec = utcevent.second
            sac_trace.nzmsec = utcevent.microsecond / 1000
            sac_trace.o = 0
            sac_trace.iztype = 'io'

            # SAC file lodation
            sub_fldr_nm = utcevent.strftime("%Y%m%d%H%M%S")
            sac_loc = os.path.join(self.sacdir, sub_fldr_nm)
            if not os.path.exists(sac_loc):
                os.mkdir(sac_loc)
            sac_flnm = [utcevent.strftime("%Y.%j.%H.%M.%S")]
            sac_flnm += ["0000"]
            sac_flnm += [
                str(sac_trace.knetwk), str(sac_trace.kstnm),
                "00", str(sac_trace.kcmpnm), "M", "SAC"
            ]
            sac_flnm_str = ".".join(sac_flnm)
            sac_pathname = os.path.join(sac_loc, sac_flnm_str)
            sac_trace.write(sac_pathname)
        return

    # ===============
    # get_waveform
    # ===============
    def get_waveform(self, event, duration):
        utcevent, dirnames = self.get_dirname(event["starttime"], duration)
        # check if folders exists
        for i in range(len(dirnames)):
            if not os.path.exists(os.path.join(self.mseeddir, dirnames[i])):
                msg = "{} not exist".format(dirnames[i])
                logger.error(msg)
                return
        for key, value in self.stations.iteritems():    # loop over all stations
            station = {key: value}
            st = self._read_mseed(station, dirnames, utcevent, duration)
            # Reading error
            if not st:
                continue
            self.writesac(st, station, event, utcevent)


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
            "starttime": starttime,
            "latitude": latitude,
            "longitude": longitude,
            "depth": depth,
            "magnitude": magnitude,
        }
        events.append(event)
    return events

if __name__ == '__main__':
    client = Client(
        "../station.info.norm",
        "/run/media/seispider/Seagate Backup Plus Drive/",
        "../test/"
    )
    duration = 6000

    events = read_catalog("../bg6.5.csv")
    for event in events:
        client.get_waveform(event, duration)
