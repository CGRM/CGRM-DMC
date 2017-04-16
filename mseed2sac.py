#!/usr/bin/env python
# -*- coding:utf8 -*-
"""
Scripts used to trim earthquake event waveform from continues waveform.

miniSEED should be organized as:

    |--- YYYYMMDD
    |    |-- NET.STA.LOC.CHA.STARTTIME.mseed
    |    |-- NET.STA.LOC.CHA.STARTTIME.mseed
    |    `-- ...
    |--- YYYYMMDD
    |    |-- NET.STA.LOC.CHA.STARTTIME.mseed
    |    |-- NET.STA.LOC.CHA.STARTTIME.mseed
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

Output SAC files are organized as:

    |--- YYYYMMDDHHMMSS
    |    |-- YYYY.JDAY.HH.MM.SS.0000.NET.STA.LOC.CHA.M.SAC
    |    |-- YYYY.JDAY.HH.MM.SS.0000.NET.STA.LOC.CHA.M.SAC
    |    `-- ...
    |--- YYYYMMDDHHMMSS
    |    |-- YYYY.JDAY.HH.MM.SS.0000.NET.STA.LOC.CHA.M.SAC
    |    |-- YYYY.JDAY.HH.MM.SS.0000.NET.STA.LOC.CHA.M.SAC
    |    `-- ...
    |--- ...

For example:


    |--- 20160103230522
    |    |-- 2016.003.23.05.22.0000.AH.ANQ.00.BHE.M.mseed
    |    |-- 2016.003.23.05.22.0000.AH.ANQ.00.BHN.M.mseed
    |    |-- 2016.003.23.05.22.0000.AH.ANQ.00.BHZ.M.mseed
    |    `-- ...
    |--- 20160105140322
    |    |-- 2016.005.14.03.22.0000.AH.ANQ.00.BHE.M.mseed
    |    |-- 2016.005.14.03.22.0000.AH.ANQ.00.BHN.M.mseed
    |    |-- 2016.005.14.03.22.0000.AH.ANQ.00.BHZ.M.mseed
    |    `-- ...
"""
import os
import logging
from datetime import timedelta

from obspy import read, UTCDateTime, Stream
from obspy.io.sac import SACTrace
from obspy.taup import TauPyModel
from obspy.geodetics import locations2degrees

# Setup the logger
FORMAT = "[%(asctime)s]  %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Client(object):
    def __init__(self, stationinfo, mseeddir, sacdir, model='prem'):
        self.mseeddir = mseeddir
        self.sacdir = sacdir
        self.stations = self._read_stations(stationinfo)
        self.model = model

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
                st = read(fl_dr_nm0)
            except FileNotFoundError:
                logger.warning("File not exist: %s ", fl_dr_nm0)
                st = Stream()
            except Exception as e:
                logger.error("Error in reading: %s", e.strerror)
            try:
                st += read(fl_dr_nm1)
            except FileNotFoundError:
                logger.warning("File not exist: %s ", fl_dr_nm0)
            except Exception as e:
                logger.error("Error in reading: %s", e.strerror)

        # Merge data
        try:
            st.merge(fill_value=0)
        except Exception:
            logger.error("Error in merging %s", station['name'])
            return None
        # check if st contains data
        if not st:
            logger.warning("No data %s", station['name'])
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

            # 1. when change obspy trace to sac trace.
            #    SACTrace.from_obspy_trace automatically change starttime of
            #    obspy trace to be reference time of SACTrace
            #    Thus: sac_trace.b = sac_trace.o = 0.0
            # 2. Set the sac_trace.o to be event origin, and set the iztype is
            #    'io' which means the reference time is origin
            #    Here: These statements not only changed the origin time of sac
            #    and they automatically changed the b and e

            # 1.from_obspy_trace
            #   o
            #   |
            #   b----------------------e
            #   |=>   shift  <=|
            # reftime          |
            #               origin time
            #
            # 2.sac_trace.o = shift
            #   o:reset to be zero
            #   |
            #   b---------------------e
            #   |            |
            #   | refer(origin) time
            # -shift

            sac_trace.o = event["origin"] - sac_trace.reftime
            sac_trace.iztype = 'io'

            sac_trace.lcalda = True

            # SAC file location
            sac_flnm = ".".join([event["origin"].strftime("%Y.%j.%H.%M.%S"),
                                 "0000", trace.id, "M", "SAC"])
            sac_fullname = os.path.join(outdir, sac_flnm)
            sac_trace.write(sac_fullname)
        return

    def _time_determin(self, event, station=None,
                       event_determ=None, phase_determ=None):
        """
        Determin the starttime and endtime

        Parameters
        ----------

        event: dict
            Contain information of events
        station: dict
            Contain information of station
        event_dterm: dict

        """
        if event_determ:
            starttime = event['origin'] + event_determ['start_offset']
            endtime = starttime + event_determ['duration']
            return starttime, endtime

        dist = locations2degrees(event["latitude"], event["longitude"],
                                 station["stla"], station["stlo"])

        start_ref_phase = phase_determ['start_ref_phase']
        end_ref_phase = phase_determ['end_ref_phase']
        start_offset = phase_determ['start_offset']
        end_offset = phase_determ['end_offset']

        model = TauPyModel(model=self.model)
        start_arris = model.get_travel_times(source_depth_in_km=event['depth'],
                                             distance_in_degree=dist,
                                             phase_list=start_ref_phase)
        end_arris = model.get_travel_times(source_depth_in_km=event['depth'],
                                           distance_in_degree=dist,
                                           phase_list=end_ref_phase)
        # In start_arris, time are sorted from first arrival to last one
        start_arrival = [arrival.time for arrival in start_arris][0]
        end_arrival = [arrival.time for arrival in end_arris][-1]

        # determine starttime and endtime
        starttime = event['origin'] + start_arrival + start_offset
        endtime = event['origin'] + end_arrival + end_offset
        return starttime, endtime

    def get_waveform(self, event, event_determ=None, phase_determ=None):
        """
        Trim waveform from dataset of CGRM

        Parameters
        ----------
        event: dict
            Event information container
        event_determ: dict
            Determine waveform window with source time
        phase_determ: dict
            Determine waveform window with several phases

        """
        # check the destination
        eventdir = event['origin'].strftime("%Y%m%d%H%M%S")
        outdir = os.path.join(self.sacdir, eventdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir, exist_ok=True)

        if event_determ:
            starttime, endtime = self._time_determin(event=event,
                                                     event_determ=event_determ)

            dirnames = self._get_dirname(starttime, endtime)
            logger.debug("dirnames: %s", dirnames)
            # check if folders exists
            for dirname in dirnames:
                if not os.path.exists(os.path.join(self.mseeddir, dirname)):
                    msg = "{} not exist".format(dirname)
                    logger.error(msg)
                    return

        # loop over all stations
        for station in self.stations:
            if not event_determ:
                starttime, endtime = self._time_determin(event=event,
                                                         station=station,
                                                         phase_determ=phase_determ)

                dirnames = self._get_dirname(starttime, endtime)
                logger.debug("dirnames: %s", dirnames)
                # check if folders exists
                for dirname in dirnames:
                    if not os.path.exists(os.path.join(self.mseeddir, dirname)):
                        msg = "{} not exist".format(dirname)
                        logger.error(msg)
                        return

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
                    sacdir="SAC",
                    model="prem")

    events = read_catalog("events.csv")
    for event in events:
        logger.info("origin: %s", event['origin'])
        event_determ = {"start_offset": 0, "duration": 6000}
        phase_determ = {
            "start_ref_phase": ['P', 'pP'],
            "start_offset": -100,
            "end_ref_phase": ['PcP'],
            "end_offset": 200
        }
        client.get_waveform(event, event_determ=event_determ)
